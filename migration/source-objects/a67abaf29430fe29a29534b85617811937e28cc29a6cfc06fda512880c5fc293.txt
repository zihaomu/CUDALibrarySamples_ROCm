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

#include <iostream>
#include <unordered_map>
#include <vector>

#include <hip/hip_runtime.h>
#include <hiptensor/hiptensor.h>

#include "utils.cuh"


int main()
try
{
    typedef float floatTypeA;
    typedef float floatTypeB;
    typedef float floatTypeC;
    typedef float floatTypeD;

    hiptensorDataType_t typeA = HIPTENSOR_R_32F;
    hiptensorDataType_t typeB = HIPTENSOR_R_32F;
    hiptensorDataType_t typeC = HIPTENSOR_R_32F;
    hiptensorDataType_t typeD = HIPTENSOR_R_32F;
    const hiptensorComputeDescriptor_t descCompute = HIPTENSOR_COMPUTE_DESC_32F;

    /**********************
     * Computing: D_{m,n,b,r,a} = alpha * A_{m,k,a,j,b,i} B_{k,n,i} C_{r,j} + beta * D_{m,n,b,r,a}
     **********************/

    std::vector<int> modeD{'m','n','b','r','a'};
    std::vector<int> modeA{'m','k','a','j','b','i'};
    std::vector<int> modeB{'k','n','i'};
    std::vector<int> modeC{'r','j'};
    int nmodeA = modeA.size();
    int nmodeB = modeB.size();
    int nmodeC = modeC.size();
    int nmodeD = modeD.size();

    std::unordered_map<int, int64_t> extent;
    extent['m'] = 256;
    extent['a'] = 32;
    extent['b'] = 32;
    extent['n'] = 64;
    extent['r'] = 64;
    extent['k'] = 8;
    extent['i'] = 8;
    extent['j'] = 64;

    double gflopsFirstContraction  = 2.0 * extent['m'] * extent['a'] * extent['b'] * extent['j'] * extent['n'] * extent['k'] * extent['i'] / 1e9;
    double gflopsSecondContraction = 2.0 * extent['m'] * extent['a'] * extent['b'] * extent['n'] * extent['r'] * extent['j'] / 1e9;
    double gflops = gflopsFirstContraction + gflopsSecondContraction;

    std::vector<int64_t> extentD;
    for (auto mode : modeD)
        extentD.push_back(extent[mode]);
    std::vector<int64_t> extentA;
    for (auto mode : modeA)
        extentA.push_back(extent[mode]);
    std::vector<int64_t> extentB;
    for (auto mode : modeB)
        extentB.push_back(extent[mode]);
    std::vector<int64_t> extentC;
    for (auto mode : modeC)
        extentC.push_back(extent[mode]);

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
    size_t elementsD = 1;
    for (auto mode : modeD)
        elementsD *= extent[mode];

    size_t sizeA = sizeof(floatTypeA) * elementsA;
    size_t sizeB = sizeof(floatTypeB) * elementsB;
    size_t sizeC = sizeof(floatTypeC) * elementsC;
    size_t sizeD = sizeof(floatTypeD) * elementsD;
    printf("Total memory: %.2f GiB\n", (sizeA + sizeB + sizeC + sizeD)/1024./1024./1024);

    auto A_d = cuda_alloc     <floatTypeA>(elementsA); 
    auto B_d = cuda_alloc     <floatTypeB>(elementsB); 
    auto C_d = cuda_alloc     <floatTypeC>(elementsC); 
    auto D_d = cuda_alloc     <floatTypeD>(elementsD); 
   
    auto A   = cuda_host_alloc<floatTypeA>(elementsA); 
    auto B   = cuda_host_alloc<floatTypeB>(elementsB); 
    auto C   = cuda_host_alloc<floatTypeC>(elementsC); 
    auto D   = cuda_host_alloc<floatTypeD>(elementsD); 

    /*******************
     * Initialize data
     *******************/

    // Random data.
    std::generate(A.get(),A.get()+elementsA, randomgen<floatTypeA>() );
    std::generate(B.get(),B.get()+elementsB, randomgen<floatTypeB>() );
    std::generate(C.get(),C.get()+elementsC, randomgen<floatTypeC>() );
    std::generate(D.get(),D.get()+elementsD, randomgen<floatTypeD>() );

    handle_error(hipMemcpy(A_d.get(), A.get(), sizeA, hipMemcpyHostToDevice));
    handle_error(hipMemcpy(B_d.get(), B.get(), sizeB, hipMemcpyHostToDevice));
    handle_error(hipMemcpy(C_d.get(), C.get(), sizeC, hipMemcpyHostToDevice));
    handle_error(hipMemcpy(D_d.get(), D.get(), sizeD, hipMemcpyHostToDevice));

    const uint32_t kAlignment = 128; // Alignment of the global-memory device pointers (bytes)
    assert(uintptr_t(A_d.get()) % kAlignment == 0);
    assert(uintptr_t(B_d.get()) % kAlignment == 0);
    assert(uintptr_t(C_d.get()) % kAlignment == 0);
    assert(uintptr_t(D_d.get()) % kAlignment == 0);

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

    hiptensorTensorDescriptor_t descD;
    handle_error(hiptensorCreateTensorDescriptor(handle,
                 &descD,
                 nmodeD,
                 extentD.data(),
                 NULL,/*stride*/
                 typeD, kAlignment));
    auto guardDescD = finally( [&descD]() { hiptensorDestroyTensorDescriptor(descD); } );

    /*******************************
     * Create Contraction Descriptor
     *******************************/

    hiptensorOperationDescriptor_t desc;
    handle_error(hiptensorCreateContractionTrinary(handle, 
                 &desc,
                 descA, modeA.data(), /* unary operator A*/HIPTENSOR_OP_IDENTITY,
                 descB, modeB.data(), /* unary operator B*/HIPTENSOR_OP_IDENTITY,
                 descC, modeC.data(), /* unary operator C*/HIPTENSOR_OP_IDENTITY,
                 descD, modeD.data(), /* unary operator D*/HIPTENSOR_OP_IDENTITY,
                 descD, modeD.data(),
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
    auto guardStream = finally( [&stream](){ hipStreamDestroy(stream); } );

    double minTimeCUTENSOR = 1e100;
    for (int i=0; i < 3; ++i)
    {
        handle_error(hipMemcpy(C_d.get(), C.get(), sizeC, hipMemcpyHostToDevice));
        handle_error(hipDeviceSynchronize());

        // Set up timing
        GPUTimer timer(stream);

        handle_error(hiptensorContractTrinary(handle,
                               plan,
                               (void*) &alpha, A_d.get(), B_d.get(), C_d.get(),
                               (void*) &beta,  D_d.get(), D_d.get(),
                               work.get(), actualWorkspaceSize, stream));

        // Synchronize and measure timing
        auto time = timer.seconds(stream);
        minTimeCUTENSOR = (minTimeCUTENSOR < time) ? minTimeCUTENSOR : time;
    }

    /*************************/

    double transferedBytes = sizeA + sizeB + sizeC + sizeD;
    transferedBytes += ((float) beta != 0.f) ? sizeD : 0;
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

