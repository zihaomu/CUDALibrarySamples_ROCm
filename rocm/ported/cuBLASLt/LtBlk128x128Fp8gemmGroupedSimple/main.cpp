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
#include <hip/hip_bf16.h>
#include <hip/hip_fp8.h>
#include <hip/hip_runtime_api.h>

#include "helpers.h"
#include "sample_cublasLt_LtBlk128x128Fp8gemmGroupedSimple.h"

int main() {
    // FP8 grouped GEMM with block scaling (VEC128 for A, BLK128x128 for B)
    // Uses __nv_fp8_e4m3 for A, B and __nv_bfloat16 for C, D
    // ScaleType = float (32-bit float scales)
    TestBench<__hip_fp8_e4m3_fnuz, __hip_bfloat16, float, float, float, __hip_bfloat16> props(
        HIPBLAS_OP_T, HIPBLAS_OP_N, 64, 128, 256, 2.0f, 1.0f, 32ULL * 1024 * 1024, 2, 2.0f, 0.5f, 1.0f, 1.0f,
        HIPBLASLT_MATMUL_MATRIX_SCALE_VEC128_32F, HIPBLASLT_MATMUL_MATRIX_SCALE_BLK128x128_32F,
        HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F, HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
        HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F, false, true, true);

    props.run([&props] {
        LtBlk128x128Fp8gemmGroupedSimple(
            props.ltHandle, props.transa, props.transb, props.mArrayDev, props.avgM, props.nArrayDev, props.avgN,
            props.kArrayDev, props.avgK, &props.alpha, props.AscalePtrArrayDev, props.APtrArrayDev, props.ldaArrayDev,
            props.BscalePtrArrayDev, props.BPtrArrayDev, props.ldbArrayDev, &props.beta, props.CPtrArrayDev,
            props.ldcArrayDev, props.DPtrArrayDev, props.lddArrayDev, props.N, props.workspace, props.workspaceSize,
            props.AScaleMode, props.BScaleMode);
    });

    return 0;
}
