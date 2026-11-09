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
#include <hipsparse.h>         // hipsparseSpMM
#include <stdio.h>            // printf
#include <stdlib.h>           // EXIT_FAILURE
#include <math.h>             // fabs

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
    int   A_num_rows  = 4;
    int   A_num_cols  = 4;
    int   A_nnz       = 9;
    int   B_num_rows  = A_num_cols;
    int   B_num_cols  = 3;
    int   ldb         = B_num_rows;
    int   ldc         = A_num_rows;
    int   B_size      = ldb * B_num_cols;
    int   C_size      = ldc * B_num_cols;
    int   num_batches = 2;

    int   hA_csrOffsets[]  = { 0, 3, 4, 7, 9 };
    int   hA_columns1[]    = { 0, 2, 3, 1, 0, 2, 3, 1, 3 };
    int   hA_columns2[]    = { 1, 2, 3, 0, 0, 1, 3, 1, 2 };
    float hA_values1[]     = { 1.0f, /*0*/ 2.0f, 3.0f,
                               /*0*/ 4.0f, /*0*/ /*0*/
                               5.0f, /*0*/ 6.0f, 7.0f,
                               /*0*/ 8.0f, /*0*/ 9.0f };
    float hA_values2[]     = { /*0*/ 10.0f,  11.0f, 12.0f,
                               13.0f, /*0*/  /*0*/ /*0*/
                               14.0f, 15.0f, /*0*/ 16.0f,
                               /*0*/ 17.0f, 18.0f  /*0*/ };
    float hB1[]            = { 1.0f,  2.0f,  3.0f,  4.0f,
                               5.0f,  6.0f,  7.0f,  8.0f,
                               9.0f, 10.0f, 11.0f, 12.0f };
    float hB2[]            = { 6.0f,  4.0f,  3.0f,  2.0f,
                               1.0f,  6.0f,  9.0f,  8.0f,
                               9.0f, 3.0f,   2.0f,  5.0f };

    float hC1[]            = { 0.0f, 0.0f, 0.0f, 0.0f,
                               0.0f, 0.0f, 0.0f, 0.0f,
                               0.0f, 0.0f, 0.0f, 0.0f };
    float hC2[]            = { 0.0f, 0.0f, 0.0f, 0.0f,
                               0.0f, 0.0f, 0.0f, 0.0f,
                               0.0f, 0.0f, 0.0f, 0.0f };

    float hC1_result[]     = { 19.0f,  8.0f,  51.0f,  52.0f,
                               43.0f, 24.0f, 123.0f, 120.0f,
                               67.0f, 40.0f, 195.0f, 188.0f };
    float hC2_result[]     = { 97.0f,  78.0f,  176.0f, 122.0f,
                               255.0f, 13.0f,  232.0f, 264.0f,
                               112.0f, 117.0f, 251.0f, 87.0f };
    float alpha            = 1.0f;
    float beta             = 0.0f;
    //--------------------------------------------------------------------------
    // Device memory management
    int   *dA_csrOffsets, *dA_columns;
    float *dA_values, *dB, *dC;
    CHECK_CUDA( hipMalloc((void**) &dA_csrOffsets,
                           (A_num_rows + 1) * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &dA_columns,
                           A_nnz * num_batches * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &dA_values,
                           A_nnz * num_batches * sizeof(float)) )
    CHECK_CUDA( hipMalloc((void**) &dB,
                           B_size * num_batches * sizeof(float)) )
    CHECK_CUDA( hipMalloc((void**) &dC,
                           C_size * num_batches * sizeof(float)) )

    CHECK_CUDA( hipMemcpy(dA_csrOffsets, hA_csrOffsets,
                           (A_num_rows + 1) * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_columns, hA_columns1, A_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_columns + A_nnz, hA_columns2, A_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_values, hA_values1, A_nnz * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_values + A_nnz, hA_values2, A_nnz * sizeof(float),
                           hipMemcpyHostToDevice) )

    CHECK_CUDA( hipMemcpy(dB, hB1, B_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB + B_size, hB2, B_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC, hC1, C_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC + C_size, hC2, C_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpMatDescr_t matA;
    hipsparseDnMatDescr_t matB, matC;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse matrix A in CSR format
    CHECK_CUSPARSE( hipsparseCreateCsr(&matA, A_num_rows, A_num_cols, A_nnz,
                                      dA_csrOffsets, dA_columns, dA_values,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    CHECK_CUSPARSE( hipsparseCsrSetStridedBatch(matA, num_batches, 0, A_nnz) )
    // Alternatively, the following code can be used for matA broadcast
    // CHECK_CUSPARSE( hipsparseCsrSetStridedBatch(matA, num_batches, 0, 0) )
    // Create dense matrix B
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matB, A_num_cols, B_num_cols, ldb, dB,
                                        HIP_R_32F, HIPSPARSE_ORDER_COL) )
    CHECK_CUSPARSE( hipsparseDnMatSetStridedBatch(matB, num_batches, B_size) )
    // Create dense matrix C
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matC, A_num_rows, B_num_cols, ldc, dC,
                                        HIP_R_32F, HIPSPARSE_ORDER_COL) )
    CHECK_CUSPARSE( hipsparseDnMatSetStridedBatch(matC, num_batches, C_size) )

    // allocate an external buffer if needed
    CHECK_CUSPARSE( hipsparseSpMM_bufferSize(
                                 handle,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &alpha, matA, matB, &beta, matC, HIP_R_32F,
                                 HIPSPARSE_SPMM_CSR_ALG2, &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )

    // execute SpMM
    CHECK_CUSPARSE( hipsparseSpMM(handle,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &alpha, matA, matB, &beta, matC, HIP_R_32F,
                                 HIPSPARSE_SPMM_CSR_ALG2, dBuffer) )

    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matB) )
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matC) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(hC1, dC, C_size * sizeof(float),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(hC2, dC + C_size, C_size * sizeof(float),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < A_num_rows; i++) {
        for (int j = 0; j < B_num_cols; j++) {
            if (hC1[i + j * ldc] != hC1_result[i + j * ldc]) {
                correct = 0; // direct floating point comparison is not reliable
                break;
            }
            if (hC2[i + j * ldc] != hC2_result[i + j * ldc]) {
                correct = 0;
                break;
            }
        }
    }
    if (correct)
        printf("spmm_csr_batched_example test PASSED\n");
    else
        printf("spmm_csr_batched_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer) )
    CHECK_CUDA( hipFree(dA_csrOffsets) )
    CHECK_CUDA( hipFree(dA_columns) )
    CHECK_CUDA( hipFree(dA_values) )
    CHECK_CUDA( hipFree(dB) )
    CHECK_CUDA( hipFree(dC) )
    return EXIT_SUCCESS;
}