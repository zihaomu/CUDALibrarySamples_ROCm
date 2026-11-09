/*
 * SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


using data_type = hipDoubleComplex;


int main(int argc, char *argv[]) {
    hipsolverHandle_t cusolverH = NULL;
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream = NULL;
    hipsolverDnParams_t params = NULL;

    int64_t n;
    int64_t lda; // lda >= n, we set lda = n

    /* Square sample matrices (download commands in the README) */
    const char *sample_matrices[] = {
        "conf5_0-4x4-22.mtx", // well-separated eigenvalues,
                              // moderate departure of normality
        "cavity24.mtx"        // clustered eigenvalues
    };

    /* Compute only right eigenvectors. */
    hipsolverEigMode_t jobvl = HIPSOLVER_EIG_MODE_NOVECTOR;
    hipsolverEigMode_t jobvr = HIPSOLVER_EIG_MODE_VECTOR;
    const int64_t ldvl = 1; // ldvl >= 1 if jobvl = HIPSOLVER_EIG_MODE_NOVECTOR
    int64_t ldvr;           // ldvr >= n if jobvr = HIPSOLVER_EIG_MODE_VECTOR

    std::vector<data_type> A;

    data_type *d_A = nullptr;
    data_type *d_W = nullptr;
    data_type *d_VR = nullptr;
    data_type *d_VL = nullptr;
    data_type *d_R = nullptr; // for validation R = VR * diag(W) - A * VR

    int *d_info = nullptr;
    int info = 0;
    const data_type h_minus_one = data_type{-1.0,0.0};
    const data_type h_one = data_type{1.0,0.0};
    size_t workspaceInBytesOnDevice = 0;
    size_t workspaceInBytesOnHost = 0;
    void *d_work = nullptr;
    void *h_work = nullptr;

    /* step 1: create hipsolver handle, bind a stream */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: select mixed precision with iterative refinement as the algorithm */
    CUSOLVER_CHECK(hipsolverDnCreateParams(&params));
    CUSOLVER_CHECK(hipsolverDnSetAdvOptions(params, CUSOLVERDN_GEEV, HIPSOLVER_ALG_1));

    for (const char *mtx_file : sample_matrices) {
        /* step 3: prepare input data */
        // A is n-by-n with leading dimension lda
        read_mtx_and_convert_to_dense(mtx_file, n, n, A, lda);
        std::printf("%s: n = %ld\n", mtx_file, n);
        ldvr = n; // VR is n-by-n with leading dimension ldvr

        /* step 4: allocate device memory and copy A to device */
        CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));
        CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_W), sizeof(data_type) * n));
        CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_VR), sizeof(data_type) * ldvr * n));
        CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_R), sizeof(data_type) * n * n));
        CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));
        CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(),
                                   hipMemcpyHostToDevice, stream));

        /* step 5: query size of workspace and allocate host and device buffers */
        CUSOLVER_CHECK(hipsolverDnXgeev_bufferSize(
            cusolverH,
            params,
            jobvl,
            jobvr,
            n,
            traits<data_type>::cuda_data_type,
            d_A,
            lda,
            traits<data_type>::cuda_data_type,
            d_W,
            traits<data_type>::cuda_data_type,
            d_VL,
            ldvl,
            traits<data_type>::cuda_data_type,
            d_VR,
            ldvr,
            traits<data_type>::cuda_data_type,
            &workspaceInBytesOnDevice,
            &workspaceInBytesOnHost));

        CUDA_CHECK(hipHostMalloc(&h_work, workspaceInBytesOnHost)); // pinned host memory for best performance
        CUDA_CHECK(hipMalloc(&d_work, workspaceInBytesOnDevice));

        /* step 6: compute eigenvalues and eigenvectors */
        CUSOLVER_CHECK(hipsolverDnXgeev(
            cusolverH,
            params,
            jobvl, jobvr,
            n,
            traits<data_type>::cuda_data_type,
            d_A,
            lda,
            traits<data_type>::cuda_data_type,
            d_W,
            traits<data_type>::cuda_data_type,
            d_VL,
            ldvl,
            traits<data_type>::cuda_data_type,
            d_VR,
            ldvr,
            traits<data_type>::cuda_data_type,
            d_work,
            workspaceInBytesOnDevice,
            h_work,
            workspaceInBytesOnHost,
            d_info));

        CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int),
            hipMemcpyDeviceToHost, stream));

        CUDA_CHECK(hipStreamSynchronize(stream));
        if (0 > info) {
            std::printf("%d-th parameter is wrong\n", -info);
        } else if (0 < info) {
            std::printf("info = %d : Xgeev did not converge\n", info);
        } else {
            std::printf("info = %d : Xgeev converged\n", info);

            /* step 7: verify the results */
            // Xgeev overwrites d_A. Reset d_A to the original input matrix.
            CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(),
                                       hipMemcpyHostToDevice, stream));

            // R = VR * diag(W)
            CUBLAS_CHECK(hipblasZdgmm(cublasH, HIPBLAS_SIDE_RIGHT, n, n, d_VR, ldvr,
                d_W, 1, d_R, n));
            // R = R - A * VR
            CUBLAS_CHECK(hipblasZgemm(cublasH, HIPBLAS_OP_N, HIPBLAS_OP_N,
                n, n, n, &h_minus_one, d_A, lda, d_VR, ldvr, &h_one, d_R, n));
            double dR_nrm = 0.0;
            CUBLAS_CHECK(hipblasDznrm2(cublasH, n * n, d_R, 1, &dR_nrm));
            double dA_nrm = 0.0;
            CUBLAS_CHECK(hipblasDznrm2(cublasH, n * lda, d_A, 1, &dA_nrm));
            CUDA_CHECK(hipStreamSynchronize(stream));
            std::printf("|A*VR - VR*diag(W)|/|A| = %E\n", dR_nrm / dA_nrm);
        }

        CUDA_CHECK(hipFree(d_A));
        CUDA_CHECK(hipFree(d_W));
        CUDA_CHECK(hipFree(d_VR));
        CUDA_CHECK(hipFree(d_R));
        CUDA_CHECK(hipFree(d_info));
        CUDA_CHECK(hipFree(d_work));
        CUDA_CHECK(hipHostFree(h_work));
    }

    CUSOLVER_CHECK(hipsolverDnDestroyParams(params));
    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));
    CUBLAS_CHECK(hipblasDestroy(cublasH));
    CUDA_CHECK(hipStreamDestroy(stream));
    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}
