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

#include "hip/hip_runtime.h"
#include <hip/hip_runtime_api.h> // cudaMalloc, cudaMemcpy, etc.
#include <hipsparse.h>         // hipsparseSDDMM
#include <stdio.h>            // printf
#include <stdlib.h>           // EXIT_FAILURE

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
        printf("CUSPARSE API failed at line %d with error: %s (%d)\n",         \
               __LINE__, hipsparseGetErrorString(status), status);              \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

int main(void) {
    // Host problem definition
    int   A_num_rows   = 4;
    int   A_num_cols   = 4;
    int   B_num_rows   = A_num_cols;
    int   B_num_cols   = 3;
    int   C_nnz        = 9;
    int   lda          = A_num_cols;
    int   ldb          = B_num_cols;
    int   A_size       = lda * A_num_rows;
    int   B_size       = ldb * B_num_rows;
    int   num_batches  = 2;

    float hA1[]        = { 1.0f,   2.0f,  3.0f,  4.0f,
                           5.0f,   6.0f,  7.0f,  8.0f,
                           9.0f,  10.0f, 11.0f, 12.0f,
                           13.0f, 14.0f, 15.0f, 16.0f };
    float hA2[]        = { 10.0f,   11.0f,  12.0f,  13.0f,
                           14.0f,   15.0f,  16.0f,  17.0f,
                           18.0f,   19.0f,  20.0f,  21.0f,
                           22.0f,   23.0f,  24.0f,  25.0f };
    float hB1[]        = {  1.0f,  2.0f,  3.0f,
                            4.0f,  5.0f,  6.0f,
                            7.0f,  8.0f,  9.0f,
                            10.0f, 11.0f, 12.0f };
    float hB2[]        = {  6.0f,  4.0f,  2.0f,
                            3.0f,  7.0f,  1.0f,
                            9.0f,  5.0f,  2.0f,
                            8.0f,  4.0f,  7.0f };
    int   hC_offsets[]  = { 0, 3, 4, 7, 9 };
    int   hC_columns1[] = { 0, 1, 2, 1, 0, 1, 2, 0, 2 };
    int   hC_columns2[] = { 0, 1, 2, 0, 0, 1, 2, 1, 2 };
    float hC_values1[]  = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                           0.0f, 0.0f, 0.0f, 0.0f };
    float hC_values2[]  = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f,
                           0.0f, 0.0f, 0.0f, 0.0f };
    float hC_result1[]  = { 70.0f, 80.0f, 90.0f,
                           184.0f,
                           246.0f, 288.0f, 330.0f,
                           334.0f, 450.0f };
    float hC_result2[]  = {305.0f, 229.0f, 146.0f,
                           409.0f,
                           513.0f, 389.0f, 242.0f,
                           469.0f, 290.0f };
    float alpha        = 1.0f;
    float beta         = 0.0f;
    //--------------------------------------------------------------------------
    // Device memory management
    int   *dC_offsets, *dC_columns;
    float *dC_values, *dB, *dA;
    CHECK_CUDA( hipMalloc((void**) &dA,
                           A_size * num_batches * sizeof(float)) )
    CHECK_CUDA( hipMalloc((void**) &dB,
                           B_size * num_batches * sizeof(float)) )
    CHECK_CUDA( hipMalloc((void**) &dC_offsets,
                           (A_num_rows + 1) * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &dC_columns,
                           C_nnz * num_batches * sizeof(int))   )
    CHECK_CUDA( hipMalloc((void**) &dC_values,
                           C_nnz * num_batches * sizeof(float)) )

    CHECK_CUDA( hipMemcpy(dA, hA1, A_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA + A_size, hA2, A_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB, hB1, B_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB + B_size, hB2, B_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC_offsets, hC_offsets,
                           (A_num_rows + 1) * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC_columns, hC_columns1, C_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC_columns + C_nnz, hC_columns2, C_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC_values, hC_values1, C_nnz * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC_values + C_nnz, hC_values2, C_nnz * sizeof(float),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseDnMatDescr_t matA, matB;
    hipsparseSpMatDescr_t matC;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create dense matrix A
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matA, A_num_rows, A_num_cols, lda, dA,
                                        HIP_R_32F, HIPSPARSE_ORDER_ROW) )
    CHECK_CUSPARSE( hipsparseDnMatSetStridedBatch(matA, num_batches, A_size) )
    // Create dense matrix B
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matB, A_num_cols, B_num_cols, ldb, dB,
                                        HIP_R_32F, HIPSPARSE_ORDER_ROW) )
    CHECK_CUSPARSE( hipsparseDnMatSetStridedBatch(matB, num_batches, B_size) )
    // Create sparse matrix C in CSR format
    CHECK_CUSPARSE( hipsparseCreateCsr(&matC, A_num_rows, B_num_cols, C_nnz,
                                      dC_offsets, dC_columns, dC_values,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    CHECK_CUSPARSE( hipsparseCsrSetStridedBatch(matC, num_batches, 0, C_nnz) )
    // allocate an external buffer if needed
    CHECK_CUSPARSE( hipsparseSDDMM_bufferSize(
                                 handle,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &alpha, matA, matB, &beta, matC, HIP_R_32F,
                                 HIPSPARSE_SDDMM_ALG_DEFAULT, &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )

    // execute preprocess (optional)
    CHECK_CUSPARSE( hipsparseSDDMM_preprocess(
                                  handle,
                                  HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                  HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                  &alpha, matA, matB, &beta, matC, HIP_R_32F,
                                  HIPSPARSE_SDDMM_ALG_DEFAULT, dBuffer) )
    // execute SDDMM
    CHECK_CUSPARSE( hipsparseSDDMM(handle,
                                  HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                  HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                  &alpha, matA, matB, &beta, matC, HIP_R_32F,
                                  HIPSPARSE_SDDMM_ALG_DEFAULT, dBuffer) )
    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matB) )
    CHECK_CUSPARSE( hipsparseDestroySpMat(matC) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(hC_values1, dC_values, C_nnz * sizeof(float),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(hC_values2, dC_values + C_nnz, C_nnz * sizeof(float),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < C_nnz; i++) {
        if (hC_values1[i] != hC_result1[i]) {
            correct = 0; // direct floating point comparison is not reliable
            break;
        }
        if (hC_values2[i] != hC_result2[i]) {
            correct = 0; // direct floating point comparison is not reliable
            break;
        }
    }
    if (correct)
        printf("sddmm_csr_batched_example test PASSED\n");
    else
        printf("sddmm_csr_batched_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer) )
    CHECK_CUDA( hipFree(dA) )
    CHECK_CUDA( hipFree(dB) )
    CHECK_CUDA( hipFree(dC_offsets) )
    CHECK_CUDA( hipFree(dC_columns) )
    CHECK_CUDA( hipFree(dC_values) )
    return EXIT_SUCCESS;
}