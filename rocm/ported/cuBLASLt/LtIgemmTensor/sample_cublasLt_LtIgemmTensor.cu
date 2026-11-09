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

#include <hipblaslt.h>
#include <hip/hip_runtime.h>
#include <cstdint>

#include "sample_cublasLt_LtIgemmTensor.h"
#include "helpers.h"

int roundoff(int v, int d) {
    return (v + d - 1) / d * d;
}

/// Use hipblasLtMatmul to perform tensor-op Igemm with memory order transforms on all buffers
///
/// For better performance data order transforms should be offline as much as possible.
///
/// transa, transb assumed N; alpha, beta are host pointers, tensor ops allowed, alpha assumed 1, beta assumed 0,
/// stream assumed 0
void LtIgemmTensor(hipblasLtHandle_t ltHandle,
                   hipblasOperation_t transa,
                   hipblasOperation_t transb,
                   int m,
                   int n,
                   int k,
                   const int8_t *A,
                   int lda,
                   const int8_t *B,
                   int ldb,
                   int32_t *C,
                   int ldc) {
    hipblasLtMatmulDesc_t matmulDesc = NULL;
    hipblasLtMatrixLayout_t Adesc = NULL, Bdesc = NULL, Cdesc = NULL;
    int32_t alpha = 1, beta = 0;
    hipblasOperation_t opTranspose = HIPBLAS_OP_T;

    // tensor op igemm kernels require specialized memory order of data
    hipblasLtMatrixTransformDesc_t transformDesc = NULL;
    int8_t *Atransform = NULL, *Btransform = NULL;
    int32_t *Ctransform = NULL;
    hipblasLtMatrixLayout_t AtransformDesc = NULL, BtransformDesc = NULL, CtransformDesc = NULL;
    float transformAlpha = 1.0f, transformBeta = 0.0f;
    hipblasLtOrder_t order_COL32 = CUBLASLT_ORDER_COL32;
    hipblasLtOrder_t order_COL4_4R2_8C = CUBLASLT_ORDER_COL4_4R2_8C;

    int ldatransform = 32 * m;
    int ldbtransform = 32 * roundoff(n, 8);
    int ldctransform = 32 * m;

    checkCudaStatus(
        hipMalloc(reinterpret_cast<void **>(&Atransform), sizeof(int8_t) * roundoff(k, 32) / 32 * ldatransform));
    checkCudaStatus(
        hipMalloc(reinterpret_cast<void **>(&Btransform), sizeof(int8_t) * roundoff(k, 32) / 32 * ldbtransform));
    checkCudaStatus(
        hipMalloc(reinterpret_cast<void **>(&Ctransform), sizeof(int32_t) * roundoff(n, 32) / 32 * ldctransform));

    checkCublasStatus(hipblasLtMatrixTransformDescCreate(&transformDesc, HIP_R_32F));

    checkCublasStatus(hipblasLtMatmulDescCreate(&matmulDesc, HIPBLAS_COMPUTE_32I, HIP_R_32I));
    // tensor op igemm kernels only support NT gemm
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(matmulDesc, HIPBLASLT_MATMUL_DESC_TRANSA, &transa, sizeof(transa)));
    checkCublasStatus(hipblasLtMatmulDescSetAttribute(matmulDesc, HIPBLASLT_MATMUL_DESC_TRANSB, &transb, sizeof(transb)));

    // ---------------------------------------------------------------------------------------------
    // create descriptors for original matrices

    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Adesc, HIP_R_8I, m, k, lda));
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Bdesc, HIP_R_8I, k, n, ldb));
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&Cdesc, HIP_R_32I, m, n, ldc));

    // ---------------------------------------------------------------------------------------------
    // create descriptors for transformed matrices

    checkCublasStatus(hipblasLtMatrixLayoutCreate(&AtransformDesc, HIP_R_8I, m, k, ldatransform));
    checkCublasStatus(hipblasLtMatrixLayoutSetAttribute(AtransformDesc, HIPBLASLT_MATRIX_LAYOUT_ORDER, &order_COL32,
                                                       sizeof(order_COL32)));

    // data memory order is set to CUBLASLT_ORDER_COL4_4R2_8C in order to achieve best performance on Turing devices.
    // for best performance on Ampere, consider setting the memory order to CUBLASLT_ORDER_COL32_2R_4R4.
    checkCublasStatus(hipblasLtMatrixLayoutCreate(&BtransformDesc, HIP_R_8I, n, k, ldbtransform));
    checkCublasStatus(hipblasLtMatrixLayoutSetAttribute(BtransformDesc, HIPBLASLT_MATRIX_LAYOUT_ORDER, &order_COL4_4R2_8C,
                                                       sizeof(order_COL4_4R2_8C)));

    checkCublasStatus(hipblasLtMatrixLayoutCreate(&CtransformDesc, HIP_R_32I, m, n, ldctransform));
    checkCublasStatus(hipblasLtMatrixLayoutSetAttribute(CtransformDesc, HIPBLASLT_MATRIX_LAYOUT_ORDER, &order_COL32,
                                                       sizeof(order_COL32)));

    // ---------------------------------------------------------------------------------------------
    // transforms and computation

    checkCublasStatus(hipblasLtMatrixTransform(ltHandle, transformDesc, &transformAlpha, A, Adesc, &transformBeta, NULL,
                                              NULL, Atransform, AtransformDesc, 0));

    // B matrix is non-transposed, but transposed matrix is needed - add transpose operation in matrix transform.
    checkCublasStatus(hipblasLtMatrixTransformDescSetAttribute(transformDesc, HIPBLASLT_MATRIX_TRANSFORM_DESC_TRANSA,
                                                              &opTranspose, sizeof(opTranspose)));

    checkCublasStatus(hipblasLtMatrixTransform(ltHandle, transformDesc, &transformAlpha, B, Bdesc, &transformBeta, NULL,
                                              NULL, Btransform, BtransformDesc, 0));

    // no need to transform C matrix as beta is assumed to be 0
    checkCublasStatus(hipblasLtMatmul(ltHandle, matmulDesc, &alpha, Atransform, AtransformDesc, Btransform,
                                     BtransformDesc, &beta, Ctransform, CtransformDesc, Ctransform, CtransformDesc,
                                     NULL, NULL, 0, 0));

    opTranspose = HIPBLAS_OP_N;
    checkCublasStatus(hipblasLtMatrixTransformDescSetAttribute(transformDesc, HIPBLASLT_MATRIX_TRANSFORM_DESC_TRANSA,
                                                              &opTranspose, sizeof(opTranspose)));

    // transform outputs to COL order
    checkCublasStatus(hipblasLtMatrixTransform(ltHandle, transformDesc, &transformAlpha, Ctransform, CtransformDesc,
                                              &transformBeta, NULL, NULL, C, Cdesc, 0));

    // descriptors are no longer needed as all GPU work was already enqueued
    if (CtransformDesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(CtransformDesc));
    if (BtransformDesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(BtransformDesc));
    if (AtransformDesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(AtransformDesc));
    if (Cdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Cdesc));
    if (Bdesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Bdesc));
    if (Adesc) checkCublasStatus(hipblasLtMatrixLayoutDestroy(Adesc));
    if (matmulDesc) checkCublasStatus(hipblasLtMatmulDescDestroy(matmulDesc));
    if (transformDesc) checkCublasStatus(hipblasLtMatrixTransformDescDestroy(transformDesc));

    // wait until device is done before freeing transformed buffers
    checkCudaStatus(hipDeviceSynchronize());
    if (Ctransform) checkCudaStatus(hipFree(Ctransform));
    if (Btransform) checkCudaStatus(hipFree(Btransform));
    if (Atransform) checkCudaStatus(hipFree(Atransform));
}