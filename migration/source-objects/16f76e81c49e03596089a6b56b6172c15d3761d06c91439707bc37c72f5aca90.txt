#include "observe.hpp"
/*
 * SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <limits>
#include <vector>

#include <hipblas.h>
#include <hip/hip_runtime.h>

#include "cublas_utils.h"

using data_type = double;

int main(int argc, char *argv[]) {
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream = NULL;

    const int group_count = 2;
    const int m_array[group_count] = {2, 3};
    const int n_array[group_count] = {2, 3};
    const int k_array[group_count] = {2, 3};
    const int lda_array[group_count] = {2, 3};
    const int ldb_array[group_count] = {2, 3};
    const int ldc_array[group_count] = {2, 3};
    const int group_size[group_count] = {2, 1};

    /*
     * Group 0:
     *   A = | 1.0 | 2.0 | 5.0 | 6.0 |
     *       | 3.0 | 4.0 | 7.0 | 8.0 |
     *
     *   B = | 5.0 | 6.0 |  9.0 | 10.0 |
     *       | 7.0 | 8.0 | 11.0 | 12.0 |
     *
     * Group 1:
     *   A = | 1.0 | 2.0 | 3.0 |
     *       | 4.0 | 5.0 | 6.0 |
     *       | 7.0 | 8.0 | 9.0 |
     *
     *   B = | 4.0  | 5.0  | 6.0  |
     *       | 7.0  | 8.0  | 9.0  |
     *       | 10.0 | 11.0 | 12.0 |
     */

    const std::vector<std::vector<data_type>> A_array = {
        {1.0, 3.0, 2.0, 4.0},
        {5.0, 7.0, 6.0, 8.0},
        {1.0, 4.0, 7.0, 2.0, 5.0, 8.0, 3.0, 6.0, 9.0}};
    const std::vector<std::vector<data_type>> B_array = {
        {5.0, 7.0, 6.0, 8.0},
        {9.0, 11.0, 10.0, 12.0},
        {4.0, 7.0, 10.0, 5.0, 8.0, 11.0, 6.0, 9.0, 12.0}};

    const data_type NaN = std::numeric_limits<data_type>::quiet_NaN();
    std::vector<std::vector<data_type>> C_array = {
        {NaN, NaN, NaN, NaN},
        {NaN, NaN, NaN, NaN},
        {NaN, NaN, NaN, NaN, NaN, NaN, NaN, NaN, NaN}};

    const data_type alpha_array[group_count] = {1.0, 1.0};
    const data_type beta_array[group_count] = {0.0, 0.0};

    data_type **d_A_array = nullptr;
    data_type **d_B_array = nullptr;
    data_type **d_C_array = nullptr;

    const int gemm_count = A_array.size();
    std::vector<data_type *> d_A(gemm_count, nullptr);
    std::vector<data_type *> d_B(gemm_count, nullptr);
    std::vector<data_type *> d_C(gemm_count, nullptr);

    hipblasOperation_t transa_array[group_count] = {HIPBLAS_OP_N, HIPBLAS_OP_N};
    hipblasOperation_t transb_array[group_count] = {HIPBLAS_OP_N, HIPBLAS_OP_N};

    int problem_idx = 0;
    for (int i = 0; i < group_count; i++) {
        printf("Group %d:\n", i);
        for (int j = 0; j < group_size[i]; j++) {
            printf("A[%d]\n", j);
            print_matrix(m_array[i], k_array[i], A_array[problem_idx].data(),
                         lda_array[i]);
            printf("=====\n");

            printf("B[%d]\n", j);
            print_matrix(k_array[i], n_array[i], B_array[problem_idx].data(),
                         ldb_array[i]);
            printf("=====\n");

            problem_idx++;
        }
        printf("\n");
    }

    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy data to device */
    for (int i = 0; i < gemm_count; i++) {
        CUDA_CHECK(
            hipMalloc(reinterpret_cast<void **>(&d_A[i]), sizeof(data_type) * A_array[i].size()));
        CUDA_CHECK(
            hipMalloc(reinterpret_cast<void **>(&d_B[i]), sizeof(data_type) * B_array[i].size()));
        CUDA_CHECK(
            hipMalloc(reinterpret_cast<void **>(&d_C[i]), sizeof(data_type) * C_array[i].size()));
    }

    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_A_array), sizeof(data_type *) * gemm_count));
    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_B_array), sizeof(data_type *) * gemm_count));
    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_C_array), sizeof(data_type *) * gemm_count));

    for (int i = 0; i < gemm_count; i++) {
        CUDA_CHECK(hipMemcpyAsync(d_A[i], A_array[i].data(), sizeof(data_type) * A_array[i].size(),
                                   hipMemcpyHostToDevice, stream));
        CUDA_CHECK(hipMemcpyAsync(d_B[i], B_array[i].data(), sizeof(data_type) * B_array[i].size(),
                                   hipMemcpyHostToDevice, stream));
    }

    CUDA_CHECK(hipMemcpyAsync(d_A_array, d_A.data(), sizeof(data_type *) * gemm_count,
                               hipMemcpyHostToDevice, stream));
    CUDA_CHECK(hipMemcpyAsync(d_B_array, d_B.data(), sizeof(data_type *) * gemm_count,
                               hipMemcpyHostToDevice, stream));
    CUDA_CHECK(hipMemcpyAsync(d_C_array, d_C.data(), sizeof(data_type *) * gemm_count,
                               hipMemcpyHostToDevice, stream));

    /* step 3: compute */
    CUBLAS_CHECK(hipblasDgemmGroupedBatched(
        cublasH, transa_array, transb_array, m_array, n_array, k_array,
        alpha_array, d_A_array, lda_array, d_B_array, ldb_array, beta_array,
        d_C_array, ldc_array, group_count, group_size));

    /* step 4: copy data to host */
    for (int i = 0; i < gemm_count; i++) {
        CUDA_CHECK(hipMemcpyAsync(C_array[i].data(), d_C[i], sizeof(data_type) * C_array[i].size(),
                                   hipMemcpyDeviceToHost, stream));
    }

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     * Group 0:
     *   C = | 19.0 | 22.0 | 111.0 | 122.0 |
     *       | 43.0 | 50.0 | 151.0 | 166.0 |
     *
     * Group 1:
     *   C = |  48.0 |  54.0 |  60.0 |
     *       | 111.0 | 126.0 | 141.0 |
     *       | 174.0 | 198.0 | 222.0 |
     */
    problem_idx = 0;
    for (int i = 0; i < group_count; i++) {
        printf("Group %d:\n", i);
        for (int j = 0; j < group_size[i]; j++) {
            printf("C[%d]\n", j);
            print_matrix(m_array[i], n_array[i], C_array[problem_idx].data(),
                         ldc_array[i]);
            printf("=====\n");

            problem_idx++;
        }
        if (i < group_count - 1) {
            printf("\n");
        }
    }

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.

// MIGRATION_OBSERVE_SCALARS
migration_observer::emit("NaN",&NaN,1);
/* free resources */
    CUDA_CHECK(hipFree(d_A_array));
    CUDA_CHECK(hipFree(d_B_array));
    CUDA_CHECK(hipFree(d_C_array));
    for (int i = 0; i < gemm_count; i++) {
        CUDA_CHECK(hipFree(d_A[i]));
        CUDA_CHECK(hipFree(d_B[i]));
        CUDA_CHECK(hipFree(d_C[i]));
    }

    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}