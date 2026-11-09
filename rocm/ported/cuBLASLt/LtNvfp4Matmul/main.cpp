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
#include <hip/hip_fp4.h>
#include <hip/hip_bf16.h>

#include "sample_cublasLt_LtNvfp4Matmul.h"
#include "helpers.h"

int main() {
    TestBench<__hip_fp4_e2m1, __hip_fp4_e2m1, float, __hip_fp8_e4m3_fnuz, float, __hip_bfloat16> props(
        HIPBLAS_OP_T, HIPBLAS_OP_N, 64, 128, 256, 2.0f, 1.0f, 32ULL * 1024 * 1024, 1,
        HIPBLASLT_MATMUL_MATRIX_SCALE_VEC16_UE4M3, HIPBLASLT_MATMUL_MATRIX_SCALE_VEC16_UE4M3,
        HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F, HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
        HIPBLASLT_MATMUL_MATRIX_SCALE_VEC16_UE4M3);

    props.run([&props] {
        LtNvfp4Matmul(props.ltHandle, props.transa, props.transb, props.m, props.n, props.k, &props.alpha,
                      props.AscaleDev, props.Adev, props.lda, props.BscaleDev, props.Bdev, props.ldb, &props.beta,
                      props.CscaleDev, props.Cdev, props.ldc, props.DscaleDev, props.Ddev, props.ldd,
                      props.DOutscaleDev, props.workspace, props.workspaceSize, props.AScaleMode, props.BScaleMode,
                      props.CScaleMode, props.DScaleMode, props.DOutScaleMode);
    });

    return 0;
}