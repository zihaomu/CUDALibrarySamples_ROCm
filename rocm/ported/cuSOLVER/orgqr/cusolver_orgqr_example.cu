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
#include <hipsolver.h>

#include "cusolver_utils.h"

int main(int argc, char *argv[]) {
    hipsolverHandle_t cusolverH = NULL;
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream{};

    const int m = 3;
    const int n = 2;
    const int lda = m;

    /*
     *       | 1 2 |
     *   A = | 4 5 |
     *       | 2 1 |
     */

    const std::vector<double> A = {1.0, 4.0, 2.0, 2.0, 5.0, 1.0};
    std::vector<double> Q(lda * n, 0); // orthonormal columns
    std::vector<double> R(n * n, 0);   // R = I - Q**T*Q

    /* device memory */
    double *d_A = nullptr;
    double *d_tau = nullptr;
    int *d_info = nullptr;
    double *d_work = nullptr;

    double *d_R = nullptr;

    int lwork_geqrf = 0;
    int lwork_orgqr = 0;
    int lwork = 0;
    int info = 0;

    const double h_one = 1;
    const double h_minus_one = -1;

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, n, A.data(), lda);
    std::printf("=====\n");

    /* step 1: create cudense/hipblas handle */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy A and B to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_tau), sizeof(double) * n));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_R), sizeof(double) * R.size()));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));

    /* step 3: query working space of geqrf and orgqr */
    CUSOLVER_CHECK(hipsolverDnDgeqrf_bufferSize(cusolverH, m, n, d_A, lda, &lwork_geqrf));

    CUSOLVER_CHECK(hipsolverDnDorgqr_bufferSize(cusolverH, m, n, n, d_A, lda, d_tau, &lwork_orgqr));

    lwork = std::max(lwork_geqrf, lwork_orgqr);

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    /* step 4: compute QR factorization */
    CUSOLVER_CHECK(hipsolverDnDgeqrf(cusolverH, m, n, d_A, lda, d_tau, d_work, lwork, d_info));

    /* check if QR is successful or not */
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after geqrf: info = %d\n", info);
    if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }

    /* step 5: compute Q */
    CUSOLVER_CHECK(hipsolverDnDorgqr(cusolverH, m, n, n, d_A, lda, d_tau, d_work, lwork, d_info));

    /* check if orgqr is successful or not */
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after orgqr: info = %d\n", info);
    if (0 > info) {
        printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }

    CUDA_CHECK(
        hipMemcpyAsync(Q.data(), d_A, sizeof(double) * A.size(), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("Q = (matlab base-1)\n");
    print_matrix(m, n, Q.data(), lda);

    // step 6: measure R = I - Q**T*Q

    // Set R = I.
    std::fill(R.begin(), R.end(), 0.0);
    for (int i = 0; i < n; i++) {
        R[i + i * n] = 1.0;
    }
    CUDA_CHECK(
        hipMemcpyAsync(d_R, R.data(), sizeof(double) * R.size(), hipMemcpyHostToDevice, stream));

    CUBLAS_CHECK(hipblasDgemm(cublasH,
                             HIPBLAS_OP_T,  // Q**T
                             HIPBLAS_OP_N,  // Q
                             n,            // number of rows of R
                             n,            // number of columns of R
                             m,            // number of columns of Q**T
                             &h_minus_one, /* host pointer */
                             d_A,          // Q**T
                             lda,
                             d_A,         // Q
                             lda, &h_one, /* hostpointer */
                             d_R, n));

    double dR_nrm2 = 0.0;
    CUBLAS_CHECK(hipblasDnrm2(cublasH, R.size(), d_R, 1, &dR_nrm2));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("|I - Q**T*Q| = %E\n", dR_nrm2);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("Q",Q.data(),Q.size());
migration_observer::emit("R",R.data(),R.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_tau));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));
    CUDA_CHECK(hipFree(d_R));

    CUBLAS_CHECK(hipblasDestroy(cublasH));
    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}