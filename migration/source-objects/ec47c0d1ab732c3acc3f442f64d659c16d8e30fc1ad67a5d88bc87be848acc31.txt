/*
 * SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#ifndef CURANDDX_EXAMPLE_COMMON_HPP_
#define CURANDDX_EXAMPLE_COMMON_HPP_

#include <type_traits>
#include <vector>
#include <random>

#ifndef CUDA_CHECK_AND_EXIT
#    define CUDA_CHECK_AND_EXIT(error)                                                                      \
        {                                                                                                   \
            auto status = static_cast<hipError_t>(error);                                                  \
            if (status != hipSuccess) {                                                                    \
                std::cout << hipGetErrorString(status) << " " << __FILE__ << ":" << __LINE__ << std::endl; \
                std::exit(status);                                                                          \
            }                                                                                               \
        }
#endif

#ifndef CURAND_CHECK_AND_EXIT
#    define CURAND_CHECK_AND_EXIT(error)                                                \
        {                                                                               \
            auto status = static_cast<hiprandStatus_t>(error);                           \
            if (status != HIPRAND_STATUS_SUCCESS) {                                      \
                std::cout << status << " " << __FILE__ << ":" << __LINE__ << std::endl; \
                std::exit(status);                                                      \
            }                                                                           \
        }
#endif // CURAND_CHECK

namespace example {

    struct measure {
        // Returns execution time in ms.
        template<typename Kernel>
        static float execution(Kernel&&           kernel,
                               const unsigned int warm_up_runs,
                               const unsigned int runs,
                               hipStream_t       stream) {
            hipEvent_t startEvent, stopEvent;
            CUDA_CHECK_AND_EXIT(hipEventCreate(&startEvent));
            CUDA_CHECK_AND_EXIT(hipEventCreate(&stopEvent));
            CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

            for (unsigned int i = 0; i < warm_up_runs; i++) {
                kernel(stream);
            }

            CUDA_CHECK_AND_EXIT(hipGetLastError());
            CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

            CUDA_CHECK_AND_EXIT(hipEventRecord(startEvent, stream));
            for (unsigned int i = 0; i < runs; i++) {
                kernel(stream);
            }
            CUDA_CHECK_AND_EXIT(hipEventRecord(stopEvent, stream));
            CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

            float time;
            CUDA_CHECK_AND_EXIT(hipEventElapsedTime(&time, startEvent, stopEvent));
            CUDA_CHECK_AND_EXIT(hipEventDestroy(startEvent));
            CUDA_CHECK_AND_EXIT(hipEventDestroy(stopEvent));
            return time;
        }
    };

    inline unsigned int get_cuda_device_arch() {
        int device;
        CUDA_CHECK_AND_EXIT(hipGetDevice(&device));

        int major = 0;
        int minor = 0;
        CUDA_CHECK_AND_EXIT(hipDeviceGetAttribute(&major, hipDeviceAttributeComputeCapabilityMajor, device));
        CUDA_CHECK_AND_EXIT(hipDeviceGetAttribute(&minor, hipDeviceAttributeComputeCapabilityMinor, device));

        return static_cast<unsigned>(major) * 100 + static_cast<unsigned>(minor) * 10;
    }

    inline unsigned int get_multiprocessor_count(int device) {
        int multiprocessor_count = 0;
        CUDA_CHECK_AND_EXIT(hipDeviceGetAttribute(&multiprocessor_count, hipDeviceAttributeMultiprocessorCount, device));
        return multiprocessor_count;
    }

    inline unsigned int get_multiprocessor_count() {
        int device = 0;
        CUDA_CHECK_AND_EXIT(hipGetDevice(&device));
        return get_multiprocessor_count(device);
    }

    template<template<unsigned int> class Functor>
    inline int sm_runner() {
        // Get CUDA device compute capability
        const auto cuda_device_arch = get_cuda_device_arch();

        switch (cuda_device_arch) {
// All SM supported by cuRANDDx 
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_75
            case 750: return Functor<750>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_80
            case 800: return Functor<800>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_86
            case 860: return Functor<860>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_87
            case 870: return Functor<870>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_89
            case 890: return Functor<890>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_90
            case 900: return Functor<900>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_100
            case 1000: return Functor<1000>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_103
            case 1030: return Functor<1030>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_110
            case 1100: return Functor<1100>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_120
            case 1200: return Functor<1200>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_121
            case 1210: return Functor<1210>()();
#endif
#ifdef CURANDDX_EXAMPLE_ENABLE_SM_121
            default: {
                if (cuda_device_arch > 1210) {
                    return Functor<1210>()();
                }
            }
#endif
        }
        return 1;
    }
} // namespace example

#endif
