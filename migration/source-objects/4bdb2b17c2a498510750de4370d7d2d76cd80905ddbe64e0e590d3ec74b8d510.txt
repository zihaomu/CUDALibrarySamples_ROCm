#include "observe.hpp"
#include <string>
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
// MIGRATION_BATCH4
const std::string migration_case=std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";

    hipsolverHandle_t cusolverH = NULL;
    hipblasHandle_t cublasH = NULL;
    hipStream_t stream{};

    const int m = 3;
    const int lda = m;
    const int ldb = m;
    const int nrhs = migration_case=="multiple-rhs"?2:1; // number of right hand side vectors

    /*       | 1 2 3 |
     *   A = | 4 5 6 |
     *       | 2 1 1 |
     *
     *   x = (1 1 1)'
     *   b = (6 15 4)'
     */

    std::vector<double> A = {1.0, 4.0, 2.0, 2.0, 5.0, 1.0, 3.0, 6.0, 1.0};
    // std::vector<double> X = {1.0, 1.0, 1.0}; // exact solution
    std::vector<double> B = {6.0, 15.0, 4.0};
    std::vector<double> XC(ldb * nrhs, 0); // solution matrix from GPU

if(migration_case=="changed-matrix"){A[0]+=1.;A[4]+=0.5;}if(migration_case=="Q-application"){B={2.,-1.,5.};}if(nrhs==2){B.insert(B.end(),{1.,-2.,3.});}
migration_observer::emit("input_A",A.data(),A.size());
migration_observer::emit("input_B",B.data(),B.size());
    /* device memory */
    double *d_A = nullptr;
    double *d_tau = nullptr;
    double *d_B = nullptr;
    int *d_info = nullptr;
    double *d_work = nullptr;

    int lwork_geqrf = 0;
    int lwork_ormqr = 0;
    int lwork = 0;
    int info = 0;

    const double one = 1;

    std::printf("A = (matlab base-1)\n");
    print_matrix(m, m, A.data(), lda);
    std::printf("=====\n");
    std::printf("B = (matlab base-1)\n");
    print_matrix(m, nrhs, B.data(), ldb);
    std::printf("=====\n");

    /* step 1: create cudense/hipblas handle */
    CUSOLVER_CHECK(hipsolverDnCreate(&cusolverH));
    CUBLAS_CHECK(hipblasCreate(&cublasH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSetStream(cusolverH, stream));
    CUBLAS_CHECK(hipblasSetStream(cublasH, stream));

    /* step 2: copy A and B to device */
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_tau), sizeof(double) * m));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_B), sizeof(double) * B.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));
    CUDA_CHECK(
        hipMemcpyAsync(d_B, B.data(), sizeof(double) * B.size(), hipMemcpyHostToDevice, stream));

    /* step 3: query working space of geqrf and ormqr */
    CUSOLVER_CHECK(hipsolverDnDgeqrf_bufferSize(cusolverH, m, m, d_A, lda, &lwork_geqrf));

    CUSOLVER_CHECK(hipsolverDnDormqr_bufferSize(cusolverH, HIPBLAS_SIDE_LEFT, HIPBLAS_OP_T, m, nrhs, m,
                                               d_A, lda, d_tau, d_B, ldb, &lwork_ormqr));

    lwork = std::max(lwork_geqrf, lwork_ormqr);

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    /* step 4: compute QR factorization */
    CUSOLVER_CHECK(hipsolverDnDgeqrf(cusolverH, m, m, d_A, lda, d_tau, d_work, lwork, d_info));

    /* check if QR is good or not */
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after geqrf: info = %d\n", info);
    if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }

    /* step 5: compute Q^T*B */
    CUSOLVER_CHECK(hipsolverDnDormqr(cusolverH, HIPBLAS_SIDE_LEFT, HIPBLAS_OP_T, m, nrhs, m, d_A, lda,
                                    d_tau, d_B, ldb, d_work, lwork, d_info));

    /* check if QR is good or not */
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after ormqr: info = %d\n", info);
    if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }

std::vector<double> migration_QR(A.size()),migration_tau(m),migration_QTB(B.size());
CUDA_CHECK(hipMemcpy(migration_QR.data(),d_A,A.size()*sizeof(double),hipMemcpyDeviceToHost));
CUDA_CHECK(hipMemcpy(migration_tau.data(),d_tau,m*sizeof(double),hipMemcpyDeviceToHost));
CUDA_CHECK(hipMemcpy(migration_QTB.data(),d_B,B.size()*sizeof(double),hipMemcpyDeviceToHost));
migration_observer::emit("QR",migration_QR.data(),migration_QR.size());
migration_observer::emit("tau",migration_tau.data(),migration_tau.size());
migration_observer::emit("QTB",migration_QTB.data(),migration_QTB.size());
migration_observer::emit("info",&info,1);
    /* step 6: compute x = R \ Q^T*B */
    CUBLAS_CHECK(hipblasDtrsm(cublasH, HIPBLAS_SIDE_LEFT, HIPBLAS_FILL_MODE_UPPER, HIPBLAS_OP_N,
                             HIPBLAS_DIAG_NON_UNIT, m, nrhs, &one, d_A, lda, d_B, ldb));

    CUDA_CHECK(hipMemcpyAsync(XC.data(), d_B, sizeof(double) * XC.size(), hipMemcpyDeviceToHost,
                               stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("X = (matlab base-1)\n");
    print_matrix(m, nrhs, XC.data(), ldb);

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());

migration_observer::emit("B",B.data(),B.size());
migration_observer::emit("XC",XC.data(),XC.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_tau));
    CUDA_CHECK(hipFree(d_B));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));

    CUBLAS_CHECK(hipblasDestroy(cublasH));
    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}