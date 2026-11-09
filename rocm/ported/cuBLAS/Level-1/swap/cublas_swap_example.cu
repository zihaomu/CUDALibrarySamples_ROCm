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

    /*
     *   A = | 1.0 2.0 3.0 4.0 |
     *   B = | 5.0 6.0 7.0 8.0 |
     */

    std::vector<data_type> A = {1.0, 2.0, 3.0, 4.0};
    std::vector<data_type> B = {5.0, 6.0, 7.0, 8.0};
    const int incx = 1;
    const int incy = 1;

    data_type *d_A = nullptr;
    data_type *d_B = nullptr;

    printf("A\n");
    print_vector(A.size(), A.data());
    printf("=====\n");

    printf("B\n");
    print_vector(B.size(), B.data());
    printf("=====\n");

    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy data to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_B), sizeof(data_type) * B.size()));

    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(d_B, B.data(), sizeof(data_type) * B.size(), hipMemcpyHostToDevice,
                               stream));

    /* step 3: compute */
    CUBLAS_CHECK(hipblasDswap(cublasH, A.size(), d_A, incx, d_B, incy));

    /* step 4: copy data to host */
    CUDA_CHECK(hipMemcpyAsync(A.data(), d_A, sizeof(data_type) * A.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(B.data(), d_B, sizeof(data_type) * B.size(), hipMemcpyDeviceToHost,
                               stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     *   A = | 5.0 6.0 7.0 8.0 |
     *   B = | 1.0 2.0 3.0 4.0 |
     */

    printf("A\n");
    print_vector(A.size(), A.data());
    printf("=====\n");

    printf("B\n");
    print_vector(B.size(), B.data());
    printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("B",B.data(),B.size());

// MIGRATION_OBSERVE_SCALARS
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_B));

    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}