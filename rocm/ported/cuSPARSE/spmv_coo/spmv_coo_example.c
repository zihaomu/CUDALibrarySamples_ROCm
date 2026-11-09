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
#include <hipsparse.h>         // hipsparseSpMV
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
    int   A_nnz        = 9;
    int   hA_rows[]    = { 0, 0, 0, 1, 2, 2, 2, 3, 3 };
    int   hA_columns[] = { 0, 2, 3, 1, 0, 2, 3, 1, 3 };
    float hA_values[]  = { 1.0f, 2.0f, 3.0f, 4.0f, 5.0f,
                           6.0f, 7.0f, 8.0f, 9.0f };
    float hX[]         = { 1.0f, 2.0f, 3.0f, 4.0f };
    float hY[]         = { 0.0f, 0.0f, 0.0f, 0.0f };
    float hY_result[]  = { 19.0f, 8.0f, 51.0f, 52.0f };
    float alpha        = 1.0f;
    float beta         = 0.0f;
    //--------------------------------------------------------------------------
    // Device memory management
    int   *dA_rows, *dA_columns;
    float *dA_values, *dX, *dY;
    CHECK_CUDA( hipMalloc((void**) &dA_rows,    A_nnz * sizeof(int))        )
    CHECK_CUDA( hipMalloc((void**) &dA_columns, A_nnz * sizeof(int))        )
    CHECK_CUDA( hipMalloc((void**) &dA_values,  A_nnz * sizeof(float))      )
    CHECK_CUDA( hipMalloc((void**) &dX,         A_num_cols * sizeof(float)) )
    CHECK_CUDA( hipMalloc((void**) &dY,         A_num_rows * sizeof(float)) )

    CHECK_CUDA( hipMemcpy(dA_rows, hA_rows, A_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_columns, hA_columns, A_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_values, hA_values, A_nnz * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dX, hX, A_num_cols * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dY, hY, A_num_rows * sizeof(float),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpMatDescr_t matA;
    hipsparseDnVecDescr_t vecX, vecY;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse matrix A in CSR format
    CHECK_CUSPARSE( hipsparseCreateCoo(&matA, A_num_rows, A_num_cols, A_nnz,
                                      dA_rows, dA_columns, dA_values,
                                      HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    // Create dense vector X
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vecX, A_num_cols, dX, HIP_R_32F) )
    // Create dense vector y
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vecY, A_num_rows, dY, HIP_R_32F) )
    // allocate an external buffer if needed
    CHECK_CUSPARSE( hipsparseSpMV_bufferSize(
                                 handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &alpha, matA, vecX, &beta, vecY, HIP_R_32F,
                                 HIPSPARSE_SPMV_ALG_DEFAULT, &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )

    // execute SpMV
    CHECK_CUSPARSE( hipsparseSpMV(handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &alpha, matA, vecX, &beta, vecY, HIP_R_32F,
                                 HIPSPARSE_SPMV_ALG_DEFAULT, dBuffer) )

    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecX) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecY) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(hY, dY, A_num_rows * sizeof(float),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < A_num_rows; i++) {
        if (hY[i] != hY_result[i]) { // direct floating point comparison is not
            correct = 0;             // reliable
            break;
        }
    }
    if (correct)
        printf("spmv_coo_example test PASSED\n");
    else
        printf("spmv_coo_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer) )
    CHECK_CUDA( hipFree(dA_rows) )
    CHECK_CUDA( hipFree(dA_columns) )
    CHECK_CUDA( hipFree(dA_values) )
    CHECK_CUDA( hipFree(dX) )
    CHECK_CUDA( hipFree(dY) )
    return EXIT_SUCCESS;
}