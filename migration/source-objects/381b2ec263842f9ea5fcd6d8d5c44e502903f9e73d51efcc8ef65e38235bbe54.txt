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

#include "sample_cublasLt_LtDgemmEmulated.h"
#include "helpers.h"

/// Sample wrapper executing double precision GEMM with a predefined algorithm using hipblasLtMatmul, nearly a drop-in
/// replacement for hipblasDgemm, with addition of the workspace to support fp64 emulation.
///
/// Pointer mode is always host. To change it, configure the appropriate matmul descriptor attribute.
/// Matmul is not using cuBLAS handle's configuration of math mode (where tensor ops are implicitly allowed).
/// To change this, configure the appropriate attribute in the preference handle.
///
/// NOTE: This sample may not work on all architectures or all problem sizes.
void LtDgemmEmulated(hipblasLtHandle_t ltHandle,
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
                     hipblasEmulationStrategy_t emulationStrategy,
                     cudaEmulationSpecialValuesSupport specialValuesSupport,
                     cudaEmulationMantissaControl mantissaControl,
                     int maxMantissaBitCount,
                     int mantissaBitOffset,
                     hipStream_t stream) {
    cublasLtEmulationDescOpaque_t emulationDescOpaque = {};
    hipblasLtMatmulDescOpaque_t operationDesc = {};
    hipblasLtMatrixLayoutOpaque_t Adesc = {}, Bdesc = {}, Cdesc = {};
    hipblasLtMatmulPreferenceOpaque_t preference = {};

    int returnedResults = 0;
    hipblasLtMatmulHeuristicResult_t heuristicResult = {};

    // Create emulation descriptor; see cublasLtEmulationDescAttributes_t for details about defaults.
    cublasLtEmulationDesc_t emulationDesc = &emulationDescOpaque;
    checkCublasStatus(cublasLtEmulationDescInit(emulationDesc));
    checkCublasStatus(cublasLtEmulationDescSetAttribute(emulationDesc, CUBLASLT_EMULATION_DESC_STRATEGY,
                                                        &emulationStrategy, sizeof(emulationStrategy)));
    checkCublasStatus(cublasLtEmulationDescSetAttribute(emulationDesc, CUBLASLT_EMULATION_DESC_SPECIAL_VALUES_SUPPORT,
                                                        &specialValuesSupport, sizeof(specialValuesSupport)));
    checkCublasStatus(cublasLtEmulationDescSetAttribute(
        emulationDesc, CUBLASLT_EMULATION_DESC_FIXEDPOINT_MANTISSA_CONTROL, &mantissaControl, sizeof(mantissaControl)));
    checkCublasStatus(cublasLtEmulationDescSetAttribute(emulationDesc,
                                                        CUBLASLT_EMULATION_DESC_FIXEDPOINT_MAX_MANTISSA_BIT_COUNT,
                                                        &maxMantissaBitCount, sizeof(maxMantissaBitCount)));
    checkCublasStatus(cublasLtEmulationDescSetAttribute(emulationDesc,
                                                        CUBLASLT_EMULATION_DESC_FIXEDPOINT_MANTISSA_BIT_OFFSET,
                                                        &mantissaBitOffset, sizeof(mantissaBitOffset)));

    // Create operation desciriptor; see hipblasLtMatmulDescAttributes_t for details about defaults.
    // Here we just need to set the transforms for A and B.
    checkCublasStatus(cublasLtMatmulDescInit(&operationDesc, CUBLAS_COMPUTE_64F_EMULATED_FIXEDPOINT, HIP_R_64F));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(&operationDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(
        hipblasLtMatmulDescSetAttribute(&operationDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(&operationDesc, CUBLASLT_MATMUL_DESC_EMULATION_DESCRIPTOR,
                                                     &emulationDesc, sizeof(emulationDesc)));

    // Create matrix descriptors.
    // We are good with the details here so no need to set any extra attributes.
    checkCublasStatus(cublasLtMatrixLayoutInit(&Adesc, HIP_R_64F, transa == HIPBLAS_OP_N ? m : k,
                                               transa == HIPBLAS_OP_N ? k : m, lda));
    checkCublasStatus(cublasLtMatrixLayoutInit(&Bdesc, HIP_R_64F, transb == HIPBLAS_OP_N ? k : n,
                                               transb == HIPBLAS_OP_N ? n : k, ldb));
    checkCublasStatus(cublasLtMatrixLayoutInit(&Cdesc, HIP_R_64F, m, n, ldc));

    // Create preference handle.
    // Here we could use extra attributes to disable tensor ops, or we could make sure that the algorithm that is
    // selected will work with badly aligned A, B, C. For simplicity, we just assume A, B, C are always well aligned
    // (e.g. directly come from cudaMalloc).
    checkCublasStatus(cublasLtMatmulPreferenceInit(&preference));
    checkCublasStatus(hipblasLtMatmulPreferenceSetAttribute(&preference, HIPBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,
                                                           &workspaceSize, sizeof(workspaceSize)));

    // We just need the best available heuristic to try and run matmul.
    // There is no guarantee this will work (e.g. if A is badly aligned).
    // You can request more (e.g. 32) algorithms and try to run them one by one until something works.
    checkCublasStatus(hipblasLtMatmulAlgoGetHeuristic(ltHandle, &operationDesc, &Adesc, &Bdesc, &Cdesc, &Cdesc,
                                                     &preference, 1, &heuristicResult, &returnedResults));

    if (returnedResults == 0) {
        checkCublasStatus(HIPBLAS_STATUS_NOT_SUPPORTED);
    }

    checkCublasStatus(hipblasLtMatmul(ltHandle, &operationDesc, alpha, A, &Adesc, B, &Bdesc, beta, C, &Cdesc, C, &Cdesc,
                                     &heuristicResult.algo, workspace, workspaceSize, stream));
}