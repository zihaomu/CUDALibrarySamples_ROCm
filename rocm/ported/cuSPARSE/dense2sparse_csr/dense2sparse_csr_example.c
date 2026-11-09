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
#include <hipsparse.h>         // hipsparseSparseToDense
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
    int   num_rows   = 5;
    int   num_cols   = 4;
    int   ld         = num_cols;
    int   dense_size = ld * num_rows;
    float h_dense[]  = { 1.0f,  0.0f,  2.0f,  3.0f,
                         0.0f,  4.0f,  0.0f,  0.0f,
                         5.0f,  0.0f,  6.0f,  7.0f,
                         0.0f,  8.0f,  0.0f,  9.0f,
                         0.0f, 10.0f, 11.0f,  0.0f };
    int   h_csr_offsets[]         = { 0, 0, 0, 0, 0, 0  };
    int   h_csr_columns[]         = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
    float h_csr_values[]          = { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
    int   h_csr_offsets_result[]  = { 0, 3, 4, 7, 9, 11 };
    int   h_csr_columns_result[]  = { 0, 2, 3, 1, 0, 2, 3, 1, 3, 1, 2 };
    float h_csr_values_result[]   = { 1.0f, 2.0f, 3.0f, 4.0f, 5.0f, 6.0f,
                                      7.0f, 8.0f, 9.0f, 10.0f, 11.0f };
    //--------------------------------------------------------------------------
    // Device memory management
    int   *d_csr_offsets, *d_csr_columns;
    float *d_csr_values,  *d_dense;
    CHECK_CUDA( hipMalloc((void**) &d_dense, dense_size * sizeof(float)))
    CHECK_CUDA( hipMalloc((void**) &d_csr_offsets,
                           (num_rows + 1) * sizeof(int)) )
    CHECK_CUDA( hipMemcpy(d_dense, h_dense, dense_size * sizeof(float),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpMatDescr_t matB;
    hipsparseDnMatDescr_t matA;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create dense matrix A
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matA, num_rows, num_cols, ld, d_dense,
                                        HIP_R_32F, HIPSPARSE_ORDER_ROW) )
    // Create sparse matrix B in CSR format
    CHECK_CUSPARSE( hipsparseCreateCsr(&matB, num_rows, num_cols, 0,
                                      d_csr_offsets, NULL, NULL,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )

    // allocate an external buffer if needed
    CHECK_CUSPARSE( hipsparseDenseToSparse_bufferSize(
                                        handle, matA, matB,
                                        HIPSPARSE_DENSETOSPARSE_ALG_DEFAULT,
                                        &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )

    // execute Sparse to Dense conversion
    CHECK_CUSPARSE( hipsparseDenseToSparse_analysis(handle, matA, matB,
                                        HIPSPARSE_DENSETOSPARSE_ALG_DEFAULT,
                                        dBuffer) )
    // get number of non-zero elements
    int64_t num_rows_tmp, num_cols_tmp, nnz;
    CHECK_CUSPARSE( hipsparseSpMatGetSize(matB, &num_rows_tmp, &num_cols_tmp,
                                         &nnz) )

    // allocate CSR column indices and values
    CHECK_CUDA( hipMalloc((void**) &d_csr_columns, nnz * sizeof(int))   )
    CHECK_CUDA( hipMalloc((void**) &d_csr_values,  nnz * sizeof(float)) )
    // reset offsets, column indices, and values pointers
    CHECK_CUSPARSE( hipsparseCsrSetPointers(matB, d_csr_offsets, d_csr_columns,
                                           d_csr_values) )
    // execute Sparse to Dense conversion
    CHECK_CUSPARSE( hipsparseDenseToSparse_convert(handle, matA, matB,
                                        HIPSPARSE_DENSETOSPARSE_ALG_DEFAULT,
                                        dBuffer) )
    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroySpMat(matB) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(h_csr_offsets, d_csr_offsets,
                           (num_rows + 1) * sizeof(int),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(h_csr_columns, d_csr_columns, nnz * sizeof(int),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(h_csr_values, d_csr_values, nnz * sizeof(float),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < num_rows + 1; i++) {
        if (h_csr_offsets[i] != h_csr_offsets_result[i]) {
            correct = 0;
            break;
        }
    }
    for (int i = 0; i < nnz; i++) {
        if (h_csr_columns[i] != h_csr_columns_result[i]) {
            correct = 0;
            break;
        }
    }
    for (int i = 0; i < nnz; i++) {
        if (h_csr_values[i] != h_csr_values_result[i]) {
            correct = 0;
            break;
        }
    }
    if (correct)
        printf("dense2sparse_csr_example test PASSED\n");
    else
        printf("dense2sparse_csr_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer) )
    CHECK_CUDA( hipFree(d_csr_offsets) )
    CHECK_CUDA( hipFree(d_csr_columns) )
    CHECK_CUDA( hipFree(d_csr_values) )
    CHECK_CUDA( hipFree(d_dense) )
    return EXIT_SUCCESS;
}