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
#include <iostream>
#include <vector>
#include <random>
#include <cmath>

#include <hipblas.h>
#include <hipsolver.h>
#include <hip/hip_complex.h>

using ordinal_type = int;

#include "cudss.h"
#include "utils.hpp"

/// Creates CSR of B := A - shift*I assuming that A and B have
/// identical sparsity pattern.
static void apply_shift(const int m,
  const std::vector<hipDoubleComplex> &h_csrValA,
  std::vector<hipDoubleComplex> &h_csrValB,
  const std::vector<int> &diag_pos,
  const hipDoubleComplex shift) {
  std::copy(h_csrValA.begin(), h_csrValA.end(), h_csrValB.begin());

  // Apply shift to diagonal entries: B(i,i) := A(i,i) - shift
  for (int i = 0; i < m; i++) {
    h_csrValB[diag_pos[i]] = hipCsub(h_csrValB[diag_pos[i]], shift);
  }
}

/// Sets A := I (identity matrix).
static void eye(hipblasHandle_t handle, int m, hipDoubleComplex *A, int lda) {
  CUDA_CHECK(hipMemset(A, 0, lda * m * sizeof(hipDoubleComplex)));
  std::vector<hipDoubleComplex> h_ones(m, make_hipDoubleComplex(1.0, 0.0));
  hipDoubleComplex *d_ones = nullptr;
  size_t size_ones = m * sizeof(hipDoubleComplex);
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_ones), size_ones));
  CUDA_CHECK(hipMemcpy(d_ones, h_ones.data(), size_ones, hipMemcpyHostToDevice));
  CUBLAS_CHECK(hipblasZcopy(handle, m, d_ones, 1, A, lda + 1));
  CUDA_CHECK(hipFree(d_ones));
}

/// On exit, diag_pos[i] holds the index to the i-th diagonal
/// entry in the CSR values array.
static void find_diagonal_positions(
    const int m,
    const std::vector<int> &h_csrRowPtrA,
    const std::vector<int> &h_csrColIndA,
    std::vector<int> &diag_pos) {

  // Find indices where the diagonal entries are located.
  for (int i = 0; i < m; i++) {
    diag_pos[i] = -1;
    for (int j = h_csrRowPtrA[i]; j < h_csrRowPtrA[i+1]; j++) {
      if (h_csrColIndA[j] == i) {
        diag_pos[i] = j;
        break;
      }
    }
    if (diag_pos[i] == -1) {
      throw std::runtime_error("Error: Diagonal entry not found for row " + std::to_string(i));
    }
  }
}

/// Creates N equispaced points between start and end.
/// On exit, x contains N+1 points from start to end.
static void linspace(double start, double end, int N, std::vector<double> &x) {
  const double h = (end - start) / (double)N;
  for (int i = 0; i <= N; i++) {
    x[i] = start + i * h;
  }
}

/// Places quadrature points on the rectangular contour.
/// The contour goes from left_bottom_corner to right_upper_corner.
/// Nh is the number of horizontal points, Nv is the number of vertical points.
/// Total number of quadrature points is 2 * (Nh + Nv).
/// On exit, z contains the quadrature points.
static void place_quadrature_points(
    hipDoubleComplex left_bottom_corner,
    hipDoubleComplex right_upper_corner,
    int Nh,
    int Nv,
    std::vector<hipDoubleComplex> &z) {
  // Extract the corners of the box
  //
  //     (a1,b2) --------- (a2, b2)
  //        |                 |
  //     (a1,b1) --------- (a2, b1)
  //
  // where left_bottom_corner = (a1 + j*b1), and
  //       right_upper_corner = (a2 + j*b2)
  //
  const double a1 = left_bottom_corner.x;
  const double b1 = left_bottom_corner.y;
  const double a2 = right_upper_corner.x;
  const double b2 = right_upper_corner.y;

  std::vector<double> x(Nh + 1);
  std::vector<double> y(Nv + 1);
  linspace(a1, a2, Nh, x);
  linspace(b1, b2, Nv, y);

  // Quadrature points along (a1,b1) -> (a2,b1)
  for (int j = 0; j <= Nh; j++) {
    z[j] = make_hipDoubleComplex(x[j], b1);
  }

  // Quadrature points along (a2,b1) -> (a2,b2).
  for (int j = 1; j <= Nv; j++) {
    z[Nh + 1 + j - 1] = make_hipDoubleComplex(a2, y[j]);
  }

  // Quadrature points along (a2,b2) -> (a1,b2).
  for (int j = 1; j <= Nh; j++) {
    z[Nh + 1 + Nv + j - 1] = make_hipDoubleComplex(x[Nh - j], b2);
  }

  // Quadrature points along (a1,b2) -> (a1,b1).
  for (int j = 1; j < Nv; j++) {
    z[Nh + 1 + Nv + Nh + j - 1] = make_hipDoubleComplex(a1, y[Nv - j]);
  }
}

/// Returns the sum of the diagonal entries of the dense m-by-m matrix d_X.
static hipDoubleComplex compute_trace(
  hipblasHandle_t cublasH,
  const int m, const hipDoubleComplex *d_X,
  hipDoubleComplex *d_diagX, std::vector<hipDoubleComplex> &h_diagX) {
  // Copy the diagonal of the X to the host.
  CUBLAS_CHECK(hipblasZcopy(cublasH, m, d_X, m + 1, d_diagX, 1));
  CUDA_CHECK(hipMemcpy(h_diagX.data(), d_diagX, m * sizeof(hipDoubleComplex),
                        hipMemcpyDeviceToHost));
  // Sum the entries.
  hipDoubleComplex trace = make_hipDoubleComplex(0.0, 0.0);
  for (int j = 0; j < m; j++) {
    trace = hipCadd(trace, h_diagX[j]);
  }
  return trace;
}


static void approximate_eigenvalue_count_cudss(
  hipsparseIndexBase_t base,
  const int m, const int nnzA,
  int *d_csrRowPtrA, int *d_csrColIndA, hipDoubleComplex *d_csrValA,       // CSR of A
  hipDoubleComplex left_bottom_corner, hipDoubleComplex right_upper_corner, // box
  int *num_eigs) {                                                        // on exit, the number
                                                                          // of eigenvalues
  // Create cuBLAS handle.
  hipblasHandle_t cublasH = nullptr;
  CUBLAS_CHECK(hipblasCreate(&cublasH));

  // Initialize cuDSS.
  cudssHandle_t cudss = nullptr;
  cudssConfig_t config = nullptr;
  cudssData_t data = nullptr;
  CUDSS_CHECK(cudssCreate(&cudss));
  CUDSS_CHECK(cudssConfigCreate(&config));
  CUDSS_CHECK(cudssDataCreate(cudss, &data));

  // Configure cuDSS to use CUDSS_REORDERING_ALG_BTF_COLAMD for robustness. Alternatively,
  // CUDSS_REORDERING_ALG_DEFAULT yields a faster, but maybe less accurate
  // computation.
  cudssReorderingAlg_t reordering_alg = CUDSS_REORDERING_ALG_BTF_COLAMD;
  CUDSS_CHECK(cudssConfigSet(config, CUDSS_CONFIG_REORDERING_ALG,
    &reordering_alg, sizeof(cudssReorderingAlg_t)));

  // Set data type and index base.
  constexpr hipDataType dtype = HIP_C_64F;
  cudssIndexBase_t indexBase = (base == HIPSPARSE_INDEX_BASE_ZERO) ?
    CUDSS_BASE_ZERO : CUDSS_BASE_ONE;

  // Host copy of A.
  std::vector<int> h_csrRowPtrA(m + 1);
  std::vector<int> h_csrColIndA(nnzA);
  std::vector<hipDoubleComplex> h_csrValA(nnzA);
  CUDA_CHECK(hipMemcpy(h_csrRowPtrA.data(), d_csrRowPtrA,
    (m + 1) * sizeof(int), hipMemcpyDeviceToHost));
  CUDA_CHECK(hipMemcpy(h_csrColIndA.data(), d_csrColIndA,
    nnzA * sizeof(int), hipMemcpyDeviceToHost));
  CUDA_CHECK(hipMemcpy(h_csrValA.data(), d_csrValA,
    nnzA * sizeof(hipDoubleComplex), hipMemcpyDeviceToHost));

  //
  // Step 1: Place the quadrature points on the contour.
  //
  // More points can increase the resolution.
  const int Nh = 100;
  const int Nv = 100;
  int N = 2 * (Nh + Nv); // total number of quadrature points
  std::vector<hipDoubleComplex> z(N); // the quadrature points
  place_quadrature_points(left_bottom_corner, right_upper_corner, Nh, Nv, z);

  //
  // Step 2: Prepare the computation of B_k := A - z[k]*I
  //         by finding the positions of the diagonal entries of A.
  //         Recall that we assume that all diagonal entries
  //         of A are non-zero.
  //
  int nnzB = nnzA; // assume that A has non-zeros on the diagonal
  std::vector<hipDoubleComplex> h_csrValB(nnzB);
  std::vector<int> diag_pos(m);
  find_diagonal_positions(m, h_csrRowPtrA, h_csrColIndA, diag_pos);

  //
  // Step 3: Compute the symbolic factorization of B_k := A - z[k]*I.
  //         The symbolic factorization is shared across all k.
  //
  cudssMatrix_t obj_B, obj_X, obj_I;
  CUDSS_CHECK(cudssMatrixCreateCsr(&obj_B, m, m, nnzA, d_csrRowPtrA, nullptr,
                                   d_csrColIndA, d_csrValA, HIP_R_32I, HIP_R_32I,
                                   dtype, CUDSS_MTYPE_GENERAL, CUDSS_MVIEW_FULL,
                                   indexBase));
  // Create right-hand side matrix as the identity matrix.
  hipDoubleComplex *d_I = nullptr;
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_I),
    m * m * sizeof(hipDoubleComplex)));
  eye(cublasH, m, d_I, m);
  CUDSS_CHECK(cudssMatrixCreateDn(&obj_I, m, m, m, d_I, dtype,
                                  CUDSS_LAYOUT_COL_MAJOR));
  // Create solution matrix.
  hipDoubleComplex *d_X = nullptr;
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_X),
    m * m * sizeof(hipDoubleComplex)));
  CUDSS_CHECK(cudssMatrixCreateDn(&obj_X, m, m, m, d_X, dtype,
                                  CUDSS_LAYOUT_COL_MAJOR));
  // Analyze.
  CUDSS_CHECK(cudssExecute(cudss, CUDSS_PHASE_ANALYSIS, config, data,
                           obj_B, obj_X, obj_I));

  //
  // Step 4: Evaluate the integrand on every quadrature point.
  //
  std::vector<hipDoubleComplex> h_integrandValues(N);

  // Allocate device and host workspace for diagonal entries of solution X.
  hipDoubleComplex *d_diagX = nullptr;
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_diagX), m * sizeof(hipDoubleComplex)));
  std::vector<hipDoubleComplex> h_diagX(m);

  for (int k = 0; k < N; k++) {
    // Form B_k := A - z[k]*I. Since we assume that A has non-zeros on
    // the diagonal, we can apply the shift to the diagonal entries
    // directly and do not have to address any fill-in.
    apply_shift(m, h_csrValA, h_csrValB, diag_pos, z[k]);
    CUDA_CHECK(hipMemcpy(d_csrValA, h_csrValB.data(),
                          nnzA * sizeof(hipDoubleComplex),
                          hipMemcpyHostToDevice));

    // Factorize B_k := A - z[k]*I.
    // Alternatively, instead of computing a new factorization for
    // every point, refactorizations can be used for a faster computation,
    // though potentially at the expense of some accuracy. The impact on the
    // accuracy depends on the data and the quadrature points on the box.
    CUDSS_CHECK(cudssExecute(cudss, CUDSS_PHASE_FACTORIZATION, config, data,
                             obj_B, obj_X, obj_I));

    // Solve B_k * X = I for X using the computed factorization of B_k.
    // If successful, X = inv(B_k).
    CUDSS_CHECK(cudssExecute(cudss, CUDSS_PHASE_SOLVE, config, data,
                             obj_B, obj_X, obj_I));

    // Compute -trace(X).
    hipDoubleComplex trace = compute_trace(cublasH, m, d_X, d_diagX, h_diagX);
    h_integrandValues[k] = hipCmul(trace, make_hipDoubleComplex(-1.0, 0.0));
  }

  //
  // Step 5: Compute the integral using the trapezoidal rule.
  //         ∫f(z)dz ≈ (f(z[k]) + f(z[k+1]))/2 * (z[k+1] - z[k]).
  //
  hipDoubleComplex integral = make_hipDoubleComplex(0.0, 0.0);
  for (int k = 0; k < N-1; k++) {
    hipDoubleComplex avg = hipCadd(h_integrandValues[k], h_integrandValues[k+1]);
    avg = hipCmul(avg, make_hipDoubleComplex(0.5, 0.0));
    hipDoubleComplex dz = hipCsub(z[k+1], z[k]);
    integral = hipCadd(integral, hipCmul(avg, dz));
   }
  // Handle wraparound for closed contour.
  hipDoubleComplex avg = hipCadd(h_integrandValues[N-1], h_integrandValues[0]);
  avg = hipCmul(avg, make_hipDoubleComplex(0.5, 0.0));
  hipDoubleComplex dz = hipCsub(z[N-1], z[0]);
  integral = hipCadd(integral, hipCmul(avg, dz));

  // Number of eigenvalues = 1/(2*pi*i) * integral.
  *num_eigs = (int)round(integral.y / (2.0 * M_PI));

  // Free resources.
  CUDA_CHECK(hipFree(d_diagX));
  CUDA_CHECK(hipFree(d_I));
  CUDA_CHECK(hipFree(d_X));
  CUDSS_CHECK(cudssMatrixDestroy(obj_I));
  CUDSS_CHECK(cudssMatrixDestroy(obj_B));
  CUDSS_CHECK(cudssMatrixDestroy(obj_X));
  CUDSS_CHECK(cudssDataDestroy(cudss, data));
  CUDSS_CHECK(cudssConfigDestroy(config));
  CUDSS_CHECK(cudssDestroy(cudss));
  CUBLAS_CHECK(hipblasDestroy(cublasH));
}


int main(int argc, char *argv[]) {
  hipStream_t stream = nullptr;
  CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));

  /*
   * A = |  1+i   1+i    0      0   |
   *     |   0    1-2i  -1-i    0   |
   *     |   0     0     1-2i  1-i  |
   *     | -2+2i   0      0     i   |
   * CSR of A is 0-based
   *
   * To keep the transition example short, A has nonzero
   * diagonal entries. If this is not the case, fill-in is created
   * when forming B := A - z*I. In this case, the CSR of B
   * can be constructed by either using the routine shift_diagonal
   * in csreigvsi2cuDSS_double.cpp or by adding explicit zero values
   * on the diagonal entries to the CSR of A.
   */
  const int m = 4;
  const int nnzA = 8;
  std::vector<int> csrRowPtrA = {0, 2, 4, 6, 8};
  std::vector<int> csrColIndA = {0, 1, 1, 2, 2, 3, 0, 3};
  std::vector<hipDoubleComplex> csrValA = { {1.0, 1.0}, {1.0, 1.0},
    {1.0, -2.0}, {-1.0, -1.0}, {1.0, -2.0}, {1.0, -1.0}, {-2.0, 2.0}, {0.0, 1.0} };
  hipsparseIndexBase_t base = HIPSPARSE_INDEX_BASE_ZERO;

  //
  // Device copies.
  //
  int *d_csrRowPtrA = nullptr;
  int *d_csrColIndA = nullptr;
  hipDoubleComplex *d_csrValA = nullptr;

  //
  // Allocate on device.
  //
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrValA), sizeof(hipDoubleComplex)*nnzA));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrColIndA), sizeof(int)*nnzA));
  CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_csrRowPtrA), sizeof(int)*(m+1)));

  //
  // Copy A to device.
  //
  CUDA_CHECK(hipMemcpyAsync(d_csrValA, csrValA.data(), sizeof(hipDoubleComplex)*nnzA,
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipMemcpyAsync(d_csrColIndA, csrColIndA.data(), sizeof(int)*nnzA,
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipMemcpyAsync(d_csrRowPtrA, csrRowPtrA.data(), sizeof(int)*(m+1),
                             hipMemcpyHostToDevice, stream));
  CUDA_CHECK(hipStreamSynchronize(stream));

  //
  // Define the box in which the number of eigenvalues are counted.
  //
  hipDoubleComplex left_bottom_corner = make_hipDoubleComplex(-1.0, -3.0);
  hipDoubleComplex right_upper_corner = make_hipDoubleComplex(1.0, 1.0);
  std::cout << "Box is defined by the bottom left corner [" 
    << left_bottom_corner.x  << " + " << left_bottom_corner.y << "i] "
    << "and the top right corner [" 
    << right_upper_corner.x << " + " << right_upper_corner.y << "i] " << std::endl;
  int num_eigs = 0; // Number of eigenvalues in the box

  //
  // Approximate eigenvalue count in box using cusolverSp.
  //
  {
    hipsolverSpHandle_t cusolverH = nullptr;
    hipsparseMatDescr_t descrA = nullptr;
    CUSOLVER_CHECK(hipsolverSpCreate(&cusolverH));
    CUSPARSE_CHECK(hipsparseCreateMatDescr(&descrA));
    CUSPARSE_CHECK(hipsparseSetMatType(descrA, HIPSPARSE_MATRIX_TYPE_GENERAL));
    CUSPARSE_CHECK(hipsparseSetMatIndexBase(descrA, base));

    std::cout << "Compute eigenvalue count in box with cusolverSp\n";
    CUSOLVER_CHECK(cusolverSpZcsreigsHost(
      cusolverH, m, nnzA, descrA, csrValA.data(), csrRowPtrA.data(), csrColIndA.data(),
      left_bottom_corner, right_upper_corner, &num_eigs));
    std::cout << "Number of eigenvalues = " << num_eigs << std::endl;

    // Free resources.
    CUSPARSE_CHECK(hipsparseDestroyMatDescr(descrA));
    CUSOLVER_CHECK(hipsolverSpDestroy(cusolverH));
  }

  //
  // Approximate eigenvalue count in box using cuDSS.
  //
  {
    std::cout << "Compute eigenvalue count in box with cuDSS\n";
    approximate_eigenvalue_count_cudss(
      base, m, nnzA, d_csrRowPtrA, d_csrColIndA, d_csrValA,
      left_bottom_corner, right_upper_corner, &num_eigs);
    std::cout << "Number of eigenvalues = " << num_eigs << std::endl;
  }

  // Free resources.
  CUDA_CHECK(hipFree(d_csrRowPtrA));
  CUDA_CHECK(hipFree(d_csrColIndA));
  CUDA_CHECK(hipFree(d_csrValA));
  CUDA_CHECK(hipStreamDestroy(stream));
  CUDA_CHECK(hipDeviceReset());

  return EXIT_SUCCESS;
}