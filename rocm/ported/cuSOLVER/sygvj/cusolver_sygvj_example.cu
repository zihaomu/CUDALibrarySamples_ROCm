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
    hipsolverSyevjInfo_t syevj_params = NULL;

    const int m = 3;
    const int lda = m;
    /*
     *       | 3.5 0.5 0 |
     *   A = | 0.5 3.5 0 |
     *       | 0   0   2 |
     *
     *       | 10  2   3 |
     *   B = | 2  10   5 |
     *       | 3   5  10 |
     */

    const std::vector<double> A = {3.5, 0.5, 0, 0.5, 3.5, 0.0, 0.0, 0.0, 2.0};
    const std::vector<double> B = {10.0, 2.0, 3.0, 2.0, 10.0, 5.0, 3.0, 5.0, 10.0};
    const std::vector<double> lambda = {0.158660256604, 0.370751508101882, 0.6};

    std::vector<double> V(lda * m, 0); // eigenvectors
    std::vector<double> W(m, 0);       // eigenvalues

    double *d_A = nullptr;
    double *d_B = nullptr;
    double *d_W = nullptr;
    int *d_info = nullptr;
    double *d_work = nullptr;
    int lwork = 0;
    int info = 0;

    /* configuration of syevj  */
    const double tol = 1.e-7;
    const int max_sweeps = 15;
    const hipsolverEigType_t itype = HIPSOLVER_EIG_TYPE_1;     // A*x = (lambda)*B*x
    const hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_VECTOR; // compute eigenvectors.
    const hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_LOWER;

    /* numerical results of syevj  */
    double residual = 0;
    int executed_sweeps = 0;

    std::printf("tol = %E, default value is machine zero \n", tol);
    std::printf("max. sweeps = %d, default value is 100\n", max_sweeps);

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, m, A.data(), lda);
    std::printf("=====\n");

    std::printf("B = (matlab base-1)\n");
    print_matrix(m, m, B.data(), lda);
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

    /* step 3: copy A to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_B), sizeof(double) * B.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_W), sizeof(double) * W.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));
    CUDA_CHECK(
        hipMemcpyAsync(d_B, B.data(), sizeof(double) * B.size(), hipMemcpyHostToDevice, stream));

    /* step 4: query working space of sygvj */
    CUSOLVER_CHECK(hipsolverDnDsygvj_bufferSize(cusolverH, itype, jobz, uplo, m, d_A, lda, d_B,
                                               lda, /* ldb */
                                               d_W, &lwork, syevj_params));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    /* step 5: compute spectrum of (A,B) */
    CUSOLVER_CHECK(hipsolverDnDsygvj(cusolverH, itype, jobz, uplo, m, d_A, lda, d_B, lda, /* ldb */
                                    d_W, d_work, lwork, d_info, syevj_params));

    CUDA_CHECK(
        hipMemcpyAsync(V.data(), d_A, sizeof(double) * A.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(
        hipMemcpyAsync(W.data(), d_W, sizeof(double) * W.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    if (0 == info) {
        std::printf("sygvj converges \n");
    } else if (0 > info) {
        std::printf("Error: %d-th parameter is wrong \n", -info);
        exit(1);
    } else if (m >= info) {
        std::printf("Error: leading minor of order %d of B is not positive definite\n", -info);
        exit(1);
    } else { /* info = m+1 */
        std::printf("WARNING: info = %d : sygvj does not converge \n", info);
    }

    std::printf("Eigenvalue = (matlab base-1), ascending order\n");
    int idx = 1;
    for (auto const &i : W) {
        std::printf("W[%i] = %E\n", idx, i);
        idx++;
    }

    std::printf("V = (matlab base-1)\n");
    print_matrix(m, m, V.data(), lda);
    std::printf("=====\n");

    /* step 6: check eigenvalues */
    double lambda_sup = 0;
    for (int i = 0; i < m; i++) {
        double error = fabs(lambda[i] - W[i]);
        lambda_sup = (lambda_sup > error) ? lambda_sup : error;
    }
    std::printf("|lambda - W| = %E\n", lambda_sup);

    CUSOLVER_CHECK(hipsolverDnXsyevjGetSweeps(cusolverH, syevj_params, &executed_sweeps));

    CUSOLVER_CHECK(hipsolverDnXsyevjGetResidual(cusolverH, syevj_params, &residual));

    std::printf("residual |A - V*W*V**H|_F = %E \n", residual);
    std::printf("number of executed sweeps = %d \n", executed_sweeps);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("B",B.data(),B.size());
migration_observer::emit("lambda",lambda.data(),lambda.size());
migration_observer::emit("V",V.data(),V.size());
migration_observer::emit("W",W.data(),W.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_B));
    CUDA_CHECK(hipFree(d_W));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));

    CUSOLVER_CHECK(hipsolverDnDestroySyevjInfo(syevj_params));

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}