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
#include <hipsparse.h>         // cusparseSpGEMM
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
    #define   A_NUM_ROWS 4   // C compatibility
    const int A_num_rows = 4;
    const int A_num_cols = 4;
    const int A_nnz      = 9;
    const int B_num_rows = 4;
    const int B_num_cols = 4;
    const int B_nnz      = 9;
    int   hA_csrOffsets[] = { 0, 3, 4, 7, 9 };
    int   hA_columns[]    = { 0, 2, 3, 1, 0, 2, 3, 1, 3 };
    float hA_values[]     = { 1.0f, 2.0f, 3.0f, 4.0f, 5.0f,
                              6.0f, 7.0f, 8.0f, 9.0f };
    int   hB_csrOffsets[] = { 0, 2, 4, 7, 8 };
    int   hB_columns[]    = { 0, 3, 1, 3, 0, 1, 2, 1 };
    float hB_values[]     = { 1.0f, 2.0f, 3.0f, 4.0f, 5.0f,
                              6.0f, 7.0f, 8.0f };
    int   hC_csrOffsets[] = { 0, 4, 6, 10, 12 };
    int   hC_columns[]    = { 0, 1, 2, 3, 1, 3, 0, 1, 2, 3, 1, 3 };
    float hC_values[]     = { 11.0f, 36.0f, 14.0f, 2.0f,  12.0f,
                              16.0f, 35.0f, 92.0f, 42.0f, 10.0f,
                              96.0f, 32.0f };
    const int C_nnz       = 12;
    #define   C_NUM_NNZ 12   // C compatibility
    float               alpha       = 1.0f;
    float               beta        = 0.0f;
    hipsparseOperation_t opA         = HIPSPARSE_OPERATION_NON_TRANSPOSE;
    hipsparseOperation_t opB         = HIPSPARSE_OPERATION_NON_TRANSPOSE;
    hipDataType        computeType = HIP_R_32F;
    //--------------------------------------------------------------------------
    // Device memory management: Allocate and copy A, B
    int   *dA_csrOffsets, *dA_columns, *dB_csrOffsets, *dB_columns,
          *dC_csrOffsets, *dC_columns;
    float *dA_values, *dB_values, *dC_values;
    // allocate A
    CHECK_CUDA( hipMalloc((void**) &dA_csrOffsets,
                           (A_num_rows + 1) * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &dA_columns, A_nnz * sizeof(int))   )
    CHECK_CUDA( hipMalloc((void**) &dA_values,  A_nnz * sizeof(float)) )
    // allocate B
    CHECK_CUDA( hipMalloc((void**) &dB_csrOffsets,
                           (B_num_rows + 1) * sizeof(int)) )
    CHECK_CUDA( hipMalloc((void**) &dB_columns, B_nnz * sizeof(int))   )
    CHECK_CUDA( hipMalloc((void**) &dB_values,  B_nnz * sizeof(float)) )
    // allocate C offsets
    CHECK_CUDA( hipMalloc((void**) &dC_csrOffsets,
                           (A_num_rows + 1) * sizeof(int)) )
    // copy A
    CHECK_CUDA( hipMemcpy(dA_csrOffsets, hA_csrOffsets,
                           (A_num_rows + 1) * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_columns, hA_columns, A_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dA_values, hA_values,
                           A_nnz * sizeof(float), hipMemcpyHostToDevice) )
    // copy B
    CHECK_CUDA( hipMemcpy(dB_csrOffsets, hB_csrOffsets,
                           (B_num_rows + 1) * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB_columns, hB_columns, B_nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB_values, hB_values,
                           B_nnz * sizeof(float), hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpMatDescr_t matA, matB, matC;
    void*  dBuffer1    = NULL;
    void*  dBuffer2    = NULL;
    void*  dBuffer3    = NULL;
    void*  dBuffer4    = NULL;
    void*  dBuffer5    = NULL;
    size_t bufferSize1 = 0;
    size_t bufferSize2 = 0;
    size_t bufferSize3 = 0;
    size_t bufferSize4 = 0;
    size_t bufferSize5 = 0;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse matrix A in CSR format
    CHECK_CUSPARSE( hipsparseCreateCsr(&matA, A_num_rows, A_num_cols, A_nnz,
                                      dA_csrOffsets, dA_columns, dA_values,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    CHECK_CUSPARSE( hipsparseCreateCsr(&matB, B_num_rows, B_num_cols, B_nnz,
                                      dB_csrOffsets, dB_columns, dB_values,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    CHECK_CUSPARSE( hipsparseCreateCsr(&matC, A_num_rows, B_num_cols, 0,
                                      dC_csrOffsets, NULL, NULL,
                                      HIPSPARSE_INDEX_32I, HIPSPARSE_INDEX_32I,
                                      HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    //==========================================================================
    // SpGEMM Computation
    //==========================================================================
    hipsparseSpGEMMDescr_t spgemmDesc;
    CHECK_CUSPARSE( hipsparseSpGEMM_createDescr(&spgemmDesc) )

    // ask bufferSize1 bytes for external memory
    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_workEstimation(handle, opA, opB, matA, matB, matC,
                                           HIPSPARSE_SPGEMM_DEFAULT,
                                           spgemmDesc, &bufferSize1, NULL)
    )
    CHECK_CUDA( hipMalloc((void**) &dBuffer1, bufferSize1) )
    // inspect the matrices A and B to understand the memory requirement for
    // the next step
    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_workEstimation(handle, opA, opB, matA, matB, matC,
                                           HIPSPARSE_SPGEMM_DEFAULT,
                                           spgemmDesc, &bufferSize1, dBuffer1)
    )
    //--------------------------------------------------------------------------

    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_nnz(handle, opA, opB, matA, matB,
                                matC, HIPSPARSE_SPGEMM_DEFAULT, spgemmDesc,
                                &bufferSize2, NULL, &bufferSize3, NULL,
                                &bufferSize4, NULL)
    )
    CHECK_CUDA( hipMalloc((void**) &dBuffer2, bufferSize2) )
    CHECK_CUDA( hipMalloc((void**) &dBuffer3, bufferSize3) )
    CHECK_CUDA( hipMalloc((void**) &dBuffer4, bufferSize4) )
    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_nnz(handle, opA, opB, matA, matB,
                                matC, HIPSPARSE_SPGEMM_DEFAULT, spgemmDesc,
                                &bufferSize2, dBuffer2, &bufferSize3, dBuffer3,
                                &bufferSize4, dBuffer4)
    )
    CHECK_CUDA( hipFree(dBuffer1) )
    CHECK_CUDA( hipFree(dBuffer2) )
    //--------------------------------------------------------------------------

    // get matrix C non-zero entries C_nnz1
    int64_t C_num_rows1, C_num_cols1, C_nnz1;
    CHECK_CUSPARSE( hipsparseSpMatGetSize(matC, &C_num_rows1, &C_num_cols1,
                                         &C_nnz1) )
    // allocate matrix C
    CHECK_CUDA( hipMalloc((void**) &dC_columns, C_nnz1 * sizeof(int))   )
    CHECK_CUDA( hipMalloc((void**) &dC_values,  C_nnz1 * sizeof(float)) )
    CHECK_CUDA( hipMemset(dC_values, 0x0, C_nnz1 * sizeof(float)) )
    // fill dC_values if needed
    // update matC with the new pointers
    CHECK_CUSPARSE(
        hipsparseCsrSetPointers(matC, dC_csrOffsets, dC_columns, dC_values) )
    //--------------------------------------------------------------------------

    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_copy(handle, opA, opB, matA, matB, matC,
                                 HIPSPARSE_SPGEMM_DEFAULT, spgemmDesc,
                                 &bufferSize5, NULL)
    )
    CHECK_CUDA( hipMalloc((void**) &dBuffer5, bufferSize5) )
    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_copy(handle, opA, opB, matA, matB, matC,
                                 HIPSPARSE_SPGEMM_DEFAULT, spgemmDesc,
                                 &bufferSize5, dBuffer5)
    )
    CHECK_CUDA( hipFree(dBuffer3) )
    //--------------------------------------------------------------------------
    // first run
    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_compute(handle, opA, opB, &alpha, matA, matB, &beta,
                                    matC, computeType, HIPSPARSE_SPGEMM_DEFAULT,
                                    spgemmDesc)
    )
    // update dA_values, dB_values
    CHECK_CUDA( hipMemcpy(dA_values, hA_values,
                           A_nnz * sizeof(float), hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB_values, hB_values,
                           B_nnz * sizeof(float), hipMemcpyHostToDevice) )
    // second run
    CHECK_CUSPARSE(
        hipsparseSpGEMMreuse_compute(handle, opA, opB, &alpha, matA, matB, &beta,
                                    matC, computeType, HIPSPARSE_SPGEMM_DEFAULT,
                                    spgemmDesc)
    )
    //==========================================================================
    //==========================================================================
    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseSpGEMM_destroyDescr(spgemmDesc) )
    CHECK_CUSPARSE( hipsparseDestroySpMat(matA) )
    CHECK_CUSPARSE( hipsparseDestroySpMat(matB) )
    CHECK_CUSPARSE( hipsparseDestroySpMat(matC) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    int   hC_csrOffsets_tmp[A_NUM_ROWS + 1];
    int   hC_columns_tmp[C_NUM_NNZ];
    float hC_values_tmp[C_NUM_NNZ];
    CHECK_CUDA( hipMemcpy(hC_csrOffsets_tmp, dC_csrOffsets,
                           (A_num_rows + 1) * sizeof(int),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(hC_columns_tmp, dC_columns, C_nnz * sizeof(int),
                           hipMemcpyDeviceToHost) )
    CHECK_CUDA( hipMemcpy(hC_values_tmp, dC_values, C_nnz * sizeof(float),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < A_num_rows + 1; i++) {
        if (hC_csrOffsets_tmp[i] != hC_csrOffsets[i]) {
            correct = 0;
            break;
        }
    }
    for (int i = 0; i < C_nnz; i++) {
        if (hC_columns_tmp[i] != hC_columns[i]) { // direct floating point
            correct = 0;                          // comparison is not reliable
            break;
        }
    }
    for (int i = 0; i < C_nnz; i++) {
        if (hC_columns_tmp[i] != hC_columns[i] ||
            hC_values_tmp[i]  != hC_values[i]) { // direct floating point
            correct = 0;                         // comparison is not reliable
            break;
        }
    }
    if (correct)
        printf("spgemm_reuse_example test PASSED\n");
    else {
        printf("spgemm_reuse_example test FAILED: wrong result\n");
        return EXIT_FAILURE;
    }
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dBuffer4) )
    CHECK_CUDA( hipFree(dBuffer5) )
    CHECK_CUDA( hipFree(dA_csrOffsets) )
    CHECK_CUDA( hipFree(dA_columns) )
    CHECK_CUDA( hipFree(dA_values) )
    CHECK_CUDA( hipFree(dB_csrOffsets) )
    CHECK_CUDA( hipFree(dB_columns) )
    CHECK_CUDA( hipFree(dB_values) )
    CHECK_CUDA( hipFree(dC_csrOffsets) )
    CHECK_CUDA( hipFree(dC_columns) )
    CHECK_CUDA( hipFree(dC_values) )
    return EXIT_SUCCESS;
}