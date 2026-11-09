#include "observe.hpp"
#include <string>
#include <vector>
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

// Graph qualification body, appended to each backend's original licensed prefix.
// MIGRATION_BATCH3: deterministic inputs and device-result stream capture.
int main(void) {
    const std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";
    int64_t size=migration_case=="original"?65536:migration_case=="sparse-small"?37:32;
    int64_t nnz=migration_case=="original"?65536:migration_case=="sparse-small"?17:16;
    int capture_calls=migration_case=="original"?1000:7;
    std::vector<int> indices(nnz);
    std::vector<float> x(nnz),y(size);
    for(int i=0;i<nnz;++i){
        indices[i]=migration_case=="original"?i:2*i;
        x[i]=migration_case=="cancellation"?(i%2?-1.f:1.f)*(1+i%3)/4.f:1.f+float(i%7)/8.f;
    }
    for(int i=0;i<size;++i)y[i]=float(i%11-5)/4.f;
    migration_observer::emit("input_size",&size,1);
    migration_observer::emit("input_indices",indices.data(),indices.size());
    migration_observer::emit("input_X",x.data(),x.size());
    int *d_indices=nullptr;
    float *d_x=nullptr,*d_y=nullptr,*d_result=nullptr;
    void* buffer=nullptr;
    CHECK_CUDA(hipMalloc((void**)&d_indices,nnz*sizeof(int)))
    CHECK_CUDA(hipMalloc((void**)&d_x,nnz*sizeof(float)))
    CHECK_CUDA(hipMalloc((void**)&d_y,size*sizeof(float)))
    CHECK_CUDA(hipMalloc((void**)&d_result,sizeof(float)))
    CHECK_CUDA(hipMemcpy(d_indices,indices.data(),nnz*sizeof(int),hipMemcpyHostToDevice))
    CHECK_CUDA(hipMemcpy(d_x,x.data(),nnz*sizeof(float),hipMemcpyHostToDevice))
    CHECK_CUDA(hipMemcpy(d_y,y.data(),size*sizeof(float),hipMemcpyHostToDevice))
    hipsparseHandle_t handle;
    hipsparseSpVecDescr_t vecX;
    hipsparseDnVecDescr_t vecY;
    CHECK_CUSPARSE(hipsparseCreate(&handle))
    // Host pointer mode may synchronize/copy results during capture. The graph
    // must retain a device scalar, copied to the host only after actual replay.
    CHECK_CUSPARSE(hipsparseSetPointerMode(handle,HIPSPARSE_POINTER_MODE_DEVICE))
    CHECK_CUSPARSE(hipsparseCreateSpVec(&vecX,size,nnz,d_indices,d_x,
        HIPSPARSE_INDEX_32I,HIPSPARSE_INDEX_BASE_ZERO,HIP_R_32F))
    CHECK_CUSPARSE(hipsparseCreateDnVec(&vecY,size,d_y,HIP_R_32F))
    size_t buffer_size=0;
    CHECK_CUSPARSE(hipsparseSpVV_bufferSize(handle,HIPSPARSE_OPERATION_NON_TRANSPOSE,
        vecX,vecY,d_result,HIP_R_32F,&buffer_size))
    CHECK_CUDA(hipMalloc(&buffer,buffer_size))
    for(int i=0;i<capture_calls;++i){
        CHECK_CUSPARSE(hipsparseSpVV(handle,HIPSPARSE_OPERATION_NON_TRANSPOSE,
            vecX,vecY,d_result,HIP_R_32F,buffer))
    }
    float result;
    CHECK_CUDA(hipMemcpy(&result,d_result,sizeof(float),hipMemcpyDeviceToHost))
    migration_observer::emit("standard_result",&result,1);
    hipStream_t stream;
    hipGraph_t graph;
    hipGraphExec_t executable;
    CHECK_CUDA(hipStreamCreate(&stream))
    CHECK_CUSPARSE(hipsparseSetStream(handle,stream))
    CHECK_CUDA(hipStreamBeginCapture(stream,hipStreamCaptureModeGlobal))
    for(int i=0;i<capture_calls;++i){
        CHECK_CUSPARSE(hipsparseSpVV(handle,HIPSPARSE_OPERATION_NON_TRANSPOSE,
            vecX,vecY,d_result,HIP_R_32F,buffer))
    }
    CHECK_CUDA(hipStreamEndCapture(stream,&graph))
    size_t node_count=0,kernel_count=0;
    CHECK_CUDA(hipGraphGetNodes(graph,nullptr,&node_count))
    std::vector<hipGraphNode_t> nodes(node_count);
    CHECK_CUDA(hipGraphGetNodes(graph,nodes.data(),&node_count))
    for(auto node:nodes){
        hipGraphNodeType type;
        CHECK_CUDA(hipGraphNodeGetType(node,&type))
        if(type==hipGraphNodeTypeKernel)++kernel_count;
    }
    migration_observer::emit("graph_nodes",&node_count,1);
    migration_observer::emit("graph_kernels",&kernel_count,1);
    migration_observer::emit("capture_calls",&capture_calls,1);
    if(!node_count || kernel_count<size_t(capture_calls))return EXIT_FAILURE;
    CHECK_CUDA(hipGraphInstantiateWithFlags(&executable,graph,0))
    int replay_count=0;
    for(int replay=0;replay<3;++replay){
        if(replay==1)for(int i=0;i<size;++i)y[i]=2*y[i]+1.f+float(i%5)/8.f;
        if(replay==2)for(auto& v:y)v=0;
        migration_observer::emit(("input_Y_"+std::to_string(replay)).c_str(),y.data(),y.size());
        // The input is updated outside capture, on the same stream as replay.
        CHECK_CUDA(hipMemcpyAsync(d_y,y.data(),size*sizeof(float),hipMemcpyHostToDevice,stream))
        CHECK_CUDA(hipGraphLaunch(executable,stream))
        CHECK_CUDA(hipMemcpyAsync(&result,d_result,sizeof(float),hipMemcpyDeviceToHost,stream))
        CHECK_CUDA(hipStreamSynchronize(stream))
        ++replay_count;
        migration_observer::emit(("replay_"+std::to_string(replay)).c_str(),&result,1);
    }
    migration_observer::emit("replay_count",&replay_count,1);
    CHECK_CUDA(hipGraphExecDestroy(executable))
    CHECK_CUDA(hipGraphDestroy(graph))
    CHECK_CUDA(hipStreamDestroy(stream))
    CHECK_CUSPARSE(hipsparseDestroySpVec(vecX))
    CHECK_CUSPARSE(hipsparseDestroyDnVec(vecY))
    CHECK_CUSPARSE(hipsparseDestroy(handle))
    CHECK_CUDA(hipFree(d_indices))
    CHECK_CUDA(hipFree(d_x))
    CHECK_CUDA(hipFree(d_y))
    CHECK_CUDA(hipFree(d_result))
    CHECK_CUDA(hipFree(buffer))
    return EXIT_SUCCESS;
}
