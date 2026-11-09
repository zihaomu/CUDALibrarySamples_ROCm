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
    hipsolverHandle_t cusolverH = NULL;
    hipStream_t stream = NULL;
    hipsolverDnParams_t params = NULL;

    using data_type = double;

    const int m = 3;
    const int lda = m;
    /*
     *       | 3.5 0.5 0.0 |
     *   A = | 0.5 3.5 0.0 |
     *       | 0.0 0.0 2.0 |
     *
     */
    const std::vector<data_type> A = {3.5, 0.5, 0.0, 0.5, 3.5, 0.0, 0.0, 0.0, 2.0};
    const std::vector<data_type> lambda = {2.0, 3.0, 4.0};

    std::vector<data_type> V(lda * m, 0); // eigenvectors
    std::vector<data_type> W(m, 0);       // eigenvalues

    data_type *d_A = nullptr;
    data_type *d_W = nullptr;
    int *d_info = nullptr;

    int info = 0;

    size_t workspaceInBytesOnDevice = 0; /* size of workspace */
    void *d_work = nullptr;              /* device workspace */
    size_t workspaceInBytesOnHost = 0;   /* size of workspace */
    void *h_work = nullptr;              /* host workspace for */

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, m, A.data(), lda);
    std::printf("=====\n");

    /* step 1: create hipsolver handle, bind a stream */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));
    CUSOLVER_CHECK(hipsolverDnCreateParams(&params));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_W), sizeof(data_type) * W.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));

    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));

    // step 3: query working space of syevd
    hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_VECTOR; // compute eigenvalues and eigenvectors.
    hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_LOWER;

    CUSOLVER_CHECK(hipsolverDnXsyevd_bufferSize(
        cusolverH, params, jobz, uplo, m, traits<data_type>::cuda_data_type, d_A, lda,
        traits<data_type>::cuda_data_type, d_W, traits<data_type>::cuda_data_type, &workspaceInBytesOnDevice,
        &workspaceInBytesOnHost));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), workspaceInBytesOnDevice));

    if (0 < workspaceInBytesOnHost) {
        h_work = reinterpret_cast<void *>(malloc(workspaceInBytesOnHost));
        if (h_work == nullptr) {
            throw std::runtime_error("Error: h_work not allocated.");
        }
    }

    // step 4: compute spectrum
    CUSOLVER_CHECK(hipsolverDnXsyevd(
        cusolverH, params, jobz, uplo, m, traits<data_type>::cuda_data_type, d_A, lda,
        traits<data_type>::cuda_data_type, d_W, traits<data_type>::cuda_data_type, d_work, workspaceInBytesOnDevice,
        h_work, workspaceInBytesOnHost, d_info));

    CUDA_CHECK(hipMemcpyAsync(V.data(), d_A, sizeof(data_type) * V.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(W.data(), d_W, sizeof(data_type) * W.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after Xsyevd: info = %d\n", info);
    if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }

    std::printf("eigenvalue = (matlab base-1), ascending order\n");
    int idx = 1;
    for (auto const& i : W ) {
        std::printf("W[%i] = %E\n", idx, i);
        idx++;
    }

    std::printf("V = (matlab base-1)\n");
    print_matrix(m, m, V.data(), lda);
    std::printf("=====\n");

    // step 4: check eigenvalues
    data_type lambda_sup = 0;
    for (int i = 0; i < m; i++) {
        data_type error = fabs(lambda[i] - W[i]);
        lambda_sup = (lambda_sup > error) ? lambda_sup : error;
    }
    std::printf("|lambda - W| = %E\n", lambda_sup);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("lambda",lambda.data(),lambda.size());
migration_observer::emit("V",V.data(),V.size());
migration_observer::emit("W",W.data(),W.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_W));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));
    free(h_work);

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}