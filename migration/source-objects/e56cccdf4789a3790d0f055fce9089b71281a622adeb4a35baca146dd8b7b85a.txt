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

#include <hip/hip_runtime.h>
#include <hipsolver.h>

#include "cusolver_utils.h"

int main(int argc, char *argv[]) {
// MIGRATION_BATCH2: default is unchanged original input and mathematical GPU API.
const std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";

    hipsolverHandle_t cusolverH = NULL;
    hipStream_t stream = NULL;
    hipsolverDnParams_t params = NULL;

    using data_type = double;

    const int64_t m = 3;
    const int64_t lda = m;
    const int64_t ldb = m;

    /*
     *       | 1 2 3 |
     *   A = | 2 5 5 |
     *       | 3 5 12 |
     */

    std::vector<data_type> A = {1.0, 2.0, 3.0, 2.0, 5.0, 5.0, 3.0, 5.0, 12.0};
    const std::vector<data_type> B = {1.0, 2.0, 3.0};
    std::vector<data_type> tau(m, 0);
    int info = 0;

    data_type *d_A = nullptr; /* device copy of A */
    data_type *d_B = nullptr; /* device copy of B */
    int64_t *d_tau = nullptr; /* pivoting sequence */
    int *d_info = nullptr;    /* error info */

    size_t workspaceInBytesOnDevice = 0; /* size of workspace */
    void *d_work = nullptr;              /* device workspace */
    size_t workspaceInBytesOnHost = 0;   /* size of workspace */
    void *h_work = nullptr;              /* host workspace */

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, m, A.data(), lda);
    std::printf("=====\n");

    std::printf("B = (matlab base-1)\n");
    print_matrix(m, 1, B.data(), ldb);
    std::printf("=====\n");

    /* step 1: create hipsolver handle, bind a stream */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));
    CUSOLVER_CHECK(hipsolverDnCreateParams(&params));

    /* step 2: copy A to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_B), sizeof(data_type) * B.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_tau), sizeof(data_type) * tau.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));

    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(d_B, B.data(), sizeof(data_type) * B.size(), hipMemcpyHostToDevice,
                               stream));

    /* step 3: query working space of geqrf */
    CUSOLVER_CHECK(
        hipsolverDnXgeqrf_bufferSize(cusolverH, params, m, m, traits<data_type>::cuda_data_type, d_A,
                                    lda, traits<data_type>::cuda_data_type, d_tau,
                                    traits<data_type>::cuda_data_type, &workspaceInBytesOnDevice,
                                    &workspaceInBytesOnHost));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), workspaceInBytesOnDevice));

    if (0 < workspaceInBytesOnHost) {
        h_work = reinterpret_cast<void *>(malloc(workspaceInBytesOnHost));
        if (h_work == nullptr) {
            throw std::runtime_error("Error: h_work not allocated.");
        }
    }

    /* step 4: QR factorization */
    CUSOLVER_CHECK(hipsolverDnXgeqrf(cusolverH, params, m, m, traits<data_type>::cuda_data_type, d_A,
                                    lda, traits<data_type>::cuda_data_type, d_tau,
                                    traits<data_type>::cuda_data_type, d_work, workspaceInBytesOnDevice, h_work,
                                    workspaceInBytesOnHost, d_info));

    CUDA_CHECK(hipMemcpyAsync(tau.data(), d_tau, sizeof(data_type) * tau.size(),
                               hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after Xgeqrf: info = %d\n", info);
    if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }

    std::printf("tau = (matlab base-1)\n");
    print_matrix(m, 1, tau.data(), lda);
    std::printf("=====\n");

    CUDA_CHECK(hipMemcpyAsync(A.data(), d_A, sizeof(data_type) * A.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, m, A.data(), lda);
    std::printf("=====\n");

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("B",B.data(),B.size());
migration_observer::emit("tau",tau.data(),tau.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_B));
    CUDA_CHECK(hipFree(d_tau));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));
    free(h_work);

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}