/*
 * SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <hipblaslt.h>

#include "sample_cublasLt_LtSgemmGreenCtx.h"
#include "helpers.h"

void LtSgemmGCtx(hipblasLtHandle_t ltHandle,
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
                 unsigned int minGreenContextSmCount,
                 hipStream_t primaryContextStream) {

    cudaExecutionContext_t greenCtx = 0;
    hipStream_t stream = 0;
    {
        int device = 0;
        cudaDevResource input;
        cudaDevResource smPartition;
        unsigned int nbGroups = 1;
        cudaDevResourceDesc_t smPartitionDesc;
        checkCudaStatus(cudaDeviceGetDevResource(device, &input, cudaDevResourceTypeSm));
        checkCudaStatus(
            cudaDevSmResourceSplitByCount(&smPartition, &nbGroups, &input, NULL, 0, minGreenContextSmCount));
        checkCudaStatus(cudaDevResourceGenerateDesc(&smPartitionDesc, &smPartition, 1));
        checkCudaStatus(cudaGreenCtxCreate(&greenCtx, smPartitionDesc, device, 0));
        checkCudaStatus(cudaExecutionCtxStreamCreate(&stream, greenCtx, 0, 0));
        // Note: streams created on the green context are non-blocking and need explicit synchronization.
        hipEvent_t ev;
        checkCudaStatus(hipEventCreate(&ev));
        checkCudaStatus(hipEventRecord(ev, primaryContextStream));
        checkCudaStatus(hipStreamWaitEvent(stream, ev, 0));
        checkCudaStatus(hipEventDestroy(ev));
    }

    hipblasLtMatmulDesc_t operationDesc = NULL;
    hipblasLtMatrixLayout_t Adesc = NULL, Bdesc = NULL, Cdesc = NULL;
    hipblasLtMatmulPreference_t preference = NULL;

    int returnedResults = 0;
    hipblasLtMatmulHeuristicResult_t heuristicResult = {};

    // create operation descriptor; see hipblasLtMatmulDescAttributes_t for details about defaults; here we just need to
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

    // we just need the best available heuristic to try and run matmul with the green context resources in mind passed
    // via the stream.
    checkCublasStatus(cublasLtMatmulAlgoGetHeuristicForStream(ltHandle, operationDesc, Adesc, Bdesc, Cdesc, Cdesc,
                                                              preference, 1, &heuristicResult, &returnedResults,
                                                              stream));

    if (returnedResults == 0) {
        checkCublasStatus(HIPBLAS_STATUS_NOT_SUPPORTED);
    }

    checkCublasStatus(hipblasLtMatmul(ltHandle, operationDesc, alpha, A, Adesc, B, Bdesc, beta, C, Cdesc, C, Cdesc,
                                     &heuristicResult.algo, workspace, workspaceSize, stream));

    checkCudaStatus(hipStreamSynchronize(stream));
    // descriptors are no longer needed as all GPU work was already enqueued
    if (preference) checkCublasStatus(hipblasLtMatmulPreferenceDestroy(preference));
    if (Cdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Cdesc));
    if (Bdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Bdesc));
    if (Adesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Adesc));
    if (operationDesc) checkCublasStatus(hipblasLtMatmulDescDestroy(operationDesc));
    if (stream) checkCudaStatus(hipStreamDestroy(stream));
    if (greenCtx) checkCudaStatus(cudaExecutionCtxDestroy(greenCtx));
}
