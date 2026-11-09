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
#include <stdint.h>           // int64_t

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
    //==========================================================================
    // INITIALIZATION
    //==========================================================================
    // Host problem definition
    float   result;
    int64_t size       = 65536; // 2^16
    int64_t nnz        = 65536; // 2^16
    int*    hX_indices = (int*) malloc(nnz * sizeof(int));
    for (int i = 0; i < nnz; i++)
        hX_indices[i] = i;
    //--------------------------------------------------------------------------
    // Device memory management
    int   *dX_indices;
    float *dY, *dX_values;
    CHECK_CUDA( hipMalloc((void**) &dX_indices, nnz * sizeof(int))    )
    CHECK_CUDA( hipMalloc((void**) &dX_values,  nnz * sizeof(float))  )
    CHECK_CUDA( hipMalloc((void**) &dY,         size * sizeof(float)) )

    CHECK_CUDA( hipMemcpy(dX_indices, hX_indices, nnz * sizeof(int),
                           hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    // Timer setup
    float       cuda_elapsed_ms  = 0;
    float       graph_elapsed_ms = 0;
    hipEvent_t start_event, stop_event;
    CHECK_CUDA( hipEventCreate(&start_event) )
    CHECK_CUDA( hipEventCreate(&stop_event) )
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

    CHECK_CUSPARSE( hipsparseSpVV_bufferSize(handle,
                                            HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                            vecX, vecY, &result, HIP_R_32F,
                                            &bufferSize) )
    CHECK_CUDA( hipMalloc(&dBuffer, bufferSize) )

    CHECK_CUSPARSE( hipsparseSpVV(handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                 vecX, vecY, &result, HIP_R_32F, dBuffer) )

    //==========================================================================
    // STANDARD CALL
    //==========================================================================
    CHECK_CUDA( hipEventRecord(start_event, NULL) )

    // execute SpVV
    for (int j = 0; j < 1000; j++) {
        CHECK_CUSPARSE( hipsparseSpVV(handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                     vecX, vecY, &result, HIP_R_32F, dBuffer) )
    }

    CHECK_CUDA( hipEventRecord(stop_event, NULL) )
    CHECK_CUDA( hipEventSynchronize(stop_event) )
    CHECK_CUDA( hipEventElapsedTime(&cuda_elapsed_ms, start_event,
                                     stop_event) )
    //==========================================================================
    // GRAPH CAPTURE
    //==========================================================================
    hipGraph_t     graph;
    hipStream_t    stream;
    hipGraphExec_t graph_exec;
    CHECK_CUDA( hipStreamCreate(&stream) )
    CHECK_CUSPARSE( hipsparseSetStream(handle, stream) )
    CHECK_CUDA( hipStreamBeginCapture(stream, hipStreamCaptureModeGlobal) )

    for (int j = 0; j < 1000; j++) {
        CHECK_CUSPARSE( hipsparseSpVV(handle, HIPSPARSE_OPERATION_NON_TRANSPOSE,
                                     vecX, vecY, &result, HIP_R_32F, dBuffer) )
    }

    CHECK_CUDA( hipStreamEndCapture(stream, &graph) )
    CHECK_CUDA( hipDeviceSynchronize() )
    CHECK_CUDA( hipGetLastError() )
    CHECK_CUDA( hipGraphInstantiateWithFlags(&graph_exec, graph, 0) )
    //==========================================================================
    // GRAPH EXECUTION
    //==========================================================================
    CHECK_CUDA( hipEventRecord(start_event, NULL) )

    CHECK_CUDA( hipGraphLaunch(graph_exec, stream) )

    CHECK_CUDA( hipEventRecord(stop_event, NULL) )
    CHECK_CUDA( hipEventSynchronize(stop_event) )
    CHECK_CUDA( hipEventElapsedTime(&graph_elapsed_ms, start_event,
                                     stop_event) )
    //==========================================================================
    //==========================================================================
    // destroy events
    CHECK_CUDA( hipEventDestroy(start_event) )
    CHECK_CUDA( hipEventDestroy(stop_event) )
    // destroy graph
    CHECK_CUDA( hipDeviceSynchronize() )
    CHECK_CUDA( hipGraphExecDestroy(graph_exec) )
    CHECK_CUDA( hipGraphDestroy(graph) )
    CHECK_CUDA( hipStreamDestroy(stream) )
    // destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpVec(vecX) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecY) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    // device memory deallocation
    CHECK_CUDA( hipFree(dX_indices) )
    CHECK_CUDA( hipFree(dX_values)  )
    CHECK_CUDA( hipFree(dY) )
    CHECK_CUDA( hipFree(dBuffer) )
    free(hX_indices);
    //--------------------------------------------------------------------------
    // device result check
    float speedup = ((cuda_elapsed_ms - graph_elapsed_ms) / cuda_elapsed_ms)
                    * 100.0f;
    printf("\nStandard call:    %.1f ms"
           "\nGraph Capture:    %.1f ms"
           "\nPerf improvement: %.1f%%\n\n",
           cuda_elapsed_ms, graph_elapsed_ms, speedup);
    //--------------------------------------------------------------------------
    return EXIT_SUCCESS;
}