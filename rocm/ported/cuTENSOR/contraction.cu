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

#include <assert.h>
#include <stdlib.h>

#include <vector>
#include <iostream>
#include <unordered_map>

#include <hip/hip_runtime.h>
#include <hiptensor/hiptensor.h>

#include "utils.cuh"

int main()
try
{
    typedef float floatTypeA;
    typedef float floatTypeB;
    typedef float floatTypeC;

    hiptensorDataType_t typeA = HIPTENSOR_R_32F;
    hiptensorDataType_t typeB = HIPTENSOR_R_32F;
    hiptensorDataType_t typeC = HIPTENSOR_R_32F;
    const hiptensorComputeDescriptor_t descCompute = HIPTENSOR_COMPUTE_DESC_32F;

    /**********************
     * Computing: C_{m,u,n,v} = alpha * A_{m,h,k,n} B_{u,k,v,h} + beta * C_{m,u,n,v}
     **********************/

    std::vector<int> modeC{'m','u','n','v'};
    std::vector<int> modeA{'m','h','k','n'};
    std::vector<int> modeB{'u','k','v','h'};
    int nmodeA = modeA.size();
    int nmodeB = modeB.size();
    int nmodeC = modeC.size();

    std::unordered_map<int, int64_t> extent;
    extent['m'] = 96;
    extent['n'] = 96;
    extent['u'] = 96;
    extent['v'] = 64;
    extent['h'] = 64;
    extent['k'] = 64;

    double gflops = (2.0 * extent['m'] * extent['n'] * extent['u'] * extent['v'] * extent['k'] * extent['h']) /1e9;

    std::vector<int64_t> extentC;
    for (auto mode : modeC)
        extentC.push_back(extent[mode]);
    std::vector<int64_t> extentA;
    for (auto mode : modeA)
        extentA.push_back(extent[mode]);
    std::vector<int64_t> extentB;
    for (auto mode : modeB)
        extentB.push_back(extent[mode]);

    /**********************
     * Allocating data
     **********************/

    size_t elementsA = 1;
    for (auto mode : modeA)
        elementsA *= extent[mode];
    size_t elementsB = 1;
    for (auto mode : modeB)
        elementsB *= extent[mode];
    size_t elementsC = 1;
    for (auto mode : modeC)
        elementsC *= extent[mode];

    size_t sizeA = sizeof(floatTypeA) * elementsA;
    size_t sizeB = sizeof(floatTypeB) * elementsB;
    size_t sizeC = sizeof(floatTypeC) * elementsC;
    printf("Total memory: %.2f GiB\n", (sizeA + sizeB + sizeC)/1024./1024./1024);

    auto A_d = cuda_alloc     <floatTypeA>(elementsA); 
    auto B_d = cuda_alloc     <floatTypeB>(elementsB); 
    auto C_d = cuda_alloc     <floatTypeC>(elementsC); 
   
    auto A   = cuda_host_alloc<floatTypeA>(elementsA); 
    auto B   = cuda_host_alloc<floatTypeB>(elementsB); 
    auto C   = cuda_host_alloc<floatTypeC>(elementsC); 

    /*******************
     * Initialize data
     *******************/

    // Random data.
    std::generate(A.get(),A.get()+elementsA, randomgen<floatTypeA>() );
    std::generate(B.get(),B.get()+elementsB, randomgen<floatTypeB>() );
    std::generate(C.get(),C.get()+elementsC, randomgen<floatTypeC>() );

    handle_error(hipMemcpy(A_d.get(), A.get(), sizeA, hipMemcpyHostToDevice));
    handle_error(hipMemcpy(B_d.get(), B.get(), sizeB, hipMemcpyHostToDevice));
    handle_error(hipMemcpy(C_d.get(), C.get(), sizeC, hipMemcpyHostToDevice));

    const uint32_t kAlignment = 128; // Alignment of the global-memory device pointers (bytes)
    assert(uintptr_t(A_d.get()) % kAlignment == 0);
    assert(uintptr_t(B_d.get()) % kAlignment == 0);
    assert(uintptr_t(C_d.get()) % kAlignment == 0);

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
                 NULL,/*stride*/
                 typeA, kAlignment));
    auto guardDescA = finally( [&descA]() { hiptensorDestroyTensorDescriptor(descA); } );

    hiptensorTensorDescriptor_t descB;
    handle_error(hiptensorCreateTensorDescriptor(handle,
                 &descB,
                 nmodeB,
                 extentB.data(),
                 NULL,/*stride*/
                 typeB, kAlignment));
    auto guardDescB = finally( [&descB]() { hiptensorDestroyTensorDescriptor(descB); } );

    hiptensorTensorDescriptor_t descC;
    handle_error(hiptensorCreateTensorDescriptor(handle,
                 &descC,
                 nmodeC,
                 extentC.data(),
                 NULL,/*stride*/
                 typeC, kAlignment));
    auto guardDescC = finally( [&descC]() { hiptensorDestroyTensorDescriptor(descC); } );

    /*******************************
     * Create Contraction Descriptor
     *******************************/

    hiptensorOperationDescriptor_t desc;
    handle_error(hiptensorCreateContraction(handle, 
                 &desc,
                 descA, modeA.data(), /* unary operator A*/HIPTENSOR_OP_IDENTITY,
                 descB, modeB.data(), /* unary operator B*/HIPTENSOR_OP_IDENTITY,
                 descC, modeC.data(), /* unary operator C*/HIPTENSOR_OP_IDENTITY,
                 descC, modeC.data(),
                 descCompute));
    auto guardDesc = finally( [&desc]() { hiptensorDestroyOperationDescriptor(desc); } );

    /*****************************
     * Optional (but recommended): ensure that the scalar type is correct.
     *****************************/

    hiptensorDataType_t scalarType;
    handle_error(hiptensorOperationDescriptorGetAttribute(handle,
        desc,
        HIPTENSOR_OPERATION_DESCRIPTOR_SCALAR_TYPE,
        (void*)&scalarType,
        sizeof(scalarType)));

    assert(scalarType == HIPTENSOR_R_32F);
    typedef float floatTypeCompute;
    floatTypeCompute alpha = (floatTypeCompute)1.1f;
    floatTypeCompute beta  = (floatTypeCompute)0.f;

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
    auto guardStream = finally( [&stream]() { hipStreamDestroy(stream); } );

    double minTimeCUTENSOR = 1e100;
    for (int i=0; i < 3; ++i)
    {
        handle_error(hipMemcpy(C_d.get(), C.get(), sizeC, hipMemcpyHostToDevice));
        handle_error(hipDeviceSynchronize());

        // Set up timing
        GPUTimer timer(stream);

        handle_error(hiptensorContract(handle,
                               plan,
                               (void*) &alpha, A_d.get(), B_d.get(),
                               (void*) &beta,  C_d.get(), C_d.get(), 
                               work.get(), actualWorkspaceSize, stream));

        // Synchronize and measure timing
        auto time = timer.seconds(stream);
        minTimeCUTENSOR = (minTimeCUTENSOR < time) ? minTimeCUTENSOR : time;
    }

    /*************************/

    double transferedBytes = sizeC + sizeA + sizeB;
    transferedBytes += ((float) beta != 0.f) ? sizeC : 0;
    transferedBytes /= 1e9;
    printf("cuTensor: %.2f GFLOPs/s %.2f GB/s\n", gflops / minTimeCUTENSOR, transferedBytes/ minTimeCUTENSOR);

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

