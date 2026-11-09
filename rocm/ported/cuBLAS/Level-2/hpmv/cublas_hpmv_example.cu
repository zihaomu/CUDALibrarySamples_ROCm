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

using data_type = hipDoubleComplex;

int main(int argc, char *argv[]) {
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream = NULL;

    const int n = 2;

    /*
     *   A = | 1.1 + 1.2j | 2.3 + 2.4j |
     *       |            | 4.7 + 4.8j |
     *   x = | 5.1 + 6.2j | 7.3 + 8.4j |
     */

    const std::vector<data_type> AP = {{1.1, 1.2}, {2.3, 2.4}, {4.7, 4.8}};
    const std::vector<data_type> x = {{5.1, 6.2}, {7.3, 8.4}};
    std::vector<data_type> y(n);
    const data_type alpha = {1.0, 1.0};
    const data_type beta = {0.0, 0.0};
    const int incx = 1;
    const int incy = 1;

    data_type *d_AP = nullptr;
    data_type *d_x = nullptr;
    data_type *d_y = nullptr;

    hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_UPPER;

    printf("AP\n");
    print_packed_matrix(uplo, n, AP.data());
    printf("=====\n");

    printf("x\n");
    print_vector(x.size(), x.data());
    printf("=====\n");

    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy data to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_AP), sizeof(data_type) * AP.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_x), sizeof(data_type) * x.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_y), sizeof(data_type) * y.size()));

    CUDA_CHECK(hipMemcpyAsync(d_AP, AP.data(), sizeof(data_type) * AP.size(), hipMemcpyHostToDevice,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(d_x, x.data(), sizeof(data_type) * x.size(), hipMemcpyHostToDevice,
                               stream));

    /* step 3: compute */
    CUBLAS_CHECK(hipblasZhpmv(cublasH, uplo, n, &alpha, d_AP, d_x, incx, &beta, d_y, incy));

    /* step 4: copy data to host */
    CUDA_CHECK(hipMemcpyAsync(y.data(), d_y, sizeof(data_type) * y.size(), hipMemcpyDeviceToHost,
                               stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     *   y = | -41.42 + 45.90j 19.42 + 102.42j  |
     */

    printf("y\n");
    print_vector(y.size(), y.data());
    printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("AP",AP.data(),AP.size());
migration_observer::emit("x",x.data(),x.size());
migration_observer::emit("y",y.data(),y.size());

// MIGRATION_OBSERVE_SCALARS
migration_observer::emit("alpha",&alpha,1);
migration_observer::emit("beta",&beta,1);
/* free resources */
    CUDA_CHECK(hipFree(d_AP));
    CUDA_CHECK(hipFree(d_x));
    CUDA_CHECK(hipFree(d_y));

    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}