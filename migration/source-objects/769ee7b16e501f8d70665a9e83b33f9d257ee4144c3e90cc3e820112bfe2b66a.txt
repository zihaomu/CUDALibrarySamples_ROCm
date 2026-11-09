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

#include "helpers.h"
#include "sample_cublasLt_LtNvfp4gemmGroupedSimple.h"

/// (!) EXPERIMENTAL: This sample implements an experimental grouped gemm
/// feature and may be changed or removed in the future. Refer to the
/// documentation for more details and limitations.
///
/// Sample wrapper executing grouped NVFP4 gemm with hipblasLtMatmul, using VEC16_UE4M3 block scaling.
/// Output is bfloat16, alpha/beta are host pointers shared across all groups.
///
/// matmul is not using hipblas handle's configuration of math mode, here tensor ops are implicitly allowed
void LtNvfp4gemmGroupedSimple(hipblasLtHandle_t ltHandle,
                              hipblasOperation_t transa,
                              hipblasOperation_t transb,
                              const void *mArrayDev,
                              int64_t avgM,
                              const void *nArrayDev,
                              int64_t avgN,
                              const void *kArrayDev,
                              int64_t avgK,
                              const float *alpha,
                              const __hip_fp8_e4m3_fnuz *const *a_scale,
                              const typename StorageType<__hip_fp4_e2m1>::type *const *A,
                              const void *ldaArrayDev,
                              const __hip_fp8_e4m3_fnuz *const *b_scale,
                              const typename StorageType<__hip_fp4_e2m1>::type *const *B,
                              const void *ldbArrayDev,
                              const float *beta,
                              const __hip_bfloat16 *const *C,
                              const void *ldcArrayDev,
                              __hip_bfloat16 *const *D,
                              const void *lddArrayDev,
                              int batchCount,
                              void *workspace,
                              size_t workspaceSize,
                              hipblasLtMatmulMatrixScale_t AScaleMode,
                              hipblasLtMatmulMatrixScale_t BScaleMode) {
    hipblasLtMatmulDesc_t operationDesc = NULL;
    hipblasLtMatrixLayout_t Adesc = NULL, Bdesc = NULL, Cdesc = NULL, Ddesc = NULL;

    // create operation descriptor; see hipblasLtMatmulDescAttributes_t for
    // details about defaults; here we need to set the transforms for A and B
    // pointer mode is host (default) - alpha/beta are shared across all groups
    checkCublasStatus(hipblasLtMatmulDescCreate(&operationDesc, HIPBLAS_COMPUTE_32F, HIP_R_32F));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));

    // set block scaling mode (VEC16_UE4M3 for NVFP4)
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_A_SCALE_MODE, &AScaleMode,
                                                     sizeof(AScaleMode)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_B_SCALE_MODE, &BScaleMode,
                                                     sizeof(BScaleMode)));

    // set scaling factors (A, B only - D is bf16, no scaling needed)
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_A_SCALE_POINTER, &a_scale, sizeof(a_scale)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(operationDesc, HIPBLASLT_MATMUL_DESC_B_SCALE_POINTER, &b_scale, sizeof(b_scale)));

    // create grouped matrix descriptors
    checkCublasStatus(cublasLtGroupedMatrixLayoutCreate(&Adesc, HIP_R_4F_E2M1, batchCount,
                                                        transa == HIPBLAS_OP_N ? mArrayDev : kArrayDev,
                                                        transa == HIPBLAS_OP_N ? kArrayDev : mArrayDev, ldaArrayDev));
    checkCublasStatus(cublasLtGroupedMatrixLayoutCreate(&Bdesc, HIP_R_4F_E2M1, batchCount,
                                                        transb == HIPBLAS_OP_N ? kArrayDev : nArrayDev,
                                                        transb == HIPBLAS_OP_N ? nArrayDev : kArrayDev, ldbArrayDev));
    checkCublasStatus(
        cublasLtGroupedMatrixLayoutCreate(&Cdesc, HIP_R_16BF, batchCount, mArrayDev, nArrayDev, ldcArrayDev));
    checkCublasStatus(
        cublasLtGroupedMatrixLayoutCreate(&Ddesc, HIP_R_16BF, batchCount, mArrayDev, nArrayDev, lddArrayDev));

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

    checkCublasStatus(hipblasLtMatmul(ltHandle, operationDesc, alpha, A, Adesc, B, Bdesc, beta, C, Cdesc, (void *)D,
                                     Ddesc, &heuristicResult.algo, workspace, workspaceSize, 0));

    // descriptors are no longer needed as all GPU work was already enqueued
    if (preference) checkCublasStatus(hipblasLtMatmulPreferenceDestroy(preference));
    if (Cdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Cdesc));
    if (Bdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Bdesc));
    if (Adesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Adesc));
    if (Ddesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Ddesc));
    if (operationDesc) checkCublasStatus(hipblasLtMatmulDescDestroy(operationDesc));
}
