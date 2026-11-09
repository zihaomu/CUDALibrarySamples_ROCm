/*
 * SPDX-FileCopyrightText: Copyright (c) 2019 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <cstring>
#include <iostream>
#include <string>

#include <hip/hip_runtime.h>
#include <hipsolver.h>

#include "cusolver_utils.h"

int main(int argc, const char *argv[]) {
    bool verbose = false;

    // Matrix size
    const int N = 1024;

    // Numer of right hand sides
    const int nrhs = 1;

    // Use double precision matrix and half precision factorization
    typedef double T;
    const hipDataType matrix_precision = HIP_R_64F;
    // make sure that you specify matrix precision that matches to the data type
    assert(traits<T>::cuda_data_type == matrix_precision);
    const hipDataType compute_lower_precision = HIP_R_16F;

    // Use GMRES refinement solver
    const cusolverIRSRefinement_t refinement_solver = CUSOLVER_IRS_REFINE_GMRES;

    T *hA;
    int lda;
    T *hB;
    int ldb;
    T *hX;
    int ldx;

    hipStream_t stream;
    hipEvent_t event_start, event_end;
    hipsolverHandle_t handle;
    cusolverDnIRSParams_t gesv_params;
    cusolverDnIRSInfos_t gesv_info;

    std::cout << "Generating matrix A on host..." << std::endl;
    generate_random_matrix<T>(N, N, &hA, &lda);
    std::cout << "make A diagonal dominant..." << std::endl;
    make_diag_dominant_matrix<T>(N, N, hA, lda);
    std::cout << "Generating matrix B on host..." << std::endl;
    generate_random_matrix<T>(N, nrhs, &hB, &ldb);
    std::cout << "Generating matrix X on host..." << std::endl;
    generate_random_matrix<T>(N, nrhs, &hX, &ldx);

    if (verbose) {
        std::cout << "A: \n";
        print_matrix(N, N, hA, lda);
        std::cout << "B: \n";
        print_matrix(nrhs, N, hB, ldb);
        std::cout << "X: \n";
        print_matrix(nrhs, N, hX, ldx);
    }

    std::cout << "Initializing CUDA..." << std::endl;
    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUDA_CHECK(hipEventCreate(&event_start));
    CUDA_CHECK(hipEventCreate(&event_end));
    CUSOLVER_CHECK(hipsolverDnCreate(&handle));
    CUSOLVER_CHECK(hipsolverSetStream(handle, stream));

    std::cout << "Setting up gesv() parameters..." << std::endl;
    // create solver parameters
    CUSOLVER_CHECK(cusolverDnIRSParamsCreate(&gesv_params));
    // set matrix precision and factorization precision
    CUSOLVER_CHECK(cusolverDnIRSParamsSetSolverPrecisions(gesv_params, matrix_precision,
                                                          compute_lower_precision));
    // set refinement solver
    CUSOLVER_CHECK(cusolverDnIRSParamsSetRefinementSolver(gesv_params, refinement_solver));
    // create solve info structure
    CUSOLVER_CHECK(cusolverDnIRSInfosCreate(gesv_params, &gesv_info));

    // matrix on device
    T *dA;
    int ldda = ALIGN_TO(N * sizeof(T), device_alignment) / sizeof(T);
    // right hand side on device
    T *dB;
    int lddb = ALIGN_TO(N * sizeof(T), device_alignment) / sizeof(T);
    // solution on device
    T *dX;
    int lddx = ALIGN_TO(N * sizeof(T), device_alignment) / sizeof(T);

    // pivot sequence on device
    int *dipiv;
    // info indicator on device
    int *dinfo;
    // work buffer
    void *dwork;
    // size of work buffer
    size_t dwork_size;
    // number of refinement iterations returned by solver
    int iter;

    std::cout << "Allocating memory on device..." << std::endl;
    // allocate data
    CUDA_CHECK(hipMalloc(&dA, ldda * N * sizeof(T)));
    CUDA_CHECK(hipMalloc(&dB, lddb * nrhs * sizeof(T)));
    CUDA_CHECK(hipMalloc(&dX, lddx * nrhs * sizeof(T)));
    CUDA_CHECK(hipMalloc(&dipiv, N * sizeof(int)));
    CUDA_CHECK(hipMalloc(&dinfo, sizeof(int)));

    // copy input data
    CUDA_CHECK(hipMemcpy2D(dA, ldda * sizeof(T), hA, lda * sizeof(T), N * sizeof(T), N,
                            hipMemcpyDefault));
    CUDA_CHECK(hipMemcpy2D(dB, lddb * sizeof(T), hB, ldb * sizeof(T), N * sizeof(T), nrhs,
                            hipMemcpyDefault));

    // get required device work buffer size
    CUSOLVER_CHECK(cusolverDnIRSXgesv_bufferSize(handle, gesv_params, N, nrhs, &dwork_size));
    std::cout << "Workspace is " << dwork_size << " bytes" << std::endl;
    CUDA_CHECK(hipMalloc(&dwork, dwork_size));

    std::cout << "Solving matrix on device..." << std::endl;
    CUDA_CHECK(hipEventRecord(event_start, stream));

    hipsolverStatus_t gesv_status =
        cusolverDnIRSXgesv(handle, gesv_params, gesv_info, traits<T>::cuda_data_type, N, nrhs, dA,
                           ldda, dipiv, dB, lddb, dX, lddx, dwork, dwork_size, &iter, dinfo);
    CUSOLVER_CHECK(gesv_status);

    CUDA_CHECK(hipEventRecord(event_end, stream));
    // check solve status
    int info = 0;
    CUDA_CHECK(
        hipMemcpyAsync(&info, dinfo, sizeof(int), hipMemcpyDeviceToHost, stream));
    CUDA_CHECK(hipStreamSynchronize(stream));

    std::cout << "Solve info is: " << info << ", iter is: " << iter << std::endl;

    CUDA_CHECK(hipMemcpy2D(hX, ldx * sizeof(T), dX, lddx * sizeof(T), N * sizeof(T), nrhs,
                            hipMemcpyDefault));
    if (verbose) {
        std::cout << "X:\n";
        print_matrix(nrhs, N, hX, ldx);
    }

    CUDA_CHECK(hipGetLastError());

    float solve_time = 0.f;
    CUDA_CHECK(hipEventElapsedTime(&solve_time, event_start, event_end));
    std::cout << "Solved matrix " << N << "x" << N << " with " << nrhs << " right hand sides in "
              << solve_time << "ms" << std::endl;

    std::cout << "Releasing resources..." << std::endl;
    CUDA_CHECK(hipFree(dwork));
    CUDA_CHECK(hipFree(dinfo));
    CUDA_CHECK(hipFree(dipiv));
    CUDA_CHECK(hipFree(dX));
    CUDA_CHECK(hipFree(dB));
    CUDA_CHECK(hipFree(dA));

    free(hA);
    free(hB);
    free(hX);

    CUSOLVER_CHECK(hipsolverDnDestroy(handle));
    CUDA_CHECK(hipEventDestroy(event_start));
    CUDA_CHECK(hipEventDestroy(event_end));
    CUDA_CHECK(hipStreamDestroy(stream));

    std::cout << "Done!" << std::endl;

    return 0;
}