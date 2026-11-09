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
#include <hipsparse.h>

#include "cusolver_utils.h"

int main(int argc, char *argv[]) {
    hipsolverSpHandle_t cusolverH = NULL;
    csrqrInfo_t info = NULL;
    hipsparseMatDescr_t descrA = NULL;
    hipStream_t stream = NULL;

    // GPU does batch QR
    // d_A is CSR format, d_csrValA is of size nnzA*batchSize
    // d_x is a matrix of size batchSize * m
    // d_b is a matrix of size batchSize * m
    int *d_csrRowPtrA = nullptr;
    int *d_csrColIndA = nullptr;
    double *d_csrValA = nullptr;
    double *d_b = nullptr; // batchSize * m
    double *d_x = nullptr; // batchSize * m

    size_t size_qr = 0;
    size_t size_internal = 0;
    void *buffer_qr = nullptr; // working space for numerical factorization

    /*
     *      | 1                |
     *  A = |       2          |
     *      |            3     |
     *      | 0.1  0.1  0.1  4 |
     *  CSR of A is based-1
     *
     *  b = [1 1 1 1]
     */

    const int m = 4;
    const int nnzA = 7;
    const std::vector<int> csrRowPtrA = {1, 2, 3, 4, 8};
    const std::vector<int> csrColIndA = {1, 2, 3, 1, 2, 3, 4};
    const std::vector<double> csrValA = {1.0, 2.0, 3.0, 0.1, 0.1, 0.1, 4.0};
    const std::vector<double> b = {1.0, 1.0, 1.0, 1.0};
    const int batchSize = 17;

    std::vector<double> csrValABatch(nnzA * batchSize);
    std::vector<double> bBatch(m * batchSize);
    std::vector<double> xBatch(m * batchSize);

    // step 1: prepare Aj and bj on host
    //  Aj is a small perturbation of A
    //  bj is a small perturbation of b
    //  csrValABatch = [A0, A1, A2, ...]
    //  bBatch = [b0, b1, b2, ...]
    for (int colidx = 0; colidx < nnzA; colidx++) {
        double Areg = csrValA[colidx];
        for (int batchId = 0; batchId < batchSize; batchId++) {
            double eps = (static_cast<double>((std::rand() % 100) + 1)) * 1.e-4;
            csrValABatch[batchId * nnzA + colidx] = Areg + eps;
        }
    }

    for (int j = 0; j < m; j++) {
        double breg = b[j];
        for (int batchId = 0; batchId < batchSize; batchId++) {
            double eps = (static_cast<double>((std::rand() % 100) + 1)) * 1.e-4;
            bBatch[batchId * m + j] = breg + eps;
        }
    }

    // step 2: create hipsolver handle, qr info and matrix descriptor
    CUSOLVER_CHECK(hipsolverSpCreate(&cusolverH));

    CUDA_CHECK(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUSOLVER_CHECK(hipsolverSpSetStream(cusolverH, stream));

    CUSPARSE_CHECK(hipsparseCreateMatDescr(&descrA));

    CUSPARSE_CHECK(hipsparseSetMatType(descrA, HIPSPARSE_MATRIX_TYPE_GENERAL));
    CUSPARSE_CHECK(hipsparseSetMatIndexBase(descrA, HIPSPARSE_INDEX_BASE_ONE)); // base-1

    CUSOLVER_CHECK(cusolverSpCreateCsrqrInfo(&info));

    // step 3: copy Aj and bj to device
    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_csrValA), sizeof(double) * csrValABatch.size()));
    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_csrColIndA), sizeof(int) * csrColIndA.size()));
    CUDA_CHECK(
        hipMalloc(reinterpret_cast<void **>(&d_csrRowPtrA), sizeof(int) * csrRowPtrA.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_b), sizeof(double) * bBatch.size()));
    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&d_x), sizeof(double) * xBatch.size()));

    CUDA_CHECK(hipMemcpyAsync(d_csrColIndA, csrColIndA.data(), sizeof(int) * csrColIndA.size(),
                               hipMemcpyHostToDevice, stream));
    CUDA_CHECK(hipMemcpyAsync(d_csrRowPtrA, csrRowPtrA.data(), sizeof(int) * csrRowPtrA.size(),
                               hipMemcpyHostToDevice, stream));

    // step 4: symbolic analysis
    CUSOLVER_CHECK(cusolverSpXcsrqrAnalysisBatched(cusolverH, m, m, nnzA, descrA, d_csrRowPtrA,
                                                   d_csrColIndA, info));

    CUDA_CHECK(hipStreamSynchronize(stream));

    // step 5: find "proper" batchSize
    // get available device memory
    size_t free_mem = 0;
    size_t total_mem = 0;
    CUDA_CHECK(hipMemGetInfo(&free_mem, &total_mem));

    int batchSizeMax = 2;
    while (batchSizeMax < batchSize) {
        std::printf("batchSizeMax = %d\n", batchSizeMax);
        CUSOLVER_CHECK(cusolverSpDcsrqrBufferInfoBatched(cusolverH, m, m, nnzA,
                                                         // d_csrValA is don't care
                                                         descrA, d_csrValA, d_csrRowPtrA,
                                                         d_csrColIndA,
                                                         batchSizeMax, // WARNING: use batchSizeMax
                                                         info, &size_internal, &size_qr));
        CUDA_CHECK(hipStreamSynchronize(stream));

        if ((size_internal + size_qr) > free_mem) {
            // current batchSizeMax exceeds hardware limit, so cut it by half.
            batchSizeMax /= 2;
            break;
        }
        batchSizeMax *= 2; // double batchSizMax and try it again.
    }
    // correct batchSizeMax such that it is not greater than batchSize.
    batchSizeMax = std::min(batchSizeMax, batchSize);
    std::printf("batchSizeMax = %d\n", batchSizeMax);

    // Assume device memory is not big enough, and batchSizeMax = 2
    batchSizeMax = 2;

    // step 6: prepare working space
    // [necessary]
    // Need to call cusolverDcsrqrBufferInfoBatched again with batchSizeMax
    // to fix batchSize used in numerical factorization.
    CUSOLVER_CHECK(cusolverSpDcsrqrBufferInfoBatched(cusolverH, m, m, nnzA,
                                                     // d_csrValA is don't care
                                                     descrA, d_csrValA, d_csrRowPtrA, d_csrColIndA,
                                                     batchSizeMax, // WARNING: use batchSizeMax
                                                     info, &size_internal, &size_qr));
    CUDA_CHECK(hipStreamSynchronize(stream));

    std::printf("numerical factorization needs internal data %lld bytes\n",
           static_cast<long long>(size_internal));
    std::printf("numerical factorization needs working space %lld bytes\n",
           static_cast<long long>(size_qr));

    CUDA_CHECK(hipMalloc(reinterpret_cast<void **>(&buffer_qr), size_qr));

    // step 7: solve Aj*xj = bj
    for (int idx = 0; idx < batchSize; idx += batchSizeMax) {
        // current batchSize 'cur_batchSize' is the batchSize used in numerical
        // factorization
        const int cur_batchSize = std::min(batchSizeMax, batchSize - idx);
        std::printf("current batchSize = %d\n", cur_batchSize);
        // copy part of Aj and bj to device
        CUDA_CHECK(hipMemcpyAsync(d_csrValA, csrValABatch.data() + idx * nnzA,
                                   sizeof(double) * nnzA * cur_batchSize, hipMemcpyHostToDevice,
                                   stream));
        CUDA_CHECK(hipMemcpyAsync(d_b, bBatch.data() + idx * m, sizeof(double) * m * cur_batchSize,
                                   hipMemcpyHostToDevice, stream));
        // solve part of Aj*xj = bj
        CUSOLVER_CHECK(cusolverSpDcsrqrsvBatched(cusolverH, m, m, nnzA, descrA, d_csrValA,
                                                 d_csrRowPtrA, d_csrColIndA, d_b, d_x,
                                                 cur_batchSize, // WARNING: use current batchSize
                                                 info, buffer_qr));
        // copy part of xj back to host
        CUDA_CHECK(hipMemcpyAsync(xBatch.data() + idx * m, d_x, sizeof(double) * m * cur_batchSize,
                                   hipMemcpyDeviceToHost, stream));
    }

    CUDA_CHECK(hipStreamSynchronize(stream));

    // step 8: check residual
    // xBatch = [x0, x1, x2, ...]
    const int baseA = (HIPSPARSE_INDEX_BASE_ONE == hipsparseGetMatIndexBase(descrA)) ? 1 : 0;

    for (int batchId = 0; batchId < batchSize; batchId++) {
        // measure |bj - Aj*xj|
        double *csrValAj = csrValABatch.data() + batchId * nnzA;
        double *xj = xBatch.data() + batchId * m;
        double *bj = bBatch.data() + batchId * m;
        // sup| bj - Aj*xj|
        double sup_res = 0;
        for (int row = 0; row < m; row++) {
            const int start = csrRowPtrA[row] - baseA;
            const int end = csrRowPtrA[row + 1] - baseA;
            double Ax = 0.0; // Aj(row,:)*xj
            for (int colidx = start; colidx < end; colidx++) {
                const int col = csrColIndA[colidx] - baseA;
                const double Areg = csrValAj[colidx];
                const double xreg = xj[col];
                Ax = Ax + Areg * xreg;
            }
            double r = bj[row] - Ax;
            sup_res = (sup_res > fabs(r)) ? sup_res : fabs(r);
        }
        std::printf("batchId %d: sup|bj - Aj*xj| = %E \n", batchId, sup_res);
    }

    for (int batchId = 0; batchId < batchSize; batchId++) {
        double *xj = xBatch.data() + batchId * m;
        for (int row = 0; row < m; row++) {
            std::printf("x%d[%d] = %E\n", batchId, row, xj[row]);
        }
        std::printf("\n");
    }

    
// MIGRATION_OBSERVE_ORIGINAL: host buffers after GPU synchronization.
migration_observer::emit("csrRowPtrA",csrRowPtrA.data(),csrRowPtrA.size());
migration_observer::emit("csrColIndA",csrColIndA.data(),csrColIndA.size());
migration_observer::emit("csrValA",csrValA.data(),csrValA.size());
migration_observer::emit("b",b.data(),b.size());
migration_observer::emit("csrValABatch",csrValABatch.data(),csrValABatch.size());
migration_observer::emit("bBatch",bBatch.data(),bBatch.size());
migration_observer::emit("xBatch",xBatch.data(),xBatch.size());
/* free resources */
    CUDA_CHECK(hipFree(d_csrRowPtrA));
    CUDA_CHECK(hipFree(d_csrColIndA));
    CUDA_CHECK(hipFree(d_csrValA));
    CUDA_CHECK(hipFree(d_b));
    CUDA_CHECK(hipFree(d_x));
    CUDA_CHECK(hipFree(buffer_qr));

    CUSOLVER_CHECK(hipsolverSpDestroy(cusolverH));

    CUDA_CHECK(hipStreamDestroy(stream));

    CUDA_CHECK(hipDeviceReset());

    return EXIT_SUCCESS;
}