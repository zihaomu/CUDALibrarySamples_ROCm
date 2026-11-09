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
#ifndef CUBLASDX_EXAMPLE_NVRTC_CUBLAS_REFERENCE_HPP
#define CUBLASDX_EXAMPLE_NVRTC_CUBLAS_REFERENCE_HPP

#include <vector>

#include <hipblas.h>
#include <hip/hip_fp16.h>
#include <hip/hip_runtime_api.h>

#include "common_nvrtc.hpp"

namespace example {
    namespace nvrtc {
        namespace cublas_reference {
            inline std::vector<float> gemm(const std::vector<__half>& a,
                                           const std::vector<__half>& b,
                                           const std::vector<float>&  c,
                                           const unsigned             m,
                                           const unsigned             n,
                                           const unsigned             k,
                                           const float                alpha,
                                           const float                beta) {
                std::vector<float> reference(c);

                __half* d_a = nullptr;
                __half* d_b = nullptr;
                float*  d_c = nullptr;
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_a), sizeof(__half) * a.size()));
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_b), sizeof(__half) * b.size()));
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_c), sizeof(float) * reference.size()));
                CUDA_CHECK_AND_EXIT(hipMemcpy(d_a, a.data(), sizeof(__half) * a.size(), hipMemcpyHostToDevice));
                CUDA_CHECK_AND_EXIT(hipMemcpy(d_b, b.data(), sizeof(__half) * b.size(), hipMemcpyHostToDevice));
                CUDA_CHECK_AND_EXIT(
                    hipMemcpy(d_c, reference.data(), sizeof(float) * reference.size(), hipMemcpyHostToDevice));

                hipblasHandle_t handle = nullptr;
                CUBLAS_CHECK_AND_EXIT(hipblasCreate(&handle));
                CUBLAS_CHECK_AND_EXIT(hipblasGemmEx(handle,
                                                   HIPBLAS_OP_T,
                                                   HIPBLAS_OP_N,
                                                   static_cast<int>(m),
                                                   static_cast<int>(n),
                                                   static_cast<int>(k),
                                                   &alpha,
                                                   d_a,
                                                   HIP_R_16F,
                                                   static_cast<int>(k),
                                                   d_b,
                                                   HIP_R_16F,
                                                   static_cast<int>(k),
                                                   &beta,
                                                   d_c,
                                                   HIP_R_32F,
                                                   static_cast<int>(m),
                                                   HIPBLAS_COMPUTE_32F,
                                                   HIPBLAS_GEMM_DEFAULT));
                CUDA_CHECK_AND_EXIT(
                    hipMemcpy(reference.data(), d_c, sizeof(float) * reference.size(), hipMemcpyDeviceToHost));

                CUBLAS_CHECK_AND_EXIT(hipblasDestroy(handle));
                CUDA_CHECK_AND_EXIT(hipFree(d_a));
                CUDA_CHECK_AND_EXIT(hipFree(d_b));
                CUDA_CHECK_AND_EXIT(hipFree(d_c));
                return reference;
            }

            inline std::vector<float> left_lower_trsm(const std::vector<float>& a,
                                                      const std::vector<float>& b,
                                                      const unsigned           m,
                                                      const unsigned           n) {
                std::vector<float> reference(b);

                float* d_a = nullptr;
                float* d_b = nullptr;
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_a), sizeof(float) * a.size()));
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_b), sizeof(float) * b.size()));
                CUDA_CHECK_AND_EXIT(hipMemcpy(d_a, a.data(), sizeof(float) * a.size(), hipMemcpyHostToDevice));
                CUDA_CHECK_AND_EXIT(
                    hipMemcpy(d_b, reference.data(), sizeof(float) * reference.size(), hipMemcpyHostToDevice));

                float** d_a_ptrs = nullptr;
                float** d_b_ptrs = nullptr;
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_a_ptrs), sizeof(float*)));
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_b_ptrs), sizeof(float*)));
                CUDA_CHECK_AND_EXIT(hipMemcpy(d_a_ptrs, &d_a, sizeof(float*), hipMemcpyHostToDevice));
                CUDA_CHECK_AND_EXIT(hipMemcpy(d_b_ptrs, &d_b, sizeof(float*), hipMemcpyHostToDevice));

                hipblasHandle_t handle = nullptr;
                CUBLAS_CHECK_AND_EXIT(hipblasCreate(&handle));
                const float alpha = 1.f;
                CUBLAS_CHECK_AND_EXIT(hipblasStrsmBatched(handle,
                                                         HIPBLAS_SIDE_LEFT,
                                                         HIPBLAS_FILL_MODE_LOWER,
                                                         HIPBLAS_OP_N,
                                                         HIPBLAS_DIAG_NON_UNIT,
                                                         static_cast<int>(m),
                                                         static_cast<int>(n),
                                                         &alpha,
                                                         (const float* const*)d_a_ptrs,
                                                         static_cast<int>(m),
                                                         (float* const*)d_b_ptrs,
                                                         static_cast<int>(m),
                                                         1));
                CUDA_CHECK_AND_EXIT(
                    hipMemcpy(reference.data(), d_b, sizeof(float) * reference.size(), hipMemcpyDeviceToHost));

                CUBLAS_CHECK_AND_EXIT(hipblasDestroy(handle));
                CUDA_CHECK_AND_EXIT(hipFree(d_a));
                CUDA_CHECK_AND_EXIT(hipFree(d_b));
                CUDA_CHECK_AND_EXIT(hipFree(d_a_ptrs));
                CUDA_CHECK_AND_EXIT(hipFree(d_b_ptrs));
                return reference;
            }
        } // namespace cublas_reference
    } // namespace nvrtc
} // namespace example

#endif // CUBLASDX_EXAMPLE_NVRTC_CUBLAS_REFERENCE_HPP
