#include "observe.hpp"
/*
 * SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


#include <cstdio>
#include <cstdlib>
#include <vector>

#include <hipblas.h>
#include <hip/hip_runtime.h>

#include "cublas_utils.h"

using data_type = double;

int main(int argc, char *argv[]) {
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream = NULL;

    const int m = 2;
    const int n = 2;
    const int k = 2;
    const int lda = 2;
    const int ldb = 2;
    const int ldc = 2;
    /*
     *   A = | 1.0 | 2.0 |
     *       | 3.0 | 4.0 |
     *
     *   B = | 5.0 | 6.0 |
     *       | 7.0 | 8.0 |
     */

    const std::vector<data_type> A = {1.0, 3.0, 2.0, 4.0};
    const std::vector<data_type> B = {5.0, 7.0, 6.0, 8.0};
    std::vector<data_type> C(m * n);
    const data_type alpha = 1.0;
    const data_type beta = 0.0;

    data_type *d_A = nullptr;
    data_type *d_B = nullptr;
    data_type *d_C = nullptr;

    hipblasOperation_t transa = HIPBLAS_OP_N;
    hipblasOperation_t transb = HIPBLAS_OP_N;

    printf("A\n");
    print_matrix(m, k, A.data(), lda);
    printf("=====\n");

    printf("B\n");
    print_matrix(k, n, B.data(), ldb);
    printf("=====\n");

    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy data to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_B), sizeof(data_type) * B.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_C), sizeof(data_type) * C.size()));

    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(d_B, B.data(), sizeof(data_type) * B.size(), hipMemcpyHostToDevice,
                               stream));

    /* step 3: set up CUDA events for timing */
    hipEvent_t start, stop;
    CUDA_CHECK(hipEventCreate(&start));
    CUDA_CHECK(hipEventCreate(&stop));

    float time = 0.f;

    /* step 4: first call: without autotuning (library initialization) */
    CUDA_CHECK(hipEventRecord(start, stream));
    CUBLAS_CHECK(hipblasGemmEx(
        cublasH, transa, transb,
        m, n, k,
        &alpha,
        d_A, traits<data_type>::cuda_data_type, lda,
        d_B, traits<data_type>::cuda_data_type, ldb,
        &beta,
        d_C, traits<data_type>::cuda_data_type, ldc,
        HIPBLAS_COMPUTE_64F,
        HIPBLAS_GEMM_DEFAULT));
    CUDA_CHECK(hipEventRecord(stop, stream));
    CUDA_CHECK(hipEventSynchronize(stop));
    CUDA_CHECK(hipEventElapsedTime(&time, start, stop));
    printf("Timing first call (without autotuning: to let the library initialize internal structures): %.3f ms\n", time);

    /* step 5: first call: without autotuning (baseline) */
    CUDA_CHECK(hipEventRecord(start, stream));
    CUBLAS_CHECK(hipblasGemmEx(
        cublasH, transa, transb,
        m, n, k,
        &alpha,
        d_A, traits<data_type>::cuda_data_type, lda,
        d_B, traits<data_type>::cuda_data_type, ldb,
        &beta,
        d_C, traits<data_type>::cuda_data_type, ldc,
        HIPBLAS_COMPUTE_64F,
        HIPBLAS_GEMM_DEFAULT));
    CUDA_CHECK(hipEventRecord(stop, stream));
    CUDA_CHECK(hipEventSynchronize(stop));
    CUDA_CHECK(hipEventElapsedTime(&time, start, stop));
    printf("Timing second call (without autotuning: baseline): %.3f ms\n", time);

    /* step 6: second call: autotune + GEMM */
    CUDA_CHECK(hipEventRecord(start, stream));
    CUBLAS_CHECK(hipblasGemmEx(
        cublasH, transa, transb,
        m, n, k,
        &alpha,
        d_A, traits<data_type>::cuda_data_type, lda,
        d_B, traits<data_type>::cuda_data_type, ldb,
        &beta,
        d_C, traits<data_type>::cuda_data_type, ldc,
        HIPBLAS_COMPUTE_64F,
        CUBLAS_GEMM_AUTOTUNE));
    CUDA_CHECK(hipEventRecord(stop, stream));
    CUDA_CHECK(hipEventSynchronize(stop));
    CUDA_CHECK(hipEventElapsedTime(&time, start, stop));
    printf("Timing third call (autotune + GEMM): %.3f ms\n", time);

    /* step 7: third call: uses cached algorithm */
    CUDA_CHECK(hipEventRecord(start, stream));
    CUBLAS_CHECK(hipblasGemmEx(
        cublasH, transa, transb,
        m, n, k,
        &alpha,
        d_A, traits<data_type>::cuda_data_type, lda,
        d_B, traits<data_type>::cuda_data_type, ldb,
        &beta,
        d_C, traits<data_type>::cuda_data_type, ldc,
        HIPBLAS_COMPUTE_64F,
        CUBLAS_GEMM_AUTOTUNE));
    CUDA_CHECK(hipEventRecord(stop, stream));
    CUDA_CHECK(hipEventSynchronize(stop));
    CUDA_CHECK(hipEventElapsedTime(&time, start, stop));
    printf("Timing fourth call (cached algorithm): %.3f ms\n", time);

    /* step 8: copy data to host */
    CUDA_CHECK(hipMemcpyAsync(C.data(), d_C, sizeof(data_type) * C.size(), hipMemcpyDeviceToHost,
                               stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     *   C = | 19.0 | 22.0 |
     *       | 43.0 | 50.0 |
     */

    printf("C\n");
    print_matrix(m, n, C.data(), ldc);
    printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("B",B.data(),B.size());
migration_observer::emit("C",C.data(),C.size());

// MIGRATION_OBSERVE_SCALARS
migration_observer::emit("alpha",&alpha,1);
migration_observer::emit("beta",&beta,1);
migration_observer::emit("time",&time,1);
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_B));
    CUDA_CHECK(hipFree(d_C));

    CUDA_CHECK(hipEventDestroy(start));
    CUDA_CHECK(hipEventDestroy(stop));

    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}