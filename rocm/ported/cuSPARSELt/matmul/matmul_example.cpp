/*
 * SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <hip/hip_runtime_api.h> // cudaMalloc, cudaMemcpy, etc.
#include <hipsparselt/hipsparselt.h>       // cusparseLt header
#include <cstdio>             // printf
#include <cstdlib>            // std::rand
                              
#include <hip/hip_fp8.h>

#define FP16 1000
#define INT8 1001
#define FP8  1002

/*
 * Choose your data type for matrices A and B
 */
#define AB_TYPE FP16
// #define AB_TYPE FP8
// #define AB_TYPE INT8

#if AB_TYPE == FP8
using AB_t         = __hip_fp8_e4m3_fnuz;
using C_t          = __half;
using COMPUTE_t    = float;
#elif AB_TYPE == FP16
using AB_t         = __half;
using C_t          = __half;
using COMPUTE_t    = float;
#elif AB_TYPE == INT8
using AB_t         = int8_t;
using C_t          = int8_t; // can also be __half, __nv_bfloat16, int
using COMPUTE_t    = int;
#endif
                              
template <typename value_t>
struct cuda_type { };

template <>
struct cuda_type <__half> {
    static constexpr hipDataType value = HIP_R_16F;
};

template <>
struct cuda_type <__hip_bfloat16> {
    static constexpr hipDataType value = HIP_R_16BF;
};

template <>
struct cuda_type <__hip_fp8_e4m3_fnuz> {
    static constexpr hipDataType value = HIP_R_8F_E4M3;
};

template <>
struct cuda_type <int8_t> {
    static constexpr hipDataType value = HIP_R_8I;
};

template <>
struct cuda_type <int> {
    static constexpr hipDataType value = HIP_R_32I;
};

template <typename value_t>
struct cusparse_compute_type {  };

template <>
struct cusparse_compute_type<float> {
    static constexpr hipsparseLtComputetype_t value = HIPSPARSELT_COMPUTE_32F;
};

template <>
struct cusparse_compute_type<int> {
    static constexpr hipsparseLtComputetype_t value = HIPSPARSELT_COMPUTE_32I;
};

#define CHECK_CUDA(func)                                                       \
{                                                                              \
    hipError_t status = (func);                                               \
    if (status != hipSuccess) {                                               \
        printf("CUDA API failed at line %d with error: %s (%d)\n",             \
               __LINE__, hipGetErrorString(status), status);                  \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}

#define CHECK_CUSPARSE(func)                                                   \
{                                                                              \
    hipsparseStatus_t status = (func);                                          \
    if (status != HIPSPARSE_STATUS_SUCCESS) {                                   \
        printf("CUSPARSE API failed at line %d with error: %s (%d)\n",         \
               __LINE__, hipsparseGetErrorString(status), status);            \
        return EXIT_FAILURE;                                                   \
    }                                                                          \
}


constexpr int EXIT_UNSUPPORTED = 2;


int main(void) {
    int major_cc, minor_cc;
    CHECK_CUDA( hipDeviceGetAttribute(&major_cc,
                                       hipDeviceAttributeComputeCapabilityMajor, 0) )
    CHECK_CUDA( hipDeviceGetAttribute(&minor_cc,
                                       hipDeviceAttributeComputeCapabilityMinor, 0) )
    if (!(major_cc == 8 && minor_cc == 0) &&
        !(major_cc == 8 && minor_cc == 6) &&
        !(major_cc == 8 && minor_cc == 7) &&
        !(major_cc == 8 && minor_cc == 9) &&
        !(major_cc == 9 && minor_cc == 0) &&
        !(major_cc == 10 && minor_cc == 0) &&
        !(major_cc == 10 && minor_cc == 1) &&
        !(major_cc == 11 && minor_cc == 0) &&
        !(major_cc == 12 && minor_cc == 0) &&
        !(major_cc == 12 && minor_cc == 1)) {
        std::printf("\ncusparseLt is supported only on GPU devices with"
                    " compute capability == 8.0, 8.6, 8.7, 8.9, 9.0 10.0 10.1 110 12.0 12.1 current: %d.%d\n\n",
                     major_cc, minor_cc);
        return EXIT_UNSUPPORTED;
    }
    // Host problem definition, row-major order
    // bigger sizes may require dynamic allocations
    constexpr int m            = 32;
    constexpr int n            = 32;
    constexpr int k            = 64;

    auto     order          = HIPSPARSE_ORDER_ROW;
    auto     opA            = HIPSPARSE_OPERATION_NON_TRANSPOSE;
    auto     opB            = HIPSPARSE_OPERATION_TRANSPOSE;
    auto     type_AB        = cuda_type<AB_t>::value;
    auto     type_C         = cuda_type<C_t>::value;
    auto     compute_type   = cusparse_compute_type<COMPUTE_t>::value;
    bool     matmul_search  = true;
    bool     is_rowmajor    = (order == HIPSPARSE_ORDER_ROW);
    bool     isA_transposed = (opA != HIPSPARSE_OPERATION_NON_TRANSPOSE);
    bool     isB_transposed = (opB != HIPSPARSE_OPERATION_NON_TRANSPOSE);
    auto     num_A_rows     = (isA_transposed) ? k : m;
    auto     num_A_cols     = (isA_transposed) ? m : k;
    auto     num_B_rows     = (isB_transposed) ? n : k;
    auto     num_B_cols     = (isB_transposed) ? k : n;
    auto     num_C_rows     = m;
    auto     num_C_cols     = n;
    unsigned alignment      = 16;
    auto     lda            = (is_rowmajor) ? num_A_cols : num_A_rows;
    auto     ldb            = (is_rowmajor) ? num_B_cols : num_B_rows;
    auto     ldc            = (is_rowmajor) ? num_C_cols : num_C_rows;
    auto     A_height       = (is_rowmajor) ? num_A_rows : num_A_cols;
    auto     B_height       = (is_rowmajor) ? num_B_rows : num_B_cols;
    auto     C_height       = (is_rowmajor) ? num_C_rows : num_C_cols;
    
    auto     A_size         = A_height * lda * sizeof(AB_t);
    auto     B_size         = B_height * ldb * sizeof(AB_t);
    auto     C_size         = C_height * ldc * sizeof(C_t);

    auto     hA             = new AB_t[A_size / sizeof(AB_t)];
    auto     hB             = new AB_t[B_size / sizeof(AB_t)];
    auto     hC             = new C_t[C_size / sizeof(C_t)];

    for (int i = 0; i < m * k; i++) 
        hA[i] = static_cast<AB_t>(static_cast<float>(std::rand() % 5 - 2)); // -2 ~ 2

    for (int i = 0; i < k * n; i++)
        hB[i] = static_cast<AB_t>(static_cast<float>(std::rand() % 5 - 2));

    for (int i = 0; i < m * n; i++)
        hC[i] = static_cast<C_t>(static_cast<float>(std::rand() % 5 - 2));

    float alpha = 1.0f;
    float beta  = 1.0f;

    //--------------------------------------------------------------------------
    // Device memory management

    AB_t* dA, *dB, *dA_compressed;
    C_t* dC, *dD;
    int    *d_valid;

    CHECK_CUDA( hipMalloc((void**) &dA, A_size) )
    CHECK_CUDA( hipMalloc((void**) &dB, B_size) )
    CHECK_CUDA( hipMalloc((void**) &dC, C_size) )
    CHECK_CUDA( hipMalloc((void**) &d_valid, sizeof(int)) )
    dD = dC;

    CHECK_CUDA( hipMemcpy(dA, hA, A_size, hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB, hB, B_size, hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC, hC, C_size, hipMemcpyHostToDevice) )
    //--------------------------------------------------------------------------
    hipsparseLtHandle_t             handle;
    hipsparseLtMatDescriptor_t      matA, matB, matC;
    hipsparseLtMatmulDescriptor_t   matmul;
    hipsparseLtMatmulAlgSelection_t alg_sel;
    hipsparseLtMatmulPlan_t         plan;
    hipStream_t                   stream = nullptr;

    CHECK_CUSPARSE( hipsparseLtInit(&handle) )

    // matrix descriptor initialization
    CHECK_CUSPARSE( hipsparseLtStructuredDescriptorInit(
                                            &handle, &matA, num_A_rows,
                                            num_A_cols, lda, alignment,
                                            type_AB, order,
                                            HIPSPARSELT_SPARSITY_50_PERCENT) )

    CHECK_CUSPARSE( hipsparseLtDenseDescriptorInit(
                                            &handle, &matB, num_B_rows,
                                            num_B_cols, ldb, alignment,
                                            type_AB, order) )
    CHECK_CUSPARSE( hipsparseLtDenseDescriptorInit(
                                            &handle, &matC, num_C_rows,
                                            num_C_cols, ldc, alignment,
                                            type_C, order) )

    // matmul, algorithm selection, and plan initialization
    CHECK_CUSPARSE( hipsparseLtMatmulDescriptorInit(
                                            &handle, &matmul, opA, opB,
                                            &matA, &matB, &matC, &matC,
                                            compute_type) )

    CHECK_CUSPARSE( hipsparseLtMatmulAlgSelectionInit(
                                            &handle, &alg_sel, &matmul,
                                            HIPSPARSELT_MATMUL_ALG_DEFAULT) )

    CHECK_CUSPARSE( hipsparseLtMatmulPlanInit(&handle, &plan, &matmul, &alg_sel))

    CHECK_CUSPARSE(hipsparseLtMatmulDescSetAttribute(&handle,
                                                    &matmul,
                                                    HIPSPARSELT_MATMUL_SPARSE_MAT_POINTER,
                                                    &dA,
                                                    sizeof(dA)));

    //--------------------------------------------------------------------------
    // Prune the A matrix (in-place) and check the correctness
    CHECK_CUSPARSE( hipsparseLtSpMMAPrune(&handle, &matmul, dA, dA,
                                         HIPSPARSELT_PRUNE_SPMMA_TILE, stream) )
    CHECK_CUSPARSE( hipsparseLtSpMMAPruneCheck(&handle, &matmul, dA,
                                              d_valid, stream) )
    int is_valid;
    CHECK_CUDA( hipMemcpyAsync(&is_valid, d_valid, sizeof(int),
                                hipMemcpyDeviceToHost, stream) )
    CHECK_CUDA( hipStreamSynchronize(stream) )
    if (is_valid != 0) {
        std::printf("!!!! The matrix has been pruned in a wrong way. "
                    "hipsparseLtMatmul will not provide correct results\n");
        return EXIT_FAILURE;
    }
    //--------------------------------------------------------------------------
    // Compress the A matrix
    size_t compressed_size, compressed_buffer_size;
    void*  dA_compressedBuffer;
    CHECK_CUSPARSE( hipsparseLtSpMMACompressedSize(&handle, &plan,
                                                  &compressed_size,
                                                  &compressed_buffer_size) )
    CHECK_CUDA( hipMalloc((void**) &dA_compressed, compressed_size) )
    CHECK_CUDA( hipMalloc((void**) &dA_compressedBuffer,
                           compressed_buffer_size) )

    CHECK_CUSPARSE( hipsparseLtSpMMACompress(&handle, &plan, dA, dA_compressed,
                                            dA_compressedBuffer,stream) )

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Search the best kernel
    int           num_streams = 0;
    hipStream_t* streams     = nullptr;

    if (matmul_search) {
        CHECK_CUSPARSE( hipsparseLtMatmulSearch(&handle, &plan, &alpha,
                                               dA_compressed, dB, &beta,
                                               dC, dD, nullptr,
                                               streams, num_streams) )
        // dC accumulates so reset dC for correctness check
        CHECK_CUDA( hipMemcpy(dC, hC, C_size, hipMemcpyHostToDevice) )
    }

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    size_t workspace_size;

    CHECK_CUSPARSE( hipsparseLtMatmulGetWorkspace(&handle, &plan,
                                                 &workspace_size))
    void* d_workspace;
    CHECK_CUDA( hipMalloc((void**) &d_workspace, workspace_size) )
    // Perform the matrix multiplication
    CHECK_CUSPARSE( hipsparseLtMatmul(&handle, &plan, &alpha, dA_compressed, dB,
                                     &beta, dC, dD, d_workspace, streams,
                                     num_streams) )
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // destroy plan and handle
    CHECK_CUSPARSE( hipsparseLtMatDescriptorDestroy(&matA) )
    CHECK_CUSPARSE( hipsparseLtMatDescriptorDestroy(&matB) )
    CHECK_CUSPARSE( hipsparseLtMatDescriptorDestroy(&matC) )
    CHECK_CUSPARSE( hipsparseLtMatmulAlgSelectionDestroy(&alg_sel) )
    CHECK_CUSPARSE( hipsparseLtMatmulPlanDestroy(&plan) )
    CHECK_CUSPARSE( hipsparseLtDestroy(&handle) )

    //--------------------------------------------------------------------------
    // device result check
    // matrix A has been pruned
    CHECK_CUDA( hipMemcpy(hA, dA, A_size, hipMemcpyDeviceToHost) )

    bool A_std_layout = (is_rowmajor != isA_transposed);
    bool B_std_layout = (is_rowmajor != isB_transposed);

    // host computation
    C_t* hC_result = new C_t[C_height * ldc];

    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            COMPUTE_t sum  = static_cast<COMPUTE_t>(0);
            for (int k1 = 0; k1 < k; k1++) {
                auto posA = (A_std_layout) ? i * lda + k1 : i + k1 * lda;
                auto posB = (B_std_layout) ? k1 * ldb + j : k1 + j * ldb;
                sum      += static_cast<COMPUTE_t>(hA[posA]) *  // [i][k]
                            static_cast<COMPUTE_t>(hB[posB]);   // [k][j]
            }
            auto posC       = (is_rowmajor) ? i * ldc + j : i + j * ldc;
            hC_result[posC] = static_cast<C_t>(alpha * sum + beta * static_cast<float>(hC[posC]));  // [i][j]
        }
    }

    // reuse hC for device results
    CHECK_CUDA( hipMemcpy(hC, dD, C_size, hipMemcpyDeviceToHost) )

    // host-device comparison
    int correct = 1;
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            auto pos          = (is_rowmajor) ? i * ldc + j : i + j * ldc;
            auto device_value = hC[pos];
            auto host_value   = hC_result[pos];
            if (device_value != host_value) {
                // direct floating point comparison is not reliable
                std::printf("(%d, %d):\t%3.0f vs. %3.0f\n",
                            i, j, static_cast<float>(host_value), static_cast<float>(device_value));
                correct = 0;
                break;
            }
        }
    }

    if (correct) {
        std::printf("matmul_example test PASSED\n");
    }
    else {
        std::printf("matmul_example test FAILED: wrong result\n");
    }

    //--------------------------------------------------------------------------
    // host memory deallocation
    delete[] hA;
    delete[] hB;
    delete[] hC;
    delete[] hC_result;
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dA_compressed) )
    CHECK_CUDA( hipFree(dA) )
    CHECK_CUDA( hipFree(dB) )
    CHECK_CUDA( hipFree(dC) )
    CHECK_CUDA( hipFree(d_valid) )
    CHECK_CUDA( hipFree(d_workspace) )
    CHECK_CUDA( hipFree(dA_compressedBuffer) )

    return EXIT_SUCCESS;
}