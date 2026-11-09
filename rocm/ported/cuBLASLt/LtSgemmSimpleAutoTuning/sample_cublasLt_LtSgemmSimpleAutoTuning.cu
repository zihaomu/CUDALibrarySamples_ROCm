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

#include "hip/hip_runtime.h"
#include <cstdio>
#include <vector>
#include <algorithm>

#include <hipblaslt.h>
#include <hip/hip_runtime_api.h>

#include "sample_cublasLt_LtSgemmSimpleAutoTuning.h"
#include "helpers.h"

float median(std::vector<float> &times) {
    const size_t size = times.size();
    if (size == 0) {
        return 0;
    }

    std::sort(times.begin(), times.end());

    const size_t mid = size / 2;
    if (size % 2 == 0) {
        return (times[mid] + times[mid - 1]) / 2;
    } else {
        return times[mid];
    }
}

/// Sample wrapper executing single precision gemm algorithm auto tuning by querying cublasLt heuristics for best
/// algorithms, iterate over the results and pick the algorithm that have the best performance for the given problem
///
/// pointer mode is always host, to change it configure the appropriate matmul descriptor attribute
/// matmul is not using hipblas handle's configuration of math mode, here tensor ops are implicitly allowed; to change
/// this configure appropriate attribute in the preference handle
void LtSgemmSimpleAutoTuning(hipblasLtHandle_t ltHandle,
                             hipblasOperation_t transa,
                             hipblasOperation_t transb,
                             int m,
                             int n,
                             int k,
                             const float *alpha, /* host pointer */
                             const float *A,
                             int lda,
                             const float *B,
                             int ldb,
                             const float *beta, /* host pointer */
                             float *C,
                             int ldc,
                             void *workspace,
                             size_t workspaceSize,
                             hipblasLtMatmulAlgo_t &algo) {
    hipblasLtMatmulDesc_t operationDesc = NULL;
    hipblasLtMatrixLayout_t Adesc = NULL, Bdesc = NULL, Cdesc = NULL;
    hipblasLtMatmulPreference_t preference = NULL;

    const int requestedAlgoCount = 8;
    int returnedResults = 0;
    hipblasLtMatmulHeuristicResult_t heuristicResult[requestedAlgoCount] = {0};
    int bestAlgoIdx = 0;
    float time = 0;
    float bestAlgoTime = 0;
    hipStream_t stream;
    hipEvent_t startEvent, stopEvent;

    // create operation desciriptor; see hipblasLtMatmulDescAttributes_t for details about defaults; here we just need to
    // set the transforms for A and B
    checkCublasStatus(hipblasLtMatmulDescCreate(&operationDesc, HIPBLAS_COMPUTE_32F, HIP_R_32F));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));

    // create matrix descriptors, we are good with the details here so no need to set any extra attributes
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Adesc, HIP_R_32F, transa == HIPBLAS_OP_N ? m : k,
                                                 transa == HIPBLAS_OP_N ? k : m, lda));
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Bdesc, HIP_R_32F, transb == HIPBLAS_OP_N ? k : n,
                                                 transb == HIPBLAS_OP_N ? n : k, ldb));
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Cdesc, HIP_R_32F, m, n, ldc));

    // create preference handle; here we could use extra attributes to disable tensor ops or to make sure algo selected
    // will work with badly aligned A, B, C; here for simplicity we just assume A,B,C are always well aligned (e.g.
    // directly come from cudaMalloc)
    checkCublasStatus(hipblasLtMatmulPreferenceCreate(&preference));
    checkCublasStatus(hipblasLtMatmulPreferenceSetAttribute(preference, HIPBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,
                                                           &workspaceSize, sizeof(workspaceSize)));

    // we just need the best available heuristic to try and run matmul. There is no guarantee this will work, e.g. if A
    // is badly aligned, you can request more (e.g. 32) algos and try to run them one by one until something works
    checkCublasStatus(hipblasLtMatmulAlgoGetHeuristic(ltHandle, operationDesc, Adesc, Bdesc, Cdesc, Cdesc, preference,
                                                     requestedAlgoCount, heuristicResult, &returnedResults));

    if (returnedResults == 0) {
        checkCublasStatus(HIPBLAS_STATUS_NOT_SUPPORTED);
    }

    checkCudaStatus(hipStreamCreate(&stream));
    checkCudaStatus(hipEventCreate(&startEvent));
    checkCudaStatus(hipEventCreate(&stopEvent));

    constexpr int repeatAlgoCheck = 5;
    std::vector<float> algoTimes(repeatAlgoCheck);

    for (int algoIdx = 0; algoIdx < returnedResults; algoIdx++) {
        for (int checkIdx = 0; checkIdx < repeatAlgoCheck; checkIdx++) {
            checkCudaStatus(hipEventRecord(startEvent, stream));

            checkCublasStatus(hipblasLtMatmul(ltHandle, operationDesc, alpha, A, Adesc, B, Bdesc, beta, C, Cdesc, C,
                                             Cdesc, &heuristicResult[algoIdx].algo, workspace, workspaceSize, stream));

            checkCudaStatus(hipEventRecord(stopEvent, stream));
            checkCudaStatus(hipEventSynchronize(stopEvent));
            checkCudaStatus(hipEventElapsedTime(&time, startEvent, stopEvent));
            algoTimes[checkIdx] = time;
        }

        time = median(algoTimes);

        if (algoIdx == 0 || time < bestAlgoTime) {
            bestAlgoTime = time;
            bestAlgoIdx = algoIdx;
        }
    }

    memcpy(&algo, &heuristicResult[bestAlgoIdx].algo, sizeof(algo));

    // descriptors are no longer needed as all GPU work was already enqueued
    if (preference) checkCublasStatus(hipblasLtMatmulPreferenceDestroy(preference));
    if (Cdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Cdesc));
    if (Bdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Bdesc));
    if (Adesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Adesc));
    if (operationDesc) hipblasLtMatmulDescDestroy(operationDesc);
    if (stream) checkCudaStatus(hipStreamDestroy(stream));
    if (startEvent) checkCudaStatus(hipEventDestroy(startEvent));
    if (stopEvent) checkCudaStatus(hipEventDestroy(stopEvent));
}