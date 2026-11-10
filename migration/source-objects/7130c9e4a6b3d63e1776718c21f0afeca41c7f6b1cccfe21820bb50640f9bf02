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
#ifndef CUSOLVERDX_EXAMPLE_CUBLAS_COMMON_CUBLAS_REFERENCE_GEQRF_GELS_HPP
#define CUSOLVERDX_EXAMPLE_CUBLAS_COMMON_CUBLAS_REFERENCE_GEQRF_GELS_HPP

#include <hipblas.h>
#include "measure.hpp"

namespace common {
    template<typename T, typename cuda_data_type, bool do_solver = false, bool check_blas_perf = false>
    bool reference_cublas_geqrf_gels(std::vector<T>&    A,
                                     std::vector<T>&    B,
                                     std::vector<T>&    tau,
                                     const unsigned int m,
                                     const unsigned int n,
                                     const unsigned int nrhs           = 1,
                                     const unsigned int padded_batches = 1,
                                     const bool         is_col_major_a = true,
                                     const bool         is_col_major_b = true,
                                     const bool         is_trans_a     = false,
                                     const unsigned int actual_batches = 0) {

        if (m < n && do_solver) {
            std::cout << "Comparing cuSolverDx GELS for m <= n cases with cuSolver and cuBlas APIs are not implemented in the example." << std::endl;
            return false;
        }

        const unsigned int                  a_size = m * n;
        const unsigned int                  mn     = std::min(m, n);
        [[maybe_unused]] const unsigned int b_size = std::max(m, n) * nrhs;

        // lda and ldb are the leading dimensions of A and B to be used in cuSolver, which uses column major storage only
        [[maybe_unused]] const unsigned int lda = m;
        [[maybe_unused]] const unsigned int ldb = std::max(m, n);

        const unsigned batches = (actual_batches == 0) ? padded_batches : actual_batches;

        hipStream_t stream = nullptr;
        CUDA_CHECK_AND_EXIT(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));

        hipblasHandle_t cublasH = nullptr;
        CUBLAS_CHECK_AND_EXIT(hipblasCreate(&cublasH));
        CUBLAS_CHECK_AND_EXIT(hipblasSetStream(cublasH, stream));

        // if row major, transpose the input A
        // Function: transpose_matrix(A, m, n, batch)
        //           Input A:  n x m x batch, with n the fastest dim and batch the slowest
        //           Output A: m x n x batch, with m the fastest dim and batch the slowest
        if (!is_col_major_a) {
            transpose_matrix<T>(A, m, n, batches);
        }
        if (!is_col_major_b && do_solver && nrhs > 1) {
            transpose_matrix<T>(B, ldb, nrhs, batches); // fast, second_fast, batch -> after transpose, swap fast and second_fast
        }

        int h_info = 0;

        if constexpr (!do_solver) { // use cublasgetqrfBatched

            cuda_data_type**             d_A_array   = nullptr;
            cuda_data_type**             d_tau_array = nullptr;
            std::vector<cuda_data_type*> d_A(batches, nullptr);
            std::vector<cuda_data_type*> d_tau(batches, nullptr);

            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A[i]), sizeof(cuda_data_type) * a_size));
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_tau[i]), sizeof(cuda_data_type) * mn));
            }

            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A_array), sizeof(cuda_data_type*) * batches));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_tau_array), sizeof(cuda_data_type*) * batches));

            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A[i], A.data() + i * a_size, sizeof(cuda_data_type) * a_size, hipMemcpyHostToDevice, stream));
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_tau[i], tau.data() + i * mn, sizeof(cuda_data_type) * mn, hipMemcpyHostToDevice, stream));
            }

            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A_array, d_A.data(), sizeof(cuda_data_type*) * batches, hipMemcpyHostToDevice, stream));
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_tau_array, d_tau.data(), sizeof(cuda_data_type*) * batches, hipMemcpyHostToDevice, stream));

            auto execute_cublas_geqrf_api = [&](hipStream_t str) {
                constexpr bool is_complex = common::is_complex<T>();
                constexpr bool is_float   = std::is_same_v<typename common::get_precision<T>::type, float>;
                if constexpr (is_float && !is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasSgeqrfBatched(cublasH, m, n, d_A_array, lda, d_tau_array, &h_info, batches));
                } else if constexpr (is_float && is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasCgeqrfBatched(cublasH, m, n, d_A_array, lda, d_tau_array, &h_info, batches));
                } else if constexpr (!is_float && !is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasDgeqrfBatched(cublasH, m, n, d_A_array, lda, d_tau_array, &h_info, batches));
                } else if constexpr (!is_float && is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasZgeqrfBatched(cublasH, m, n, d_A_array, lda, d_tau_array, &h_info, batches));
                }
                CUDA_CHECK_AND_EXIT(hipStreamSynchronize(str));
            };

            if constexpr (check_blas_perf) {
                // cuBlasXgetrfBatched forces in-place A, so need to reset A after execution to get appropriate performance data
                auto execute_reset_a = [&](hipStream_t str) {
                    for (int i = 0; i < batches; i++) {
                        CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A[i], A.data() + i * a_size, sizeof(cuda_data_type) * a_size, hipMemcpyHostToDevice, str));
                    }
                };
                // measure and report cusolver API performance
                const unsigned int warmup_repeats = 1;
                const unsigned int repeats        = 1;

                double ms_geqrf = common::measure::execution(execute_cublas_geqrf_api, execute_reset_a, warmup_repeats, repeats, stream) / repeats;
                // report the timing
                double seconds_per_giga_batch = ms_geqrf / 1e3 / batches * 1e9;
                double gb_s                   = a_size * 2 * sizeof(T) / seconds_per_giga_batch; // A read and write
                double gflops                 = common::get_flops_geqrf<T>(m, n) / seconds_per_giga_batch;
                common::print_perf("Ref_cublasXgeqrfBatched", batches, m, n, 0, gflops, gb_s, ms_geqrf, 0); // dummy 0 for k andblockDim
            } else {
                execute_cublas_geqrf_api(stream);
            }

            // copy the results back to host for verification
            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(A.data() + i * a_size, d_A[i], sizeof(cuda_data_type) * a_size, hipMemcpyDeviceToHost, stream));
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(tau.data() + i * mn, d_tau[i], sizeof(cuda_data_type) * mn, hipMemcpyDeviceToHost, stream));
            }
            CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));

            CUDA_CHECK_AND_EXIT(hipFree(d_A_array));
            CUDA_CHECK_AND_EXIT(hipFree(d_tau_array));
            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipFree(d_A[i]));
                CUDA_CHECK_AND_EXIT(hipFree(d_tau[i]));
            }

            // check for errors
            if (h_info != 0) {
                printf("cublas<t>geqrfBatched %d-th parameter is wrong \n", h_info);
                CUBLAS_CHECK_AND_EXIT(hipblasDestroy(cublasH));
                CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
                return false;
            }


        } else { // do_solver is true -> use cublasgelsBatched
            if (m < n || is_trans_a) {
                std::cout << "cuBlas<t>gelsBatched API only supports m >= n and is_trans_a = false cases." << std::endl;
                CUBLAS_CHECK_AND_EXIT(hipblasDestroy(cublasH));
                CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
                return false;
            }
            hipblasOperation_t trans = is_trans_a ? (common::is_complex<T>() ? HIPBLAS_OP_C : HIPBLAS_OP_T) : HIPBLAS_OP_N;

            int* d_info = nullptr;
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_info), sizeof(int) * batches));
            std::vector<int> info(batches, 0);

            cuda_data_type**             d_A_array = nullptr;
            cuda_data_type**             d_B_array = nullptr;
            std::vector<cuda_data_type*> d_A(batches, nullptr);
            std::vector<cuda_data_type*> d_B(batches, nullptr);

            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A[i]), sizeof(cuda_data_type) * a_size));
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_B[i]), sizeof(cuda_data_type) * b_size));
            }

            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A_array), sizeof(cuda_data_type*) * batches));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_B_array), sizeof(cuda_data_type*) * batches));

            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A[i], A.data() + i * a_size, sizeof(cuda_data_type) * a_size, hipMemcpyHostToDevice, stream));
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B[i], B.data() + i * b_size, sizeof(cuda_data_type) * b_size, hipMemcpyHostToDevice, stream));
            }

            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A_array, d_A.data(), sizeof(cuda_data_type*) * batches, hipMemcpyHostToDevice, stream));
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B_array, d_B.data(), sizeof(cuda_data_type*) * batches, hipMemcpyHostToDevice, stream));

            auto execute_cublas_gels_api = [&](hipStream_t str) {
                constexpr bool is_complex = common::is_complex<T>();
                constexpr bool is_float   = std::is_same_v<typename common::get_precision<T>::type, float>;
                if constexpr (is_float && !is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasSgelsBatched(cublasH, trans, m, n, nrhs, d_A_array, lda, d_B_array, ldb, &h_info, d_info, batches));
                } else if constexpr (is_float && is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasCgelsBatched(cublasH, trans, m, n, nrhs, d_A_array, lda, d_B_array, ldb, &h_info, d_info, batches));
                } else if constexpr (!is_float && !is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasDgelsBatched(cublasH, trans, m, n, nrhs, d_A_array, lda, d_B_array, ldb, &h_info, d_info, batches));
                } else {
                    CUBLAS_CHECK_AND_EXIT(hipblasZgelsBatched(cublasH, trans, m, n, nrhs, d_A_array, lda, d_B_array, ldb, &h_info, d_info, batches));
                }
                CUDA_CHECK_AND_EXIT(hipStreamSynchronize(str));
            };

            if constexpr (check_blas_perf) {
                // Users can adjust the repeats parameter to get more accurate performance data depending on the system and the workload
                const unsigned int warmup_repeats = 1;
                const unsigned int repeats        = 1;

                // cuBlasXgelsBatched forces in-place A, so need to reset A after execution to get appropriate performance data
                auto execute_reset_ab = [&](hipStream_t str) {
                    for (int i = 0; i < batches; i++) {
                        CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A[i], A.data() + i * a_size, sizeof(cuda_data_type) * a_size, hipMemcpyHostToDevice, str));
                        CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B[i], B.data() + i * b_size, sizeof(cuda_data_type) * b_size, hipMemcpyHostToDevice, str));
                    }
                };

                double ms_gels = common::measure::execution(execute_cublas_gels_api, execute_reset_ab, warmup_repeats, repeats, stream) / repeats;
                // report the timing
                double seconds_per_giga_batch = ms_gels / 1e3 / batches * 1e9;
                double gb_s                   = (a_size + b_size) * 2 * sizeof(T) / seconds_per_giga_batch; // A read only, B write and read
                double gflops = (common::get_flops_geqrf<T>(m, n) + common::get_flops_unmqr<T>(cusolverdx::side::left, m, nrhs, n) + common::get_flops_trsm<T>(n, nrhs)) / seconds_per_giga_batch;

                common::print_perf("Ref_cublasXgelsBatched", batches, m, n, nrhs, gflops, gb_s, ms_gels, 0); // dummy 0 for k andblockDim
            } else {
                execute_cublas_gels_api(stream);

                for (int i = 0; i < batches; i++) {
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(B.data() + i * b_size, d_B[i], sizeof(cuda_data_type) * b_size, hipMemcpyDeviceToHost, stream));
                }
            }
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(info.data(), d_info, sizeof(int) * batches, hipMemcpyDeviceToHost, stream));
            CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));

            CUDA_CHECK_AND_EXIT(hipFree(d_A_array));
            CUDA_CHECK_AND_EXIT(hipFree(d_B_array));
            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipFree(d_A[i]));
                CUDA_CHECK_AND_EXIT(hipFree(d_B[i]));
            }
            CUDA_CHECK_AND_EXIT(hipFree(d_info));

            // check for errors
            if (h_info != 0) {
                printf("cublas<t>gelsBatched %d-th parameter is wrong \n", h_info);
                return false;
            }
            for (int i = 0; i < batches; i++) {
                if (info[i] != 0) {
                    printf("cublas<t>gelsBatched %d-th batch is wrong, info = %d \n", i, info[i]);
                    return false;
                }
            }
        }

        // if row major, transpose the result A back to row major
        if (!is_col_major_a) {
            transpose_matrix<T>(A, n, m, batches);
        }
        if (!is_col_major_b && do_solver && nrhs > 1) {
            transpose_matrix<T>(B, nrhs, ldb, batches); // fast, second fast, batch
        }


        CUBLAS_CHECK_AND_EXIT(hipblasDestroy(cublasH));
        CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
        return true;
    }

} // namespace common

#endif // CUSOLVERDX_EXAMPLE_CUBLAS_COMMON_CUBLAS_REFERENCE_GEQRF_GELS_HPP
