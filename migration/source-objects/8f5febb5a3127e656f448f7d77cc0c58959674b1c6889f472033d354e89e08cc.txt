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
    hipsolverGesvdjInfo_t gesvdj_params = NULL;

    const int m = 3;                   /* 1 <= m <= 32 */
    const int n = 2;                   /* 1 <= n <= 32 */
    const int lda = m;                 /* lda >= m */
    const int ldu = m;                 /* ldu >= m */
    const int ldv = n;                 /* ldv >= n */
    const int minmn = (m < n) ? m : n; /* min(m,n) */

    /*
     *       | 1 2 |
     *   A = | 4 5 |
     *       | 2 1 |
     */

    std::vector<double> A = {1.0, 4.0, 2.0, 2.0, 5.0, 1.0};
    std::vector<double> U(ldu * m, 0); /* m-by-m unitary matrix, left singular vectors  */
    std::vector<double> V(ldv * n, 0); /* n-by-n unitary matrix, right singular vectors */
    std::vector<double> S(minmn, 0);   /* numerical singular value */
    std::vector<double> S_exact = {7.065283497082729,
                                   1.040081297712078}; /* exact singular values */
    int info = 0;                                      /* host copy of error info */

    double *d_A = nullptr;
    double *d_S = nullptr; /* singular values */
    double *d_U = nullptr; /* left singular vectors */
    double *d_V = nullptr; /* right singular vectors */

    int *d_info = nullptr;

    int lwork = 0;            /* size of workspace */
    double *d_work = nullptr; /* device workspace for getrf */

    /* configuration of gesvdj  */
    const double tol = 1.e-7;
    const int max_sweeps = 15;
    const hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_VECTOR; // compute eigenvectors.
    const int econ = 0;                                      /* econ = 1 for economy size */

    /* numerical results of gesvdj  */
    double residual = 0;
    int executed_sweeps = 0;

    std::printf("m = %d, n = %d \n", m, n);
    std::printf("tol = %E, default value is machine zero \n", tol);
    std::printf("max. sweeps = %d, default value is 100\n", max_sweeps);
    std::printf("econ = %d \n", econ);

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, n, A.data(), lda);
    std::printf("=====\n");

    /* step 1: create hipsolver handle, bind a stream */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));

    /* step 2: configuration of gesvdj */
    CUSOLVER_CHECK(hipsolverDnCreateGesvdjInfo(&gesvdj_params));

    /* default value of tolerance is machine zero */
    CUSOLVER_CHECK(hipsolverDnXgesvdjSetTolerance(gesvdj_params, tol));

    /* default value of max. sweeps is 100 */
    CUSOLVER_CHECK(hipsolverDnXgesvdjSetMaxSweeps(gesvdj_params, max_sweeps));

    /* step 3: copy A to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_S), sizeof(double) * S.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_U), sizeof(double) * U.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_V), sizeof(double) * V.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * lda * n, hipMemcpyHostToDevice, stream));

    /* step 4: query working space of SVD */
    CUSOLVER_CHECK(hipsolverDnDgesvdj_bufferSize(
        cusolverH, jobz, /* HIPSOLVER_EIG_MODE_NOVECTOR: compute singular values only */
                         /* HIPSOLVER_EIG_MODE_VECTOR: compute singular value and singular vectors */
        econ,            /* econ = 1 for economy size */
        m,               /* number of rows of A, 0 <= m */
        n,               /* number of columns of A, 0 <= n  */
        d_A,             /* m-by-n */
        lda,             /* leading dimension of A */
        d_S,             /* min(m,n) */
                         /* the singular values in descending order */
        d_U,             /* m-by-m if econ = 0 */
                         /* m-by-min(m,n) if econ = 1 */
        ldu,             /* leading dimension of U, ldu >= max(1,m) */
        d_V,             /* n-by-n if econ = 0  */
                         /* n-by-min(m,n) if econ = 1  */
        ldv,             /* leading dimension of V, ldv >= max(1,n) */
        &lwork, gesvdj_params));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    /* step 5: compute SVD*/
    CUSOLVER_CHECK(hipsolverDnDgesvdj(
        cusolverH, jobz, /* HIPSOLVER_EIG_MODE_NOVECTOR: compute singular values only */
                         /* HIPSOLVER_EIG_MODE_VECTOR: compute singular value and singular vectors */
        econ,            /* econ = 1 for economy size */
        m,               /* number of rows of A, 0 <= m */
        n,               /* number of columns of A, 0 <= n  */
        d_A,             /* m-by-n */
        lda,             /* leading dimension of A */
        d_S,             /* min(m,n)  */
                         /* the singular values in descending order */
        d_U,             /* m-by-m if econ = 0 */
                         /* m-by-min(m,n) if econ = 1 */
        ldu,             /* leading dimension of U, ldu >= max(1,m) */
        d_V,             /* n-by-n if econ = 0  */
                         /* n-by-min(m,n) if econ = 1  */
        ldv,             /* leading dimension of V, ldv >= max(1,n) */
        d_work, lwork, d_info, gesvdj_params));

    CUDA_CHECK(
        hipMemcpyAsync(U.data(), d_U, sizeof(double) * U.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(
        hipMemcpyAsync(V.data(), d_V, sizeof(double) * V.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(
        hipMemcpyAsync(S.data(), d_S, sizeof(double) * S.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    if (0 == info) {
        std::printf("gesvdj converges \n");
    } else if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    } else {
        std::printf("WARNING: info = %d : gesvdj does not converge \n", info);
    }

    std::printf("S = singular values (matlab base-1)\n");
    print_matrix(minmn, 1, S.data(), minmn);
    std::printf("=====\n");

    std::printf("U = left singular vectors (matlab base-1)\n");
    print_matrix(m, m, U.data(), ldu);
    std::printf("=====\n");

    std::printf("V = right singular vectors (matlab base-1)\n");
    print_matrix(n, n, V.data(), ldv);
    std::printf("=====\n");

    /* step 6: measure error of singular value */
    double ds_sup = 0;
    for (int j = 0; j < minmn; j++) {
        double err = fabs(S[j] - S_exact[j]);
        ds_sup = (ds_sup > err) ? ds_sup : err;
    }
    std::printf("|S - S_exact|_sup = %E \n", ds_sup);

    CUSOLVER_CHECK(hipsolverDnXgesvdjGetSweeps(cusolverH, gesvdj_params, &executed_sweeps));

    CUSOLVER_CHECK(hipsolverDnXgesvdjGetResidual(cusolverH, gesvdj_params, &residual));

    std::printf("internal residual |E|_F = %E \n",   residual);
    std::printf("number of executed sweeps = %d \n", executed_sweeps);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("U",U.data(),U.size());
migration_observer::emit("V",V.data(),V.size());
migration_observer::emit("S",S.data(),S.size());
migration_observer::emit("S_exact",S_exact.data(),S_exact.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_U));
    CUDA_CHECK(hipFree(d_V));
    CUDA_CHECK(hipFree(d_S));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));

    CUSOLVER_CHECK(hipsolverDnDestroyGesvdjInfo(gesvdj_params));

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}