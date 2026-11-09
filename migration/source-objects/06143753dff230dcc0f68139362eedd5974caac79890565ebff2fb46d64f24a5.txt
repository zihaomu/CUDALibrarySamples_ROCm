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
#ifndef CUSOLVERDX_EXAMPLE_CUBLAS_REFERENCE_TRSM_HPP_
#define CUSOLVERDX_EXAMPLE_CUBLAS_REFERENCE_TRSM_HPP_

#include <hipblas.h>
#include <vector>
#include "measure.hpp"

namespace common {

    template<typename T, typename CUDA_T, bool check_blas_trsm_perf = false>
    void reference_cublas_trsm(std::vector<T>& A,
                               std::vector<T>& B,
                               const int       m,
                               const int       n,
                               const int       padded_batches,
                               const bool      is_side_left,
                               const bool      is_lower,
                               const bool      is_diag_unit,
                               const bool      is_trans_a,
                               const bool      is_col_major_a,
                               const bool      is_col_major_b,
                               const int       actual_batches = 0) {

        const unsigned int a_size = A.size() / padded_batches;
        const unsigned int b_size = m * n;
        const unsigned int a_m    = is_side_left ? m : n;

        // lda and ldb are used in the cuBlas API, which is always column major
        const unsigned int lda = a_m;
        const unsigned int ldb = m;

        const unsigned batches = (actual_batches == 0) ? padded_batches : actual_batches;

        // if row major, transpose the input A and B
        if (!is_col_major_a) {
            transpose_matrix<T>(A, a_m, a_m, batches); 
        }
        if (!is_col_major_b) {
            transpose_matrix<T>(B, m, n, batches); 
        }

        const hipblasSideMode_t  side  = is_side_left ? HIPBLAS_SIDE_LEFT : HIPBLAS_SIDE_RIGHT;
        const hipblasFillMode_t  uplo  = is_lower ? HIPBLAS_FILL_MODE_LOWER : HIPBLAS_FILL_MODE_UPPER;
        const hipblasOperation_t trans = (is_trans_a) ? (common::is_complex<T>() ? HIPBLAS_OP_C : HIPBLAS_OP_T) : HIPBLAS_OP_N;
        const hipblasDiagType_t  diag  = is_diag_unit ? HIPBLAS_DIAG_UNIT : HIPBLAS_DIAG_NON_UNIT;

        // create cublas handle, bind a stream
        hipblasHandle_t cublasH = nullptr;
        CUBLAS_CHECK_AND_EXIT(hipblasCreate(&cublasH));

        hipStream_t stream = nullptr;
        CUDA_CHECK_AND_EXIT(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
        CUBLAS_CHECK_AND_EXIT(hipblasSetStream(cublasH, stream));

        if constexpr (check_blas_trsm_perf) { // use cuBlasTrsmBatched API to measure the performance

            CUDA_T** d_A_array = nullptr;
            CUDA_T** d_B_array = nullptr;

            std::vector<CUDA_T*> d_A(batches, nullptr);
            std::vector<CUDA_T*> d_B(batches, nullptr);

            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A[i]), sizeof(CUDA_T) * a_size));
                CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_B[i]), sizeof(CUDA_T) * b_size));
            }

            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A_array), sizeof(CUDA_T*) * batches));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_B_array), sizeof(CUDA_T*) * batches));

            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A[i], A.data() + i * a_size, sizeof(CUDA_T) * a_size, hipMemcpyHostToDevice, stream));
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B[i], B.data() + i * b_size, sizeof(CUDA_T) * b_size, hipMemcpyHostToDevice, stream));
            }

            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A_array, d_A.data(), sizeof(CUDA_T*) * batches, hipMemcpyHostToDevice, stream));
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B_array, d_B.data(), sizeof(CUDA_T*) * batches, hipMemcpyHostToDevice, stream));

            auto execute_cublas_trsm_api = [&](hipStream_t str) {
                constexpr bool is_complex = common::is_complex<T>();
                constexpr bool is_float   = std::is_same_v<typename common::get_precision<T>::type, float>;
                const CUDA_T   alpha      = common::traits<CUDA_T>::one;
                if constexpr (is_float && !is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasStrsmBatched(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_array, lda, d_B_array, ldb, batches));
                } else if constexpr (is_float && is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasCtrsmBatched(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_array, lda, d_B_array, ldb, batches));
                } else if constexpr (!is_float && !is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasDtrsmBatched(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_array, lda, d_B_array, ldb, batches));
                } else if constexpr (!is_float && is_complex) {
                    CUBLAS_CHECK_AND_EXIT(hipblasZtrsmBatched(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_array, lda, d_B_array, ldb, batches));
                }
                CUDA_CHECK_AND_EXIT(hipStreamSynchronize(str));
            };

            // cuBlasXtrsmBatched forces in-place B, so need to reset B after execution to get good performance data
            auto execute_reset_b = [&](hipStream_t str) {
                for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B[i], B.data() + i * b_size, sizeof(CUDA_T) * b_size, hipMemcpyHostToDevice, str)) ;
                }
            };

            // measure and report cusolver API performance
            // Users can adjust the repeats parameter to get more accurate performance data depending on the system and the workload
            const unsigned int warmup_repeats = 1;
            const unsigned int repeats        = 1;

            double ms_trsm = common::measure::execution(execute_cublas_trsm_api, execute_reset_b, warmup_repeats, repeats, stream) / repeats;

            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(B.data() + i * b_size, d_B[i], sizeof(CUDA_T) * b_size, hipMemcpyDeviceToHost, stream));
            }

            CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));

            CUDA_CHECK_AND_EXIT(hipFree(d_A_array));
            CUDA_CHECK_AND_EXIT(hipFree(d_B_array));
            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipFree(d_A[i]));
                CUDA_CHECK_AND_EXIT(hipFree(d_B[i]));
            }

            // report the timing
            double seconds_per_giga_batch = ms_trsm / 1e3 / batches * 1e9;
            double gb_s                   = (a_size + b_size * 2) * sizeof(T) / seconds_per_giga_batch; // A read only, Bread and write
            double gflops                 = common::get_flops_trsm<T>(m, n) / seconds_per_giga_batch;
            common::print_perf("Ref_cublasXtrsmBatched", batches, m, n, 0, gflops, gb_s, ms_trsm, 0); // dummy 0 for k andblockDim

        } else { // Use simpler cublas trsm API to check the correctness
            CUDA_T* d_A_onebatch  = nullptr;
            CUDA_T* d_B_onebatch = nullptr;
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A_onebatch), sizeof(T) * a_size));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_B_onebatch), sizeof(T) * b_size));


            for (int i = 0; i < batches; i++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A_onebatch, A.data() + i * a_size, sizeof(T) * a_size, hipMemcpyHostToDevice, stream));
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B_onebatch, B.data() + i * b_size, sizeof(T) * b_size, hipMemcpyHostToDevice, stream));


                // use cublas trsm API to solve the system of linear equations for each batch
                auto execute_cublas_trsm_api = [&](hipStream_t str) {
                    constexpr bool is_complex = common::is_complex<T>();
                    constexpr bool is_float   = std::is_same_v<typename common::get_precision<T>::type, float>;
                    const CUDA_T   alpha      = common::traits<CUDA_T>::one;
                    if constexpr (is_float && !is_complex) {
                        CUBLAS_CHECK_AND_EXIT(hipblasStrsm(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_onebatch, lda, d_B_onebatch, ldb));
                    } else if constexpr (is_float && is_complex) {
                        CUBLAS_CHECK_AND_EXIT(hipblasCtrsm(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_onebatch, lda, d_B_onebatch, ldb));
                    } else if constexpr (!is_float && !is_complex) {
                        CUBLAS_CHECK_AND_EXIT(hipblasDtrsm(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_onebatch, lda, d_B_onebatch, ldb));
                    } else if constexpr (!is_float && is_complex) {
                        CUBLAS_CHECK_AND_EXIT(hipblasZtrsm(cublasH, side, uplo, trans, diag, m, n, &alpha, d_A_onebatch, lda, d_B_onebatch, ldb));
                    }
                    CUDA_CHECK_AND_EXIT(hipStreamSynchronize(str));
                };
                execute_cublas_trsm_api(stream);

                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(B.data() + i * b_size, d_B_onebatch, sizeof(T) * b_size, hipMemcpyDeviceToHost, stream));
                CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
            }

            CUDA_CHECK_AND_EXIT(hipFree(d_A_onebatch));
            CUDA_CHECK_AND_EXIT(hipFree(d_B_onebatch));
        }

        // if row major, transpose the result A
        if (!is_col_major_a) {
            transpose_matrix<T>(A, a_m, a_m, batches); 
        }
        if (!is_col_major_b) {
            transpose_matrix<T>(B, n, m, batches); 
        }

        CUBLAS_CHECK_AND_EXIT(hipblasDestroy(cublasH));
        CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
    }

} // namespace common

#endif // CUSOLVERDX_EXAMPLE_CUBLAS_REFERENCE_TRSM_HPP_
