/*
 * SPDX-FileCopyrightText: Copyright (c) 2020-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include "LtMatmulCustomFind.h"
#include "helpers.h"

int main() {
    TestBench<__hip_fp8_e4m3_fnuz, __hip_fp8_e4m3_fnuz, float, float, float, __hip_bfloat16> props(
        HIPBLAS_OP_T, HIPBLAS_OP_N, 1024, 512, 4096, 2.0f, 0.0f, 1024 * 1024 * 16);

    props.run([&props] {
        LtMatmulCustomFind(props.ltHandle, props.transa, props.transb, props.m, props.n, props.k, HIP_R_32F,
                           &props.alpha, HIP_R_8F_E4M3, props.Adev, props.lda, HIP_R_8F_E4M3, props.Bdev, props.ldb,
                           &props.beta, HIP_R_16BF, props.Cdev, props.ldc, HIP_R_8F_E4M3, props.Ddev, props.ldd,
                           props.workspace, props.workspaceSize);
    });

    return 0;
}