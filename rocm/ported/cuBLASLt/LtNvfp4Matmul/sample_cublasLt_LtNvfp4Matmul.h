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
#include <hipblaslt.h>

#include "helpers.h"

/// Sample wrapper executing nvfp4 matmul with hipblasLtMatmul, with addition of per-tensor block scaling, and
/// the workspace to support split-K algorithms.
///
/// pointer mode is for alpha and beta is always host, to change it configure the appropriate matmul descriptor
/// attribute matmul is not using hipblas handle's configuration of math mode, here tensor ops are implicitly allowed; to
/// change this configure appropriate attribute in the preference handle
void LtNvfp4Matmul(hipblasLtHandle_t ltHandle,
                   hipblasOperation_t transa,
                   hipblasOperation_t transb,
                   int m,
                   int n,
                   int k,
                   const float *alpha,           /* host pointer */
                   const __hip_fp8_e4m3_fnuz *a_scale, /* device pointer */
                   const typename StorageType<__hip_fp4_e2m1>::type *A,
                   int lda,
                   const __hip_fp8_e4m3_fnuz *b_scale, /* device pointer */
                   const typename StorageType<__hip_fp4_e2m1>::type *B,
                   int ldb,
                   const float *beta,
                   const __hip_fp8_e4m3_fnuz *c_scale, /* device pointer */
                   __hip_bfloat16 *C,
                   int ldc,
                   const float *d_scale, /* device pointer */
                   typename StorageType<__hip_fp4_e2m1>::type *D,
                   int ldd,
                   __hip_fp8_e4m3_fnuz *d_out_scale, /* device pointer */
                   void *workspace,
                   size_t workspaceSize,
                   hipblasLtMatmulMatrixScale_t AScaleMode,
                   hipblasLtMatmulMatrixScale_t BScaleMode,
                   hipblasLtMatmulMatrixScale_t CScaleMode,
                   hipblasLtMatmulMatrixScale_t DScaleMode,
                   hipblasLtMatmulMatrixScale_t DOutScaleMode);
