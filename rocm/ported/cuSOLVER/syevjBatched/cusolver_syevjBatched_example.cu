#include "observe.hpp"
#include "binary_observe.hpp"
#include <string>
#include <vector>
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
// MIGRATION_BATCH3: preserve original GPU mathematical calls.
const std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";

    hipsolverHandle_t cusolverH = NULL;
    hipStream_t stream = NULL;
    hipsolverSyevjInfo_t syevj_params = NULL;

    const int m = 3;
    const int lda = m;
    const int batchSize = 2;
    /*
     *        |  1  -1   0 |
     *   A0 = | -1   2   0 |
     *        |  0   0   0 |
     *
     *   A0 = V0 * W0 * V0**T
     *
     *   W0 = diag(0, 0.3820, 2.6180)
     *
     *        |  3   4  0 |
     *   A1 = |  4   7  0 |
     *        |  0   0  0 |
     *
     *   A1 = V1 * W1 * V1**T
     *
     *   W1 = diag(0, 0.5279, 9.4721)
     *
     */

    std::vector<double> A(lda * m * batchSize, 0); /* V = [A0 ; A1] */
    std::vector<double> V(lda * m * batchSize, 0); /* V = [V0 ; V1] */
    std::vector<double> W(m * batchSize, 0);       /* W = [W0 ; W1] */
    std::vector<int> info(batchSize, 0);           /* info = [info0 ; info1] */

    double *d_A = nullptr;    /* lda-by-m-by-batchSize */
    double *d_W = nullptr;    /* m-by-batchSize */
    int *d_info = nullptr;    /* batchSize */
    double *d_work = nullptr; /* device workspace for syevjBatched */
    int lwork = 0;            /* size of workspace */

    /* configuration of syevj  */
    const double tol = 1.e-7;
    const int max_sweeps = 15;
    const int sort_eig = migration_case=="sorted"?1:0;                                  /* don't sort eigenvalues */
    const hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_VECTOR; /* compute eigenvectors */
    const hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_LOWER;

    double *A0 = A.data();
    double *A1 = A.data() + lda * m;
    /*
     *        |  1  -1   0 |
     *   A0 = | -1   2   0 |
     *        |  0   0   0 |
     *   A0 is column-major
     */
    A0[0 + 0 * lda] = 1.0;
    A0[1 + 0 * lda] = -1.0;
    A0[2 + 0 * lda] = 0.0;

    A0[0 + 1 * lda] = -1.0;
    A0[1 + 1 * lda] = 2.0;
    A0[2 + 1 * lda] = 0.0;

    A0[0 + 2 * lda] = 0.0;
    A0[1 + 2 * lda] = 0.0;
    A0[2 + 2 * lda] = 0.0;
    /*
     *        |  3   4  0 |
     *   A1 = |  4   7  0 |
     *        |  0   0  0 |
     *   A1 is column-major
     */
    A1[0 + 0 * lda] = 3.0;
    A1[1 + 0 * lda] = 4.0;
    A1[2 + 0 * lda] = 0.0;

    A1[0 + 1 * lda] = 4.0;
    A1[1 + 1 * lda] = 7.0;
    A1[2 + 1 * lda] = 0.0;

    A1[0 + 2 * lda] = 0.0;
    A1[1 + 2 * lda] = 0.0;
    A1[2 + 2 * lda] = 0.0;

    std::printf("A0 = (matlab base-1)\n");
    print_matrix(m, m, A0, lda);
    std::printf("=====\n");

    std::printf("A1 = (matlab base-1)\n");
    print_matrix(m, m, A1, lda);
    std::printf("=====\n");

    /* step 1: create hipsolver handle, bind a stream */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));

    /* step 2: configuration of syevj */
    CUSOLVER_CHECK(hipsolverDnCreateSyevjInfo(&syevj_params));

    /* default value of tolerance is machine zero */
    CUSOLVER_CHECK(hipsolverDnXsyevjSetTolerance(syevj_params, tol));

    /* default value of max. sweeps is 100 */
    CUSOLVER_CHECK(hipsolverDnXsyevjSetMaxSweeps(syevj_params, max_sweeps));

    /* disable sorting */
    CUSOLVER_CHECK(hipsolverDnXsyevjSetSortEig(syevj_params, sort_eig));

    /* step 3: copy A to device */
if(migration_case=="perturbed")for(int b=0;b<batchSize;++b){for(int i=0;i<m;++i)A[b*m*m+i*m+i]+=0.125*(b+i+1);A[b*m*m+2]=A[b*m*m+6]=0.375;}
migration_observer::emit("input_A",A.data(),A.size());
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_W), sizeof(double) * W.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int) * info.size()));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));
    /* step 4: query working space of syevj */
    CUSOLVER_CHECK(hipsolverDnDsyevjBatched_bufferSize(cusolverH, jobz, uplo, m, d_A, lda, d_W,
                                                      &lwork, syevj_params, batchSize));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    /* step 5: compute eigen-pair   */
    CUSOLVER_CHECK(hipsolverDnDsyevjBatched(cusolverH, jobz, uplo, m, d_A, lda, d_W, d_work, lwork,
                                           d_info, syevj_params, batchSize));

    CUDA_CHECK(
        hipMemcpyAsync(V.data(), d_A, sizeof(double) * A.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(
        hipMemcpyAsync(W.data(), d_W, sizeof(double) * W.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(info.data(), d_info, sizeof(int) * info.size(),
                               hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    for (int i = 0; i < batchSize; i++) {
        if (0 == info[i]) {
            std::printf("matrix %d: syevj converges \n", i);
        } else if (0 > info[i]) {
            /* only info[0] shows if some input parameter is wrong.
             * If so, the error is HIPSOLVER_STATUS_INVALID_VALUE.
             */
            std::printf("Error: %d-th parameter is wrong \n", -info[i]);
            exit(1);
        } else { /* info = m+1 */
                 /* if info[i] is not zero, Jacobi method does not converge at i-th matrix. */
            std::printf("WARNING: matrix %d, info = %d : sygvj does not converge \n", i, info[i]);
        }
    }

    /* Step 6: show eigenvalues and eigenvectors */
    double *W0 = W.data();
    double *W1 = W.data() + m;

    std::printf("==== \n");
    for (int i = 0; i < m; i++) {
        std::printf("W0[%d] = %f\n", i, W0[i]);
    }
    std::printf("==== \n");
    for (int i = 0; i < m; i++) {
        std::printf("W1[%d] = %f\n", i, W1[i]);
    }
    std::printf("==== \n");

    double *V0 = V.data();
    double *V1 = V.data() + lda * m;

    std::printf("V0 = (matlab base-1)\n");
    print_matrix(m, m, V0, lda);
    std::printf("V1 = (matlab base-1)\n");
    print_matrix(m, m, V1, lda);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("V",V.data(),V.size());
migration_observer::emit("W",W.data(),W.size());
migration_observer::emit("info",info.data(),info.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_W));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));

    CUSOLVER_CHECK(hipsolverDnDestroySyevjInfo(syevj_params));

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}