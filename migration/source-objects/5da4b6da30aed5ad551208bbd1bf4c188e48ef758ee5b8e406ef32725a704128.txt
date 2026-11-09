#include "observe.hpp"
/*
 * SPDX-FileCopyrightText: Copyright (c) 2020 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
    const int batch_count = 2;

    /*
     *   A = | 1.0 | 2.0 | 5.0 | 6.0 |
     *       | 3.0 | 4.0 | 7.0 | 8.0 |
     *
     *   B = | 5.0 | 6.0 |  9.0 | 10.0 |
     *       | 7.0 | 8.0 | 11.0 | 12.0 |
     */

    const std::vector<std::vector<data_type>> A_array = {{1.0, 3.0, 2.0, 4.0},
                                                         {5.0, 7.0, 6.0, 8.0}};
    std::vector<std::vector<data_type>> B_array = {{5.0, 7.0, 6.0, 8.0}, {9.0, 11.0, 10.0, 12.0}};
    const data_type alpha = 1.0;

    data_type **d_A_array = nullptr;
    data_type **d_B_array = nullptr;

    std::vector<data_type *> d_A(batch_count, nullptr);
    std::vector<data_type *> d_B(batch_count, nullptr);

    hipblasSideMode_t side = HIPBLAS_SIDE_LEFT;
    hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_UPPER;
    hipblasOperation_t transa = HIPBLAS_OP_N;
    hipblasDiagType_t diag = HIPBLAS_DIAG_NON_UNIT;

    printf("A[0]\n");
    print_matrix(m, k, A_array[0].data(), lda);
    printf("=====\n");

    printf("A[1]\n");
    print_matrix(m, k, A_array[1].data(), lda);
    printf("=====\n");

    printf("B[0] (in)\n");
    print_matrix(k, n, B_array[0].data(), ldb);
    printf("=====\n");

    printf("B[1] (in)\n");
    print_matrix(k, n, B_array[1].data(), ldb);
    printf("=====\n");

    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy data to device */
    for (int i = 0; i < batch_count; i++) {
        CUDA_CHECK(
            hipMalloc(reinterpret_cast<void **>(&d_A[i]), sizeof(data_type) * A_array[i].size()));
        CUDA_CHECK(
            hipMalloc(reinterpret_cast<void **>(&d_B[i]), sizeof(data_type) * B_array[i].size()));
    }

    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_A_array), sizeof(data_type *) * batch_count));
    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_B_array), sizeof(data_type *) * batch_count));

    for (int i = 0; i < batch_count; i++) {
        CUDA_CHECK(hipMemcpyAsync(d_A[i], A_array[i].data(), sizeof(data_type) * A_array[i].size(),
                                   hipMemcpyHostToDevice, stream));
        CUDA_CHECK(hipMemcpyAsync(d_B[i], B_array[i].data(), sizeof(data_type) * B_array[i].size(),
                                   hipMemcpyHostToDevice, stream));
    }

    CUDA_CHECK(hipMemcpyAsync(d_A_array, d_A.data(), sizeof(data_type *) * batch_count,
                               hipMemcpyHostToDevice, stream));
    CUDA_CHECK(hipMemcpyAsync(d_B_array, d_B.data(), sizeof(data_type *) * batch_count,
                               hipMemcpyHostToDevice, stream));

    /* step 3: compute */
    CUBLAS_CHECK(hipblasDtrsmBatched(cublasH, side, uplo, transa, diag, m, n, &alpha, d_A_array, lda,
                                    d_B_array, ldb, batch_count));

    /* step 4: copy data to host */
    for (int i = 0; i < batch_count; i++) {
        CUDA_CHECK(hipMemcpyAsync(B_array[i].data(), d_B[i], sizeof(data_type) * B_array[i].size(),
                                   hipMemcpyDeviceToHost, stream));
    }

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     *   B = | 1.50 | 2.00 | 0.15 | 0.20 |
     *       | 1.75 | 2.00 | 1.38 | 1.50 |
     */

    printf("B[0] (out)\n");
    print_matrix(k, n, B_array[0].data(), ldb);
    printf("=====\n");

    printf("B[1] (out)\n");
    print_matrix(k, n, B_array[1].data(), ldb);
    printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.

// MIGRATION_OBSERVE_SCALARS
migration_observer::emit("alpha",&alpha,1);
/* free resources */
    CUDA_CHECK(hipFree(d_A_array));
    CUDA_CHECK(hipFree(d_B_array));
    for (int i = 0; i < batch_count; i++) {
        CUDA_CHECK(hipFree(d_A[i]));
        CUDA_CHECK(hipFree(d_B[i]));
    }
    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}