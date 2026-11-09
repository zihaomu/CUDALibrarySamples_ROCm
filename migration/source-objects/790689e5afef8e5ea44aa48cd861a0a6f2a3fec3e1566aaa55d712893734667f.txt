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

#include "sample_cublasLt_LtHSHgemmGroupedSimple.h"
#include "helpers.h"

/// (!) EXPERIMENTAL: This sample implements an experimental grouped gemm
/// feature and may be changed or removed in the future. Refer to the
/// documentation for more details and limitations.
///
/// Sample wrapper executing a grouped mixed precision gemm with hipblasLtMatmul
///
/// pointer mode is always device, to change it configure the appropriate matmul
/// descriptor attribute matmul is not using hipblas handle's configuration of
/// math mode, here tensor ops are implicitly allowed
///
void LtHSHgemmGroupedSimple(hipblasLtHandle_t ltHandle,
                            hipblasOperation_t transa,
                            hipblasOperation_t transb,
                            const void *mArrayDev,
                            int64_t avgM,
                            const void *nArrayDev,
                            int64_t avgN,
                            const void *kArrayDev,
                            int64_t avgK,
                            const float *const *alphaArrayDev,
                            const __half *const *A,
                            const void *ldaArrayDev,
                            const __half *const *B,
                            const void *ldbArrayDev,
                            const float *const *betaArrayDev,
                            const __half *const *C,
                            const void *ldcArrayDev,
                            __half *const *D,
                            const void *lddArrayDev,
                            const void *biasPtr,
                            int batchCount,
                            void *workspace,
                            size_t workspaceSize) {
    hipblasLtMatmulDesc_t operationDesc = NULL;
    hipblasLtMatrixLayout_t Adesc = NULL, Bdesc = NULL, Cdesc = NULL, Ddesc = NULL;
    hipblasLtPointerMode_t pointerMode = HIPBLASLT_POINTER_MODE_DEVICE;
    int64_t alphaBatchStride = 1;
    int64_t betaBatchStride = 1;
    // create operation desciriptor; see hipblasLtMatmulDescAttributes_t for
    // details about defaults; here we need to set the transforms for A and B
    // and pointer mode and alpha/beta batch stride
    checkCublasStatus(hipblasLtMatmulDescCreate(&operationDesc, HIPBLAS_COMPUTE_32F, HIP_R_32F));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_POINTER_MODE, &pointerMode,
                                                     sizeof(pointerMode)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, CUBLASLT_MATMUL_DESC_ALPHA_BATCH_STRIDE,
                                                     &alphaBatchStride, sizeof(alphaBatchStride)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, CUBLASLT_MATMUL_DESC_BETA_BATCH_STRIDE,
                                                     &betaBatchStride, sizeof(betaBatchStride)));

    // create matrix descriptors
    checkCublasStatus(cublasLtGroupedMatrixLayoutCreate(&Adesc, HIP_R_16F, batchCount,
                                                        transa == HIPBLAS_OP_N ? mArrayDev : kArrayDev,
                                                        transa == HIPBLAS_OP_N ? kArrayDev : mArrayDev, ldaArrayDev));
    checkCublasStatus(cublasLtGroupedMatrixLayoutCreate(&Bdesc, HIP_R_16F, batchCount,
                                                        transb == HIPBLAS_OP_N ? kArrayDev : nArrayDev,
                                                        transb == HIPBLAS_OP_N ? nArrayDev : kArrayDev, ldbArrayDev));
    checkCublasStatus(
        cublasLtGroupedMatrixLayoutCreate(&Cdesc, HIP_R_16F, batchCount, mArrayDev, nArrayDev, ldcArrayDev));
    checkCublasStatus(
        cublasLtGroupedMatrixLayoutCreate(&Ddesc, HIP_R_16F, batchCount, mArrayDev, nArrayDev, lddArrayDev));

    // Bias epilogue
    // Bias must be separate for each group, broadcast across all groups is not supported, hence the batch stride is 1
    int64_t biasBatchStride = 1;
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_BIAS_POINTER, &biasPtr, sizeof(biasPtr)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_BIAS_BATCH_STRIDE,
                                                     &biasBatchStride, sizeof(biasBatchStride)));
    hipblasLtEpilogue_t epilogue = HIPBLASLT_EPILOGUE_BIAS;
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_EPILOGUE, &epilogue, sizeof(epilogue)));

    // Since M, N, K are located on the device, it is highly recommended to
    // provide average values for them to improve the heuristics result. Without
    // this, the functionality will still work, but the heuristics result may
    // not be optimal.
    hipblasLtMatmulPreference_t preference = NULL;
    checkCublasStatus(hipblasLtMatmulPreferenceCreate(&preference));
    checkCublasStatus(hipblasLtMatmulPreferenceSetAttribute(preference, CUBLASLT_MATMUL_PREF_GROUPED_DESC_D_AVERAGE_ROWS,
                                                           &avgM, sizeof(avgM)));
    checkCublasStatus(hipblasLtMatmulPreferenceSetAttribute(preference, CUBLASLT_MATMUL_PREF_GROUPED_DESC_D_AVERAGE_COLS,
                                                           &avgN, sizeof(avgN)));
    checkCublasStatus(hipblasLtMatmulPreferenceSetAttribute(
        preference, CUBLASLT_MATMUL_PREF_GROUPED_AVERAGE_REDUCTION_DIM, &avgK, sizeof(avgK)));
    checkCublasStatus(hipblasLtMatmulPreferenceSetAttribute(preference, HIPBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,
                                                           &workspaceSize, sizeof(workspaceSize)));
    int returnedResults = 0;
    hipblasLtMatmulHeuristicResult_t heuristicResult = {};
    checkCublasStatus(hipblasLtMatmulAlgoGetHeuristic(ltHandle, operationDesc, Adesc, Bdesc, Cdesc, Ddesc, preference, 1,
                                                     &heuristicResult, &returnedResults));

    if (returnedResults == 0) {
        checkCublasStatus(HIPBLAS_STATUS_NOT_SUPPORTED);
    }

    // in this simplified example we take advantage of hipblasLtMatmul shortcut
    // notation with algo=NULL which will force matmul to get the basic
    // heuristic result internally. Downsides of this approach are that there is
    // no way to configure search preferences (e.g. disallow tensor operations
    // or some reduction schemes) and no way to store the algo for later use
    checkCublasStatus(hipblasLtMatmul(ltHandle, operationDesc, alphaArrayDev, A, Adesc, B, Bdesc, betaArrayDev, C, Cdesc,
                                     (void *)D, Ddesc, &heuristicResult.algo, workspace, workspaceSize, 0));

    // descriptors are no longer needed as all GPU work was already enqueued
    if (preference) checkCublasStatus(hipblasLtMatmulPreferenceDestroy(preference));
    if (Cdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Cdesc));
    if (Bdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Bdesc));
    if (Adesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Adesc));
    if (Ddesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Ddesc));
    if (operationDesc) checkCublasStatus(hipblasLtMatmulDescDestroy(operationDesc));
}
