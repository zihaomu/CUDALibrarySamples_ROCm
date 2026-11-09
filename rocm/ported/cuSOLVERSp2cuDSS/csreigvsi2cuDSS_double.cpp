/*
 * SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


#include "hip/hip_runtime.h"
#include <hipblas.h>
#include <hipsparse.h>

using ordinal_type = int;

#include "cudss.h"
#include "utils.hpp"


static void normalize_vector(hipblasHandle_t cublasH, int m, double *d_x) {
  double norm = 0.0;
  CUBLAS_CHECK(hipblasDnrm2(cublasH, m, d_x, 1, &norm));
  if (norm != 0.0) {
    const double alpha = 1.0 / norm;
    CUBLAS_CHECK(hipblasDscal(cublasH, m, &alpha, d_x, 1));
  }
}

/// Creates CSR of B, where B = A - mu * I.
static void shift_diagonal(hipsparseIndexBase_t base,
  std::vector<int> &csrRowPtrA,
  std::vector<int> &csrColIndA, std::vector<double> &csrValA,
  double mu,
  std::vector<int> &csrRowPtrB, std::vector<int> &csrColIndB,
  std::vector<double> &csrValB, int &nnzB) {
  int nnzA = csrValA.size();
  int m = csrRowPtrA.size()-1;

  int offset = (base == HIPSPARSE_INDEX_BASE_ZERO) ? 0 : 1;

  // Compute how much fill-in is created by applying the shift.
  int fill = csrRowPtrA.size()-1;
  int j = 0;
  for (int row = 0; row < csrRowPtrA.size()-1; row++) {
    int nz = csrRowPtrA[row+1]-csrRowPtrA[row];
    for (int idx = 0; idx < nz; idx++) {
      int col = csrColIndA[j];
      if (row + offset == col) {
        fill--;
      }
      j++;
    }
  }

  // Resize.
  nnzB = nnzA + fill;
  csrRowPtrB.resize(csrRowPtrA.size());
  csrColIndB.resize(nnzB);
  csrValB.resize(nnzB);

  // Convert to matrix market format and apply shift to diagonal.
  using ijx_type = coo_t<double>;
  std::vector<ijx_type> mmA;
  csr_to_coo<double>(m, nnzA, csrRowPtrA, csrColIndA, csrValA, mmA);
  for (int i = 0; i < m; i++) {
    mmA.push_back(ijx_type(i+offset, i+offset, -mu));
  }
  std::sort(mmA.begin(), mmA.end(), std::less<ijx_type>());

  // Convert B.
  coo_to_csr(m, nnzB, mmA, csrRowPtrB, csrColIndB, csrValB, offset == 0);
}

static void approximate_eigenpair_cudss(
  hipsparseIndexBase_t base,
  const int m, const int nnzA,
  int *d_csrRowPtrA, int *d_csrColIndA, double *d_csrValA, // CSR of A
  double mu0, double *d_x0,                                // initial guess
  int maxite, double tol,                                  // stopping criteria
  double *d_mu, double *d_x,                               // on exit, the computed eigenpair
  hipStream_t stream) {
  double one = 1.0;
  double zero = 0.0;
  constexpr hipDataType dtype = HIP_R_64F;

  double mu = mu0;

  // Init cuBlas (norm computation).
  hipblasHandle_t cublasH = nullptr;
  CUBLAS_CHECK(hipblasCreate(&cublasH));

  // Init cuSparse (sparse matrix-vector multiplication).
  hipsparseHandle_t cusparseH = nullptr;
  CUSPARSE_CHECK(hipsparseCreate(&cusparseH));

  // Initialize cuDSS.
  cudssHandle_t cudss = nullptr;
  cudssConfig_t config = nullptr;
  cudssData_t data = nullptr;
  CUDSS_CHECK(cudssCreate(&cudss));
  CUDSS_CHECK(cudssConfigCreate(&config));
  CUDSS_CHECK(cudssDataCreate(cudss, &data));

  // Host copy of A.
  std::vector<int> csrRowPtrA(m+1);
  std::vector<int> csrColIndA(nnzA);
  std::vector<double> csrValA(nnzA);

  //
  // CSR of B := A - mu0 * I
  // Initialization is deferred until fill-in is determined.
  //
  int nnzB = -1;
  std::vector<int> csrRowPtrB;
  std::vector<int> csrColIndB;
  std::vector<double> csrValB;
  // Device copies.
  int *d_csrRowPtrB = nullptr;
  int *d_csrColIndB = nullptr;
  double *d_csrValB = nullptr;

  //
  // Prepare computation of y = A * x through cusparseSpMV.
  //
  hipsparseConstSpMatDescr_t matA;
  hipsparseDnVecDescr_t vecX, vecY;
  double *d_y = nullptr;
  double *d_buffer = nullptr;
  size_t bufferSize = 0;
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_y), sizeof(double)*m));
  CUSPARSE_CHECK(hipsparseCreateConstCsr(&matA, m, m, nnzA,
    d_csrRowPtrA, d_csrColIndA, d_csrValA, HIPSPARSE_INDEX_32I,
    HIPSPARSE_INDEX_32I, base, dtype));
  CUSPARSE_CHECK(hipsparseCreateDnVec(&vecX, m, d_x, dtype));
  CUSPARSE_CHECK(hipsparseCreateDnVec(&vecY, m, d_y, dtype));
  CUSPARSE_CHECK(hipsparseSpMV_bufferSize(
    cusparseH, HIPSPARSE_OPERATION_NON_TRANSPOSE, &one, matA, vecX,
    &zero, vecY, dtype, HIPSPARSE_SPMV_ALG_DEFAULT, &bufferSize));
  CUDA_CHECK(hipMalloc(&d_buffer, bufferSize));
  CUSPARSE_CHECK(hipsparseSpMV_preprocess(
    cusparseH, HIPSPARSE_OPERATION_NON_TRANSPOSE, &one, matA, vecX,
    &zero, vecY, dtype, HIPSPARSE_SPMV_ALG_DEFAULT, d_buffer));

  //
  // Preprocessing Step 1: Form B := (A - mu0 * I).
  //
  CUDA_CHECK(hipMemcpyAsync(csrValA.data(), d_csrValA, sizeof(double)*nnzA,
             hipMemcpyDeviceToHost, stream));
  CUDA_CHECK(hipMemcpyAsync(csrColIndA.data(), d_csrColIndA, sizeof(int)*nnzA,
             hipMemcpyDeviceToHost, stream));
  CUDA_CHECK(hipMemcpyAsync(csrRowPtrA.data(), d_csrRowPtrA, sizeof(int)*(m+1),
             hipMemcpyDeviceToHost, stream));
  shift_diagonal(base, csrRowPtrA, csrColIndA, csrValA, mu0,
                 csrRowPtrB, csrColIndB, csrValB, nnzB);

  //
  // Preprocessing Step 2: The initial vector must have unit norm.
  //
  normalize_vector(cublasH, m, d_x0);

  //
  // Preprocessing Step 3: Transfer host data to device
  //
  // Allocate on device.
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrValB), sizeof(double)*nnzB));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrColIndB), sizeof(int)*nnzB));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrRowPtrB), sizeof(int)*(m+1)));

  // Copy B and x0 to device.
  CUDA_CHECK(hipMemcpyAsync(d_csrValB, csrValB.data(), sizeof(double)*nnzB,
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipMemcpyAsync(d_csrColIndB, csrColIndB.data(), sizeof(int)*nnzB,
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipMemcpyAsync(d_csrRowPtrB, csrRowPtrB.data(), sizeof(int)*(m+1),
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipStreamSynchronize(stream));

  //
  // Step 1: Compute LU factorization of B := A - mu0*I.
  //

  // Create matrix objects.
  cudssMatrix_t obj_B, obj_x, obj_x0;
  cudssIndexBase_t indexBase = (base == HIPSPARSE_INDEX_BASE_ZERO) ? 
    CUDSS_BASE_ZERO : CUDSS_BASE_ONE;
  CUDSS_CHECK(cudssMatrixCreateCsr(&obj_B, m, m, nnzB, d_csrRowPtrB, nullptr,
                                   d_csrColIndB, d_csrValB, HIP_R_32I, HIP_R_32I,
                                   dtype, CUDSS_MTYPE_GENERAL, CUDSS_MVIEW_FULL,
                                   indexBase));
  CUDSS_CHECK(cudssMatrixCreateDn(&obj_x, m, 1, m, d_x, dtype, CUDSS_LAYOUT_COL_MAJOR));
  CUDSS_CHECK(cudssMatrixCreateDn(&obj_x0, m, 1, m, d_x0, dtype, CUDSS_LAYOUT_COL_MAJOR));

  // Analyze
  CUDSS_CHECK(cudssExecute(cudss, CUDSS_PHASE_ANALYSIS, config, data, obj_B, obj_x, obj_x0));

  // Factorize
  CUDSS_CHECK(cudssExecute(cudss, CUDSS_PHASE_FACTORIZATION, config, data, obj_B, obj_x, obj_x0));

  //
  // Step 2: Inverse iteration
  //
  bool converged = false;
  int iter = 0;
  while(!converged && iter++ < maxite) {
    // Solve B * x = x0 for x using the LU factorization of B computed before.
    CUDSS_CHECK(cudssExecute(cudss, CUDSS_PHASE_SOLVE, config, data, obj_B, obj_x, obj_x0));
    CUDA_CHECK(hipStreamSynchronize(stream));

    // Normalize x := x / ||x||_2.
    normalize_vector(cublasH, m, d_x);

    // Compute y = A * x.
    CUSPARSE_CHECK(hipsparseSpMV(cusparseH, HIPSPARSE_OPERATION_NON_TRANSPOSE,
      &one, matA, vecX, &zero, vecY, dtype, HIPSPARSE_SPMV_ALG_DEFAULT, d_buffer));

    // Approximate eigenvalue mu = x**T * (A * x) = x**T * y.
    CUBLAS_CHECK(hipblasDdot(cublasH, m, d_x, 1, d_y, 1, &mu));

    // Compute norm of residual |A*x - mu*x| = |y - mu*x| for convergence check.
    double norm = 0.0;
    double neg_mu = -mu;
    CUBLAS_CHECK(hipblasDaxpy(cublasH, m, &neg_mu, d_x, 1, d_y, 1));
    CUBLAS_CHECK(hipblasDnrm2(cublasH, m, d_y, 1, &norm));
    converged = norm < tol;

    // Use current eigenvector as the right-hand side in the next iteration.
    CUDA_CHECK(hipMemcpyAsync(d_x0, d_x, m * sizeof(double), hipMemcpyDeviceToDevice, stream));
    CUDA_CHECK(hipStreamSynchronize(stream));
  }

  // Copy mu to d_mu.
  CUDA_CHECK(hipMemcpyAsync(d_mu, &mu, sizeof(double),hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipStreamSynchronize(stream));

  // Free resources
  CUDSS_CHECK(cudssMatrixDestroy(obj_B));
  CUDSS_CHECK(cudssMatrixDestroy(obj_x0));
  CUDSS_CHECK(cudssMatrixDestroy(obj_x));
  CUDA_CHECK(hipFree(d_csrRowPtrB));
  CUDA_CHECK(hipFree(d_csrColIndB));
  CUDA_CHECK(hipFree(d_csrValB));
  CUDA_CHECK(hipFree(d_y));
  CUBLAS_CHECK(hipblasDestroy(cublasH));
  CUSPARSE_CHECK(hipsparseDestroyDnVec(vecX));
  CUSPARSE_CHECK(hipsparseDestroyDnVec(vecY));
  CUSPARSE_CHECK(hipsparseDestroySpMat(matA));
  CUSPARSE_CHECK(hipsparseDestroy(cusparseH));
  CUDSS_CHECK(cudssDataDestroy(cudss, data));
  CUDSS_CHECK(cudssConfigDestroy(config));
  CUDSS_CHECK(cudssDestroy(cudss));
}

void set_zero(int m, double *d_x, double *d_mu) {
  CUDA_CHECK(hipMemset(d_x, 0, sizeof(double)*m));
  CUDA_CHECK(hipMemset(d_mu, 0, sizeof(double)));
}

void copy_eigenpair_to_host(
  int m, const double *d_mu, const double *d_x,
  void *h_mu, void *h_x) {
  CUDA_CHECK(hipMemcpy(h_mu, d_mu, sizeof(double), hipMemcpyDeviceToHost));
  CUDA_CHECK(hipMemcpy(h_x, d_x, m*sizeof(double), hipMemcpyDeviceToHost));
}

void approximate_eigenpair_cusolversp(
  hipsparseIndexBase_t base,
  const int m, const int nnzA,
  int *d_csrRowPtrA, int *d_csrColIndA, double *d_csrValA, // CSR of A
  double mu0, double *d_x0,                                // initial guess
  int maxite, double tol,                                  // stopping criteria
  double *d_mu, double *d_x,                               // on exit, the computed eigenpair
  hipStream_t stream) {
  hipsolverSpHandle_t cusolverspH = nullptr;
  CUSOLVER_CHECK(hipsolverSpCreate(&cusolverspH));

  // Set up A.
  hipsparseMatDescr_t descrA = nullptr;
  CUSPARSE_CHECK(hipsparseCreateMatDescr(&descrA));
  CUSPARSE_CHECK(hipsparseSetMatType(descrA, HIPSPARSE_MATRIX_TYPE_GENERAL));
  CUSPARSE_CHECK(hipsparseSetMatIndexBase(descrA, base));

  // Compute eigenpair.
  CUSOLVER_CHECK(cusolverSpDcsreigvsi(cusolverspH, m, nnzA, descrA,
    d_csrValA, d_csrRowPtrA, d_csrColIndA,
    mu0, d_x0, maxite, tol, d_mu, d_x));

  CUSPARSE_CHECK(hipsparseDestroyMatDescr(descrA));
  CUSOLVER_CHECK(hipsolverSpDestroy(cusolverspH));
}


int main(int argc, char *argv[]) {
  hipStream_t stream = nullptr;
  CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));

  /*
   *      | 1   2   0   0 |
   *  A = | 2   0   3   0 |
   *      | 0   3   5   6 |
   *      | 0   0   6   0 |
   *  CSR of A is 0-based
   *
   *  Since cusolverSpDcsreigvsi only supports general matrices,
   *  the symmetry of A is not exploited.
   */
  const int m = 4;
  const int nnzA = 8;
  std::vector<int> csrRowPtrA = {0, 2, 4, 7, 8};
  std::vector<int> csrColIndA = {0, 1, 0, 2, 1, 2, 3, 2};
  std::vector<double> csrValA = {1.0, 2.0, 2.0, 3.0, 3.0, 5.0, 6.0, 6.0};
  hipsparseIndexBase_t base = HIPSPARSE_INDEX_BASE_ZERO;

  //
  // Device copies.
  //
  int *d_csrRowPtrA = nullptr;
  int *d_csrColIndA = nullptr;
  double *d_csrValA = nullptr;

  //
  // Allocate on device.
  //
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrValA), sizeof(double)*nnzA));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrColIndA), sizeof(int)*nnzA));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrRowPtrA), sizeof(int)*(m+1)));

  //
  // Copy A to device.
  //
  CUDA_CHECK(hipMemcpyAsync(d_csrValA, csrValA.data(), sizeof(double)*nnzA,
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipMemcpyAsync(d_csrColIndA, csrColIndA.data(), sizeof(int)*nnzA,
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipMemcpyAsync(d_csrRowPtrA, csrRowPtrA.data(), sizeof(int)*(m+1),
                             hipMemcpyHostToDevice, stream));

  //
  // Stopping conditions.
  //
  int maxite = 10;   // maximum number of iterations
  double tol = 1e-6; // convergence tolerance - must not be less than |mu0|*eps


  //
  // Host copy of the initial guess (mu0, x0)
  // and the eigenpair (mu, x) that will be computed.
  //
  // The initial guess mu0 must be chosen such (A - mu0*I) is not singular.
  //
  double mu0 = -5.0, mu;
  std::vector<double> x0(m), x(m);
  randomize_vector(m, x0); // x0 must not be the zero vector

  //
  // Device copies.
  //
  double *d_x0 = nullptr;
  double *d_mu = nullptr;
  double *d_x = nullptr;

  //
  // Allocate on device and copy x0 to device.
  //
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_x0), sizeof(double)*m));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_x), sizeof(double)*m));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_mu), sizeof(double)));
  CUDA_CHECK(hipMemcpyAsync(d_x0, x0.data(), sizeof(double)*m,
                             hipMemcpyHostToDevice, stream));

  //
  // Solve A*x = lambda*x with cusolverSpDcsreigvsi
  //
  std::cout << "Compute eigenpair with cusolverSp\n";
  approximate_eigenpair_cusolversp(base, m, nnzA,
    d_csrRowPtrA, d_csrColIndA, d_csrValA,
    mu0, d_x0, maxite, tol, d_mu, d_x, stream);
  copy_eigenpair_to_host(m, d_mu, d_x, &mu, x.data());
  std::cout << "computed eigenvalue mu=" << mu << " and eigenvector x\n";
  show_vector("x", m, x);

  // Reset x and mu before solving with cuDSS.
  set_zero(m, d_x, d_mu);

  //
  // Find an eigenpair (mu, x) satisfying A*x = mu*x with cuDSS
  //
  std::cout << "Compute eigenpair with cuDSS\n";
  approximate_eigenpair_cudss(base, m, nnzA, d_csrRowPtrA, d_csrColIndA, d_csrValA,
    mu0, d_x0, maxite, tol, d_mu, d_x, stream);
  copy_eigenpair_to_host(m, d_mu, d_x, &mu, x.data());
  std::cout << "computed eigenvalue mu=" << mu << " and eigenvector x\n";
  show_vector("x", m, x);

  //
  // Free resources
  //
  CUDA_CHECK(hipFree(d_x0));
  CUDA_CHECK(hipFree(d_x));
  CUDA_CHECK(hipFree(d_mu));

  CUDA_CHECK(hipFree(d_csrRowPtrA));
  CUDA_CHECK(hipFree(d_csrColIndA));
  CUDA_CHECK(hipFree(d_csrValA));
  CUDA_CHECK(hipStreamDestroy(stream));
  CUDA_CHECK(hipDeviceReset());

  return EXIT_SUCCESS;
}