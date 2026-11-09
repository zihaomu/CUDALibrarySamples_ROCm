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
#include <hipsparse.h>         // cusparseSpSM
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
    const int nrhs            = 2;
    const int ldb             = A_num_cols;
    const int ldc             = A_num_rows;
    int       hA_coo_rows[] = { 0, 0, 0, 1, 2, 2, 2, 3, 3 };
    int       hA_coo_cols[] = { 0, 2, 3, 1, 0, 2, 3, 1, 3 };
    float     hA_values[]   = { 1.0f, 2.0f, 3.0f, 4.0f, 5.0f,
                                6.0f, 7.0f, 8.0f, 9.0f };
    float     hB[]            = { 1.0f, 8.0f, 23.0f, 52.0f,
                                  1.0f, 8.0f, 23.0f, 52.0f };
    float     hC[]            = { 0.0f, 0.0f, 0.0f, 0.0f,
                                  0.0f, 0.0f, 0.0f, 0.0f };
    float     hY_result[]     = { 1.0f, 2.0f, 3.0f, 4.0f,
                                  1.0f, 2.0f, 3.0f, 4.0f };
    float     alpha           = 1.0f;
    //--------------------------------------------------------------------------
    // Device memory management
    int   *dA_coo_rows, *dA_coo_cols;
    float *dA_values, *dB, *dC;
    CHECK_CUDA( hipMalloc((void**) &dA_coo_rows, A_nnz * sizeof(int))      )
    CHECK_CUDA( hipMalloc((void**) &dA_coo_cols, A_nnz * sizeof(int))      )
    CHECK_CUDA( hipMalloc((void**) &dA_values,   A_nnz * sizeof(float))    )
    CHECK_CUDA( hipMalloc((void**) &dB, nrhs * A_num_cols * sizeof(float)) )
    CHECK_CUDA( hipMalloc((void**) &dC, nrhs * A_num_rows * sizeof(float)) )

    CHECK_CUDA( hipMemcpy(dA_coo_rows, hA_coo_rows, A_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_coo_cols, hA_coo_cols, A_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_values, hA_values, A_nnz * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB, hB, nrhs * A_num_cols * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC, hC, nrhs * A_num_rows * sizeof(float),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpMatDescr_t matA;
    hipsparseDnMatDescr_t matB, matC;
    void*                dBuffer    = NULL;
    size_t               bufferSize = 0;
    hipsparseSpSMDescr_t  spsmDescr;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse matrix A in COO format
    CHECK_CUSPARSE( hipsparseCreateCoo(&matA, A_num_rows, A_num_cols, A_nnz,
                                      dA_coo_rows, dA_coo_cols, dA_values,
                                      HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    // Create dense vector X
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matB, A_num_cols, nrhs, ldb, dB,
                                        HIP_R_32F, HIPSPARSE_ORDER_COL) )
    // Create dense vector y
    CHECK_CUSPARSE( hipsparseCreateDnMat(&matC, A_num_rows, nrhs, ldc, dC,
                                        HIP_R_32F, HIPSPARSE_ORDER_COL) )
    // Create opaque data structure, that holds analysis data between calls.
    CHECK_CUSPARSE( hipsparseSpSM_createDescr(&spsmDescr) )
    // Specify Lower|Upper fill mode.
    hipsparseFillMode_t fillmode = HIPSPARSE_FILL_MODE_LOWER;
    CHECK_CUSPARSE( hipsparseSpMatSetAttribute(matA, HIPSPARSE_SPMAT_FILL_MODE,
                                              &fillmode, sizeof(fillmode)) )
    // Specify Unit|Non-Unit diagonal type.
    hipsparseDiagType_t diagtype = HIPSPARSE_DIAG_TYPE_NON_UNIT;
    CHECK_CUSPARSE( hipsparseSpMatSetAttribute(matA, HIPSPARSE_SPMAT_DIAG_TYPE,
                                              &diagtype, sizeof(diagtype)) )
    // allocate an external buffer for analysis
    CHECK_CUSPARSE( hipsparseSpSM_bufferSize(
                                handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                &alpha, matA, matB, matC, HIP_R_32F,
                                HIPSPARSE_SPSM_ALG_DEFAULT, spsmDescr,
                                &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )
    CHECK_CUSPARSE( hipsparseSpSM_analysis(
                                handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                &alpha, matA, matB, matC, HIP_R_32F,
                                HIPSPARSE_SPSM_ALG_DEFAULT, spsmDescr, dBuffer) )
    // execute SpSM
    CHECK_CUSPARSE( hipsparseSpSM_solve(handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                       HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                       &alpha, matA, matB, matC, HIP_R_32F,
                                       HIPSPARSE_SPSM_ALG_DEFAULT, spsmDescr, dBuffer) )

    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matB) )
    CHECK_CUSPARSE( hipsparseDestroyDnMat(matC) )
    CHECK_CUSPARSE( hipsparseSpSM_destroyDescr(spsmDescr));
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(hC, dC, nrhs * A_num_rows * sizeof(float),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < nrhs * A_num_rows; i++) {
        if (hC[i] != hY_result[i]) { // direct floating point comparison is not
            correct = 0;             // reliable
            break;
        }
    }
    if (correct)
        printf("spsm_coo_example test PASSED\n");
    else
        printf("spsm_coo_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer) )
    CHECK_CUDA( hipFree(dA_coo_rows) )
    CHECK_CUDA( hipFree(dA_coo_cols) )
    CHECK_CUDA( hipFree(dA_values) )
    CHECK_CUDA( hipFree(dB) )
    CHECK_CUDA( hipFree(dC) )
    return EXIT_SUCCESS;
}