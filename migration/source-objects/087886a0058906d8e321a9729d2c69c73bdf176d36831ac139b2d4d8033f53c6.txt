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
#ifndef CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_GESVD_HPP
#define CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_GESVD_HPP

#include "measure.hpp"

namespace common {
    template<typename T, typename cuda_data_type, typename precision_type = typename common::get_precision<T>::type, bool check_perf = false>
    bool reference_cusolver_gesvd(std::vector<T>&              A,
                                  std::vector<precision_type>& sigma,
                                  std::vector<T>&              U,
                                  std::vector<T>&              VT,
                                  const signed char            jobu,
                                  const signed char            jobvt,
                                  int*                         info,
                                  const unsigned int           m,
                                  const unsigned int           n,
                                  const unsigned int           padded_batches = 1,
                                  bool                         is_col_major_a = true,
                                  const unsigned int           actual_batches = 0) {

        if (m < n) {
            std::cout << "GESVD: m < n is not supported in cuSolverDn<t>getsvd API. Checking with cuSolverDn reference is disabled." << std::endl;
            return false;
        }

        const unsigned int a_size = A.size() / padded_batches;
        const unsigned int lda    = m;

        const unsigned int min_mn = m >= n ? n : m;
        const unsigned int u_size = U.size() / padded_batches;
        const unsigned int vt_size = VT.size() / padded_batches;
        // cuSolverDn<t>gesvd ldu and ldvt has to be at least 1 even if jobu and jobvt are set to 'N'
        const unsigned int act_m_u = (jobu == 'N') ? 1 : m;
        const unsigned int act_m_vt = (jobvt == 'N') ? 1 : (jobvt == 'A' ? n : min_mn); // cuSolverDn<t>gesvd only support m >= n

        unsigned int batches = (actual_batches == 0) ? padded_batches : actual_batches;

        hipStream_t stream = nullptr;
        CUDA_CHECK_AND_EXIT(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));

        hipsolverHandle_t cusolverH = nullptr;
        CUSOLVER_CHECK_AND_EXIT(hipsolverDnCreate(&cusolverH));
        CUSOLVER_CHECK_AND_EXIT(hipsolverSetStream(cusolverH, stream));

        [[maybe_unused]] double ms_gesvd_cusolver;

        // if row major, transpose the input A
        if (!is_col_major_a) {
            // For row major, transpose the matrix before calling cuSolver
            transpose_matrix<T>(A, m, n, batches);
        }

        //============================================
        // Use cuSolverDngesvd for correctness check and cuSolverDngesvdjBatched for performance check
        if constexpr (!check_perf) {
            cuda_data_type* d_A     = nullptr;
            cuda_data_type* d_U     = nullptr;
            cuda_data_type* d_VT    = nullptr;
            precision_type* d_sigma = nullptr;
            int*            d_info  = nullptr;
            int             lwork   = 0;

            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A), sizeof(T) * a_size));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_U), sizeof(T) * u_size));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_VT), sizeof(T) * vt_size));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_sigma), sizeof(precision_type) * min_mn));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_info), sizeof(int)));

            
            // Query workspace size for syevjBatched
            constexpr bool is_complex = common::is_complex<T>();
            constexpr bool is_float   = std::is_same_v<precision_type, float>;
            
            if constexpr (is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnSgesvd_bufferSize(cusolverH, m, n, &lwork));
            } else if constexpr (is_float && is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnCgesvd_bufferSize(cusolverH, m, n, &lwork));
            } else if constexpr (!is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnDgesvd_bufferSize(cusolverH, m, n, &lwork));
            } else if constexpr (!is_float && is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnZgesvd_bufferSize(cusolverH, m, n, &lwork));
            }
            
            // Allocate workspace
            cuda_data_type* d_work  = nullptr;
            precision_type* d_rwork = nullptr; // use to save unconverged superdiagonal elements of the bidiagonal matrix
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_work), sizeof(cuda_data_type) * lwork));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_rwork), sizeof(precision_type) * (min_mn - 1)));
            
            for (int b = 0; b < batches; b++) {
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A, A.data() + b * a_size, sizeof(T) * a_size, hipMemcpyHostToDevice, stream));

                // Execute gesvd
                auto execute_gesvd_api = [&](hipStream_t str) {
                    constexpr bool is_complex = common::is_complex<T>();
                    constexpr bool is_float   = std::is_same_v<precision_type, float>;
                    if constexpr (is_float && !is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnSgesvd(cusolverH, jobu, jobvt, m, n, d_A, lda, d_sigma, d_U, act_m_u, d_VT, act_m_vt, d_work, lwork, d_rwork, d_info));
                    } else if constexpr (is_float && is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnCgesvd(cusolverH, jobu, jobvt, m, n, d_A, lda, d_sigma, d_U, act_m_u, d_VT, act_m_vt, d_work, lwork, d_rwork, d_info));
                    } else if constexpr (!is_float && !is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnDgesvd(cusolverH, jobu, jobvt, m, n, d_A, lda, d_sigma, d_U, act_m_u, d_VT, act_m_vt, d_work, lwork, d_rwork, d_info));
                    } else if constexpr (!is_float && is_complex) {
                        CUSOLVER_CHECK_AND_EXIT(hipsolverDnZgesvd(cusolverH, jobu, jobvt, m, n, d_A, lda, d_sigma, d_U, act_m_u, d_VT, act_m_vt, d_work, lwork, d_rwork, d_info));
                    }
                    CUDA_CHECK_AND_EXIT(hipStreamSynchronize(str));
                };

                execute_gesvd_api(stream); // execute gesvd
                // Copy results back
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(sigma.data() + b * min_mn, d_sigma, sizeof(precision_type) * min_mn, hipMemcpyDeviceToHost, stream));
                CUDA_CHECK_AND_EXIT(hipMemcpyAsync(info + b, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));
                if (jobu == 'A' || jobu == 'S') {
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(U.data() + b * u_size, d_U, sizeof(T) * u_size, hipMemcpyDeviceToHost, stream));
                } else if (jobu == 'O') {
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(A.data() + b * a_size, d_A, sizeof(T) * a_size, hipMemcpyDeviceToHost, stream));
                }
                if (jobvt == 'A' || jobvt == 'S') {
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(VT.data() + b * vt_size, d_VT, sizeof(T) * vt_size, hipMemcpyDeviceToHost, stream));
                } else if (jobvt == 'O') {
                    CUDA_CHECK_AND_EXIT(hipMemcpyAsync(A.data() + b * a_size, d_A, sizeof(T) * a_size, hipMemcpyDeviceToHost, stream));
                }
                CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
            }
            CUDA_CHECK_AND_EXIT(hipFree(d_work));
            CUDA_CHECK_AND_EXIT(hipFree(d_rwork));
                CUDA_CHECK_AND_EXIT(hipFree(d_A));
            if (d_U != nullptr) {
                CUDA_CHECK_AND_EXIT(hipFree(d_U));
            }
            if (d_VT != nullptr) {
                CUDA_CHECK_AND_EXIT(hipFree(d_VT));
            }
            CUDA_CHECK_AND_EXIT(hipFree(d_sigma));
            CUDA_CHECK_AND_EXIT(hipFree(d_info));
        //============================================
        // Use cuSolver cusolverDnXgesvdjBatched for performance check.  cuSolver currently requires both m and n <= 32
        } else if (m <= 32 && n <= 32) {
            cuda_data_type* d_A     = nullptr;
            precision_type* d_sigma = nullptr;
            int*            d_info  = nullptr;
            cuda_data_type* d_work  = nullptr; /* device workspace */
            int             lwork   = 0;       /* size of workspace */
            const int ldu = m; /* ldu >= m */
            const int ldv = n; /* ldv >= n */
            cuda_data_type* d_U     = nullptr;
            cuda_data_type* d_VT    = nullptr;
            // gesvdjBatched requires U and VT to be allocated regardless of jobz setting
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_U), sizeof(T) * ldu * m * batches));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_VT), sizeof(T) * ldv * n * batches));


            hipsolverGesvdjInfo_t gesvdj_params = NULL;
            const double tol           = 1.e-7;
            const int    max_sweeps    = 15;
            const int    sort_svd      = 1;
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnCreateGesvdjInfo(&gesvdj_params));
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnXgesvdjSetMaxSweeps(gesvdj_params, max_sweeps));
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnXgesvdjSetSortEig(gesvdj_params, sort_svd));
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnXgesvdjSetTolerance(gesvdj_params, tol));
            const hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_NOVECTOR;

            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A), sizeof(T) * a_size * batches));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_sigma), sizeof(precision_type) * min_mn * batches));
            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_info), sizeof(int) * batches));

            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A, A.data(), sizeof(T) * a_size * batches, hipMemcpyHostToDevice, stream));

            constexpr bool is_complex = common::is_complex<T>();
            constexpr bool is_float   = std::is_same_v<precision_type, float>;

            if constexpr (is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnSgesvdjBatched_bufferSize(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, &lwork, gesvdj_params, batches));
            } else if constexpr (is_float && is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnCgesvdjBatched_bufferSize(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, &lwork, gesvdj_params, batches));
            } else if constexpr (!is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnDgesvdjBatched_bufferSize(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, &lwork, gesvdj_params, batches));
            } else if constexpr (!is_float && is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnZgesvdjBatched_bufferSize(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, &lwork, gesvdj_params, batches));
            }

            CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_work), sizeof(cuda_data_type) * lwork));


            auto execute_gesvdj_api = [&](hipStream_t str) {
                constexpr bool is_complex = common::is_complex<T>();
                constexpr bool is_float   = std::is_same_v<precision_type, float>;
                if constexpr (is_float && !is_complex) {
                    CUSOLVER_CHECK_AND_EXIT(hipsolverDnSgesvdjBatched(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, d_work, lwork, d_info, gesvdj_params, batches));
                } else if constexpr (is_float && is_complex) {
                    CUSOLVER_CHECK_AND_EXIT(hipsolverDnCgesvdjBatched(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, d_work, lwork, d_info, gesvdj_params, batches));
                } else if constexpr (!is_float && !is_complex) {
                    CUSOLVER_CHECK_AND_EXIT(hipsolverDnDgesvdjBatched(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, d_work, lwork, d_info, gesvdj_params, batches));    
                } else if constexpr (!is_float && is_complex) {
                    CUSOLVER_CHECK_AND_EXIT(hipsolverDnZgesvdjBatched(cusolverH, jobz, m, n, d_A, lda, d_sigma, d_U, ldu, d_VT, ldv, d_work, lwork, d_info, gesvdj_params, batches));
                }
                CUDA_CHECK_AND_EXIT(hipStreamSynchronize(str));
            };

            [[maybe_unused]] auto execute_reset_a = [&](hipStream_t str) { CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A, A.data(), sizeof(T) * a_size * batches, hipMemcpyHostToDevice, str)); };

            const unsigned int warmup_repeats = 1;
            const unsigned int repeats        = 2;
            ms_gesvd_cusolver                 = common::measure::execution(execute_gesvdj_api, execute_reset_a, warmup_repeats, repeats, stream) / repeats;

            double seconds_per_giga_batch = ms_gesvd_cusolver / 1e3 / batches * 1e9;
            double gb_s                   = (m * n * sizeof(T) + n * sizeof(precision_type)) / seconds_per_giga_batch; // A read, half write, and lambda write
            common::print_perf("Ref_cuSolverDnXgesvdjBatched", batches, m, n, 0, 0, gb_s, ms_gesvd_cusolver, 0);       // dummy 0 for nrhs, gflops, and blockDim
                                                                                                                       // 
            // Copy results back
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(sigma.data(), d_sigma, sizeof(precision_type) * min_mn * batches, hipMemcpyDeviceToHost, stream));
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(info, d_info, sizeof(int) * batches, hipMemcpyDeviceToHost, stream));
            CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));

            CUDA_CHECK_AND_EXIT(hipFree(d_A));
            if (d_U != nullptr) {
                CUDA_CHECK_AND_EXIT(hipFree(d_U));
            }
            if (d_VT != nullptr) {
                CUDA_CHECK_AND_EXIT(hipFree(d_VT));
            }
            CUDA_CHECK_AND_EXIT(hipFree(d_sigma));
            CUDA_CHECK_AND_EXIT(hipFree(d_info));
            CUDA_CHECK_AND_EXIT(hipFree(d_work));
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnDestroyGesvdjInfo(gesvdj_params));
        }

        // Check for errors
        for (auto i = 0; i < batches; i++) {
            if (*(info + i) != 0) {
                std::cout << "non-zero d_info returned with cuSolver gesvdjBatched for batch #" << i << std::endl;
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnDestroy(cusolverH));
                CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
                return false;
            }
        }

        // All the output A/U/VT matrices remain in col-major format after return of the function

        CUSOLVER_CHECK_AND_EXIT(hipsolverDnDestroy(cusolverH));
        CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
        return true;
    }

} // namespace common

#endif // CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_GESVD_HPP
