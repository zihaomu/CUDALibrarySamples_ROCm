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
#ifndef CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_UNMQR_HPP
#define CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_UNMQR_HPP

#include <hipblas.h>
#include <hipsolver.h>

namespace common {
    template<typename T, typename cuda_data_type>
    bool reference_cusolver_unmqr(std::vector<T>&       A,
                                  std::vector<T>&       B,
                                  const std::vector<T>& tau,
                                  const unsigned int    m,
                                  const unsigned int    n,
                                  const unsigned int    k,
                                  const unsigned int    padded_batches = 1,
                                  const unsigned int    actual_batches = 0,
                                  const bool            is_left        = true,
                                  const bool            is_col_major_a = true,
                                  const bool            is_col_major_b = true,
                                  const bool            is_trans_a     = false) {

        const unsigned int a_size = A.size() / padded_batches;
        const unsigned int b_size = B.size() / padded_batches;

        // lda and ldb are the leading dimensions of A and B to be used in cuSolver, which uses column major storage only
        const unsigned int a_m = is_left ? m : n;
        const unsigned int a_n = k;
        const unsigned int lda = a_m;
        const unsigned int ldb = m;

        const unsigned batches = (actual_batches == 0) ? padded_batches : actual_batches;

        hipStream_t stream = nullptr;
        CUDA_CHECK_AND_EXIT(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));

        hipsolverHandle_t cusolverH = NULL;
        CUSOLVER_CHECK_AND_EXIT(hipsolverDnCreate(&cusolverH));
        CUSOLVER_CHECK_AND_EXIT(hipsolverSetStream(cusolverH, stream));

        // if row major, transpose the input A and B
        if (!is_col_major_a) {
            transpose_matrix<T>(A, a_m, a_n, batches);
        }
        if (!is_col_major_b) {
            transpose_matrix<T>(B, m, n, batches);
        }

        const hipblasOperation_t trans = (is_trans_a) ? (common::is_complex<T>() ? HIPBLAS_OP_C : HIPBLAS_OP_T) : HIPBLAS_OP_N;
        const hipblasSideMode_t  side  = is_left ? HIPBLAS_SIDE_LEFT : HIPBLAS_SIDE_RIGHT;

        // Allocate device memory
        cuda_data_type* d_tau = nullptr;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_tau), sizeof(cuda_data_type) * k));

        cuda_data_type* d_A = nullptr;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_A), sizeof(cuda_data_type) * a_size));

        cuda_data_type* d_B = nullptr;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_B), sizeof(cuda_data_type) * b_size));

        // Query workspace size for UNMQR. Note the workspace is the size of the work array, not the size of the workspace in bytes
        int           lwork = 0;
        constexpr bool is_complex               = common::is_complex<T>();
        constexpr bool is_float                 = std::is_same_v<typename common::get_precision<T>::type, float>;

        if constexpr (is_float && !is_complex) {
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnSormqr_bufferSize(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, &lwork));
        } else if constexpr (is_float && is_complex) {
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnCunmqr_bufferSize(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, &lwork));
        } else if constexpr (!is_float && !is_complex) {
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnDormqr_bufferSize(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, &lwork));
        } else {
            CUSOLVER_CHECK_AND_EXIT(hipsolverDnZunmqr_bufferSize(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, &lwork));
        }

        // Allocate workspace
        void* d_work = nullptr;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_work), lwork * sizeof(cuda_data_type)));

        int* d_info = nullptr;
        int  info   = 0;
        CUDA_CHECK_AND_EXIT(hipMalloc(reinterpret_cast<void**>(&d_info), sizeof(int)));

        // Process one batch at a time
        for (unsigned int batch = 0; batch < batches; batch++) {
            // Copy A and tau to device (A should already contain QR factors from previous GEQRF)
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_A, &(A[a_size * batch]), sizeof(T) * a_size, hipMemcpyHostToDevice, stream));
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_tau, &(tau[k * batch]), sizeof(T) * k, hipMemcpyHostToDevice, stream));

            // Copy B to device
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(d_B, &(B[b_size * batch]), sizeof(T) * b_size, hipMemcpyHostToDevice, stream));

            // Perform UNMQR operation: B = Q*B or B = Q^T*B
            if constexpr (is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnSormqr(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, lwork, d_info));
            } else if constexpr (is_float && is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnCunmqr(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, lwork, d_info));
            } else if constexpr (!is_float && !is_complex) {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnDormqr(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, lwork, d_info));
            } else {
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnZunmqr(cusolverH, side, trans, m, n, k, d_A, lda, d_tau, d_B, ldb, (cuda_data_type*)d_work, lwork, d_info));
            }

            // Check for errors
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));
            CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
            if (info != 0) {
                printf("cuSolverDn UNMQR %d-th parameter is wrong \n", info);
                CUDA_CHECK_AND_EXIT(hipFree(d_A));
                CUDA_CHECK_AND_EXIT(hipFree(d_B));
                CUDA_CHECK_AND_EXIT(hipFree(d_tau));
                CUDA_CHECK_AND_EXIT(hipFree(d_work));
                CUDA_CHECK_AND_EXIT(hipFree(d_info));
                CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
                CUSOLVER_CHECK_AND_EXIT(hipsolverDnDestroy(cusolverH));
                return false;
            }

            // Copy result back to host
            CUDA_CHECK_AND_EXIT(hipMemcpyAsync(&(B[b_size * batch]), d_B, sizeof(T) * b_size, hipMemcpyDeviceToHost, stream));
            CUDA_CHECK_AND_EXIT(hipStreamSynchronize(stream));
        }

        /* free resources */
        CUDA_CHECK_AND_EXIT(hipFree(d_A));
        CUDA_CHECK_AND_EXIT(hipFree(d_B));
        CUDA_CHECK_AND_EXIT(hipFree(d_tau));
        CUDA_CHECK_AND_EXIT(hipFree(d_work));
        CUDA_CHECK_AND_EXIT(hipFree(d_info));

        // if row major, transpose the result B back to row major
        if (!is_col_major_b) {
            transpose_matrix<T>(B, n, m, batches);
        }

        CUSOLVER_CHECK_AND_EXIT(hipsolverDnDestroy(cusolverH));
        CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));
        return true;
    }

} // namespace common

#endif // CUSOLVERDX_EXAMPLE_CUSOLVERDX_COMMON_CUSOLVER_REFERENCE_UNMQR_HPP
