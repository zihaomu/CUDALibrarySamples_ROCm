/*
 * SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include "helpers.h"
#include "sample_cublasLt_LtBlk128x128Fp8Matmul.h"

/// Sample wrapper executing mxfp8 matmul with hipblasLtMatmul, with addition of per-tensor scaling, and
/// the workspace to support split-K algorithms.
///
/// pointer mode is for alpha and beta is always host, to change it configure the appropriate matmul descriptor
/// attribute matmul is not using hipblas handle's configuration of math mode, here tensor ops are implicitly allowed; to
/// change this configure appropriate attribute in the preference handle
void LtBlk128x128Fp8Matmul(hipblasLtHandle_t ltHandle,
                           hipblasOperation_t transa,
                           hipblasOperation_t transb,
                           int m,
                           int n,
                           int k,
                           const float *alpha,   /* host pointer */
                           const float *a_scale, /* device pointer */
                           const __hip_fp8_e4m3_fnuz *A,
                           int lda,
                           const float *b_scale, /* device pointer */
                           const __hip_fp8_e4m3_fnuz *B,
                           int ldb,
                           const float *beta, /* host pointer */
                           __hip_bfloat16 *C,
                           int ldc,
                           __hip_bfloat16 *D,
                           int ldd,
                           void *workspace,
                           size_t workspaceSize,
                           hipblasLtMatmulMatrixScale_t AScaleMode,
                           hipblasLtMatmulMatrixScale_t BScaleMode) {
    hipblasLtMatmulDesc_t operationDesc = NULL;
    hipblasLtMatrixLayout_t Adesc = NULL, Bdesc = NULL, Cdesc = NULL, Ddesc = NULL;
    hipblasLtMatmulPreference_t preference = NULL;

    int returnedResults = 0;
    hipblasLtMatmulHeuristicResult_t heuristicResult = {};

    // create operation desciriptor; see hipblasLtMatmulDescAttributes_t for details about defaults; here we just need to
    // set the transforms for A and B
    checkCublasStatus(hipblasLtMatmulDescCreate(&operationDesc, HIPBLAS_COMPUTE_32F, HIP_R_32F));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));

    // set block scaling mode
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_A_SCALE_MODE, &AScaleMode,
                                                     sizeof(AScaleMode)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_B_SCALE_MODE, &BScaleMode,
                                                     sizeof(BScaleMode)));

    // set scaling factors
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_A_SCALE_POINTER, &a_scale, sizeof(a_scale)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_B_SCALE_POINTER, &b_scale, sizeof(b_scale)));

    // create matrix descriptors, we are good with the details here so no need to set any extra attributes
    // table of supported type combinations can be found in the documentation:
    // https://docs.nvidia.com/cuda/hipblas/index.html#cublasltmatmul
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Adesc, HIP_R_8F_E4M3, transa == HIPBLAS_OP_N ? m : k,
                                                 transa == HIPBLAS_OP_N ? k : m, lda));
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Bdesc, HIP_R_8F_E4M3, transb == HIPBLAS_OP_N ? k : n,
                                                 transb == HIPBLAS_OP_N ? n : k, ldb));
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Cdesc, HIP_R_16BF, m, n, ldc));
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Ddesc, HIP_R_16BF, m, n, ldd));

    // create preference handle; here we could use extra attributes to disable tensor ops or to make sure algo selected
    // will work with badly aligned A, B, C; here for simplicity we just assume A,B,C are always well aligned (e.g.
    // directly come from cudaMalloc)
    checkCublasStatus(hipblasLtMatmulPreferenceCreate(&preference));
    checkCublasStatus(hipblasLtMatmulPreferenceSetAttribute(preference, HIPBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,
                                                           &workspaceSize, sizeof(workspaceSize)));

    // we just need the best available heuristic to try and run matmul. There is no guarantee this will work, e.g. if A
    // is badly aligned, you can request more (e.g. 32) algos and try to run them one by one until something works
    checkCublasStatus(hipblasLtMatmulAlgoGetHeuristic(ltHandle, operationDesc, Adesc, Bdesc, Cdesc, Ddesc, preference, 1,
                                                     &heuristicResult, &returnedResults));

    if (returnedResults == 0) {
        checkCublasStatus(HIPBLAS_STATUS_NOT_SUPPORTED);
    }

    checkCublasStatus(hipblasLtMatmul(ltHandle, operationDesc, alpha, A, Adesc, B, Bdesc, beta, C, Cdesc, D, Ddesc,
                                     &heuristicResult.algo, workspace, workspaceSize, 0));

    // descriptors are no longer needed as all GPU work was already enqueued
    if (preference) checkCublasStatus(hipblasLtMatmulPreferenceDestroy(preference));
    if (Ddesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Ddesc));
    if (Cdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Cdesc));
    if (Bdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Bdesc));
    if (Adesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Adesc));
    if (operationDesc) checkCublasStatus(hipblasLtMatmulDescDestroy(operationDesc));
}