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
#include <hipblaslt.h>

#include "sample_cublasLt_LtDgemmPresetAlgo.h"
#include "helpers.h"

/// Sample wrapper executing double precision gemm with a predefined algorithm using hipblasLtMatmul, nearly a drop-in
/// replacement for hipblasDgemm, with addition of the workspace to support split-K algorithms
///
/// pointer mode is always host, to change it configure the appropriate matmul descriptor attribute
/// matmul is not using hipblas handle's configuration of math mode, here tensor ops are implicitly allowed; to change
/// this configure appropriate attribute in the preference handle
///
/// NOTE: this sample may not work on all architectures or all problem sizes
void LtDgemmPresetAlgo(hipblasLtHandle_t ltHandle,
                       hipblasOperation_t transa,
                       hipblasOperation_t transb,
                       int m,
                       int n,
                       int k,
                       const double *alpha, /* host pointer */
                       const double *A,
                       int lda,
                       const double *B,
                       int ldb,
                       const double *beta, /* host pointer */
                       double *C,
                       int ldc,
                       void *workspace,
                       size_t workspaceSize,
                       hipStream_t stream) {
    hipblasLtMatmulDescOpaque_t operationDesc = {};
    hipblasLtMatrixLayoutOpaque_t Adesc = {}, Bdesc = {}, Cdesc = {};
    hipblasLtMatmulAlgo_t algo = {};

    const int32_t algoId = 10;
    const cublasLtMatmulTile_t tileId = CUBLASLT_MATMUL_TILE_16x16;                    // 5
    const cublasLtReductionScheme_t reductionMode = CUBLASLT_REDUCTION_SCHEME_INPLACE; // 1
    const int32_t splitKFactor = 256;

    // create operation desciriptor; see hipblasLtMatmulDescAttributes_t for details about defaults; here we just need to
    // set the transforms for A and B
    checkCublasStatus(cublasLtMatmulDescInit(&operationDesc, HIPBLAS_COMPUTE_64F, HIP_R_64F));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(&operationDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(&operationDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));

    // create matrix descriptors, we are good with the details here so no need to set any extra attributes
    checkCublasStatus(cublasLtMatrixLayoutInit(&Adesc, HIP_R_64F, transa == HIPBLAS_OP_N ? m : k,
                                               transa == HIPBLAS_OP_N ? k : m, lda));
    checkCublasStatus(cublasLtMatrixLayoutInit(&Bdesc, HIP_R_64F, transb == HIPBLAS_OP_N ? k : n,
                                               transb == HIPBLAS_OP_N ? n : k, ldb));
    checkCublasStatus(cublasLtMatrixLayoutInit(&Cdesc, HIP_R_64F, m, n, ldc));

    checkCublasStatus(cublasLtMatmulAlgoInit(ltHandle,           //
                                             HIPBLAS_COMPUTE_64F, // compute
                                             HIP_R_64F,         // scale
                                             HIP_R_64F,         // A
                                             HIP_R_64F,         // B
                                             HIP_R_64F,         // C
                                             HIP_R_64F,         // D
                                             algoId, &algo));

    checkCublasStatus(
        cublasLtMatmulAlgoConfigSetAttribute(&algo, CUBLASLT_ALGO_CONFIG_TILE_ID, &tileId, sizeof(tileId)));
    checkCublasStatus(cublasLtMatmulAlgoConfigSetAttribute(&algo, CUBLASLT_ALGO_CONFIG_REDUCTION_SCHEME, &reductionMode,
                                                           sizeof(reductionMode)));
    checkCublasStatus(cublasLtMatmulAlgoConfigSetAttribute(&algo, CUBLASLT_ALGO_CONFIG_SPLITK_NUM, &splitKFactor,
                                                           sizeof(splitKFactor)));

    checkCublasStatus(hipblasLtMatmul(ltHandle, &operationDesc, alpha, A, &Adesc, B, &Bdesc, beta, C, &Cdesc, C, &Cdesc,
                                     &algo, workspace, workspaceSize, stream));
}