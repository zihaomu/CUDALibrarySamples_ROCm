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
#ifndef CUSOLVERDX_EXAMPLE_COMMON_CUDART_HPP
#define CUSOLVERDX_EXAMPLE_COMMON_CUDART_HPP

#include "macros.hpp"
#include <hip/hip_complex.h>
#include <hipsolver.h>

namespace common {
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

    //============================
    // type traits
    //============================
    template<typename T>
    struct traits;

    template<>
    struct traits<float> {
        // scalar type
        typedef float T;
        typedef T     S;

        static constexpr T            zero          = 0.f;
        static constexpr T            one           = 1.f;
        static constexpr hipDataType cuda_data_type = HIP_R_32F;
#if CUDART_VERSION >= 11000
        static constexpr cusolverPrecType_t cusolver_precision_type = CUSOLVER_R_32F;
#endif

        inline static S abs(T val) {
            return fabs(val);
        }

        template<typename RNG>
        inline static T rand(RNG& gen) {
            return (S)gen();
        }

        inline static T add(T a, T b) {
            return a + b;
        }

        inline static T mul(T v, S f) {
            return v * f;
        }
    };

    template<>
    struct traits<double> {
        // scalar type
        typedef double T;
        typedef T      S;

        static constexpr T            zero           = 0.;
        static constexpr T            one            = 1.;
        static constexpr hipDataType cuda_data_type = HIP_R_64F;
#if CUDART_VERSION >= 11000
        static constexpr cusolverPrecType_t cusolver_precision_type = CUSOLVER_R_64F;
#endif

        inline static S abs(T val) {
            return fabs(val);
        }

        template<typename RNG>
        inline static T rand(RNG& gen) {
            return (S)gen();
        }

        inline static T add(T a, T b) {
            return a + b;
        }

        inline static T mul(T v, S f) {
            return v * f;
        }
    };

    template<>
    struct traits<hipFloatComplex> {
        // scalar type
        typedef float          S;
        typedef hipFloatComplex T;

        static constexpr T            zero           = {0.f, 0.f};
        static constexpr T            one            = {1.f, 0.f};
        static constexpr hipDataType cuda_data_type = HIP_C_32F;
#if CUDART_VERSION >= 11000
        static constexpr cusolverPrecType_t cusolver_precision_type = CUSOLVER_C_32F;
#endif

        inline static S abs(T val) {
            return hipCabsf(val);
        }

        template<typename RNG>
        inline static T rand(RNG& gen) {
            return make_hipFloatComplex((S)gen(), (S)gen());
        }

        inline static T add(T a, T b) {
            return hipCaddf(a, b);
        }
        inline static T add(T a, S b) {
            return hipCaddf(a, make_hipFloatComplex(b, 0.f));
        }

        inline static T mul(T v, S f) {
            return make_hipFloatComplex(v.x * f, v.y * f);
        }
    };

    template<>
    struct traits<hipDoubleComplex> {
        // scalar type
        typedef double          S;
        typedef hipDoubleComplex T;

        static constexpr T            zero           = {0., 0.};
        static constexpr T            one            = {1., 0.};
        static constexpr hipDataType cuda_data_type = HIP_C_64F;
#if CUDART_VERSION >= 11000
        static constexpr cusolverPrecType_t cusolver_precision_type = CUSOLVER_C_64F;
#endif

        inline static S abs(T val) {
            return hipCabs(val);
        }

        template<typename RNG>
        inline static T rand(RNG& gen) {
            return make_hipDoubleComplex((S)gen(), (S)gen());
        }

        inline static T add(T a, T b) {
            return hipCadd(a, b);
        }
        inline static T add(T a, S b) {
            return hipCadd(a, make_hipDoubleComplex(b, 0.));
        }

        inline static T mul(T v, S f) {
            return make_hipDoubleComplex(v.x * f, v.y * f);
        }
    };
} // namespace common

#endif // CUSOLVERDX_EXAMPLE_COMMON_CUDART_HPP
