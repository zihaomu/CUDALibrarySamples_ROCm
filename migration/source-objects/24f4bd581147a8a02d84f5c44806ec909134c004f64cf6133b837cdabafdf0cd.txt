/*
 * SPDX-FileCopyrightText: Copyright (c) 2019-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#include <iostream>
#include <unordered_map>
#include <stdexcept>
#include <memory>
#include <vector>

#include <hiptensor/hiptensor.h>

#include "utils.cuh"


int main()
try
{
    typedef float floatTypeA;
    typedef float floatTypeB;
    typedef float floatTypeC;
    typedef float floatTypeCompute;

    hiptensorDataType_t typeA = HIPTENSOR_R_32F;
    hiptensorDataType_t typeC = HIPTENSOR_R_32F;
    const hiptensorComputeDescriptor_t descCompute = HIPTENSOR_COMPUTE_DESC_32F;

    floatTypeCompute alpha = (floatTypeCompute)1.1f;
    floatTypeCompute beta  = (floatTypeCompute)0.f;

    /**********************
     * Computing (partial) reduction : C_{m,v} = alpha * A_{m,h,k,v} + beta * C_{m,v}
     *********************/

    std::vector<int32_t> modeA{'m','h','k','v'};
    std::vector<int32_t> modeC{'m','v'};
    int32_t nmodeA = modeA.size();
    int32_t nmodeC = modeC.size();

    std::unordered_map<int32_t, int64_t> extent;
    extent['m'] = 196;
    extent['v'] = 64;
    extent['h'] = 256;
    extent['k'] = 64;

    std::vector<int64_t> extentC;
    for (auto mode : modeC)
        extentC.push_back(extent[mode]);
    std::vector<int64_t> extentA;
    for (auto mode : modeA)
        extentA.push_back(extent[mode]);

    /**********************
     * Allocating data
     *********************/

    size_t elementsA = 1;
    for (auto mode : modeA)
        elementsA *= extent[mode];
    size_t elementsC = 1;
    for (auto mode : modeC)
        elementsC *= extent[mode];

    size_t sizeA = sizeof(floatTypeA) * elementsA;
    size_t sizeC = sizeof(floatTypeC) * elementsC;
    printf("Total memory: %.2f GiB\n",(sizeA + sizeC)/1024./1024./1024);

    auto A_d = cuda_alloc     <floatTypeA>(elementsA); 
    auto C_d = cuda_alloc     <floatTypeC>(elementsC); 
    auto A   = cuda_host_alloc<floatTypeA>(elementsA); 
    auto C   = cuda_host_alloc<floatTypeC>(elementsC); 

    const uint32_t kAlignment = 256; // Alignment of the global-memory device pointers (bytes)
    assert(uintptr_t(A_d.get()) % kAlignment == 0);
    assert(uintptr_t(C_d.get()) % kAlignment == 0);

    /*******************
     * Initialize data
     *******************/

    std::generate(A.get(),A.get()+elementsA, randomgen<floatTypeA>() );
    std::generate(C.get(),C.get()+elementsC, randomgen<floatTypeC>() );

    handle_error(hipMemcpy(C_d.get(),C.get(),sizeC,hipMemcpyHostToDevice));
    handle_error(hipMemcpy(A_d.get(),A.get(),sizeA,hipMemcpyHostToDevice));

    /*************************
     * cuTENSOR
     *************************/ 

    hiptensorHandle_t handle;
    handle_error(hiptensorCreate(&handle)); 
    auto guardHandle = finally( [&handle]() { hiptensorDestroy(handle); } );

    /**********************
     * Create Tensor Descriptors
     **********************/

    hiptensorTensorDescriptor_t descA;
    handle_error(hiptensorCreateTensorDescriptor(handle,
                 &descA,
                 nmodeA,
                 extentA.data(),
                 NULL /* stride */,
                 typeA, kAlignment));
    auto guardDescA = finally( [&descA]() { hiptensorDestroyTensorDescriptor(descA); } );

    hiptensorTensorDescriptor_t descC;
    handle_error(hiptensorCreateTensorDescriptor(handle,
                 &descC,
                 nmodeC,
                 extentC.data(),
                 NULL /* stride */,
                 typeC, kAlignment));
    auto guardDescC = finally( [&descC]() { hiptensorDestroyTensorDescriptor(descC); } );

    const hiptensorOperator_t opReduce = HIPTENSOR_OP_ADD;

    /*******************************
     * Create Reduction Descriptor
     *******************************/

    hiptensorOperationDescriptor_t desc;
    handle_error(hiptensorCreateReduction(
                 handle, &desc,
                 descA, modeA.data(), HIPTENSOR_OP_IDENTITY,
                 descC, modeC.data(), HIPTENSOR_OP_IDENTITY,
                 descC, modeC.data(),
                 opReduce, descCompute));
    auto guardDesc = finally( [&desc]() { hiptensorDestroyOperationDescriptor(desc); } );

    /**************************
    * Set the algorithm to use
    ***************************/

    const hiptensorAlgo_t algo = HIPTENSOR_ALGO_DEFAULT;

    hiptensorPlanPreference_t planPref;
    handle_error(hiptensorCreatePlanPreference(
                               handle,
                               &planPref,
                               algo,
                               HIPTENSOR_JIT_MODE_NONE));
    auto guardPlanPref = finally( [&planPref]() { hiptensorDestroyPlanPreference(planPref); } );

    /**********************
     * Query workspace estimate
     **********************/

    uint64_t workspaceSizeEstimate = 0;
    const hiptensorWorksizePreference_t workspacePref = HIPTENSOR_WORKSPACE_DEFAULT;
    handle_error(hiptensorEstimateWorkspaceSize(handle,
                                          desc,
                                          planPref,
                                          workspacePref,
                                          &workspaceSizeEstimate));

    /**************************
     * Create Contraction Plan
     **************************/

    hiptensorPlan_t plan;
    handle_error(hiptensorCreatePlan(handle,
                 &plan,
                 desc,
                 planPref,
                 workspaceSizeEstimate));
    auto guardPlan = finally( [&plan]() { hiptensorDestroyPlan(plan); } );

    /**************************
     * Optional: Query information about the created plan
     **************************/

    // query actually used workspace
    uint64_t actualWorkspaceSize = 0;
    handle_error(hiptensorPlanGetAttribute(handle,
        plan,
        HIPTENSOR_PLAN_REQUIRED_WORKSPACE,
        &actualWorkspaceSize,
        sizeof(actualWorkspaceSize)));

    // At this point the user knows exactly how much memory is need by the operation and
    // only the smaller actual workspace needs to be allocated
    assert(actualWorkspaceSize <= workspaceSizeEstimate);

    auto work = cuda_alloc<char>(actualWorkspaceSize);
    assert(uintptr_t(work.get()) % 128 == 0); // workspace must be aligned to 128 byte-boundary

    /**********************
     * Run
     **********************/

    hipStream_t stream;
    handle_error(hipStreamCreate(&stream));
    auto guardStream = finally( [&stream]() { hipStreamDestroy(stream); });

    double minTimeCUTENSOR = 1e100;
    for(int i=0; i < 3; ++i)
    {
        handle_error(hipMemcpyAsync(C_d.get(),C.get(), sizeC, hipMemcpyHostToDevice,stream));
        GPUTimer timer(stream);
        handle_error(hiptensorReduce(handle, plan,
                (const void*)&alpha, A_d.get(),
                (const void*)&beta,  C_d.get(), 
                                     C_d.get(), work.get(), actualWorkspaceSize, stream));
        auto time = timer.seconds(stream); // Synchronise and measure time.
        minTimeCUTENSOR = (minTimeCUTENSOR < time) ? minTimeCUTENSOR : time;
    }

    /*************************/

    double transferedBytes = sizeC + sizeA;
    transferedBytes += ((float) beta != 0.f) ? sizeC : 0;
    transferedBytes /= 1e9;
    printf("cuTensor: %.2f GB/s\n", transferedBytes / minTimeCUTENSOR);

    return EXIT_SUCCESS;
}
catch ( std::exception &ex )
{
    std::cerr << "Exception caught! Exiting." << std::endl;
    std::cerr << ex.what() << std::endl;
    return EXIT_FAILURE;
}
catch ( ... )
{
    std::cerr << "Unknown exception caught! Exiting." << std::endl;
    return EXIT_FAILURE;
}

