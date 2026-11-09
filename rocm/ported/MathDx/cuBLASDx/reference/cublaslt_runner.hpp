/*
 * SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#ifndef CUBLASDX_EXAMPLE_CUBLASLT_RUNNER_HPP
#define CUBLASDX_EXAMPLE_CUBLASLT_RUNNER_HPP

#include "../common/common.hpp"

#include <hipblaslt.h>

namespace example {

    constexpr hipblasOperation_t get_cublas_transpose_mode(cublasdx::transpose_mode const tmode) {
        if (tmode == cublasdx::transpose_mode::non_transposed) {
            return HIPBLAS_OP_N;
        } else if (tmode == cublasdx::transpose_mode::transposed) {
            return HIPBLAS_OP_T;
        }
        return HIPBLAS_OP_C;
    }

    constexpr hipblasOperation_t get_cublas_transpose_mode(cublasdx::arrangement const arr) {
        if (arr == cublasdx::col_major) {
            return HIPBLAS_OP_N;
        }
        return HIPBLAS_OP_T;
    }

    constexpr hipblasLtOrder_t get_cublas_layout_order(cublasdx::arrangement const arr) {
        return (arr == cublasdx::col_major) ? HIPBLASLT_ORDER_COL : HIPBLASLT_ORDER_ROW;
    }

    template<class T>
    constexpr hipDataType get_cublas_data_type() {
        if constexpr (cute::is_same_v<T, cublasdx::complex<double>>) {
            return HIP_C_64F;
        } else if constexpr (cute::is_same_v<T, cublasdx::complex<float>>) {
            return HIP_C_32F;
        } else if constexpr (cute::is_same_v<T, cublasdx::complex<__half>>) {
            return HIP_C_16F;
        } else if constexpr (cute::is_same_v<T, cublasdx::complex<__hip_bfloat16>>) {
            return HIP_C_16BF;
        } else if constexpr (cute::is_same_v<T, cublasdx::complex<int8_t>>) {
            return HIP_C_8I;
        } else if constexpr (cute::is_same_v<T, cublasdx::complex<int32_t>>) {
            return HIP_C_32I;
        } else if constexpr (cute::is_same_v<T, double>) {
            return HIP_R_64F;
        } else if constexpr (cute::is_same_v<T, float>) {
            return HIP_R_32F;
        } else if constexpr (cute::is_same_v<T, cublasdx::tfloat32_t>) {
            return HIP_R_32F;
        } else if constexpr (cute::is_same_v<T, __half>) {
            return HIP_R_16F;
        } else if constexpr (cute::is_same_v<T, __hip_bfloat16>) {
            return HIP_R_16BF;
        } else if constexpr (cute::is_same_v<T, __hip_fp8_e5m2_fnuz>) {
            return HIP_R_8F_E5M2;
        } else if constexpr (cute::is_same_v<T, __hip_fp8_e4m3_fnuz>) {
            return HIP_R_8F_E4M3;
        } else if constexpr (cute::is_same_v<T, int8_t>) {
            return HIP_R_8I;
        } else if constexpr (cute::is_same_v<T, uint8_t>) {
            return HIP_R_8U;
        } else if constexpr (cute::is_same_v<T, int32_t>) {
            return HIP_R_32I;
        } else {
            static_assert(sizeof(T) == 0, "Unsupported data type");
        }

        CUTE_GCC_UNREACHABLE;
    }

    template<class T, class Precision>
    constexpr bool is_precision() {
        return cute::is_same_v<T, Precision> or cute::is_same_v<T, cublasdx::complex<Precision>>;
    }

    template<class I, class O>
    constexpr hipblasComputeType_t get_cublas_compute_type() {
        if (is_precision<O, double>()) {
            return HIPBLAS_COMPUTE_64F;
        } else if (is_precision<I, cublasdx::tfloat32_t>()) {
            return HIPBLAS_COMPUTE_32F_FAST_TF32;
        } else if (is_precision<O, __half>()) {
            return HIPBLAS_COMPUTE_16F;
        } else if (is_precision<O, int32_t>()) {
            return HIPBLAS_COMPUTE_32I;
        }

        return HIPBLAS_COMPUTE_32F;
    }

    enum cublaslt_heuristic
    {
        run_default_best,
        search_for_best
    };

    template<class AComputeType, class BComputeType = AComputeType, class CComputeType = BComputeType>
    struct cublaslt_runner {
        unsigned int result_size {};

        hipblasLtMatmulDesc_t       operation_desc {};
        hipblasLtMatmulPreference_t preference {};
        hipblasLtMatrixLayout_t     a_desc {};
        unsigned                   num_a_elements {};

        hipblasLtMatrixLayout_t b_desc {};
        unsigned               num_b_elements {};

        hipblasLtMatrixLayout_t c_desc {};
        unsigned               num_c_elements {};

        hipblasLtOrder_t cublas_order_a {};
        hipblasLtOrder_t cublas_order_b {};
        hipblasLtOrder_t cublas_order_c {};

        hipDataType cublas_data_type_a {};
        hipDataType cublas_data_type_b {};
        hipDataType cublas_data_type_c {};

        hipDataType      cublas_scale_type {};
        hipblasComputeType_t cublas_compute_type {};

        hipblasLtHandle_t                lt_handle;
        hipblasLtMatmulHeuristicResult_t default_algorithm = {};

        // Note: 32MB is the suggested size of workspace for cublasLt starting from Hopper arch
        size_t              workspace_size_in_bytes = 32 * 1024 * 1024;
        device_vector<char> workspace_vector        = device_vector<char>(workspace_size_in_bytes);

	template<class GEMMShape, class GEMMArr, class GEMMLD>
        void initialize(GEMMShape const gemm_shape, GEMMArr const gemm_arr, GEMMLD const gemm_ld) {
            const auto [m, n, k]             = gemm_shape;
            const auto [lda, ldb, ldc]       = gemm_ld;
            const auto [arr_a, arr_b, arr_c] = gemm_arr;

            result_size = m * n;

            cublas_order_a = get_cublas_layout_order(arr_a);
            cublas_order_b = get_cublas_layout_order(arr_b);
            cublas_order_c = get_cublas_layout_order(arr_c);

            cublas_data_type_a = get_cublas_data_type<AComputeType>();
            cublas_data_type_b = get_cublas_data_type<BComputeType>();
            cublas_data_type_c = get_cublas_data_type<CComputeType>();

            CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutCreate(&a_desc, cublas_data_type_a, m, k, lda));
            CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutSetAttribute(
                a_desc, HIPBLASLT_MATRIX_LAYOUT_ORDER, &cublas_order_a, sizeof(cublas_order_a)));
            num_a_elements = arr_a == cublasdx::col_major ? m * lda : k * lda;

            CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutCreate(&b_desc, cublas_data_type_b, k, n, ldb));
            CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutSetAttribute(
                b_desc, HIPBLASLT_MATRIX_LAYOUT_ORDER, &cublas_order_b, sizeof(cublas_order_b)));
            num_b_elements = arr_b == cublasdx::col_major ? k * ldb : n * ldb;

            CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutCreate(&c_desc, cublas_data_type_c, m, n, ldc));
            CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutSetAttribute(
                c_desc, HIPBLASLT_MATRIX_LAYOUT_ORDER, &cublas_order_c, sizeof(cublas_order_c)));
            num_c_elements = arr_c == cublasdx::col_major ? m * ldc : n * ldc;

            cublas_scale_type   = cublas_data_type_c;
            cublas_compute_type = get_cublas_compute_type<AComputeType, CComputeType>();
            CUBLAS_CHECK_AND_EXIT(hipblasLtCreate(&lt_handle));

            CUBLAS_CHECK_AND_EXIT(hipblasLtMatmulDescCreate(&operation_desc, cublas_compute_type, cublas_scale_type));

            // Heuristic utils
            int returned_results = 0;

            CUBLAS_CHECK_AND_EXIT(hipblasLtMatmulPreferenceCreate(&preference));
            CUBLAS_CHECK_AND_EXIT(hipblasLtMatmulPreferenceSetAttribute(preference,
                                                                       HIPBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,
                                                                       &workspace_size_in_bytes,
                                                                       sizeof(workspace_size_in_bytes)));

            CUBLAS_CHECK_AND_EXIT(hipblasLtMatmulAlgoGetHeuristic(lt_handle,
                                                                 operation_desc,
                                                                 a_desc,
                                                                 b_desc,
                                                                 c_desc,
                                                                 c_desc,
                                                                 preference,
                                                                 1,
                                                                 &default_algorithm,
                                                                 &returned_results));

            if (returned_results == 0) {
                CUBLAS_CHECK_AND_EXIT(HIPBLAS_STATUS_NOT_SUPPORTED);
            }
	}

        template<class GEMMShape, class GEMMArr, class GEMMLD>
        cublaslt_runner(GEMMShape const gemm_shape, GEMMArr const gemm_arr, GEMMLD const gemm_ld) {
	    initialize(gemm_shape, gemm_arr, gemm_ld);
        }

        template<class GEMMShape, class GEMMArr>
        cublaslt_runner(GEMMShape const gemm_shape, GEMMArr const gemm_arr) {
            auto const [m, n, k] = gemm_shape;
            auto const [arr_a, arr_b, arr_c] = gemm_arr;
            auto const lda = (arr_a == cublasdx::col_major) ? m : k;
            auto const ldb = (arr_b == cublasdx::col_major) ? k : n;
            auto const ldc = (arr_c == cublasdx::col_major) ? m : n;
	    auto const gemm_ld = std::make_tuple(lda, ldb, ldc);
	    initialize(gemm_shape, gemm_arr, gemm_ld);
        }

        void execute(CComputeType const& alpha,
                     AComputeType const* a,
                     BComputeType const* b,
                     CComputeType const& beta,
                     CComputeType*       c,
                     hipStream_t const  stream = 0) const {
            auto runner = [&](hipStream_t const stream) {
                CUBLAS_CHECK_AND_EXIT(hipblasLtMatmul(lt_handle,
                                                     operation_desc,
                                                     reinterpret_cast<void const*>(&alpha),
                                                     reinterpret_cast<void const*>(a),
                                                     a_desc,
                                                     reinterpret_cast<void const*>(b),
                                                     b_desc,
                                                     reinterpret_cast<void const*>(&beta),
                                                     reinterpret_cast<void*>(c),
                                                     c_desc,
                                                     reinterpret_cast<void*>(c),
                                                     c_desc,
                                                     &default_algorithm.algo,
                                                     workspace_vector.data(),
                                                     workspace_size_in_bytes,
                                                     stream));
            };

            runner(stream);
            CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());
            CUDA_CHECK_AND_EXIT(hipPeekAtLastError());
        }

        [[nodiscard]] std::vector<CComputeType> execute_with_results(CComputeType const& alpha,
                                                                     AComputeType const* a,
                                                                     BComputeType const* b,
                                                                     CComputeType const& beta,
                                                                     CComputeType*       c,
                                                                     hipStream_t const  stream = 0) const {
            std::vector<CComputeType> results(result_size);
            this->execute(alpha, a, b, beta, c, stream);
            CUDA_CHECK_AND_EXIT(
                hipMemcpy(results.data(), c, results.size() * sizeof(CComputeType), hipMemcpyDeviceToHost));

            return results;
        }

        [[nodiscard]] example::measure::execution_result execute_with_time(CComputeType const& alpha,
                                                                           AComputeType const* a,
                                                                           BComputeType const* b,
                                                                           CComputeType const& beta,
                                                                           CComputeType*       c,
                                                                           unsigned const      kernel_warm_up_repeats,
                                                                           unsigned const      kernel_repeats,
                                                                           hipStream_t const  stream = 0) const {
            // Find best algorithm
            auto heuristic_runner = [&](auto const algo, hipStream_t const stream) {
                CUBLAS_CHECK_AND_EXIT(hipblasLtMatmul(lt_handle,
                                                     operation_desc,
                                                     reinterpret_cast<void const*>(&alpha),
                                                     reinterpret_cast<void const*>(a),
                                                     a_desc,
                                                     reinterpret_cast<void const*>(b),
                                                     b_desc,
                                                     reinterpret_cast<void const*>(&beta),
                                                     reinterpret_cast<void*>(c),
                                                     c_desc,
                                                     reinterpret_cast<void*>(c),
                                                     c_desc,
                                                     &algo,
                                                     workspace_vector.data(),
                                                     workspace_size_in_bytes,
                                                     stream));
            };

            constexpr int                   repeat_algo_check                       = 5;
            const int                       requested_algo_count                    = 8;
            hipblasLtMatmulHeuristicResult_t heuristic_results[requested_algo_count] = {};
            int                             returned_results                        = 0;
            int                             best_algo_index                         = 0;
            float                           best_algo_time                          = 0;

            CUBLAS_CHECK_AND_EXIT(hipblasLtMatmulAlgoGetHeuristic(lt_handle,
                                                                 operation_desc,
                                                                 a_desc,
                                                                 b_desc,
                                                                 c_desc,
                                                                 c_desc,
                                                                 preference,
                                                                 requested_algo_count,
                                                                 heuristic_results,
                                                                 &returned_results));

            if (returned_results == 0) {
                CUBLAS_CHECK_AND_EXIT(HIPBLAS_STATUS_NOT_SUPPORTED);
            }

            // Cast away const, but data will only be reloaded for L2 reset
            // no changes will actually happen to it
            auto mutable_a = const_cast<AComputeType*>(a);
            auto mutable_b = const_cast<BComputeType*>(b);

            // Prepare host data for L2 reset
            std::vector<AComputeType> host_a_data(num_a_elements);
            std::vector<BComputeType> host_b_data(num_b_elements);
            std::vector<CComputeType> host_c_data(num_c_elements);

            CUDA_CHECK_AND_EXIT(hipMemcpy((void*)host_a_data.data(),
                                           (void const*)a,
                                           host_a_data.size() * sizeof(AComputeType),
                                           hipMemcpyDeviceToHost));
            CUDA_CHECK_AND_EXIT(hipMemcpy((void*)host_b_data.data(),
                                           (void const*)b,
                                           host_b_data.size() * sizeof(BComputeType),
                                           hipMemcpyDeviceToHost));
            CUDA_CHECK_AND_EXIT(hipMemcpy((void*)host_c_data.data(),
                                           (void*)c,
                                           host_c_data.size() * sizeof(CComputeType),
                                           hipMemcpyDeviceToHost));

            for (int algo_idx = 0; algo_idx < returned_results; ++algo_idx) {
                // Reset L2 cache
                {
                    CUDA_CHECK_AND_EXIT(hipMemcpy((void*)mutable_a,
                                                   (void*)host_a_data.data(),
                                                   host_a_data.size() * sizeof(AComputeType),
                                                   hipMemcpyHostToDevice));
                    CUDA_CHECK_AND_EXIT(hipMemcpy((void*)mutable_b,
                                                   (void*)host_b_data.data(),
                                                   host_b_data.size() * sizeof(BComputeType),
                                                   hipMemcpyHostToDevice));
                    CUDA_CHECK_AND_EXIT(hipMemcpy((void*)c,
                                                   (void*)host_c_data.data(),
                                                   host_c_data.size() * sizeof(CComputeType),
                                                   hipMemcpyHostToDevice));
                }

                auto time = example::measure::execution(
                    [&](auto const stream) { heuristic_runner(heuristic_results[algo_idx].algo, stream); },
                    1 /* warm up runs*/,
                    repeat_algo_check /* kernel runs */,
                    stream);

                if (algo_idx == 0 || time < best_algo_time) {
                    best_algo_time  = time;
                    best_algo_index = algo_idx;
                }
            }

            auto time_cublas = example::measure::execution(
                [&](auto const stream) { heuristic_runner(heuristic_results[best_algo_index].algo, stream); },
                kernel_warm_up_repeats,
                kernel_repeats,
                stream);
            CUDA_CHECK_AND_EXIT(hipPeekAtLastError());
            CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

            return time_cublas;
        }

        [[nodiscard]] std::tuple<example::measure::execution_result, std::vector<CComputeType>>
        execute_with_time_and_results(
            CComputeType const& alpha,
            AComputeType const* a,
            BComputeType const* b,
            CComputeType const& beta,
            CComputeType*       c,
            unsigned const      kernel_warm_up_repeats,
            unsigned const      kernel_repeats,
            hipStream_t const  stream = 0) const {
            auto results = this->execute_with_results(alpha, a, b, beta, c, stream);
            auto time = this->execute_with_time(alpha, a, b, beta, c, kernel_warm_up_repeats, kernel_repeats, stream);

            return std::make_tuple(time, results);
        }

        ~cublaslt_runner() {
            if (preference)
                CUBLAS_CHECK_AND_EXIT(hipblasLtMatmulPreferenceDestroy(preference));
            if (c_desc)
                CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutDestroy(c_desc));
            if (b_desc)
                CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutDestroy(b_desc));
            if (a_desc)
                CUBLAS_CHECK_AND_EXIT(hipblasLtMatrixLayoutDestroy(a_desc));
            if (operation_desc)
                CUBLAS_CHECK_AND_EXIT(hipblasLtMatmulDescDestroy(operation_desc));
        }
    };
} // namespace example

#endif // CUBLASDX_EXAMPLE_CUBLASLT_RUNNER_HPP
