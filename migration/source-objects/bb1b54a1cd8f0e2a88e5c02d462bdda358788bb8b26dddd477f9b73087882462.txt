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
     *   A = 2.10
     *   B = 1.20
     */

    data_type A = 2.1;
    data_type B = 1.2;
    data_type c = 2.1;
    data_type s = 1.2;

    printf("A\n");
    std::printf("%0.2f\n", A);
    printf("=====\n");

    printf("B\n");
    std::printf("%0.2f\n", B);
    printf("=====\n");

if(migration_case=="zero"){A=0;B=0;}if(migration_case=="negative"){A=-3;B=4;}
migration_observer::emit("input_A",&A,1);
migration_observer::emit("input_B",&B,1);
    /* step 1: create hipblas handle, bind a stream */
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 3: compute */
    CUBLAS_CHECK(hipblasDrotg(cublasH, &A, &B, &c, &s));

    CUDA_CHECK(hipStreamSynchronize(stream));

    /*
     *   A = 2.42
     *   B = 0.50
     */

     printf("A\n");
     std::printf("%0.2f\n", A);
     printf("=====\n");
 
     printf("B\n");
     std::printf("%0.2f\n", B);
     printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.

// MIGRATION_OBSERVE_SCALARS
migration_observer::emit("A",&A,1);
migration_observer::emit("B",&B,1);
migration_observer::emit("c",&c,1);
migration_observer::emit("s",&s,1);
migration_observer::emit("A",&A,1);
migration_observer::emit("B",&B,1);
migration_observer::emit("c",&c,1);
migration_observer::emit("s",&s,1);
/* free resources */
    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}