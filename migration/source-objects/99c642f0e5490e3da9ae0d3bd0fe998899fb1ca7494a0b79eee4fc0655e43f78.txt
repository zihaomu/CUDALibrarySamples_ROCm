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

#include "sample_cublasLt_LtHSHgemmPointerArrayBatchSimple.h"
#include "helpers.h"

/// Sample wrapper executing mixed precision gemm with hipblasLtMatmul, nearly a drop-in replacement for hipblasGemmEx,
/// with addition of the workspace to support split-K algorithms
///
/// pointer mode is always host, to change it configure the appropriate matmul descriptor attribute
/// matmul is not using hipblas handle's configuration of math mode, here tensor ops are implicitly allowed
void LtHSHgemmPointerArrayBatchSimple(hipblasLtHandle_t ltHandle,
                                      hipblasOperation_t transa,
                                      hipblasOperation_t transb,
                                      int m,
                                      int n,
                                      int k,
                                      const float *alpha, /* host pointer */
                                      const __half *const *A,
                                      int lda,
                                      const __half *const *B,
                                      int ldb,
                                      const float *beta, /* host pointer */
                                      const __half *const *C,
                                      int ldc,
                                      __half *const *D,
                                      int ldd,
                                      int batchCount,
                                      void *workspace,
                                      size_t workspaceSize) {

    hipblasLtMatmulDesc_t operationDesc = NULL;
    hipblasLtMatrixLayout_t Adesc = NULL, Bdesc = NULL, Cdesc = NULL, Ddesc = NULL;

    // create operation desciriptor; see hipblasLtMatmulDescAttributes_t for details about defaults; here we just need to
    // set the transforms for A and B
    checkCublasStatus(hipblasLtMatmulDescCreate(&operationDesc, HIPBLAS_COMPUTE_32F, HIP_R_32F));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));

    hipblasLtBatchMode_t batchMode = HIPBLASLT_BATCH_MODE_POINTER_ARRAY;

    // create matrix descriptors, we need to configure batch size and counts in this case
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Adesc, HIP_R_16F, transa == HIPBLAS_OP_N ? m : k,
                                                 transa == HIPBLAS_OP_N ? k : m, lda));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Adesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_COUNT, &batchCount, sizeof(batchCount)));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Adesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_MODE, &batchMode, sizeof(batchMode)));

    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Bdesc, HIP_R_16F, transb == HIPBLAS_OP_N ? k : n,
                                                 transb == HIPBLAS_OP_N ? n : k, ldb));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Bdesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_COUNT, &batchCount, sizeof(batchCount)));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Bdesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_MODE, &batchMode, sizeof(batchMode)));

    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Cdesc, HIP_R_16F, m, n, ldc));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Cdesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_COUNT, &batchCount, sizeof(batchCount)));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Cdesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_MODE, &batchMode, sizeof(batchMode)));

    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Ddesc, HIP_R_16F, m, n, ldd));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Ddesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_COUNT, &batchCount, sizeof(batchCount)));
    checkCublasStatus(
        hipblasLtMatrixLayoutSetAttribute(Ddesc, HIPBLASLT_MATRIX_LAYOUT_BATCH_MODE, &batchMode, sizeof(batchMode)));

    // in this simplified example we take advantage of hipblasLtMatmul shortcut notation with algo=NULL which will force
    // matmul to get the basic heuristic result internally. Downsides of this approach are that there is no way to
    // configure search preferences (e.g. disallow tensor operations or some reduction schemes) and no way to store the
    // algo for later use
    checkCublasStatus(hipblasLtMatmul(ltHandle, operationDesc, alpha, A, Adesc, B, Bdesc, beta, C, Cdesc, (void *)D,
                                     Ddesc, NULL, workspace, workspaceSize, 0));

    // descriptors are no longer needed as all GPU work was already enqueued
    if (Cdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Cdesc));
    if (Bdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Bdesc));
    if (Adesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Adesc));
    if (Ddesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Ddesc));
    if (operationDesc) checkCublasStatus(hipblasLtMatmulDescDestroy(operationDesc));
}