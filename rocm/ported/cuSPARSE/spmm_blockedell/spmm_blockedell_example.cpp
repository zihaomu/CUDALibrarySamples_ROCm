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
#include <hip/hip_fp16.h>        // data types
#include <hip/hip_runtime_api.h> // cudaMalloc, cudaMemcpy, etc.
#include <hipsparse.h>         // hipsparseSpMM
#include <cstdio>            // printf
#include <cstdlib>           // EXIT_FAILURE

#define CHECK_CUDA(func)                                                       \
{                                                                              \
    hipError_t status = (func);                                               \
    if (status != hipSuccess) {                                               \
        std::printf("CUDA API failed at line %d with error: %s (%d)\n",        \
               __LINE__, hipGetErrorString(status), status);                  \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

#define CHECK_CUSPARSE(func)                                                   \
{                                                                              \
    hipsparseStatus_t status = (func);                                          \
    if (status != HIPSPARSE_STATUS_SUCCESS) {                                   \
        std::printf("CUSPARSE API failed at line %d with error: %s (%d)\n",    \
               __LINE__, hipsparseGetErrorString(status), status);              \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

const int EXIT_UNSUPPORTED = 2;

int main() {
    // Host problem definition
    int   A_num_rows      = 4;
    int   A_num_cols      = 4;
    int   A_ell_blocksize = 2;
    int   A_ell_cols      = 2;
    int   A_num_blocks    = A_ell_cols * A_num_rows /
                           (A_ell_blocksize * A_ell_blocksize);
    int   B_num_rows      = A_num_cols;
    int   B_num_cols      = 3;
    int   ldb             = B_num_rows;
    int   ldc             = A_num_rows;
    int   B_size          = ldb * B_num_cols;
    int   C_size          = ldc * B_num_cols;
    int   hA_columns[]    = { 1, 0};
    __half hA_values[]    = { 1.0f, 2.0f, 3.0f, 4.0f,
                              5.0f, 6.0f, 7.0f, 8.0f};
    __half hB[]           = { 1.0f,  2.0f,  3.0f,  4.0f,
                              5.0f,  6.0f,  7.0f,  8.0f,
                              9.0f, 10.0f, 11.0f, 12.0f };
    __half hC[]           = { 0.0f, 0.0f, 0.0f, 0.0f,
                              0.0f, 0.0f, 0.0f, 0.0f,
                              0.0f, 0.0f, 0.0f, 0.0f };
    __half hC_result[]    = { 11.0f, 25.0f,  17.0f,  23.0f,
                              23.0f, 53.0f,  61.0f,  83.0f,
                              35.0f, 81.0f, 105.0f, 143.0f };
    float alpha           = 1.0f;
    float beta            = 0.0f;
    //--------------------------------------------------------------------------
    // Check compute capability
    hipDeviceProp_t props;
    CHECK_CUDA( hipGetDeviceProperties(&props, 0) )
    if (props.major < 7) {
      std::printf("hipsparseSpMM with blocked ELL format is supported only "
                  "with compute capability at least 7.0\n");
      return EXIT_UNSUPPORTED;
    }
    //--------------------------------------------------------------------------
    // Device memory management
    int    *dA_columns;
    __half *dA_values, *dB, *dC;
    CHECK_CUDA( hipMalloc((void**) &dA_columns, A_num_blocks * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &dA_values,
                                    A_ell_cols * A_num_rows * sizeof(__half)) )
    CHECK_CUDA( hipMalloc((void**) &dB, B_size * sizeof(__half)) )
    CHECK_CUDA( hipMalloc((void**) &dC, C_size * sizeof(__half)) )

    CHECK_CUDA( hipMemcpy(dA_columns, hA_columns,
                           A_num_blocks * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_values, hA_values,
                           A_ell_cols * A_num_rows * sizeof(__half),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB, hB, B_size * sizeof(__half),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC, hC, C_size * sizeof(__half),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpMatDescr_t matA;
    hipsparseDnMatDescr_t matB, matC;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse matrix A in blocked ELL format
    CHECK_CUSPARSE( hipsparseCreateBlockedEll(
                                      &matA,
                                      A_num_rows, A_num_cols, A_ell_blocksize,
                                      A_ell_cols, dA_columns, dA_values,
                                      HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_16F) )
    // Create dense matrix B
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matB, A_num_cols, B_num_cols, ldb, dB,
                                        HIP_R_16F, HIPSPARSE_ORDER_COL) )
    // Create dense matrix C
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matC, A_num_rows, B_num_cols, ldc, dC,
                                        HIP_R_16F, HIPSPARSE_ORDER_COL) )
    // allocate an external buffer if needed
    CHECK_CUSPARSE( hipsparseSpMM_bufferSize(
                                 handle,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &alpha, matA, matB, &beta, matC, HIP_R_32F,
                                 HIPSPARSE_SPMM_ALG_DEFAULT, &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )

    // execute SpMM
    CHECK_CUSPARSE( hipsparseSpMM(handle,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 &alpha, matA, matB, &beta, matC, HIP_R_32F,
                                 HIPSPARSE_SPMM_ALG_DEFAULT, dBuffer) )

    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matB) )
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matC) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(hC, dC, C_size * sizeof(__half),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < A_num_rows; i++) {
        for (int j = 0; j < B_num_cols; j++) {
            float c_value  = static_cast<float>(hC[i + j * ldc]);
            float c_result = static_cast<float>(hC_result[i + j * ldc]);
            if (c_value != c_result) {
                correct = 0; // direct floating point comparison is not reliable
                break;
            }
        }
    }
    if (correct)
        std::printf("spmm_blockedell_example test PASSED\n");
    else
        std::printf("spmm_blockedell_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer) )
    CHECK_CUDA( hipFree(dA_columns) )
    CHECK_CUDA( hipFree(dA_values) )
    CHECK_CUDA( hipFree(dB) )
    CHECK_CUDA( hipFree(dC) )
    return EXIT_SUCCESS;
}