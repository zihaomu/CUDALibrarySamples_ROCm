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

    const int m = 3;   /* 1 <= m <= 32 */
    const int n = 2;   /* 1 <= n <= 32 */
    const int lda = m; /* lda >= m */
    const int ldu = m; /* ldu >= m */
    const int ldv = n; /* ldv >= n */
    const int batchSize = 2;
    const int minmn = (m < n) ? m : n; /* min(m,n) */

    /*
     *        |  1  -1  |
     *   A0 = | -1   2  |
     *        |  0   0  |
     *
     *   A0 = U0 * S0 * V0**T
     *   S0 = diag(2.6180, 0.382)
     *
     *        |  3   4  |
     *   A1 = |  4   7  |
     *        |  0   0  |
     *
     *   A1 = U1 * S1 * V1**T
     *   S1 = diag(9.4721, 0.5279)
     */

    std::vector<double> A(lda * n * batchSize, 0); /* A = [A0 ; A1] */
    std::vector<double> U(ldu * m * batchSize, 0); /* U = [U0 ; U1] */
    std::vector<double> V(ldv * n * batchSize, 0); /* V = [V0 ; V1] */
    std::vector<double> S(minmn * batchSize, 0);   /* S = [S0 ; S1] */
    std::vector<int> info(batchSize, 0);             /* info = [info0 ; info1] */

    double *d_A = nullptr; /* lda-by-n-by-batchSize */
    double *d_U = nullptr; /* ldu-by-m-by-batchSize */
    double *d_V = nullptr; /* ldv-by-n-by-batchSize */
    double *d_S = nullptr; /* minmn-by-batchSize */
    int *d_info = nullptr; /* batchSize */

    int lwork = 0;            /* size of workspace */
    double *d_work = nullptr; /* device workspace for getrf */

    const double tol = 1.e-7;
    const int max_sweeps = 15;
    const int sort_svd = 0;                                  /* don't sort singular values */
    const hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_VECTOR; /* compute singular vectors */

    double *A0 = A.data();
    double *A1 = A.data() + lda * n; /* Aj is m-by-n */

    /*
     *        |  1  -1  |
     *   A0 = | -1   2  |
     *        |  0   0  |
     *   A0 is column-major
     */
    A0[0 + 0 * lda] = 1.0;
    A0[1 + 0 * lda] = -1.0;
    A0[2 + 0 * lda] = 0.0;

    A0[0 + 1 * lda] = -1.0;
    A0[1 + 1 * lda] = 2.0;
    A0[2 + 1 * lda] = 0.0;

    /*
     *        |  3   4  |
     *   A1 = |  4   7  |
     *        |  0   0  |
     *   A1 is column-major
     */
    A1[0 + 0 * lda] = 3.0;
    A1[1 + 0 * lda] = 4.0;
    A1[2 + 0 * lda] = 0.0;

    A1[0 + 1 * lda] = 4.0;
    A1[1 + 1 * lda] = 7.0;
    A1[2 + 1 * lda] = 0.0;

    std::printf("m = %d, n = %d \n", m, n);
    std::printf("tol = %E, default value is machine zero \n", tol);
    std::printf("max. sweeps = %d, default value is 100\n", max_sweeps);

    std::printf("A0 = (matlab base-1)\n");
    print_matrix(m, n, A.data(), lda);
    std::printf("=====\n");

    std::printf("A1 = (matlab base-1)\n");
    print_matrix(m, n, A.data() + lda * n, lda);
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

    /* disable sorting */
    CUSOLVER_CHECK(hipsolverDnXgesvdjSetSortEig(gesvdj_params, sort_svd));

    /* step 3: copy A to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_U), sizeof(double) * U.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_V), sizeof(double) * V.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_S), sizeof(double) * S.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int) * info.size()));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));

    /* step 4: query working space of gesvdjBatched */
    CUSOLVER_CHECK(hipsolverDnDgesvdjBatched_bufferSize(cusolverH, jobz, m, n, d_A, lda, d_S, d_U,
                                                       ldu, d_V, ldv, &lwork, gesvdj_params,
                                                       batchSize));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    /* step 5: compute singular values of A0 and A1 */
    CUSOLVER_CHECK(hipsolverDnDgesvdjBatched(cusolverH, jobz, m, n, d_A, lda, d_S, d_U, ldu, d_V,
                                            ldv, d_work, lwork, d_info, gesvdj_params, batchSize));

    CUDA_CHECK(
        hipMemcpyAsync(U.data(), d_U, sizeof(double) * U.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(
        hipMemcpyAsync(V.data(), d_V, sizeof(double) * V.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(
        hipMemcpyAsync(S.data(), d_S, sizeof(double) * S.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(info.data(), d_info, sizeof(int) * info.size(),
                               hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    for (int i = 0; i < batchSize; i++) {
        if (0 == info[i]) {
            std::printf("matrix %d: gesvdj converges \n", i);
        } else if (0 > info[i]) {
            /* only info[0] shows if some input parameter is wrong.
             * If so, the error is HIPSOLVER_STATUS_INVALID_VALUE.
             */
            std::printf("Error: %d-th parameter is wrong \n", -info[i]);
            exit(1);
        } else { /* info = m+1 */
                 /* if info[i] is not zero, Jacobi method does not converge at i-th matrix. */
            std::printf("WARNING: matrix %d, info = %d : gesvdj does not converge \n", i, info[i]);
        }
    }

    /* Step 6: show singular values and singular vectors */
    double *S0 = S.data();
    double *S1 = S.data() + minmn;
    std::printf("==== \n");
    for (int i = 0; i < minmn; i++) {
        std::printf("S0(%d) = %20.16E\n", i + 1, S0[i]);
    }
    std::printf("==== \n");
    for (int i = 0; i < minmn; i++) {
        std::printf("S1(%d) = %20.16E\n", i + 1, S1[i]);
    }
    std::printf("==== \n");

    double *U0 = U.data();
    double *U1 = U.data() + ldu * m; /* Uj is m-by-m */
    std::printf("U0 = (matlab base-1)\n");
    print_matrix(m, m, U0, ldu);
    std::printf("U1 = (matlab base-1)\n");
    print_matrix(m, m, U1, ldu);

    double *V0 = V.data();
    double *V1 = V.data() + ldv * n; /* Vj is n-by-n */
    std::printf("V0 = (matlab base-1)\n");
    print_matrix(n, n, V0, ldv);
    std::printf("V1 = (matlab base-1)\n");
    print_matrix(n, n, V1, ldv);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("U",U.data(),U.size());
migration_observer::emit("V",V.data(),V.size());
migration_observer::emit("S",S.data(),S.size());
migration_observer::emit("info",info.data(),info.size());
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