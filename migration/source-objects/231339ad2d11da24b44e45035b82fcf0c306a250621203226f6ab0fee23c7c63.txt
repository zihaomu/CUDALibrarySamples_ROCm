#include "observe.hpp"
/*
 * SPDX-FileCopyrightText: Copyright (c) 2020-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <vector>

#include <hipblas.h>
#include <hip/hip_runtime.h>
#include <hipsolver.h>

#include "cusolver_utils.h"

int main(int argc, char *argv[]) {
    hipsolverHandle_t cusolverH = NULL;
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream = NULL;
    hipsolverDnParams_t params = NULL;

    using data_type = double;

    const int64_t m = 3;
    const int64_t n = 2;
    const int64_t lda = m;
    const int64_t ldu = m;
    const int64_t ldv = n;
    const int64_t minmn = (m < n) ? m : n;

    /*
     *       | 1 2  |
     *   A = | 4 5  |
     *       | 2 1  |
     */

    const std::vector<data_type> A = {1.0, 4.0, 2.0, 2.0, 5.0, 1.0};
    std::vector<data_type> U(ldu * m, 0);
    std::vector<data_type> V(ldv * n, 0);
    std::vector<data_type> S(n, 0);
    std::vector<data_type> S_exact = {7.065283497082729, 1.040081297712078};

    data_type *d_A = nullptr;
    data_type *d_S = nullptr;
    data_type *d_U = nullptr;
    data_type *d_V = nullptr;
    int *d_info = nullptr;
    data_type *d_W = nullptr; // W = S*VT

    int info = 0;
    const double h_one = 1;
    const double h_minus_one = -1;

    size_t workspaceInBytesOnDevice = 0; /* size of workspace */
    void *d_work = nullptr;              /* device workspace for getrf */
    size_t workspaceInBytesOnHost = 0;   /* size of workspace */
    void *h_work = nullptr;              /* host workspace for getrf */

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, n, A.data(), lda);
    std::printf("=====\n");

    /* step 1: create hipsolver handle, bind a stream */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));
    CUSOLVER_CHECK(hipsolverDnCreateParams(&params));

    /* step 2: copy A to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(data_type) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_S), sizeof(data_type) * S.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_U), sizeof(data_type) * U.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_V), sizeof(data_type) * V.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_W), sizeof(data_type) * lda * n));

    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));

    hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_VECTOR;
    // const int econ = 0; /* compute 3-by-3 U  */
    const int econ = 1; /* compute 3-by-2 U  */
    double h_err_sigma;

    /* step 3: query working space of SVD */
    CUSOLVER_CHECK(cusolverDnXgesvdp_bufferSize(
        cusolverH, params,                                   /* params */
        jobz, econ, m, n, traits<data_type>::cuda_data_type, /* dataTypeA */
        d_A, lda, traits<data_type>::cuda_data_type,         /* dataTypeS */
        d_S, traits<data_type>::cuda_data_type,              /* dataTypeU */
        d_U, ldu,
        traits<data_type>::cuda_data_type,                   /* dataTypeV */
        d_V, ldv,
        traits<data_type>::cuda_data_type,                   /* computeType */
        &workspaceInBytesOnDevice, &workspaceInBytesOnHost));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), workspaceInBytesOnDevice));

    if (0 < workspaceInBytesOnHost) {
        h_work = reinterpret_cast<void *>(malloc(workspaceInBytesOnHost));
        if (h_work == nullptr) {
            throw std::runtime_error("Error: h_work not allocated.");
        }
    }

    /* step 4: compute SVD */
    CUSOLVER_CHECK(cusolverDnXgesvdp(cusolverH, params,                           /* params */
                                     jobz, econ, m, n,
                                     traits<data_type>::cuda_data_type,           /* dataTypeA */
                                     d_A, lda, traits<data_type>::cuda_data_type, /* dataTypeS */
                                     d_S, traits<data_type>::cuda_data_type,      /* dataTypeU */
                                     d_U, ldu,
                                     traits<data_type>::cuda_data_type,           /* dataTypeV */
                                     d_V, ldv,
                                     traits<data_type>::cuda_data_type,           /* computeType */
                                     d_work, workspaceInBytesOnDevice, h_work, workspaceInBytesOnHost,
                                     d_info, &h_err_sigma)); /* h_err_sigma is always 0 starting from 13.3U1 */

    CUDA_CHECK(hipMemcpyAsync(U.data(), d_U, sizeof(data_type) * U.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(V.data(), d_V, sizeof(data_type) * V.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(S.data(), d_S, sizeof(data_type) * S.size(), hipMemcpyDeviceToHost,
                               stream));
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after Xgesvdp: info = %d\n", info);
    if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }
    std::printf("=====\n");

    std::printf("S = (matlab base-1)\n");
    print_matrix(minmn, 1, S.data(), n);
    std::printf("=====\n");

    std::printf("U = (matlab base-1)\n");
    print_matrix(m, (econ) ? minmn : m, U.data(), ldu);
    std::printf("=====\n");

    std::printf("V = (matlab base-1)\n");
    print_matrix((econ) ? minmn : n, n, V.data(), ldv);
    std::printf("=====\n");

    // step 5: measure error of singular value
    double ds_sup = 0;
    for (int j = 0; j < minmn; j++) {
        double err = fabs(S[j] - S_exact[j]);
        ds_sup = (ds_sup > err) ? ds_sup : err;
    }
    std::printf("|S - S_exact| = %E \n", ds_sup);

    /* step 6: |A - U*S*V**T| */
    /* W = V*S */
    CUBLAS_CHECK(hipblasDdgmm(cublasH, HIPBLAS_SIDE_RIGHT, n, n, d_V, ldv, d_S, 1, d_W, lda));

    /* A := -U*W**T + A */
    CUDA_CHECK(hipMemcpyAsync(d_A, A.data(), sizeof(data_type) * A.size(), hipMemcpyHostToDevice,
                               stream));

    CUBLAS_CHECK(hipblasDgemm(cublasH, HIPBLAS_OP_N, HIPBLAS_OP_T, m, /* number of rows of A */
                             n,                                    /* number of columns of A */
                             n,                                    /* number of columns of U  */
                             &h_minus_one, d_U, ldu, d_W, lda, &h_one, d_A, lda));

    double dR_fro = 0.0;
    CUBLAS_CHECK(hipblasDnrm2(cublasH, A.size(), d_A, 1, &dR_fro));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("|A - U*S*V**T| = %E \n", dR_fro);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("U",U.data(),U.size());
migration_observer::emit("V",V.data(),V.size());
migration_observer::emit("S",S.data(),S.size());
migration_observer::emit("S_exact",S_exact.data(),S_exact.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_S));
    CUDA_CHECK(hipFree(d_U));
    CUDA_CHECK(hipFree(d_V));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_W));
    CUDA_CHECK(hipFree(d_work));
    free(h_work);

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));
    CUBLAS_CHECK(hipblasDestroy(cublasH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}
