#include "observe.hpp"
#include "binary_observe.hpp"
#include <string>
#include <vector>
#include <cstdlib>
/*
 * SPDX-FileCopyrightText: Copyright (c) 1993-2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include <hipblas.h>
#include <hip/hip_runtime.h>
#include <hipsparse.h>
#include <stdio.h>  // fopen
#include <stdlib.h> // EXIT_FAILURE
#include <string.h> // strtok
#include <assert.h>

#define CHECK_CUDA(func)                                                       \
{                                                                              \
    hipError_t status = (func);                                               \
    if (status != hipSuccess) {                                               \
        printf("CUDA API failed at line %d with error: %s (%d)\n",             \
               __LINE__, hipGetErrorString(status), status);                  \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

#define CHECK_CUSPARSE(func)                                                   \
{                                                                              \
    hipsparseStatus_t status = (func);                                          \
    if (status != HIPSPARSE_STATUS_SUCCESS) {                                   \
        printf("cuSPARSE API failed at line %d with error: %s (%d)\n",         \
               __LINE__, hipsparseGetErrorString(status), status);              \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

#define CHECK_CUBLAS(func)                                                     \
{                                                                              \
    hipblasStatus_t status = (func);                                            \
    if (status != HIPBLAS_STATUS_SUCCESS) {                                     \
        printf("CUBLAS API failed at line %d with error: %d\n",                \
               __LINE__, status);                                              \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

#if defined(NDEBUG)
#   define PRINT_INFO(var)
#else
#   define PRINT_INFO(var) printf("  " #var ": %f\n", var);
#endif

typedef struct VecStruct {
    hipsparseDnVecDescr_t vec;
    double*              ptr;
} Vec;

//==============================================================================

/// A 5-point Laplacian on a g x g grid with Dirichlet boundary conditions.
/// This code allocates. The caller must free.
void make_laplace_matrix(int * n_out,
                         int **row_offsets_out, 
                         int **columns_out, 
                         double **values_out) {
    const char* mc=std::getenv("MIGRATION_CASE");
    int grid = mc && std::string(mc)=="small-varied"?23:mc && std::string(mc)=="nonzero-initial"?31:700; // grid resolution

    int n = grid * grid;
    *n_out = n;
    // vertices have 5 neighbors, 
    // but each vertex on the boundary loses 1. corners lose 2.
    int nnz = 5 * n - 4 * grid;

    printf("Creating 5-point time-dependent diffusion matrix.\n"
           " grid size: %d x %d\n"
           " matrix rows:   %d\n"
           " matrix cols:   %d\n"
           " nnz:         %d\n",
           grid, grid, n, n, nnz);

    int* row_offsets = *row_offsets_out = (int*)malloc((n + 1) * sizeof(int));
    int* columns     = *columns_out     = (int*)malloc(nnz * sizeof(int));
    double* values   = *values_out      = (double*)malloc(nnz * sizeof(double));
    assert(row_offsets);
    assert(columns);
    assert(values);

    // The Laplacian stencil looks like [-1;-1,4,-1;-1].
    // ICHOL doesn't work great with that stencil.
    // ICHOL is better suited when there's some more mass on the diagonal.
    double mass = 0.04;

    int it = 0; // next unused index into `columns`/`values`

#define INSERT(u,v, x)                    \
    if(0<=(u) && (u)<grid &&              \
       0<=(v) && (v)<grid)                \
    {                                     \
        columns[it] = ((u) * grid + (v)); \
        values[it] = x;                   \
        ++it;                             \
    }

    int row = 0;
    row_offsets[row] = 0;
    for (int i = 0; i < grid; ++i) {
        for (int j = 0; j < grid; ++j)
        {
            INSERT(i - 1, j    , -1.0);
            INSERT(i    , j - 1, -1.0);
            INSERT(i    , j    ,  4.0 + mass);
            INSERT(i    , j + 1, -1.0);
            INSERT(i + 1, j    , -1.0);
            row_offsets[++row] = it;
        }
    }
    assert(it == nnz);
#undef INSERT
}

//==============================================================================

int gpu_CG(hipblasHandle_t       cublasHandle,
           hipsparseHandle_t     cusparseHandle,
           int                  m,
           hipsparseSpMatDescr_t matA,
           hipsparseSpMatDescr_t matL,
           Vec                  d_B,
           Vec                  d_X,
           Vec                  d_R,
           Vec                  d_R_aux,
           Vec                  d_P,
           Vec                  d_T,
           Vec                  d_tmp,
           void*                d_bufferMV,
           int                  maxIterations,
           double               tolerance) {
    const double zero      = 0.0;
    const double one       = 1.0;
    const double minus_one = -1.0;
    //--------------------------------------------------------------------------
    // ### 1 ### R0 = b - A * X0 (using initial guess in X)
    //    (a) copy b in R0
    CHECK_CUDA( hipMemcpy(d_R.ptr, d_B.ptr, m * sizeof(double),
                           hipMemcpyDeviceToDevice) )
    //    (b) compute R = -A * X0 + R
    CHECK_CUSPARSE( hipsparseSpMV(cusparseHandle,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &minus_one, matA, d_X.vec, &one, d_R.vec,
                                 HIP_R_64F, HIPSPARSE_SPMV_ALG_DEFAULT,
                                 d_bufferMV) )
    //--------------------------------------------------------------------------
    // ### 2 ### R_i_aux = L^-1 L^-T R_i
    size_t              bufferSizeL, bufferSizeLT;
    void*               d_bufferL, *d_bufferLT;
    hipsparseSpSVDescr_t spsvDescrL, spsvDescrLT;
    //    (a) L^-1 tmp => R_i_aux    (triangular solver)
    CHECK_CUSPARSE( hipsparseSpSV_createDescr(&spsvDescrL) )
    CHECK_CUSPARSE( hipsparseSpSV_bufferSize(
                        cusparseHandle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                        &one, matL, d_R.vec, d_tmp.vec, HIP_R_64F,
                        HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescrL, &bufferSizeL) )
    CHECK_CUDA( hipMalloc(&d_bufferL, bufferSizeL) )
    CHECK_CUSPARSE( hipsparseSpSV_analysis(
                        cusparseHandle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                        &one, matL, d_R.vec, d_tmp.vec, HIP_R_64F,
                        HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescrL, d_bufferL) )
    CHECK_CUDA( hipMemset(d_tmp.ptr, 0x0, m * sizeof(double)) )
    CHECK_CUSPARSE( hipsparseSpSV_solve(
                        cusparseHandle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                        &one, matL, d_R.vec, d_tmp.vec, HIP_R_64F,
                        HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescrL) )

    //    (b) L^-T R_i => tmp    (triangular solver)
    CHECK_CUSPARSE( hipsparseSpSV_createDescr(&spsvDescrLT) )
    CHECK_CUSPARSE( hipsparseSpSV_bufferSize(
                        cusparseHandle, HIPSPARSE_OPERATION_TRANSPOSE,
                        &one, matL, d_tmp.vec, d_R_aux.vec, HIP_R_64F,
                        HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescrLT, &bufferSizeLT) )
    CHECK_CUDA( hipMalloc(&d_bufferLT, bufferSizeLT) )
    CHECK_CUSPARSE( hipsparseSpSV_analysis(
                        cusparseHandle, HIPSPARSE_OPERATION_TRANSPOSE,
                        &one, matL, d_tmp.vec, d_R_aux.vec, HIP_R_64F,
                        HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescrLT, d_bufferLT) )
    CHECK_CUDA( hipMemset(d_R_aux.ptr, 0x0, m * sizeof(double)) )
    CHECK_CUSPARSE( hipsparseSpSV_solve(
                        cusparseHandle, HIPSPARSE_OPERATION_TRANSPOSE,
                        &one, matL, d_tmp.vec, d_R_aux.vec, HIP_R_64F,
                        HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescrLT) )
    //--------------------------------------------------------------------------
    // ### 3 ### P0 = R0_aux
    CHECK_CUDA( hipMemcpy(d_P.ptr, d_R_aux.ptr, m * sizeof(double),
                           hipMemcpyDeviceToDevice) )
    //--------------------------------------------------------------------------
    // nrm_R0 = ||R||
    double nrm_R;
    CHECK_CUBLAS( hipblasDnrm2(cublasHandle, m, d_R.ptr, 1, &nrm_R) )
    double threshold = tolerance * nrm_R;
migration_observer::emit("initial_residual",&nrm_R,1);
migration_observer::emit("threshold",&threshold,1);
int migration_iterations=0;
    printf("  Initial Residual: Norm %e' threshold %e\n", nrm_R, threshold);
    //--------------------------------------------------------------------------
    double delta;
    CHECK_CUBLAS( hipblasDdot(cublasHandle, m, d_R.ptr, 1, d_R_aux.ptr, 1, &delta) )
    //--------------------------------------------------------------------------
    // ### 4 ### repeat until convergence based on max iterations and
    //           and relative residual
    for (int i = 0; i < maxIterations; i++) {
        ++migration_iterations;
        printf("  Iteration = %d; Error Norm = %e\n", i, nrm_R);
        //----------------------------------------------------------------------
        // ### 5 ### alpha = (R_i, R_aux_i) / (A * P_i, P_i)
        //     (a) T  = A * P_i
        CHECK_CUSPARSE( hipsparseSpMV(cusparseHandle,
                                     HIPSPARSE_OPERATION_NON_TRANSPOSE, &one,
                                     matA, d_P.vec, &zero, d_T.vec,
                                     HIP_R_64F, HIPSPARSE_SPMV_ALG_DEFAULT,
                                     d_bufferMV) )
        //     (b) denominator = (T, P_i)
        double denominator;
        CHECK_CUBLAS( hipblasDdot(cublasHandle, m, d_T.ptr, 1, d_P.ptr, 1,
                                 &denominator) )
        //     (c) alpha = delta / denominator
        double alpha = delta / denominator;
        PRINT_INFO(delta)
        PRINT_INFO(denominator)
        PRINT_INFO(alpha)
        //----------------------------------------------------------------------
        // ### 6 ###  X_i+1 = X_i + alpha * P
        //    (a) X_i+1 = -alpha * T + X_i
        CHECK_CUBLAS( hipblasDaxpy(cublasHandle, m, &alpha, d_P.ptr, 1,
                                  d_X.ptr, 1) )
        //----------------------------------------------------------------------
        // ### 7 ###  R_i+1 = R_i - alpha * (A * P)
        //    (a) R_i+1 = -alpha * T + R_i
        double minus_alpha = -alpha;
        CHECK_CUBLAS( hipblasDaxpy(cublasHandle, m, &minus_alpha, d_T.ptr, 1,
                                  d_R.ptr, 1) )
        //----------------------------------------------------------------------
        // ### 8 ###  check ||R_i+1|| < threshold
        CHECK_CUBLAS( hipblasDnrm2(cublasHandle, m, d_R.ptr, 1, &nrm_R) )
        PRINT_INFO(nrm_R)
        if (nrm_R < threshold)
            break;
        //----------------------------------------------------------------------
        // ### 9 ### R_aux_i+1 = L^-1 L^-T R_i+1
        //    (a) L^-1 R_i+1 => tmp    (triangular solver)
        CHECK_CUDA( hipMemset(d_tmp.ptr,   0x0, m * sizeof(double)) )
        CHECK_CUDA( hipMemset(d_R_aux.ptr, 0x0, m * sizeof(double)) )
        CHECK_CUSPARSE( hipsparseSpSV_solve(cusparseHandle,
                                           HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                           &one, matL, d_R.vec, d_tmp.vec,
                                           HIP_R_64F,
                                           HIPSPARSE_SPSV_ALG_DEFAULT,
                                           spsvDescrL) )
        //    (b) L^-T tmp => R_aux_i+1    (triangular solver)
        CHECK_CUSPARSE( hipsparseSpSV_solve(cusparseHandle,
                                           HIPSPARSE_OPERATION_TRANSPOSE,
                                           &one, matL, d_tmp.vec,
                                           d_R_aux.vec, HIP_R_64F,
                                           HIPSPARSE_SPSV_ALG_DEFAULT,
                                           spsvDescrLT) )
        //----------------------------------------------------------------------
        // ### 10 ### beta = (R_i+1, R_aux_i+1) / (R_i, R_aux_i)
        //    (a) delta_new => (R_i+1, R_aux_i+1)
        double delta_new;
        CHECK_CUBLAS( hipblasDdot(cublasHandle, m, d_R.ptr, 1, d_R_aux.ptr, 1,
                                 &delta_new) )
        //    (b) beta => delta_new / delta
        double beta = delta_new / delta;
        PRINT_INFO(delta_new)
        PRINT_INFO(beta)
        delta       = delta_new;
        //----------------------------------------------------------------------
        // ### 11 ###  P_i+1 = R_aux_i+1 + beta * P_i
        //    (a) P = beta * P
        CHECK_CUBLAS(hipblasDscal(cublasHandle, m, &beta, d_P.ptr, 1))
        //    (b) P = R_aux + P
        CHECK_CUBLAS(
            hipblasDaxpy(cublasHandle, m, &one, d_R_aux.ptr, 1, d_P.ptr, 1))
    }
    //--------------------------------------------------------------------------
    printf("Check Solution\n"); // ||R = b - A * X||
    //    (a) copy b in R
    CHECK_CUDA( hipMemcpy(d_R.ptr, d_B.ptr, m * sizeof(double),
                           hipMemcpyDeviceToDevice) )
    // R = -A * X + R
    CHECK_CUSPARSE( hipsparseSpMV(cusparseHandle,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE, &minus_one,
                                 matA, d_X.vec, &one, d_R.vec, HIP_R_64F,
                                 HIPSPARSE_SPMV_ALG_DEFAULT, d_bufferMV) )
    // check ||R||
    CHECK_CUBLAS( hipblasDnrm2(cublasHandle, m, d_R.ptr, 1, &nrm_R) )
    printf("Final error norm = %e\n", nrm_R);
migration_observer::emit("final_residual",&nrm_R,1);
migration_observer::emit("iterations",&migration_iterations,1);

    //--------------------------------------------------------------------------
    CHECK_CUSPARSE( hipsparseSpSV_destroyDescr(spsvDescrL) )
    CHECK_CUSPARSE( hipsparseSpSV_destroyDescr(spsvDescrLT) )
    CHECK_CUDA( hipFree(d_bufferL) )
    CHECK_CUDA( hipFree(d_bufferLT) )
    return EXIT_SUCCESS;
}

//==============================================================================
//==============================================================================

int main(int argc, char** argv) {
// MIGRATION_BATCH3: preserve original GPU mathematical calls.
const std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";

    const int    maxIterations = 10000;
    const double tolerance     = 1e-8f;
    if (argc != 1) {
        printf("Wrong number of command line arguments. cg_example accepts no arguments.\n");
        return EXIT_FAILURE;
    }
    int     base        = 0;
    int     m           = -1;
    int*    h_A_rows    = NULL;
    int*    h_A_columns = NULL;
    double* h_A_values  = NULL;
    make_laplace_matrix(&m, &h_A_rows, &h_A_columns, &h_A_values);
    int num_offsets = m + 1;
    int nnz = h_A_rows[m];
    double* h_X = (double*)malloc(m * sizeof(double));

    printf("Testing CG\n");
    for (int i = 0; i < m; i++)
        h_X[i] = migration_case=="original"?1.0:1.0+double(i%17-8)/16.0;
    //--------------------------------------------------------------------------
migration_binary::emit("input_rows.bin",h_A_rows,(m+1)*sizeof(int));
migration_binary::emit("input_columns.bin",h_A_columns,nnz*sizeof(int));
migration_binary::emit("input_values.bin",h_A_values,nnz*sizeof(double));
migration_binary::emit("input_manufactured.bin",h_X,m*sizeof(double));
migration_observer::emit("input_tolerance",&tolerance,1);
migration_observer::emit("input_max_iterations",&maxIterations,1);
    // ### Device memory management ###
    int*    d_A_rows, *d_A_columns;
    double* d_A_values, *d_L_values;
    Vec     d_B, d_X, d_R, d_R_aux, d_P, d_T, d_tmp;

    // allocate device memory for CSR matrices
    CHECK_CUDA( hipMalloc((void**) &d_A_rows,    num_offsets * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &d_A_columns, nnz * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &d_A_values,  nnz * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_L_values,  nnz * sizeof(double)) )

    CHECK_CUDA( hipMalloc((void**) &d_B.ptr,     m * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_X.ptr,     m * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_R.ptr,     m * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_R_aux.ptr, m * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_P.ptr,     m * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_T.ptr,     m * sizeof(double)) )
    CHECK_CUDA( hipMalloc((void**) &d_tmp.ptr,   m * sizeof(double)) )

    // copy the CSR matrices and vectors into device memory
    CHECK_CUDA( hipMemcpy(d_A_rows, h_A_rows, num_offsets * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(d_A_columns, h_A_columns, nnz *  sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(d_A_values, h_A_values, nnz * sizeof(double),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(d_L_values, h_A_values, nnz * sizeof(double),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(d_X.ptr, h_X, m * sizeof(double),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // ### cuSPARSE Handle and descriptors initialization ###
    // create the test matrix on the host
    hipblasHandle_t   cublasHandle   = NULL;
    hipsparseHandle_t cusparseHandle = NULL;
    CHECK_CUBLAS( hipblasCreate(&cublasHandle) )
    CHECK_CUSPARSE( hipsparseCreate(&cusparseHandle) )
    // Create dense vectors
    CHECK_CUSPARSE( hipsparseCreateDnVec(&d_B.vec,     m, d_B.ptr, HIP_R_64F) )
    CHECK_CUSPARSE( hipsparseCreateDnVec(&d_X.vec,     m, d_X.ptr, HIP_R_64F) )
    CHECK_CUSPARSE( hipsparseCreateDnVec(&d_R.vec,     m, d_R.ptr, HIP_R_64F) )
    CHECK_CUSPARSE( hipsparseCreateDnVec(&d_R_aux.vec, m, d_R_aux.ptr,
                                        HIP_R_64F) )
    CHECK_CUSPARSE( hipsparseCreateDnVec(&d_P.vec,   m, d_P.ptr,   HIP_R_64F) )
    CHECK_CUSPARSE( hipsparseCreateDnVec(&d_T.vec,   m, d_T.ptr,   HIP_R_64F) )
    CHECK_CUSPARSE( hipsparseCreateDnVec(&d_tmp.vec, m, d_tmp.ptr, HIP_R_64F) )

    hipsparseIndexBase_t  baseIdx = HIPSPARSE_INDEX_BASE_ZERO;
    hipsparseSpMatDescr_t matA, matL;
    int*                 d_L_rows      = d_A_rows;
    int*                 d_L_columns   = d_A_columns;
    hipsparseFillMode_t   fill_lower    = HIPSPARSE_FILL_MODE_LOWER;
    hipsparseDiagType_t   diag_non_unit = HIPSPARSE_DIAG_TYPE_NON_UNIT;
    // A
    CHECK_CUSPARSE( hipsparseCreateCsr(&matA, m, m, nnz, d_A_rows,
                                      d_A_columns, d_A_values,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      baseIdx, HIP_R_64F) )
    // L
    CHECK_CUSPARSE( hipsparseCreateCsr(&matL, m, m, nnz, d_L_rows,
                                      d_L_columns, d_L_values,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      baseIdx, HIP_R_64F) )
    CHECK_CUSPARSE( hipsparseSpMatSetAttribute(matL,
                                              HIPSPARSE_SPMAT_FILL_MODE,
                                              &fill_lower, sizeof(fill_lower)) )
    CHECK_CUSPARSE( hipsparseSpMatSetAttribute(matL,
                                              HIPSPARSE_SPMAT_DIAG_TYPE,
                                              &diag_non_unit,
                                              sizeof(diag_non_unit)) )
    //--------------------------------------------------------------------------
    // ### Preparation ### b = A * X
    const double alpha = 0.75;
    size_t       bufferSizeMV;
    void*        d_bufferMV;
    double       beta = 0.0;
    CHECK_CUSPARSE( hipsparseSpMV_bufferSize(
                        cusparseHandle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                        &alpha, matA, d_X.vec, &beta, d_B.vec, HIP_R_64F,
                        HIPSPARSE_SPMV_ALG_DEFAULT, &bufferSizeMV) )
    CHECK_CUDA( hipMalloc(&d_bufferMV, bufferSizeMV) )

    CHECK_CUSPARSE( hipsparseSpMV(
                        cusparseHandle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                        &alpha, matA, d_X.vec, &beta, d_B.vec, HIP_R_64F,
                        HIPSPARSE_SPMV_ALG_DEFAULT, d_bufferMV) )
    // X0 = 0
std::vector<double> migration_rhs(m),migration_initial(m,0.0);
CHECK_CUDA(hipMemcpy(migration_rhs.data(),d_B.ptr,m*sizeof(double),hipMemcpyDeviceToHost))
migration_binary::emit("generated_rhs.bin",migration_rhs.data(),m*sizeof(double));
if(const char* fixture=std::getenv("MIGRATION_INPUT_FIXTURE_DIR")){
 std::ifstream f(std::string(fixture)+"/input_rhs.bin",std::ios::binary);
 f.read(reinterpret_cast<char*>(migration_rhs.data()),m*sizeof(double));
 if(!f || f.peek()!=std::ifstream::traits_type::eof())return EXIT_FAILURE;
 CHECK_CUDA(hipMemcpy(d_B.ptr,migration_rhs.data(),m*sizeof(double),hipMemcpyHostToDevice))
}
if(migration_case=="nonzero-initial")for(int i=0;i<m;++i)migration_initial[i]=0.125+double(i%7)/64.;
CHECK_CUDA(hipMemcpy(d_X.ptr,migration_initial.data(),m*sizeof(double),hipMemcpyHostToDevice))
migration_binary::emit("input_rhs.bin",migration_rhs.data(),m*sizeof(double));
migration_binary::emit("input_initial.bin",migration_initial.data(),m*sizeof(double));

    //--------------------------------------------------------------------------
    // Perform Incomplete-Cholesky factorization of A (csric0) -> L, L^T
    hipsparseMatDescr_t descrM;
    csric02Info_t      infoM        = NULL;
    int                bufferSizeIC = 0;
    void*              d_bufferIC;
    CHECK_CUSPARSE( hipsparseCreateMatDescr(&descrM) )
    CHECK_CUSPARSE( hipsparseSetMatIndexBase(descrM, baseIdx) )
    CHECK_CUSPARSE( hipsparseSetMatType(descrM, HIPSPARSE_MATRIX_TYPE_GENERAL) )
    CHECK_CUSPARSE( hipsparseSetMatFillMode(descrM, HIPSPARSE_FILL_MODE_LOWER) )
    CHECK_CUSPARSE( hipsparseSetMatDiagType(descrM,
                                           HIPSPARSE_DIAG_TYPE_NON_UNIT) )
    CHECK_CUSPARSE( hipsparseCreateCsric02Info(&infoM) )

    CHECK_CUSPARSE( hipsparseDcsric02_bufferSize(
                        cusparseHandle, m, nnz, descrM, d_L_values,
                        d_A_rows, d_A_columns, infoM, &bufferSizeIC) )
    CHECK_CUDA( hipMalloc(&d_bufferIC, bufferSizeIC) )
    CHECK_CUSPARSE( hipsparseDcsric02_analysis(
                        cusparseHandle, m, nnz, descrM, d_L_values,
                        d_A_rows, d_A_columns, infoM,
                        HIPSPARSE_SOLVE_POLICY_NO_LEVEL, d_bufferIC) )
    int structural_zero;
    CHECK_CUSPARSE( hipsparseXcsric02_zeroPivot(cusparseHandle, infoM,
                                               &structural_zero) )
    // M = L * L^T
    CHECK_CUSPARSE( hipsparseDcsric02(
                        cusparseHandle, m, nnz, descrM, d_L_values,
                        d_A_rows, d_A_columns, infoM,
                        HIPSPARSE_SOLVE_POLICY_NO_LEVEL, d_bufferIC) )
    // Find numerical zero
    int numerical_zero;
    CHECK_CUSPARSE( hipsparseXcsric02_zeroPivot(cusparseHandle, infoM,
                                               &numerical_zero) )

    CHECK_CUSPARSE( hipsparseDestroyCsric02Info(infoM) )
    CHECK_CUSPARSE( hipsparseDestroyMatDescr(descrM) )
    CHECK_CUDA( hipFree(d_bufferIC) )
    //--------------------------------------------------------------------------
    // ### Run CG computation ###
    printf("CG loop:\n");
    if(gpu_CG(cublasHandle, cusparseHandle, m,
           matA, matL, d_B, d_X, d_R, d_R_aux, d_P, d_T,
           d_tmp, d_bufferMV, maxIterations, tolerance)!=EXIT_SUCCESS)return EXIT_FAILURE;
    //--------------------------------------------------------------------------
std::vector<double> migration_solution(m);
CHECK_CUDA(hipMemcpy(migration_solution.data(),d_X.ptr,m*sizeof(double),hipMemcpyDeviceToHost))
migration_binary::emit("solution.bin",migration_solution.data(),m*sizeof(double));
    // ### Free resources ###
    CHECK_CUSPARSE( hipsparseDestroyDnVec(d_B.vec) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(d_X.vec) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(d_R.vec) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(d_R_aux.vec) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(d_P.vec) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(d_T.vec) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(d_tmp.vec) )
    CHECK_CUSPARSE( hipsparseDestroySpMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroySpMat(matL) )
    CHECK_CUSPARSE( hipsparseDestroy(cusparseHandle) )
    CHECK_CUBLAS( hipblasDestroy(cublasHandle) )

    free(h_A_rows);
    free(h_A_columns);
    free(h_A_values);
    free(h_X);

    CHECK_CUDA( hipFree(d_X.ptr) )
    CHECK_CUDA( hipFree(d_B.ptr) )
    CHECK_CUDA( hipFree(d_R.ptr) )
    CHECK_CUDA( hipFree(d_R_aux.ptr) )
    CHECK_CUDA( hipFree(d_P.ptr) )
    CHECK_CUDA( hipFree(d_T.ptr) )
    CHECK_CUDA( hipFree(d_tmp.ptr) )
    CHECK_CUDA( hipFree(d_A_values) )
    CHECK_CUDA( hipFree(d_A_columns) )
    CHECK_CUDA( hipFree(d_A_rows) )
    CHECK_CUDA( hipFree(d_L_values) )
    CHECK_CUDA( hipFree(d_bufferMV) )
    return EXIT_SUCCESS;
}