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

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#include <algorithm>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

#include <hip/hip_runtime.h>
#include <hiptensor/hiptensor.h>

#include "utils.cuh"

int main()
try
{
    typedef float floatTypeA;
    typedef float floatTypeC;
    typedef float floatTypeCompute;

    hiptensorDataType_t          const typeA       = HIPTENSOR_R_32F;
    hiptensorDataType_t          const typeC       = HIPTENSOR_R_32F;
    hiptensorComputeDescriptor_t const descCompute = HIPTENSOR_COMPUTE_DESC_32F;

    floatTypeCompute alpha = (floatTypeCompute)1.1f;
    floatTypeCompute gamma = (floatTypeCompute)1.2f;

    /**********************
     * Computing: C_{a,b,c} = alpha * A_{b,a,c}  + gamma * C_{a,b,c}
     **********************/

    std::vector<int> modeC{'a','b','c'};
    std::vector<int> modeA{'c','b','a'};
    int nmodeA = modeA.size();
    int nmodeC = modeC.size();

    std::unordered_map<int, int64_t> extent;
    extent['a'] = 400;
    extent['b'] = 200;
    extent['c'] = 300;

    std::vector<int64_t> extentA;
    for (auto mode : modeA)
        extentA.push_back(extent[mode]);
    std::vector<int64_t> extentC;
    for (auto mode : modeC)
        extentC.push_back(extent[mode]);

    /**********************
     * Allocating data
     **********************/

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
    auto D_d = cuda_alloc     <floatTypeC>(elementsC); 

    auto A   = cuda_host_alloc<floatTypeA>(elementsA); 
    auto C   = cuda_host_alloc<floatTypeC>(elementsC); 

    uint32_t const kAlignment = 128;  // Alignment of the global-memory device pointers (bytes)
    assert(uintptr_t(A_d.get()) % kAlignment == 0);
    assert(uintptr_t(C_d.get()) % kAlignment == 0);

    /*******************
     * Initialize data
     *******************/

    std::generate(A.get(),A.get()+elementsA, randomgen<floatTypeA>() );
    std::generate(C.get(),C.get()+elementsC, randomgen<floatTypeC>() );

    handle_error(hipMemcpy2DAsync(C_d.get(), sizeC, C.get(), sizeC, sizeC, 1, hipMemcpyHostToDevice, nullptr));
    handle_error(hipMemcpy2DAsync(D_d.get(), sizeC, C.get(), sizeC, sizeC, 1, hipMemcpyHostToDevice, nullptr));
    handle_error(hipMemcpy2DAsync(A_d.get(), sizeA, A.get(), sizeA, sizeA, 1, hipMemcpyHostToDevice, nullptr));

    /*************************
     * Memcpy perf 
     *************************/

    double minTimeMEMCPY = 1e100;
    handle_error(hipDeviceSynchronize());
    GPUTimer timer;
    handle_error(hipMemcpy2DAsync(D_d.get(), sizeC, C_d.get(), sizeC, sizeC, 1, hipMemcpyDeviceToDevice, nullptr));
    handle_error(hipDeviceSynchronize());
    minTimeMEMCPY = timer.seconds();

    /*************************
     * cuTENSOR
     *************************/

    hiptensorHandle_t handle;
    handle_error(hiptensorCreate(&handle));
    auto guardHandle = finally( [&handle]() { hiptensorDestroy(handle); } );

    /**********************
     * Create Tensor Descriptors
     **********************/

    hiptensorTensorDescriptor_t  descA;
    handle_error(hiptensorCreateTensorDescriptor(handle,
                                                &descA, nmodeA, extentA.data(),
                                                nullptr /* stride */,
                                                typeA,
                                                kAlignment));
    auto guardDescA = finally( [&descA]() { hiptensorDestroyTensorDescriptor(descA); } );

    hiptensorTensorDescriptor_t  descC;
    handle_error(hiptensorCreateTensorDescriptor(handle,
                                                &descC, nmodeC, extentC.data(),
                                                nullptr /* stride */,
                                                typeC,
                                                kAlignment));
    auto guardDescC = finally( [&descC]() { hiptensorDestroyTensorDescriptor(descC); } );

    /*******************************
     * Create Elementwise Binary Descriptor
     *******************************/

    hiptensorOperationDescriptor_t  desc;
    handle_error(hiptensorCreateElementwiseBinary(handle, &desc,
                                                 descA, modeA.data(), /* unary operator A  */ HIPTENSOR_OP_IDENTITY,
                                                 descC, modeC.data(), /* unary operator C  */ HIPTENSOR_OP_IDENTITY,
                                                 descC, modeC.data(), /* unary operator AC */ HIPTENSOR_OP_ADD,
                                                 descCompute));
    auto guardDesc = finally( [&desc]() { hiptensorDestroyOperationDescriptor(desc); } );

    /*****************************
     * Optional (but recommended): ensure that the scalar type is correct.
     *****************************/

    hiptensorDataType_t scalarType;
    handle_error(hiptensorOperationDescriptorGetAttribute(handle, desc,
                                                         HIPTENSOR_OPERATION_DESCRIPTOR_SCALAR_TYPE,
                                                         (void*)&scalarType,
                                                         sizeof(scalarType)));

    assert(scalarType == HIPTENSOR_R_32F);

    /**************************
    * Set the algorithm to use
    ***************************/

    const hiptensorAlgo_t algo = HIPTENSOR_ALGO_DEFAULT;

    hiptensorPlanPreference_t  planPref;
    handle_error(hiptensorCreatePlanPreference(handle,
                                              &planPref,
                                              algo,
                                              HIPTENSOR_JIT_MODE_NONE));
    auto guardPlanPref = finally( [&planPref]() { hiptensorDestroyPlanPreference(planPref); } );

    /**************************
     * Create Plan
     **************************/

    hiptensorPlan_t  plan;
    handle_error(hiptensorCreatePlan(handle,
                                    &plan,
                                    desc,
                                    planPref,
                                    0 /* workspaceSizeLimit */));
    auto guardPlan = finally( [&plan]() { hiptensorDestroyPlan(plan); } );

    /**********************
     * Run
     **********************/

    double minTimeCUTENSOR = 1e100;
    for (int i = 0; i < 3; i++)
    {
        handle_error(hipMemcpy2DAsync(C_d.get(), sizeC, C.get(), sizeC, sizeC, 1, hipMemcpyHostToDevice, nullptr));
        timer.start();
        handle_error(hiptensorElementwiseBinaryExecute(handle, plan,
                                               (void*)&alpha, A_d.get(),
                                               (void*)&gamma, C_d.get(),
                                                              C_d.get(), nullptr /* stream */));
        auto time = timer.seconds();
        minTimeCUTENSOR = (minTimeCUTENSOR < time)? minTimeCUTENSOR : time;
    }

    /*************************/

    double transferedBytes = sizeC;
    transferedBytes += ((float)alpha != 0.f) ? sizeA : 0;
    transferedBytes += ((float)gamma != 0.f) ? sizeC : 0;
    transferedBytes /= 1e9;
    printf("cuTensor: %.2f GB/s\n", transferedBytes / minTimeCUTENSOR);
    printf("memcpy: %.2f GB/s\n", 2 * sizeC / minTimeMEMCPY / 1e9 );

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

