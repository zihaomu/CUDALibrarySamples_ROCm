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
#include <stdexcept>

#include <hip/hip_runtime.h>
#include <hipsolver.h>

#include "cusolver_utils.h"

template <typename T>
void trtri(hipsolverHandle_t handle, int n, T *d_A, int lda,
           hipblasFillMode_t uplo, hipblasDiagType_t diag, int *d_info) {
    void *d_work = nullptr;
    size_t workspaceInBytesOnDevice = 0;
    void *h_work = nullptr;
    size_t workspaceInBytesOnHost = 0;

    try {
        printf("Querying required device and host workspace size...\n");
        CUSOLVER_CHECK(cusolverDnXtrtri_bufferSize(handle, uplo, diag, n, traits<T>::cuda_data_type,
                                                   reinterpret_cast<void *>(d_A), lda, &workspaceInBytesOnDevice,
                                                   &workspaceInBytesOnHost));

        printf("Allocating required device workspace...\n");
        CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), workspaceInBytesOnDevice));

        printf("Allocating required host workspace...\n");
        if (workspaceInBytesOnHost) {
            h_work = malloc(workspaceInBytesOnHost);
            if (h_work == nullptr) {
                throw std::bad_alloc();
            }
        }

        printf("Computing the inverse of a %s triangular matrix...\n",
               (uplo == HIPBLAS_FILL_MODE_UPPER ? "upper" : "lower"));
        CUSOLVER_CHECK(cusolverDnXtrtri(handle, uplo, diag, n, traits<T>::cuda_data_type, d_A, lda,
                                        d_work, workspaceInBytesOnDevice, h_work, workspaceInBytesOnHost, d_info));
    } catch (const std::exception &e) {
        fprintf(stderr, "error: %s\n", e.what());
    }

    CUDA_CHECK(hipFree(d_work));
    free(h_work);
}

// calculate |I - A * A^-1| and compare with eps
template <typename T>
void residual_check(int n, T *d_A, T *d_A_inv, int lda, double eps) {
    // create identity matrix
    T *h_A_res = (T *)calloc(n * lda, sizeof(T));

    for (int i = 0; i < n; i++) {
        h_A_res[i * lda + i] = T(1);
    }

    T alpha = -1;
    T beta = 1;

    T *d_A_res;
    CUDA_CHECK(hipMalloc(&d_A_res, sizeof(T) * n * lda));
    CUDA_CHECK(hipMemcpy(d_A_res, h_A_res, sizeof(T) * n * lda, hipMemcpyHostToDevice));

    hipblasHandle_t handle;
    CUBLAS_CHECK(hipblasCreate(&handle));

    CUBLAS_CHECK(hipblasGemmEx(handle, HIPBLAS_OP_N, HIPBLAS_OP_N, n, n, n,
                              reinterpret_cast<void *>(&alpha), reinterpret_cast<void *>(d_A),
                              traits<T>::cuda_data_type, lda, reinterpret_cast<void *>(d_A_inv),
                              traits<T>::cuda_data_type, lda, reinterpret_cast<void *>(&beta),
                              reinterpret_cast<void *>(d_A_res), traits<T>::cuda_data_type, lda,
                              traits<T>::cuda_data_type, HIPBLAS_GEMM_DEFAULT));

    CUDA_CHECK(hipDeviceSynchronize());

    CUDA_CHECK(hipMemcpy(h_A_res, d_A_res, sizeof(T) * n * lda, hipMemcpyDeviceToHost));

    double A_res_norm = 0.0;
    for (int i = 0; i < n; i++) {
        double sum = 0.0;
        for (int j = 0; j < n; j++) {
            sum += traits<T>::abs(h_A_res[i + j * lda]);
        }
        A_res_norm = std::max(A_res_norm, sum);
    }

    printf("Check: %s\n", (A_res_norm > eps ? "FAILED" : "PASSED"));

    CUBLAS_CHECK(hipblasDestroy(handle));

    free(h_A_res);
    CUDA_CHECK(hipFree(d_A_res));
}

int main(int argc, char *argv[]) {
    using data_type = double;
    const double eps = 1.e-15;

    hipsolverHandle_t handle;

    hipStream_t stream;

    int n = 1000;
    int lda = n + 1;

    data_type *d_A = nullptr;
    data_type *d_A_inv = nullptr;
    data_type *h_A = nullptr;
    int *d_info;
    int h_info;

    const hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_UPPER;
    const hipblasDiagType_t diag = HIPBLAS_DIAG_NON_UNIT;

    printf("Generating random diagonal dominant matrix...\n");
    generate_random_matrix<data_type>(lda, n, &h_A, &lda);
    make_diag_dominant_matrix<data_type>(lda, n, h_A, lda);

    // zero lower triangle
    for (int j = 0; j < n; j++) {
        for (int i = j + 1; i < n; i++) {
            h_A[j * lda + i] = 0;
        }
    }

    printf("Initializing required CUDA and cuSOLVER miscellaneous variables...\n");
    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverDnCreate(&handle));
    CUSOLVER_CHECK(hipsolverSetStream(handle, stream));

    printf("Allocating required device memory...\n");
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * lda * n));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A_inv), sizeof(data_type) * lda * n));
    CUDA_CHECK(hipMalloc(&d_info, sizeof(int)));

    printf("Copying input data to the device...\n");
    CUDA_CHECK(hipMemcpy(d_A, h_A, sizeof(data_type) * lda * n, hipMemcpyHostToDevice));
    CUDA_CHECK(hipMemcpy(d_A_inv, d_A, sizeof(data_type) * lda * n, hipMemcpyDeviceToDevice));
    CUDA_CHECK(hipMemset(d_info, 0, sizeof(int)));

    trtri(handle, n, d_A_inv, lda, uplo, diag, d_info);

    CUDA_CHECK(hipStreamSynchronize(stream));

    printf("Copying information back to the host...\n");
    CUDA_CHECK(hipMemcpy(&h_info, d_info, sizeof(int), hipMemcpyDeviceToHost));

    printf("Checking returned information...\n");
    if (h_info > 0) {
        fprintf(stderr, "warning: leading minor of order %d is not p.d.\n", h_info);
    } else if (h_info < 0) {
        fprintf(stderr, "error: %d-th argument had an illegal value\n", h_info);
    }

    printf("Verifying results...\n");
    residual_check(n, d_A, d_A_inv, lda, eps);

    printf("Destroying CUDA and cuSOLVER miscellaneous variables...\n");
    CUDA_CHECK(hipStreamDestroy(stream));
    CUSOLVER_CHECK(hipsolverDnDestroy(handle));

    printf("Freeing memory...\n");
    free(h_A);
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_A_inv));
    CUDA_CHECK(hipFree(d_info));

    printf("Done...\n");

    return EXIT_SUCCESS;
}