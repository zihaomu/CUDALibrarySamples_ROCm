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

using data_type = hipComplex;

int main(int argc, char *argv[]) {
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream = NULL;

    const int m = 2;
    const int n = 2;
    const int k = 2;
    const int lda = 2;
    const int ldc = 2;

    /*
     *   A = | 1.1 + 1.2j | 2.3 + 2.4j |
     *       | 3.5 + 3.6j | 4.7 + 4.8j |
     */

    const std::vector<data_type> A = {{1.1, 1.2}, {3.5, 3.6},{2.3, 2.4},  {4.7, 4.8}};
    std::vector<data_type> C(m * n);
    const float alpha = 1.0;
    const float beta = 0.0;

    hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_UPPER;
    hipblasOperation_t trans = HIPBLAS_OP_N;

    data_type *d_A = nullptr;
    data_type *d_C = nullptr;

    printf("A\n");
    print_matrix(n, k, A.data(), lda);
    printf("=====\n");

    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy data to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_C), sizeof(data_type) * C.size()));

    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));

    /* step 3: compute */
    CUBLAS_CHECK(hipblasHerkEx(cublasH, uplo, trans, n, k, &alpha, d_A,
                               traits<data_type>::cuda_data_type, lda, &beta, d_C,
                               traits<data_type>::cuda_data_type, ldc));

    /* step 4: copy data to host */
    CUDA_CHECK(hipMemcpyAsync(C.data(), d_C, sizeof(data_type) * C.size(), hipMemcpyDeviceToHost,
                               stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     *   C = | 13.70 + 0.00j | 30.50 + 0.48j |
     *       |  0.00 + 0.00j | 70.34 + 0.00j |
     */

    printf("C\n");
    print_matrix(n, k, C.data(), ldc);
    printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("C",C.data(),C.size());

// MIGRATION_OBSERVE_SCALARS
migration_observer::emit("alpha",&alpha,1);
migration_observer::emit("beta",&beta,1);
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_C));

    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}