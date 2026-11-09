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
#include <hip/hip_fp8.h>
#include <hipblaslt.h>

/// Sample wrapper executing fp8 matmul with hipblasLtMatmul, with addition of per-tensor scaling, amax calculations, and
/// the workspace to support split-K algorithms.
///
/// pointer mode is for alpha and beta is always host, to change it configure the appropriate matmul descriptor
/// attribute matmul is not using hipblas handle's configuration of math mode, here tensor ops are implicitly allowed; to
/// change this configure appropriate attribute in the preference handle
void LtFp8Matmul(hipblasLtHandle_t ltHandle,
                 hipblasOperation_t transa,
                 hipblasOperation_t transb,
                 int m,
                 int n,
                 int k,
                 const float *alpha,   /* host pointer */
                 const float *a_scale, /* device pointer */
                 const __hip_fp8_e4m3_fnuz *A,
                 int lda,
                 const float *b_scale, /* device pointer */
                 const __hip_fp8_e4m3_fnuz *B,
                 int ldb,
                 const float *beta,    /* host pointer */
                 const float *c_scale, /* device pointer */
                 __hip_bfloat16 *C,
                 int ldc,
                 const float *d_scale, /* device pointer */
                 __hip_fp8_e4m3_fnuz *D,
                 int ldd,
                 float *amax_d, /* device pointer */
                 void *workspace,
                 size_t workspaceSize);