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


#include <cassert>
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

    double vl = 0.0;
    double vu = 0.0;
    int il = 1;
    int iu = 2;
    int h_meig = 0;

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

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_A), sizeof(double) * A.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_B), sizeof(double) * B.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_W), sizeof(double) * W.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_info), sizeof(int)));

    CUDA_CHECK(
        hipMemcpyAsync(d_A, A.data(), sizeof(double) * A.size(), hipMemcpyHostToDevice, stream));
    CUDA_CHECK(
        hipMemcpyAsync(d_B, B.data(), sizeof(double) * B.size(), hipMemcpyHostToDevice, stream));

    // step 3: query working space of sygvd
    hipsolverEigType_t itype = HIPSOLVER_EIG_TYPE_1;     // A*x = (lambda)*B*x
    hipsolverEigMode_t jobz = HIPSOLVER_EIG_MODE_VECTOR; // compute eigenvalues and eigenvectors.
    hipsolverEigRange_t range = HIPSOLVER_EIG_RANGE_I;
if(migration_case=="value-range"){range=HIPSOLVER_EIG_RANGE_V;vl=0.2;vu=0.7;}
if(migration_case=="all-range")range=HIPSOLVER_EIG_RANGE_ALL;
if(migration_case=="empty-range"){range=HIPSOLVER_EIG_RANGE_V;vl=10.;vu=11.;}
   // eigenvalues/eigenvectors in the half-open
                                                       // interval (vl,vu] will be found
    hipblasFillMode_t uplo = HIPBLAS_FILL_MODE_LOWER;

    /*
    hipsolverStatus_t
    hipsolverDnDsygvd_bufferSize(
        hipsolverDnHandle_t handle,
        hipsolverEigType_t itype,
        hipsolverEigMode_t jobz,
        hipblasFillMode_t uplo,
        int n,
        const double *A,
        int lda,
        const double *B,
        int ldb,
        const double *W,
        int *lwork);
    */
    /*
    hipsolverStatus_t
    hipsolverDnDsygvdx_bufferSize(
        hipsolverDnHandle_t handle,
        hipsolverEigType_t itype,
        hipsolverEigMode_t jobz,
        hipsolverEigRange_t range, <- new
        hipblasFillMode_t uplo,
        int n,
        const double *A,
        int lda,
        const double *B,
        int ldb,
        double vl, <- new
        double vu, <- new
        int il, <- new
        int iu, <- new
        int *h_meig, <- new
        const double *W,
        int *lwork);
    */

    CUSOLVER_CHECK(hipsolverDnDsygvdx_bufferSize(cusolverH, itype, jobz, range, uplo, m, d_A, lda,
                                               d_B, lda, vl, vu, il, iu, &h_meig, d_W, &lwork));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_work), sizeof(double) * lwork));

    // step 4: compute spectrum of (A,B)
    CUSOLVER_CHECK(hipsolverDnDsygvdx(cusolverH, itype, jobz, range, uplo, m, d_A, lda, d_B, lda, vl,
                                    vu, il, iu, &h_meig, d_W, d_work, lwork, d_info));

    CUDA_CHECK(
        hipMemcpyAsync(V.data(), d_A, sizeof(double) * A.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(
        hipMemcpyAsync(W.data(), d_W, sizeof(double) * W.size(), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipMemcpyAsync(&info, d_info, sizeof(int), hipMemcpyDeviceToHost, stream));

    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("after sygvd: info = %d\n", info);
    if (0 > info) {
        std::printf("%d-th parameter is wrong \n", -info);
        exit(1);
    }

    std::printf("Eigenvalues found = %d\n",h_meig);
    for(int i=0;i<h_meig;++i)std::printf("W[%d] = %.17g\n",i,W[i]);
    print_matrix(m,h_meig,V.data(),lda);
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("A",A.data(),A.size());
migration_observer::emit("B",B.data(),B.size());
migration_observer::emit("lambda",lambda.data(),lambda.size());
migration_observer::emit("V",V.data(),m*h_meig);
migration_observer::emit("W",W.data(),h_meig);
migration_observer::emit("info",&info,1);
migration_observer::emit("meig",&h_meig,1);
migration_observer::emit("input_il",&il,1);
migration_observer::emit("input_iu",&iu,1);
migration_observer::emit("input_vl",&vl,1);
migration_observer::emit("input_vu",&vu,1);
migration_observer::emit("input_A",A.data(),A.size());
migration_observer::emit("input_B",B.data(),B.size());
/* free resources */
    CUDA_CHECK(hipFree(d_A));
    CUDA_CHECK(hipFree(d_B));
    CUDA_CHECK(hipFree(d_W));
    CUDA_CHECK(hipFree(d_info));
    CUDA_CHECK(hipFree(d_work));

    CUSOLVER_CHECK(hipsolverDnDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}