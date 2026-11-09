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
    hipStream_t stream = NULL;

    const int m = 3;
    const int n = 2;
    const int lda = m;  // lda >= m
    const int ldu = m;  // ldu >= m
    const int ldvt = n; // ldvt >= n if jobu = 'A'

    /*
     *       | 1 2 |
     *   A = | 4 5 |
     *       | 2 1 |
     */

    const std::vector<double> A = {1.0, 4.0, 2.0, 2.0, 5.0, 1.0};
    std::vector<double> U(ldu * m, 0);  /* m-by-m unitary matrix, left singular vectors  */
    std::vector<double> VT(ldvt * n, 0); /* n-by-n unitary matrix, right singular vectors */
    std::vector<double> S(n, 0);        /* numerical singular value */
    std::vector<double> S_exact = {7.065283497082729,
                                   1.040081297712078}; /* exact singular values */
    int info_gpu = 0;                                  /* host copy of error info */

    double *d_A = nullptr;
    double *d_S = nullptr;  /* singular values */
    double *d_U = nullptr;  /* left singular vectors */
    double *d_VT = nullptr; /* right singular vectors */
    double *d_W = nullptr;  /* W = S*VT */

    int *devInfo = nullptr;

    int lwork = 0; /* size of workspace */
    double *d_work = nullptr;
    double *d_rwork = nullptr;

    const double h_one = 1;
    const double h_minus_one = -1;

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, n, A.data(), lda);
    std::printf("=====\n");

    /* step 1: create hipsolver handle, bind a stream */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy A to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_S), sizeof(double) * S.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_U), sizeof(double) * U.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_VT), sizeof(double) * VT.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_W), sizeof(double) * lda * n));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&devInfo), sizeof(int)));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));

    /* step 3: query working space of SVD */
    CUSOLVER_CHECK(hipsolverDnDgesvd_bufferSize(cusolverH, m, n, &lwork));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    /* step 4: compute SVD */
    signed char jobu = 'A';  // all m columns of U
    signed char jobvt = 'A'; // all n rows of VT
    CUSOLVER_CHECK(hipsolverDnDgesvd(cusolverH, jobu, jobvt, m, n, d_A, lda,
                                    d_S, d_U, ldu, d_VT, ldvt,
                                    d_work, lwork, d_rwork, devInfo));

    CUDA_CHECK(
        hipMemcpyAsync(U.data(), d_U, sizeof(double) * U.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(VT.data(), d_VT, sizeof(double) * VT.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(
        hipMemcpyAsync(S.data(), d_S, sizeof(double) * S.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(&info_gpu, devInfo, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after gesvd: info_gpu = %d\n", info_gpu);
    if (0 == info_gpu) {
        std::printf("gesvd converges \n");
    } else if (0 > info_gpu) {
        std::printf("%d-th parameter is wrong \n", -info_gpu);
        exit(1);
    } else {
        std::printf("WARNING: info = %d : gesvd does not converge \n", info_gpu);
    }

    std::printf("S = singular values (matlab base-1)\n");
    print_matrix(n, 1, S.data(), n);
    std::printf("=====\n");

    std::printf("U = left singular vectors (matlab base-1)\n");
    print_matrix(m, m, U.data(), ldu);
    std::printf("=====\n");

    std::printf("VT = right singular vectors (matlab base-1)\n");
    print_matrix(n, n, VT.data(), ldvt);
    std::printf("=====\n");

    // step 5: measure error of singular value
    double ds_sup = 0;
    for (int j = 0; j < n; j++) {
        double err = fabs(S[j] - S_exact[j]);
        ds_sup = (ds_sup > err) ? ds_sup : err;
    }
    std::printf("|S - S_exact| = %E \n", ds_sup);

    CUBLAS_CHECK(hipblasDdgmm(cublasH, HIPBLAS_SIDE_LEFT, n, n, d_VT, ldvt, d_S, 1, d_W, lda));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));

    CUBLAS_CHECK(hipblasDgemm(cublasH,
                             HIPBLAS_OP_N,  // U
                             HIPBLAS_OP_N,  // W
                             m,            // number of rows of A
                             n,            // number of columns of A
                             n,            // number of columns of U
                             &h_minus_one, /* host pointer */
                             d_U,          // U
                             ldu,
                             d_W,         // W
                             lda, &h_one, /* hostpointer */
                             d_A, lda));

    double dR_fro = 0.0;
    CUBLAS_CHECK(hipblasDnrm2(cublasH, lda * n, d_A, 1, &dR_fro));

    std::printf("|A - U*S*VT| = %E \n", dR_fro);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("U",U.data(),U.size());
migration_observer::emit("VT",VT.data(),VT.size());
migration_observer::emit("S",S.data(),S.size());
migration_observer::emit("S_exact",S_exact.data(),S_exact.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_U));
    CUDA_CHECK(hipFree(d_VT));
    CUDA_CHECK(hipFree(d_S));
    CUDA_CHECK(hipFree(d_W));
    CUDA_CHECK(hipFree(devInfo));
    CUDA_CHECK(hipFree(d_work));
    CUDA_CHECK(hipFree(d_rwork));

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));
    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}