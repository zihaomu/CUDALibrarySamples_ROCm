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
#ifndef CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_GEQRF_GELS_HPP
#define CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_GEQRF_GELS_HPP

#include <hipblas.h>
#include <hipsolver.h>
#include "measure.hpp"

// cusolver reference GEQRF and GELS, only single batch is supported. Batched version is in cuBLAS. 

namespace common {
    template<typename T, typename cuda_data_type, bool do_solver = false, bool check_cusolver_geqrfperf = false>
    bool reference_cusolver_geqrf_gels(std::vector<T>&    A,
                                       std::vector<T>&    B,
                                       std::vector<T>&    tau,
                                       const unsigned int m,
                                       const unsigned int n,
                                       const unsigned int nrhs           = 1,
                                       const unsigned int padded_batches = 1,
                                       const bool is_col_major_a = true,
                                       const bool is_col_major_b = true,
                                       const bool is_trans_a     = false,
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
        [[maybe_unused]] const unsigned int ldb = max(m, n); 

        const unsigned batches = (actual_batches == 0) ? padded_batches : actual_batches;

        hipStream_t stream = nullptr;
        CUDA_CHECK_AND_EXIT(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));

        hipsolverHandle_t cusolverH = NULL;
        hipblasHandle_t     cublasH   = NULL;
        hipsolverDnParams_t params    = nullptr;
        CUSOLVER_CHECK_AND_EXIT(hipsolverDnCreate(&cusolverH));
        CUBLAS_CHECK_AND_EXIT(hipblasCreate(&cublasH));

        CUSOLVER_CHECK_AND_EXIT(hipsolverSetStream(cusolverH, stream));
        CUBLAS_CHECK_AND_EXIT(hipblasSetStream(cublasH, stream));
        CUSOLVER_CHECK_AND_EXIT(hipsolverDnCreateParams(&params));

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

        [[maybe_unused]] hipblasOperation_t trans = common::is_complex<T>() ? HIPBLAS_OP_C : HIPBLAS_OP_T;

        // d_tau
        cuda_data_type* d_tau = nullptr;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_tau), sizeof(cuda_data_type) * mn));

        cuda_data_type* d_A = nullptr;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A), sizeof(cuda_data_type) * a_size));

        [[maybe_unused]] cuda_data_type* d_B = nullptr;
        if constexpr (do_solver) {
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_B), sizeof(T) * b_size));
        }

        size_t            workspaceInBytesOnDevice = 0;       /* size of workspace */
        void*             d_work                   = nullptr; /* device workspace */
        std::vector<char> h_work;                             /* host workspace*/
        size_t            workspaceInBytesOnHost = 0;         /* size of workspace */

        [[maybe_unused]] int workspaceInBytesOnDevice_unmqr = 0; /* size of workspace */

        // query working space of geqrf and unmqr
        // geqrf -> A = QR
        // unmqr -> Q^H B
        CUSOLVER_CHECK_AND_EXIT(hipsolverDnXgeqrf_bufferSize(cusolverH,
                                                            params,
                                                            int64_t(m),
                                                            int64_t(n),
                                                            common::traits<cuda_data_type>::cuda_data_type,
                                                            d_A,
                                                            int64_t(m),
                                                            common::traits<cuda_data_type>::cuda_data_type,
                                                            d_tau,
                                                            common::traits<cuda_data_type>::cuda_data_type,
                                                            &workspaceInBytesOnDevice,
                                                            &workspaceInBytesOnHost));

        constexpr bool is_complex = common::is_complex<T>();
        constexpr bool is_float   = std::is_same_v<typename common::get_precision<T>::type, float>;

        if constexpr (do_solver) {
            // unmqr does not have 64-bit cusolver API
            if constexpr (is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnSormqr_bufferSize(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, &workspaceInBytesOnDevice_unmqr));
            } else if constexpr (is_float && is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnCunmqr_bufferSize(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, &workspaceInBytesOnDevice_unmqr));
            } else if constexpr (!is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnDormqr_bufferSize(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, &workspaceInBytesOnDevice_unmqr));
            } else {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnZunmqr_bufferSize(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, &workspaceInBytesOnDevice_unmqr));
            }
        }

        workspaceInBytesOnDevice = std::max(workspaceInBytesOnDevice, size_t(workspaceInBytesOnDevice_unmqr));
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_work), workspaceInBytesOnDevice));
        if (0 < workspaceInBytesOnHost) {
            h_work.resize(workspaceInBytesOnHost);
        }

        int* d_info = nullptr; // only used in cuSolverAPI
        int  info   = 0;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_info), sizeof(int)));
        // QR factorization one batch at a time
        for (unsigned int batch = 0; batch < batches; batch++) {
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A, &(A[a_size * batch]), sizeof(T) * a_size, hipMemcpyHostToDevice, stream));

            auto execute_geqrf = [&](hipStream_t str) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnXgeqrf(cusolverH,
                                                         params,
                                                         int64_t(m),
                                                         int64_t(n),
                                                         common::traits<cuda_data_type>::cuda_data_type,
                                                         d_A,
                                                         int64_t(m),
                                                         common::traits<cuda_data_type>::cuda_data_type,
                                                         d_tau,
                                                         common::traits<cuda_data_type>::cuda_data_type,
                                                         d_work,
                                                         workspaceInBytesOnDevice,
                                                         h_work.data(),
                                                         workspaceInBytesOnHost,
                                                         d_info));
                CUDA_CHECK_AND_EXIT(hipStreamSynchronize(str));
            };

            if constexpr (check_cusolver_geqrfperf) {
                const unsigned int warmup_repeats = 1;
                const unsigned int repeats        = 5;
                auto   execute_reset_a = [&](hipStream_t str) { CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A, &(A[a_size * batch]), sizeof(T) * a_size, hipMemcpyHostToDevice, str)); };
                double ms_geqrf        = common::measure::execution(execute_geqrf, execute_reset_a, warmup_repeats, repeats, stream) / repeats;
                // report the timing
                double seconds_per_giga_batch = ms_geqrf / 1e3 / batches * 1e9;
                double gb_s                   = a_size * 2 * sizeof(T) / seconds_per_giga_batch; // A read and write
                double gflops                 = common::get_flops_geqrf<T>(m, n) / seconds_per_giga_batch;
                common::print_perf("hipsolverDnXgeqrf", batches, m, n, 0, gflops, gb_s, ms_geqrf, 0); // dummy 0 for k andblockDim
            } else {
                execute_geqrf(stream);

                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&(A[a_size * batch]), d_A, sizeof(T) * a_size, hipMemcpyDeviceToHost, stream));
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&tau[mn * batch], d_tau, sizeof(T) * mn, hipMemcpyDeviceToHost, stream));
            }
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));
            CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));

            if (0 > info) {
                printf("cuSolverDnXgeqrf %d-th parameter is wrong \n", info);
                return false;
            }

            if constexpr (do_solver) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B, &(B[b_size * batch]), sizeof(T) * b_size, hipMemcpyHostToDevice, stream));
                
                if (!is_trans_a) { // A is not transposed
                    // calculate B = Q^T b
                    if constexpr (is_float && !is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnSormqr(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    } else if constexpr (is_float && is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnCunmqr(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    } else if constexpr (!is_float && !is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnDormqr(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    } else {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnZunmqr(cusolverH, HIPBLAS_SIDE_LEFT, trans, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    }
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));
                    CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
                    if (0 > info) {
                        printf("cuSolverDnXunmqr %d-th parameter is wrong \n", info);
                        return false;
                    }

                    // Solver R x = B
                    if constexpr (is_float && !is_complex) {
                        const cuda_data_type one = 1;
                        CUSOLVER_CHECK_AND_EXIT(hipblasStrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, HIPBLAS_OP_N, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    } else if constexpr (is_float && is_complex) {
                        const cuda_data_type one = {1, 0};
                        CUSOLVER_CHECK_AND_EXIT(hipblasCtrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, HIPBLAS_OP_N, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    } else if constexpr (!is_float && !is_complex) {
                        const cuda_data_type one = 1;
                        CUSOLVER_CHECK_AND_EXIT(hipblasDtrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, HIPBLAS_OP_N, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    } else {
                        const cuda_data_type one = {1, 0};
                        CUSOLVER_CHECK_AND_EXIT(hipblasZtrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, HIPBLAS_OP_N, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    }
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&B[b_size * batch], d_B, sizeof(T) * b_size, hipMemcpyDeviceToHost, stream));
                    CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
                    if (0 > info) {
                        printf("cuBlas %d-th parameter is wrong \n", info);
                        return false;
                    }
                } else { // if A is transposed
                    // solve Q^T x = B / (R^T), first calculate B / (R^T)
                    if constexpr (is_float && !is_complex) {
                        const cuda_data_type one = 1;
                        CUSOLVER_CHECK_AND_EXIT(hipblasStrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, trans, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    } else if constexpr (is_float && is_complex) {
                        const cuda_data_type one = {1, 0};
                        CUSOLVER_CHECK_AND_EXIT(hipblasCtrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, trans, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    } else if constexpr (!is_float && !is_complex) {
                        const cuda_data_type one = 1;
                        CUSOLVER_CHECK_AND_EXIT(hipblasDtrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, trans, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    } else {
                        const cuda_data_type one = {1, 0};
                        CUSOLVER_CHECK_AND_EXIT(hipblasZtrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, trans, HIPBLAS_DIAG_NON_UNIT, n, nrhs, &one, d_A, lda, d_B, ldb));
                    }

                    // the output d_B is of size n x nrhs, need to set d_B{n:m, 0:nrhs} = 0
                    CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
                    CUDA_CHECK_AND_EXIT(hipMemcpy(&B[b_size * batch], d_B, sizeof(T) * b_size, hipMemcpyDeviceToHost));
                    for (unsigned int j = 0; j < nrhs; j++) {
                        for (unsigned int i = n; i < m; i++) {
                            B[b_size * batch + j * m + i] = common::convert<T, float>(0.f);
                        }
                    }
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B, &B[b_size * batch], sizeof(T) * b_size, hipMemcpyHostToDevice));

                    // x = Q (B / (R^T))
                    if constexpr (is_float && !is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnSormqr(cusolverH, HIPBLAS_SIDE_LEFT, HIPBLAS_OP_N, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    } else if constexpr (is_float && is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnCunmqr(cusolverH, HIPBLAS_SIDE_LEFT, HIPBLAS_OP_N, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    } else if constexpr (!is_float && !is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnDormqr(cusolverH, HIPBLAS_SIDE_LEFT, HIPBLAS_OP_N, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    } else {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnZunmqr(cusolverH, HIPBLAS_SIDE_LEFT, HIPBLAS_OP_N, m, nrhs, n, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, workspaceInBytesOnDevice, d_info));
                    }

                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&B[b_size * batch], d_B, sizeof(T) * b_size, hipMemcpyDeviceToHost, stream));
                    CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
                    if (0 > info) {
                        printf("cuSolverDnXunmqr %d-th parameter is wrong \n", info);
                        return false;
                    }
                } 
            }

        } // end batch loop

        /* free resources */
        CUDA_CHECK_AND_EXIT(hipFree(d_A));
        CUDA_CHECK_AND_EXIT(hipFree(d_info));
        CUDA_CHECK_AND_EXIT(hipFree(d_tau));
        CUDA_CHECK_AND_EXIT(hipFree(d_work));
        if constexpr (do_solver) {
            CUDA_CHECK_AND_EXIT(hipFree(d_B));
        }


        // if row major, transpose the result A back to row major
        if (!is_col_major_a) {
            transpose_matrix<T>(A, n, m, batches);
        }
        if (!is_col_major_b && do_solver && nrhs > 1) {
            transpose_matrix<T>(B, nrhs, ldb, batches); // fast, second fast, batch
        }


        CUSOLVER_CHECK_AND_EXIT(hipsolverDnDestroy(cusolverH));
        CUBLAS_CHECK_AND_EXIT(hipblasDestroy(cublasH));
        CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
        return true;
    }

} // namespace common

#endif // CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_GEQRF_GELS_HPP
