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
#include <algorithm>          // std::min
#include <cstdio>             // printf
#include <cstdlib>            // std::rand
#include <hip/hip_runtime_api.h> // cudaMalloc, cudaMemcpy, etc.
#include <hipsparselt/hipsparselt.h>       // cusparseLt header

#include <hip/hip_fp8.h>

#define FP16 1000
#define INT8 1001
#define FP8  1002

/*
 * Choose your data type for AB
 */
#define AB_TYPE FP16
// #define AB_TYPE FP8
// #define AB_TYPE INT8

#if AB_TYPE == FP8
using AB_t         = __hip_fp8_e4m3_fnuz;
using C_t          = __half;
using COMPUTE_t    = float;
using Bias_t       = C_t;
#elif AB_TYPE == FP16
using AB_t         = __half;
using C_t          = __half;
using COMPUTE_t    = float;
using Bias_t       = C_t;
#elif AB_TYPE == INT8
using AB_t         = int8_t;
using C_t          = int8_t; // can also be __half, __nv_bfloat16, int
using COMPUTE_t    = int;
// for bias type, refer to https://docs.nvidia.com/cuda/cusparselt/types.html#cusparseltmatmuldescattribute-t
using Bias_t       = float; 
#endif
                              
template <typename T>
T random_value_gen() {
    return static_cast<T>(static_cast<float>(std::rand() % 10));
}

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

template <typename T>
void print_matrix(const T* matrix,
                  int64_t  height,
                  int64_t  width,
                  int64_t  ld,
                  int      num_batches,
                  int64_t  batch_stride) {
    for (int b = 0; b < num_batches; b++) {
        for (int i = 0; i < height; i++) {
            for (int j = 0; j < width; j++) {
                printf("%3.0f",
                     static_cast<float>(matrix[b * batch_stride + i * ld + j]));
            }
            printf("\n");
        }
        if (b == num_batches - 1)
            printf("================================================\n");
        else
            printf("------------------------------------------------\n");
    }
    printf("\n");
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
    constexpr bool print_sparse_matrix = true;
    // Host problem definition, row-major order
    constexpr int     num_batches   = 2;
    constexpr int64_t m             = 32;
    constexpr int64_t n             = 16;
    constexpr int64_t k             = 32;
    constexpr int64_t batch_strideA = m * k + 128;
    constexpr int64_t batch_strideB = k * n + 128;
    constexpr int64_t batch_strideC = m * n + 128;
    constexpr auto    order         = HIPSPARSE_ORDER_ROW;
    constexpr auto    opA           = HIPSPARSE_OPERATION_NON_TRANSPOSE;
    constexpr auto    opB           = HIPSPARSE_OPERATION_TRANSPOSE;

    auto     type_AB        = cuda_type<AB_t>::value;
    auto     type_C         = cuda_type<C_t>::value;
    auto     compute_type   = cusparse_compute_type<COMPUTE_t>::value;
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
    auto     C_height       = (is_rowmajor) ? num_B_rows : num_C_cols;
    auto     A_width        = (is_rowmajor) ? num_A_cols : num_A_rows;
    auto     B_width        = (is_rowmajor) ? num_B_cols : num_B_rows;
    auto     C_width        = (is_rowmajor) ? num_C_cols : num_C_rows;
    auto     A_size         = num_batches * batch_strideA;
    auto     B_size         = num_batches * batch_strideB;
    auto     C_size         = num_batches * batch_strideC;
    auto     A_size_bytes   = num_batches * batch_strideA * sizeof(AB_t);
    auto     B_size_bytes   = num_batches * batch_strideB * sizeof(AB_t);
    auto     C_size_bytes   = num_batches * batch_strideC * sizeof(C_t);
    auto     hA             = new AB_t[A_size];
    auto     hB             = new AB_t[B_size];
    auto     hC             = new C_t[C_size]();

    for (int b = 0; b < num_batches; b++) {
        for (int i = 0; i < A_height; i++) {
            for (int j = 0; j < A_width; j++)
                hA[b * batch_strideA + i * lda + j] = random_value_gen<AB_t>();
        }
    }
    for (int b = 0; b < num_batches; b++) {
        for (int i = 0; i < B_height; i++) {
            for (int j = 0; j < B_width; j++)
                hB[b * batch_strideB + i * ldb + j] = random_value_gen<AB_t>();
        }
    }
    for (int b = 0; b < num_batches; b++) {
        for (int i = 0; i < C_height; i++) {
            for (int j = 0; j < C_width; j++)
                hC[b * batch_strideC + i * ldc + j] = random_value_gen<C_t>();
        }
    }

    if (print_sparse_matrix)
        print_matrix(hA, A_height, A_width, lda, num_batches, batch_strideA);
    float alpha = 1.0f;
    float beta  = 1.0f;
    //--------------------------------------------------------------------------
    // Device memory management
    AB_t* dA, *dB, *dA_compressed;
    C_t* dC, *dD;
    int    *d_valid;
    CHECK_CUDA( hipMalloc((void**) &dA, A_size_bytes) )
    CHECK_CUDA( hipMalloc((void**) &dB, B_size_bytes) )
    CHECK_CUDA( hipMalloc((void**) &dC, C_size_bytes) )
    CHECK_CUDA( hipMalloc((void**) &d_valid, sizeof(int)) )
    dD = dC;

    CHECK_CUDA( hipMemcpy(dA, hA, A_size_bytes, hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dB, hB, B_size_bytes, hipMemcpyHostToDevice) )
    CHECK_CUDA( hipMemcpy(dC, hC, C_size_bytes, hipMemcpyHostToDevice) )
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
    //--------------------------------------------------------------------------
    // SET NUM BATCHES
    CHECK_CUSPARSE( hipsparseLtMatDescSetAttribute(&handle, &matA,
                                            HIPSPARSELT_MAT_NUM_BATCHES,
                                            &num_batches, sizeof(num_batches)) )
    CHECK_CUSPARSE( hipsparseLtMatDescSetAttribute(&handle, &matB,
                                            HIPSPARSELT_MAT_NUM_BATCHES,
                                            &num_batches, sizeof(num_batches)) )
    CHECK_CUSPARSE( hipsparseLtMatDescSetAttribute(&handle, &matC,
                                            HIPSPARSELT_MAT_NUM_BATCHES,
                                            &num_batches, sizeof(num_batches)) )
    //--------------------------------------------------------------------------
    // SET BATCH STRIDE
    // if batch_strideA = 0, the matrix multiplication performs a broadcast of
    // the matrix A
    CHECK_CUSPARSE(  hipsparseLtMatDescSetAttribute(&handle, &matA,
                                                HIPSPARSELT_MAT_BATCH_STRIDE,
                                                &batch_strideA,
                                                sizeof(batch_strideA)) )
    CHECK_CUSPARSE(  hipsparseLtMatDescSetAttribute(&handle, &matB,
                                                HIPSPARSELT_MAT_BATCH_STRIDE,
                                                &batch_strideB,
                                                sizeof(batch_strideB)) )
    CHECK_CUSPARSE(  hipsparseLtMatDescSetAttribute(&handle, &matC,
                                                HIPSPARSELT_MAT_BATCH_STRIDE,
                                                &batch_strideC,
                                                sizeof(batch_strideC)) )
    //--------------------------------------------------------------------------
    // MATMUL DESCRIPTOR INITIALIZATION
    CHECK_CUSPARSE( hipsparseLtMatmulDescriptorInit(&handle, &matmul, opA, opB,
                                                   &matA, &matB, &matC, &matC,
                                                   compute_type) )

    //--------------------------------------------------------------------------
    // SET POINTER TO SPARSE MATRIX
    CHECK_CUSPARSE(hipsparseLtMatmulDescSetAttribute(&handle,
                                                    &matmul,
                                                    HIPSPARSELT_MATMUL_SPARSE_MAT_POINTER,
                                                    &dA,
                                                    sizeof(dA)));
    //--------------------------------------------------------------------------
    // ENABLE ReLU ACTIVATION FUNCTION
    int   true_value       = 1;
    float relu_upper_bound = 15.0f;
    float relu_threshold   = 1.0f;
    CHECK_CUSPARSE( hipsparseLtMatmulDescSetAttribute(&handle, &matmul,
                                            HIPSPARSELT_MATMUL_ACTIVATION_RELU,
                                            &true_value, sizeof(true_value)) )
    CHECK_CUSPARSE( hipsparseLtMatmulDescSetAttribute(
                                &handle, &matmul,
                                HIPSPARSELT_MATMUL_ACTIVATION_RELU_UPPERBOUND,
                                &(relu_upper_bound),
                                sizeof(relu_upper_bound)) )
    CHECK_CUSPARSE( hipsparseLtMatmulDescSetAttribute(
                                &handle, &matmul,
                                HIPSPARSELT_MATMUL_ACTIVATION_RELU_THRESHOLD,
                                &(relu_threshold), sizeof(relu_threshold)) )
    //--------------------------------------------------------------------------
    // SET BIAS POINTER
    void* dBias;
    auto  hBias = new Bias_t[m];
    for (int i = 0; i < m; i++)
        hBias[i] = static_cast<Bias_t>(1.0f);
    CHECK_CUDA( hipMalloc((void**) &dBias, m * sizeof(Bias_t)) )
    CHECK_CUDA( hipMemcpy(dBias, hBias, m * sizeof(Bias_t),
                           hipMemcpyHostToDevice) )
    CHECK_CUSPARSE( hipsparseLtMatmulDescSetAttribute(&handle, &matmul,
                                                HIPSPARSELT_MATMUL_BIAS_POINTER,
                                                &dBias, sizeof(dBias)) )

    //--------------------------------------------------------------------------
    // Algorithm selection, and plan initialization
    CHECK_CUSPARSE( hipsparseLtMatmulAlgSelectionInit(
                                            &handle, &alg_sel, &matmul,
                                            HIPSPARSELT_MATMUL_ALG_DEFAULT) )

    CHECK_CUSPARSE( hipsparseLtMatmulPlanInit(&handle, &plan, &matmul, &alg_sel) )
    //--------------------------------------------------------------------------
    // Split-K Mode
    int splitK, splitKBuffers;
    hipsparseLtSplitKMode_t splitKMode;
    CHECK_CUSPARSE( hipsparseLtMatmulAlgGetAttribute(&handle, &alg_sel,
                                       HIPSPARSELT_MATMUL_SPLIT_K,
                                       &splitK, sizeof(splitK)) )

    CHECK_CUSPARSE( hipsparseLtMatmulAlgGetAttribute(&handle, &alg_sel,
                                       HIPSPARSELT_MATMUL_SPLIT_K_MODE,
                                       &splitKMode, sizeof(splitKMode)) )

    CHECK_CUSPARSE( hipsparseLtMatmulAlgGetAttribute(&handle, &alg_sel,
                                       HIPSPARSELT_MATMUL_SPLIT_K_BUFFERS,
                                       &splitKBuffers, sizeof(splitKBuffers)) )
    auto mode = splitKMode == HIPSPARSELT_SPLIT_K_MODE_ONE_KERNEL
                    ? "ONE_KERNEL"  :
                (splitKMode == HIPSPARSELT_SPLIT_K_MODE_TWO_KERNELS
                    ? "TWO_KERNELS" : "invalid");
    printf("splitK=%d, splitK-mode=%s, splitK-buffers=%d\n\n",
           splitK, mode, splitKBuffers);

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

    void*  d_workspace    = nullptr;
    size_t workspace_size = 0;
    CHECK_CUSPARSE( hipsparseLtMatmulGetWorkspace(&handle, &plan,
                                                 &workspace_size) )

    CHECK_CUDA( hipMalloc((void**) &d_workspace, workspace_size) )
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Perform the matrix multiplication
    int           num_streams = 0;
    hipStream_t* streams     = nullptr;

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
    CHECK_CUDA( hipMemcpy(hA, dA, A_size_bytes, hipMemcpyDeviceToHost) )

    if (print_sparse_matrix)
        print_matrix(hA, A_height, A_width, lda, num_batches, batch_strideA);
    bool A_std_layout = (is_rowmajor != isA_transposed);
    bool B_std_layout = (is_rowmajor != isB_transposed);
    auto ReLU         = [=](float value) {
        if (value <= relu_threshold)
            return 0.0f;
        return std::min(value, relu_upper_bound);
    };

    // host computation
    C_t* hC_result = new C_t[C_size];
    for (int b = 0; b < num_batches; b++) {
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                COMPUTE_t sum  = static_cast<COMPUTE_t>(0);
                for (int k1 = 0; k1 < k; k1++) {
                    auto posA = (A_std_layout) ? i * lda + k1 : i + k1 * lda;
                    auto posB = (B_std_layout) ? k1 * ldb + j : k1 + j * ldb;
                    posA     += b * batch_strideA;
                    posB     += b * batch_strideB;
                    sum      += static_cast<COMPUTE_t>(hA[posA]) *  // [i][k]
                                static_cast<COMPUTE_t>(hB[posB]);   // [k][j]
                }
                auto posC       = (is_rowmajor) ? i * ldc + j : i + j * ldc;
                posC           += b * batch_strideC;
                auto hC_ij = static_cast<float>(hC[posC]);
                hC_result[posC] = ReLU(sum + beta * hC_ij + (float)hBias[i]);  // [i][j]
            }
        }
    }

    CHECK_CUDA( hipMemcpy(hC, dC, C_size_bytes, hipMemcpyDeviceToHost) )
    // host-device comparison
    int correct = 1;
    for (int b = 0; b < num_batches; b++) {
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < n; j++) {
                auto pos          = (is_rowmajor) ? i * ldc + j : i + j * ldc;
                pos              += b * batch_strideC;
                auto device_value = hC[pos];
                auto host_value   = hC_result[pos];
                if (device_value != host_value) {
                    // direct floating point comparison is not reliable
                    correct = 0;
                    break;
                }
            }
        }
    }
    if (correct)
        std::printf("matmul_advanced_example test PASSED\n");
    else
        std::printf("matmul_advanced_example test FAILED: wrong result\n");
    //--------------------------------------------------------------------------
    // host memory deallocation
    delete[] hA;
    delete[] hB;
    delete[] hC;
    delete[] hC_result;
    delete[] hBias;
    //--------------------------------------------------------------------------
    // device memory deallocation
    CHECK_CUDA( hipFree(dA_compressed) )
    CHECK_CUDA( hipFree(dA) )
    CHECK_CUDA( hipFree(dB) )
    CHECK_CUDA( hipFree(dC) )
    CHECK_CUDA( hipFree(dBias) )
    CHECK_CUDA( hipFree(d_valid) )
    CHECK_CUDA( hipFree(d_workspace) )
    CHECK_CUDA( hipFree(dA_compressedBuffer) )
    return EXIT_SUCCESS;
}