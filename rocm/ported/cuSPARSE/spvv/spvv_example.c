#include "observe.hpp"
#include <string>
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

#include "hip/hip_runtime.h"
#include <hip/hip_runtime_api.h> // cudaMalloc, cudaMemcpy, etc.
#include <hipsparse.h>         // hipsparseSpVV
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
// MIGRATION_BATCH2: default is unchanged original input and mathematical GPU API.
const std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";

    // Host problem definition
    int   size         = 8;
    int   nnz          = 4;
    int   hX_indices[] = { 0, 3, 4, 7 };
    float hX_values[]  = { 1.0f, 2.0f, 3.0f, 4.0f };
    float hY[]         = { 1.0f, 2.0f, 3.0f, 4.0f,
                           5.0f, 6.0f, 7.0f, 8.0f };
    float result       = { 56.0f };
    float tmp_result;
    //--------------------------------------------------------------------------
if(migration_case=="changed-values"){for(auto& x:hX_values)x*=-0.5f;result*=-0.5f;}
migration_observer::emit("input_X_indices",hX_indices,nnz);
migration_observer::emit("input_X",hX_values,nnz);
migration_observer::emit("input_Y",hY,size);
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
    size_t               bufferSize = 0;
    void*                dBuffer    = NULL;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse vector X
    CHECK_CUSPARSE( hipsparseCreateSpVec(&vecX, size, nnz, dX_indices, dX_values,
                                        HIPSPARSE_INDEX_32I,
                                        HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    // Create dense vector y
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vecY, size, dY, HIP_R_32F) )

    // execute SpVV
    CHECK_CUSPARSE( hipsparseSpVV_bufferSize(handle,
                                            HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                            vecX, vecY, &tmp_result, HIP_R_32F,
                                            &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )

    CHECK_CUSPARSE( hipsparseSpVV(handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 vecX, vecY, &tmp_result, HIP_R_32F, dBuffer) )

    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpVec(vecX) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecY) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    //--------------------------------------------------------------------------
migration_observer::emit("result",&tmp_result,1);
    // device result check
    if (tmp_result == result)
        printf("spvv_example test PASSED\n");
    else
        printf("spvv_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dX_indices) )
    CHECK_CUDA( hipFree(dX_values)  )
    CHECK_CUDA( hipFree(dY) )
    CHECK_CUDA( hipFree(dBuffer) )
    return EXIT_SUCCESS;
}