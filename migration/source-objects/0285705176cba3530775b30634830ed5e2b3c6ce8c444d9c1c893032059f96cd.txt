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
#include <hipsparse.h>         // hipsparseScatter
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
    int   size         = 8;
    int   nnz          = 4;
    int   hX_indices[] = { 0, 3, 4, 7 };
    float hX_values[]  = { 1.0f, 2.0f, 3.0f, 4.0f };
    float hY[]         = { 0.0f, 0.0f, 0.0f, 0.0f,
                           0.0f, 0.0f, 0.0f, 0.0f };
    float hY_result[]  = { 1.0f, 0.0f, 0.0f, 2.0f,
                           3.0f, 0.0f, 0.0f, 4.0f };
    //--------------------------------------------------------------------------
    // Device memory management
    int   *dX_indices;
    float *dY, *dX_values;
    CHECK_CUDA( hipMalloc((void**) &dX_indices, nnz * sizeof(int))    )
    CHECK_CUDA( hipMalloc((void**) &dX_values,  nnz * sizeof(float))  )
    CHECK_CUDA( hipMalloc((void**) &dY,         size * sizeof(float)) )

    CHECK_CUDA( hipMemcpy(dX_indices, hX_indices, nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dX_values, hX_values, nnz * sizeof(float),
                           hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dY, hY, size * sizeof(float),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpVecDescr_t vecX;
    hipsparseDnVecDescr_t vecY;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse vector X
    CHECK_CUSPARSE( hipsparseCreateSpVec(&vecX, size, nnz, dX_indices, dX_values,
                                        HIPSPARSE_INDEX_32I,
                                        HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    // Create dense vector y
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vecY, size, dY, HIP_R_32F) )

    // execute Scatter
    CHECK_CUSPARSE( hipsparseScatter(handle, vecX, vecY) )

    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpVec(vecX) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecY) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
    // device result check
    CHECK_CUDA( hipMemcpy(hY, dY, nnz * sizeof(float),
                           hipMemcpyDeviceToHost) )
    int correct = 1;
    for (int i = 0; i < nnz; i++) {
        if (hY[i] != hY_result[i]) {
            correct = 0;
            break;
        }
    }
    if (correct)
        printf("scatter_example test PASSED\n");
    else
        printf("scatter_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dX_indices) )
    CHECK_CUDA( hipFree(dX_values)  )
    CHECK_CUDA( hipFree(dY) )
    return EXIT_SUCCESS;
}