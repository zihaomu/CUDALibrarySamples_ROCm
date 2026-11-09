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
#include <hip/hip_runtime_api.h>
#include <hip/hip_fp8.h>
#include <hipblaslt.h>

#include "sample_cublasLt_LtBlk128x128Fp8Matmul.h"
#include "helpers.h"

int main() {
    TestBench<__hip_fp8_e4m3_fnuz, __hip_bfloat16, float, float, float, __hip_bfloat16> props(
        HIPBLAS_OP_T, HIPBLAS_OP_N, 64, 128, 256, 2.0f, 1.0f, 32ULL * 1024 * 1024, 1,
        HIPBLASLT_MATMUL_MATRIX_SCALE_VEC128_32F, HIPBLASLT_MATMUL_MATRIX_SCALE_BLK128x128_32F,
        HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F, HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
        HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F);

    props.run([&props] {
        LtBlk128x128Fp8Matmul(props.ltHandle, props.transa, props.transb, props.m, props.n, props.k, &props.alpha,
                              props.AscaleDev, props.Adev, props.lda, props.BscaleDev, props.Bdev, props.ldb,
                              &props.beta, props.Cdev, props.ldc, props.Ddev, props.ldd, props.workspace,
                              props.workspaceSize, props.AScaleMode, props.BScaleMode);
    });

    return 0;
}