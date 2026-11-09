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
#include <hipsparse.h>         // cusparseSpSV
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
    const int A_num_rows      = 4;
    const int A_num_cols      = 4;
    const int A_nnz           = 9;
    int       hA_csrOffsets[] = { 0, 3, 4, 7, 9 };
    int       hA_columns[]    = { 0, 2, 3, 1, 0, 2, 3, 1, 3 };
    float     hA_values[]     = { 1.0f, 2.0f, 3.0f, 4.0f, 5.0f,
                                  6.0f, 7.0f, 8.0f, 9.0f };
    float     hX[]            = { 1.0f, 8.0f, 23.0f, 52.0f };
    float     hY[]            = { 0.0f, 0.0f, 0.0f, 0.0f };
    float     hY_result[]     = { 1.0f, 2.0f, 3.0f, 4.0f };
    float     alpha           = 1.0f;
    //--------------------------------------------------------------------------
    // Device memory management
    int   *dA_csrOffsets, *dA_columns;
    float *dA_values, *dX, *dY;
    CHECK_CUDA( hipMalloc((void**) &dA_csrOffsets,
                           (A_num_rows + 1) * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &dA_columns, A_nnz * sizeof(int))        )
    CHECK_CUDA( hipMalloc((void**) &dA_values,  A_nnz * sizeof(float))      )
    CHECK_CUDA( hipMalloc((void**) &dX,         A_num_cols * sizeof(float)) )
    CHECK_CUDA( hipMalloc((void**) &dY,         A_num_rows * sizeof(float)) )

    CHECK_CUDA( hipMemcpy(dA_csrOffsets, hA_csrOffsets,
                           (A_num_rows + 1) * sizeof(int),
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
    hipsparseSpSVDescr_t  spsvDescr;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse matrix A in CSR format
    CHECK_CUSPARSE( hipsparseCreateCsr(&matA, A_num_rows, A_num_cols, A_nnz,
                                      dA_csrOffsets, dA_columns, dA_values,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    // Create dense vector X
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vecX, A_num_cols, dX, HIP_R_32F) )
    // Create dense vector y
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vecY, A_num_rows, dY, HIP_R_32F) )
    // Create opaque data structure, that holds analysis data between calls.
    CHECK_CUSPARSE( hipsparseSpSV_createDescr(&spsvDescr) )
    // Specify Lower|Upper fill mode.
    hipsparseFillMode_t fillmode = HIPSPARSE_FILL_MODE_LOWER;
    CHECK_CUSPARSE( hipsparseSpMatSetAttribute(matA, HIPSPARSE_SPMAT_FILL_MODE,
                                              &fillmode, sizeof(fillmode)) )
    // Specify Unit|Non-Unit diagonal type.
    hipsparseDiagType_t diagtype = HIPSPARSE_DIAG_TYPE_NON_UNIT;
    CHECK_CUSPARSE( hipsparseSpMatSetAttribute(matA, HIPSPARSE_SPMAT_DIAG_TYPE,
                                              &diagtype, sizeof(diagtype)) )
    // allocate an external buffer for analysis
    CHECK_CUSPARSE( hipsparseSpSV_bufferSize(
                                handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                &alpha, matA, vecX, vecY, HIP_R_32F,
                                HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescr,
                                &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )
    CHECK_CUSPARSE( hipsparseSpSV_analysis(
                                handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                &alpha, matA, vecX, vecY, HIP_R_32F,
                                HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescr, dBuffer) )
    // execute SpSV
    CHECK_CUSPARSE( hipsparseSpSV_solve(handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                       &alpha, matA, vecX, vecY, HIP_R_32F,
                                       HIPSPARSE_SPSV_ALG_DEFAULT, spsvDescr) )

    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecX) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecY) )
    CHECK_CUSPARSE( hipsparseSpSV_destroyDescr(spsvDescr));
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
        printf("spsv_csr_example test PASSED\n");
    else
        printf("spsv_csr_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer) )
    CHECK_CUDA( hipFree(dA_csrOffsets) )
    CHECK_CUDA( hipFree(dA_columns) )
    CHECK_CUDA( hipFree(dA_values) )
    CHECK_CUDA( hipFree(dX) )
    CHECK_CUDA( hipFree(dY) )
    return EXIT_SUCCESS;
}