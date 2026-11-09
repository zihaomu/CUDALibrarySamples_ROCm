#include "observe.hpp"
#include <string>
#include <cstdlib>
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
// MIGRATION_BATCH2: default is unchanged original input and mathematical GPU API.
const std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";

    hipblasHandle_t cublasH = NULL;
    hipStream_t stream = NULL;

    /*
     *   A = | 1.0 2.0 3.0 4.0 |
     */

    std::vector<data_type> A = {1.0, 2.0, 3.0, 4.0};
    const int incx = 1;

    int result = 0.0;

    data_type *d_A = nullptr;

    printf("A\n");
    print_vector(A.size(), A.data());
    printf("=====\n");

if(migration_case=="ties"){A={-4,4,1,-1};}
migration_observer::emit("input_A",A.data(),A.size());
    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy data to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));

    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));

    /* step 3: compute */
    CUBLAS_CHECK(hipblasIdamin(cublasH, migration_case=="empty"?0:A.size(), d_A, incx, &result));

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     *   result = 1
     */

    printf("result\n");
    std::printf("%d\n", result);
    printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());

// MIGRATION_OBSERVE_SCALARS
migration_observer::emit("result",&result,1);
/* free resources */
    CUDA_CHECK(hipFree(d_A));

    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}