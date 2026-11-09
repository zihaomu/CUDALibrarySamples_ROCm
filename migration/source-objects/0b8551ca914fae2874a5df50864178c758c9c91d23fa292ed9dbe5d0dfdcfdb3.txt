#include "observe.hpp"
/*
 * SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#pragma once

#include <cassert>
#include <cstdio>
#include <stdexcept>
#include <vector>
#include <functional>
#include <cstdlib>

#include <hipblaslt.h>
#include <hip/hip_fp8.h>
#include <hip/hip_fp4.h>
#include <hip/hip_runtime_api.h>

static size_t roundoff(size_t x, size_t granul) {
    return granul * ((x + (granul - 1)) / granul);
}

template <typename T> static T ceildiv(T x, size_t divisor) {
    return (x + (divisor - 1)) / divisor;
}

template <typename T> struct StorageType {
    static constexpr size_t packing = 1;
    using type = T;
};

template <> struct StorageType<__hip_fp4_e2m1> {
    static constexpr size_t packing = 2;
    using type = __hip_fp4x2_e2m1;
};

template <typename T> constexpr size_t sizeofElements(size_t N) {
    return ceildiv(N, StorageType<T>::packing);
}

template <typename T> constexpr size_t sizeofBytes(size_t N) {
    return sizeofElements<T>(N) * sizeof(StorageType<T>::type);
}

inline void checkCudaStatus(hipError_t status) {
    if (status != hipSuccess) {
        printf("cuda API failed with status %d: %s\n", status, hipGetErrorString(status));
        throw std::logic_error("cuda API failed");
    }
}

inline void checkCublasStatus(hipblasStatus_t status) {
    if (status != HIPBLAS_STATUS_SUCCESS) {
        printf("cuBLAS API failed with status %d\n", status);
        throw std::logic_error("cuBLAS API failed");
    }
}

inline bool isPtrArray(bool ptrArrayBatch, bool groupedBatch) {
    return ptrArrayBatch || groupedBatch;
}

// Block scales used for mxfp8 and nvfp8 require a special layout:
// https://docs.nvidia.com/cuda/hipblas/index.html#d-block-scaling-factors-layout for more details.
inline size_t getScaleTensorSize(int inner, int outer, hipblasLtMatmulMatrixScale_t scaleMode) {
    if (scaleMode == HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F)
        return 1;

    if (scaleMode == HIPBLASLT_MATMUL_MATRIX_SCALE_VEC32_UE8M0 ||
        scaleMode == HIPBLASLT_MATMUL_MATRIX_SCALE_VEC16_UE4M3) {
        static const size_t S_VSCALE = scaleMode == HIPBLASLT_MATMUL_MATRIX_SCALE_VEC32_UE8M0 ? 32 : 16;
        static const size_t S_BLOCK_COLS = 32;
        static const size_t S_BLOCK_ROWS = 4;
        static const size_t S_BLOCK_INNER = 4;

        static const size_t BLOCK_ROWS = S_BLOCK_INNER * S_VSCALE;
        static const size_t BLOCK_COLS = S_BLOCK_COLS * S_BLOCK_ROWS;

        size_t s_rows = roundoff(size_t(inner), BLOCK_ROWS) / S_VSCALE;
        size_t s_cols = roundoff(size_t(outer), BLOCK_COLS);

        return s_rows * s_cols;
    }

    if (scaleMode == HIPBLASLT_MATMUL_MATRIX_SCALE_OUTER_VEC_32F) {
        return outer;
    }

    if (scaleMode == HIPBLASLT_MATMUL_MATRIX_SCALE_VEC128_32F) {
        return ceildiv(inner, 128) * outer;
    }

    if (scaleMode == HIPBLASLT_MATMUL_MATRIX_SCALE_BLK128x128_32F) {
        return roundoff(ceildiv(inner, 128), 4) * ceildiv(outer, 128);
    }

    return 0;
}

template <typename T> static bool isNarrowPrecision() {
    return std::is_same<T, __hip_fp8_e4m3_fnuz>::value || std::is_same<T, __hip_fp8_e5m2_fnuz>::value ||
           std::is_same<T, __hip_fp4_e2m1>::value;
}

template <typename InTypeAB,
          typename OutType = InTypeAB,
          typename ComputeType = OutType,
          typename ScaleType = ComputeType,
          typename DScaleType = ScaleType,
          typename InTypeC = OutType>
struct TestBench {
    using SampleRunner = std::function<void()>;

    TestBench(hipblasOperation_t transa,
              hipblasOperation_t transb,
              int m,
              int n,
              int k,
              ComputeType alpha = ComputeType{1.0f},
              ComputeType beta = ComputeType{0.0f},
              size_t workspaceSize = 1024 * 1024 * 4,
              int N = 1,
              bool ptrArrayBatch = false,
              bool forceOutOfPlace = false,
              bool groupedBatch = false)
        : TestBench(transa,
                    transb,
                    m,
                    n,
                    k,
                    alpha,
                    beta,
                    workspaceSize,
                    N,
                    ScaleType{2.0f},
                    ScaleType{0.5f},
                    ScaleType{1.0f},
                    DScaleType{1.0f},
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    ptrArrayBatch,
                    forceOutOfPlace,
                    groupedBatch) {
    }

    TestBench(hipblasOperation_t transa,
              hipblasOperation_t transb,
              int m,
              int n,
              int k,
              ComputeType alpha,
              ComputeType beta,
              size_t workspaceSize,
              int N,
              hipblasLtMatmulMatrixScale_t AScaleMode,
              hipblasLtMatmulMatrixScale_t BScaleMode,
              hipblasLtMatmulMatrixScale_t CScaleMode,
              hipblasLtMatmulMatrixScale_t DScaleMode,
              hipblasLtMatmulMatrixScale_t DOutScaleMode)
        : TestBench(transa,
                    transb,
                    m,
                    n,
                    k,
                    alpha,
                    beta,
                    workspaceSize,
                    N,
                    ScaleType{2.0f},
                    ScaleType{0.5f},
                    ScaleType{1.0f},
                    DScaleType{1.0f},
                    AScaleMode,
                    BScaleMode,
                    CScaleMode,
                    DScaleMode,
                    DOutScaleMode,
                    false,
                    false,
                    false) {
    }

    TestBench(hipblasOperation_t transa,
              hipblasOperation_t transb,
              int m,
              int n,
              int k,
              ComputeType alpha,
              ComputeType beta,
              size_t workspaceSize,
              int N,
              ScaleType Ascale,
              ScaleType Bscale,
              ScaleType Cscale,
              DScaleType Dscale,
              bool ptrArrayBatch = false,
              bool forceOutOfPlace = false,
              bool groupedBatch = false)
        : TestBench(transa,
                    transb,
                    m,
                    n,
                    k,
                    alpha,
                    beta,
                    workspaceSize,
                    N,
                    Ascale,
                    Bscale,
                    Cscale,
                    Dscale,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    HIPBLASLT_MATMUL_MATRIX_SCALE_SCALAR_32F,
                    ptrArrayBatch,
                    forceOutOfPlace,
                    groupedBatch) {
    }

    TestBench(hipblasOperation_t transa,
              hipblasOperation_t transb,
              int m,
              int n,
              int k,
              ComputeType alpha,
              ComputeType beta,
              size_t workspaceSize,
              int N,
              ScaleType Ascale,
              ScaleType Bscale,
              ScaleType Cscale,
              DScaleType Dscale,
              hipblasLtMatmulMatrixScale_t AScaleMode,
              hipblasLtMatmulMatrixScale_t BScaleMode,
              hipblasLtMatmulMatrixScale_t CScaleMode,
              hipblasLtMatmulMatrixScale_t DScaleMode,
              hipblasLtMatmulMatrixScale_t DOutScaleMode,
              bool ptrArrayBatch = false,
              bool forceOutOfPlace = false,
              bool groupedBatch = false)
        : outOfPlace(forceOutOfPlace || !std::is_same<InTypeC, OutType>::value), transa(transa), transb(transb), m(m),
          n(n), k(k), N(N), lda(transa != HIPBLAS_OP_N ? k : m), ldb(transb != HIPBLAS_OP_N ? n : k), ldc(m), ldd(m),
          alpha(alpha), beta(beta), workspaceSize(workspaceSize), Ahost(sizeofElements<InTypeAB>(m * k * N)),
          Bhost(sizeofElements<InTypeAB>(n * k * N)), Chost(sizeofElements<InTypeC>(m * n * N)),
          Dhost(outOfPlace ? sizeofElements<OutType>(m * n * N) : 0), biasHost(sizeofElements<OutType>(m * N)),
          APtrArrayHost(isPtrArray(ptrArrayBatch, groupedBatch) ? N : 0),
          BPtrArrayHost(isPtrArray(ptrArrayBatch, groupedBatch) ? N : 0),
          CPtrArrayHost(isPtrArray(ptrArrayBatch, groupedBatch) ? N : 0),
          DPtrArrayHost((isPtrArray(ptrArrayBatch, groupedBatch) && outOfPlace) ? N : 0),
          BiasPtrArrayHost(isPtrArray(ptrArrayBatch, groupedBatch) ? N : 0), AScaleMode(AScaleMode),
          BScaleMode(BScaleMode), CScaleMode(CScaleMode), DScaleMode(DScaleMode), DOutScaleMode(DOutScaleMode),
          ptrArrayBatch(ptrArrayBatch), groupedBatch(groupedBatch) {
        assert(!(ptrArrayBatch && groupedBatch));
        // Currently only fp8 supports per-tensor scaling (from second file)
        perTensorScalingEnabled =
            std::is_same<InTypeAB, __hip_fp8_e4m3_fnuz>::value || std::is_same<InTypeAB, __hip_fp8_e5m2_fnuz>::value;

        if (isNarrowPrecision<InTypeAB>()) {
            AscaleHost.resize(
                getScaleTensorSize(transa != HIPBLAS_OP_N ? k : m, transa != HIPBLAS_OP_N ? m : k, AScaleMode));
            BscaleHost.resize(
                getScaleTensorSize(transb != HIPBLAS_OP_N ? n : k, transb != HIPBLAS_OP_N ? k : n, BScaleMode));
        }

        if (isNarrowPrecision<InTypeC>()) {
            CscaleHost.resize(getScaleTensorSize(m, n, CScaleMode));
        }

        if (isNarrowPrecision<OutType>()) {
            DOutscaleHost.resize(getScaleTensorSize(m, n, DOutScaleMode));
            DscaleHost.resize(getScaleTensorSize(m, n, DScaleMode));
        }

        checkCublasStatus(hipblasLtCreate(&ltHandle));

        checkCudaStatus(hipStreamCreate(&stream));

        // For Grouped GEMM, the m, n, k are the maximum values across all batches to simplify code
        if (groupedBatch) {
            // Grouped GEMM requires m, n, k to be 16 bytes aligned, for now we limit it to 1 byte data type size or
            // larger
            constexpr size_t alignment_requirement = 16; // the smallest
            const size_t element_size = sizeofElements<InTypeAB>(1);
            const size_t alignment_factor = alignment_requirement / element_size;
            assert(element_size >= 1);
            assert(alignment_requirement % element_size == 0);
            m = roundoff(m, alignment_factor);
            n = roundoff(n, alignment_factor);
            k = roundoff(k, alignment_factor);
            Ahost.resize(sizeofElements<InTypeAB>(m * k * N));
            Bhost.resize(sizeofElements<InTypeAB>(n * k * N));
            Chost.resize(sizeofElements<InTypeC>(m * n * N));
            if (outOfPlace) {
                Dhost.resize(sizeofElements<OutType>(m * n * N));
            }
            biasHost.resize(sizeofElements<OutType>(m * N));
            // fill mArray, nArray, kArray with values up to m, n, k
            mArray.resize(N);
            nArray.resize(N);
            kArray.resize(N);
            int seed = 42;
            std::srand(seed);
            avgM = 0;
            avgN = 0;
            avgK = 0;
            for (int i = 0; i < N; ++i) {
                mArray[i] = (std::rand() % (m / alignment_factor + 1)) * alignment_factor;
                nArray[i] = (std::rand() % (n / alignment_factor + 1)) * alignment_factor;
                kArray[i] = (std::rand() % (k / alignment_factor + 1)) * alignment_factor;
                avgM += mArray[i];
                avgN += nArray[i];
                avgK += kArray[i];
            }
            avgM /= N;
            avgN /= N;
            avgK /= N;
            // Allocate mArrayDev, nArrayDev, kArrayDev and copy mArray, nArray, kArray to them
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&mArrayDev), N * sizeof(mArray[0])));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&nArrayDev), N * sizeof(nArray[0])));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&kArrayDev), N * sizeof(kArray[0])));
            // fill ldaArray, ldbArray, ldcArray and lddArray with values up to lda, ldb, ldc and ldd
            ldaArray.resize(N);
            ldbArray.resize(N);
            ldcArray.resize(N);
            lddArray.resize(N);
            for (int i = 0; i < N; ++i) {
                ldaArray[i] = transa != HIPBLAS_OP_N ? kArray[i] : mArray[i];
                ldbArray[i] = transb != HIPBLAS_OP_N ? nArray[i] : kArray[i];
                ldcArray[i] = mArray[i];
                lddArray[i] = mArray[i];
            }
            // Allocate ldaArrayDev, ldbArrayDev, ldcArrayDev and copy ldaArray, ldbArray, ldcArray to them
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&ldaArrayDev), N * sizeof(ldaArray[0])));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&ldbArrayDev), N * sizeof(ldbArray[0])));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&ldcArrayDev), N * sizeof(ldcArray[0])));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&lddArrayDev), N * sizeof(lddArray[0])));
            // Fill alphaArray, betaArray with values up to alpha, beta
            alphaArray.resize(N);
            betaArray.resize(N);
            for (int i = 0; i < N; ++i) {
                alphaArray[i] = alpha;
                betaArray[i] = beta;
            }
            // Allocate alphaArrayDev, betaArrayDev for an array of pointers that will point to alphaDataDev,
            // betaDataDev elements
            alphaArrayHost.resize(N);
            betaArrayHost.resize(N);
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&alphaArrayDev), N * sizeof(void *)));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&betaArrayDev), N * sizeof(void *)));
            for (int i = 0; i < N; ++i) {
                checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&alphaArrayHost[i]), sizeof(alphaArray[0])));
                checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&betaArrayHost[i]), sizeof(betaArray[0])));
            }

            // Print the Grouped GEMM parameters while they are available on the host
            printf("Grouped GEMM parameters: avgM = %ld, avgN = %ld, avgK = %ld\n", avgM, avgN, avgK);
            for (int i = 0; i < N; ++i) {
                printf("Group %d: m = %d, n = %d, k = %d, lda = %d, ldb = %d, ldc = %d, ldd = %d\n", i, mArray[i],
                       nArray[i], kArray[i], ldaArray[i], ldbArray[i], ldcArray[i], lddArray[i]);
            }
            printf("\n");

            // Allocate per-group scale tensors for narrow precision types
            // Note: D scaling and amax are not supported for grouped GEMM
            if (isNarrowPrecision<InTypeAB>() || perTensorScalingEnabled) {
                AscalePtrArrayHost.resize(N);
                BscalePtrArrayHost.resize(N);

                checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&AscalePtrArrayDev), N * sizeof(void *)));
                checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&BscalePtrArrayDev), N * sizeof(void *)));

                for (int i = 0; i < N; ++i) {
                    // Calculate per-group scale tensor sizes
                    int groupM = mArray[i];
                    int groupN = nArray[i];
                    int groupK = kArray[i];
                    int aInner = transa != HIPBLAS_OP_N ? groupK : groupM;
                    int aOuter = transa != HIPBLAS_OP_N ? groupM : groupK;
                    int bInner = transb != HIPBLAS_OP_N ? groupN : groupK;
                    int bOuter = transb != HIPBLAS_OP_N ? groupK : groupN;

                    size_t AscaleSize = getScaleTensorSize(aInner, aOuter, AScaleMode);
                    size_t BscaleSize = getScaleTensorSize(bInner, bOuter, BScaleMode);

                    // Ensure minimum allocation of 1 element for scalar scales
                    AscaleSize = std::max(AscaleSize, size_t(1));
                    BscaleSize = std::max(BscaleSize, size_t(1));

                    checkCudaStatus(
                        hipMalloc(reinterpret_cast<void **>(&AscalePtrArrayHost[i]), AscaleSize * sizeof(ScaleType)));
                    checkCudaStatus(
                        hipMalloc(reinterpret_cast<void **>(&BscalePtrArrayHost[i]), BscaleSize * sizeof(ScaleType)));
                }
            }
        }

        if (isPtrArray(ptrArrayBatch, groupedBatch)) {
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&APtrArrayDev), N * sizeof(void *)));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&BPtrArrayDev), N * sizeof(void *)));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&CPtrArrayDev), N * sizeof(void *)));
            if (outOfPlace)
                checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&DPtrArrayDev), N * sizeof(void *)));
            else
                DPtrArrayDev = reinterpret_cast<decltype(DPtrArrayDev)>(CPtrArrayDev);
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&BiasPtrArrayDev), N * sizeof(void *)));
            for (int i = 0; i < N; ++i) {
                checkCudaStatus(
                    hipMalloc(reinterpret_cast<void **>(&APtrArrayHost[i]), Ahost.size() * sizeof(Ahost[0]) / N));
                checkCudaStatus(
                    hipMalloc(reinterpret_cast<void **>(&BPtrArrayHost[i]), Bhost.size() * sizeof(Bhost[0]) / N));
                checkCudaStatus(
                    hipMalloc(reinterpret_cast<void **>(&CPtrArrayHost[i]), Chost.size() * sizeof(Chost[0]) / N));
                checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&BiasPtrArrayHost[i]),
                                           biasHost.size() * sizeof(biasHost[0]) / N));
                if (outOfPlace)
                    checkCudaStatus(
                        hipMalloc(reinterpret_cast<void **>(&DPtrArrayHost[i]), Dhost.size() * sizeof(Dhost[0]) / N));
            }
        } else {
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&Adev), Ahost.size() * sizeof(Ahost[0])));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&Bdev), Bhost.size() * sizeof(Bhost[0])));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&Cdev), Chost.size() * sizeof(Chost[0])));
            if (outOfPlace)
                checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&Ddev), Dhost.size() * sizeof(Dhost[0])));
            else
                Ddev = reinterpret_cast<decltype(Ddev)>(Cdev);
        }
        checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&biasDev), biasHost.size() * sizeof(biasHost[0])));
        checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&workspace), workspaceSize));

        checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&AscaleDev), AscaleHost.size() * sizeof(AscaleHost[0])));
        checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&BscaleDev), BscaleHost.size() * sizeof(BscaleHost[0])));
        checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&CscaleDev), CscaleHost.size() * sizeof(CscaleHost[0])));
        checkCudaStatus(
            hipMalloc(reinterpret_cast<void **>(&DOutscaleDev), DOutscaleHost.size() * sizeof(DOutscaleHost[0])));
        checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&DscaleDev), DscaleHost.size() * sizeof(DscaleHost[0])));
        checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&DamaxDev), sizeof(DamaxHost)));

        // Additional per-tensor scaling allocation (from second file)
        if (perTensorScalingEnabled && AscaleHost.empty()) {
            // Fallback allocation for simple per-tensor scaling when not using advanced scaling modes
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&AscaleDev), sizeof(ScaleType)));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&BscaleDev), sizeof(ScaleType)));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&CscaleDev), sizeof(ScaleType)));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&DscaleDev), sizeof(DScaleType)));
            checkCudaStatus(hipMalloc(reinterpret_cast<void **>(&DamaxDev), sizeof(ComputeType)));
        }

        fillData();
        fillScales(Ascale, Bscale, Cscale, Dscale);
    }

    ~TestBench() {
        checkCublasStatus(hipblasLtDestroy(ltHandle));

        if (groupedBatch) {
            checkCudaStatus(hipFree(mArrayDev));
            checkCudaStatus(hipFree(nArrayDev));
            checkCudaStatus(hipFree(kArrayDev));
            checkCudaStatus(hipFree(ldaArrayDev));
            checkCudaStatus(hipFree(ldbArrayDev));
            checkCudaStatus(hipFree(ldcArrayDev));
            checkCudaStatus(hipFree(lddArrayDev));
            checkCudaStatus(hipFree(alphaArrayDev));
            checkCudaStatus(hipFree(betaArrayDev));
            for (int i = 0; i < N; ++i) {
                checkCudaStatus(hipFree(alphaArrayHost[i]));
                checkCudaStatus(hipFree(betaArrayHost[i]));
            }

            // Free per-group scale tensors
            if (!AscalePtrArrayHost.empty()) {
                for (int i = 0; i < N; ++i) {
                    checkCudaStatus(hipFree(AscalePtrArrayHost[i]));
                    checkCudaStatus(hipFree(BscalePtrArrayHost[i]));
                }
                checkCudaStatus(hipFree(AscalePtrArrayDev));
                checkCudaStatus(hipFree(BscalePtrArrayDev));
            }
        }
        if (isPtrArray(ptrArrayBatch, groupedBatch)) {
            for (int i = 0; i < N; ++i) {
                checkCudaStatus(hipFree(APtrArrayHost[i]));
                checkCudaStatus(hipFree(BPtrArrayHost[i]));
                checkCudaStatus(hipFree(CPtrArrayHost[i]));
                checkCudaStatus(hipFree(BiasPtrArrayHost[i]));
                if (outOfPlace) checkCudaStatus(hipFree(DPtrArrayHost[i]));
            }
            checkCudaStatus(hipFree(APtrArrayDev));
            checkCudaStatus(hipFree(BPtrArrayDev));
            checkCudaStatus(hipFree(CPtrArrayDev));
            checkCudaStatus(hipFree(BiasPtrArrayDev));
            if (outOfPlace) checkCudaStatus(hipFree(DPtrArrayDev));
        } else {
            checkCudaStatus(hipFree(Bdev));
            checkCudaStatus(hipFree(Adev));
            checkCudaStatus(hipFree(Cdev));
            if (outOfPlace) checkCudaStatus(hipFree(Ddev));
            checkCudaStatus(hipFree(biasDev));
        }
        checkCudaStatus(hipFree(workspace));
        checkCudaStatus(hipFree(AscaleDev));
        checkCudaStatus(hipFree(BscaleDev));
        checkCudaStatus(hipFree(CscaleDev));
        checkCudaStatus(hipFree(DscaleDev));
        checkCudaStatus(hipFree(DOutscaleDev));
        checkCudaStatus(hipFree(DamaxDev));
        checkCudaStatus(hipStreamDestroy(stream));
    }

    void fillData() {
        for (size_t i = 0; i < Ahost.size(); i++) Ahost[i] = InTypeAB(i);
        for (size_t i = 0; i < Bhost.size(); i++) Bhost[i] = InTypeAB(i);
        for (size_t i = 0; i < Chost.size(); i++) Chost[i] = InTypeC(i);
        for (size_t i = 0; i < biasHost.size(); i++) biasHost[i] = OutType(i + 1);
    }

    void fillScales(ScaleType Ascale, ScaleType Bscale, ScaleType Cscale, DScaleType Dscale) {
        for (size_t i = 0; i < AscaleHost.size(); i++) AscaleHost[i] = Ascale;
        for (size_t i = 0; i < BscaleHost.size(); i++) BscaleHost[i] = Bscale;
        for (size_t i = 0; i < CscaleHost.size(); i++) CscaleHost[i] = Cscale;
        for (size_t i = 0; i < DscaleHost.size(); i++) DscaleHost[i] = Dscale;
    }

    void copyDataToDevice() {
        if (groupedBatch) {
            // Copy mArray, nArray, kArray to device
            checkCudaStatus(
                hipMemcpyAsync(mArrayDev, mArray.data(), N * sizeof(mArray[0]), hipMemcpyHostToDevice, stream));
            checkCudaStatus(
                hipMemcpyAsync(nArrayDev, nArray.data(), N * sizeof(nArray[0]), hipMemcpyHostToDevice, stream));
            checkCudaStatus(
                hipMemcpyAsync(kArrayDev, kArray.data(), N * sizeof(kArray[0]), hipMemcpyHostToDevice, stream));
            // Copy ldaArray, ldbArray, ldcArray, lddArray to device
            checkCudaStatus(
                hipMemcpyAsync(ldaArrayDev, ldaArray.data(), N * sizeof(ldaArray[0]), hipMemcpyHostToDevice, stream));
            checkCudaStatus(
                hipMemcpyAsync(ldbArrayDev, ldbArray.data(), N * sizeof(ldbArray[0]), hipMemcpyHostToDevice, stream));
            checkCudaStatus(
                hipMemcpyAsync(ldcArrayDev, ldcArray.data(), N * sizeof(ldcArray[0]), hipMemcpyHostToDevice, stream));
            checkCudaStatus(
                hipMemcpyAsync(lddArrayDev, lddArray.data(), N * sizeof(lddArray[0]), hipMemcpyHostToDevice, stream));
            // Copy alphaArray, betaArray to device
            checkCudaStatus(hipMemcpyAsync(alphaArrayDev, alphaArrayHost.data(), N * sizeof(alphaArrayHost[0]),
                                            hipMemcpyHostToDevice, stream));
            checkCudaStatus(hipMemcpyAsync(betaArrayDev, betaArrayHost.data(), N * sizeof(betaArrayHost[0]),
                                            hipMemcpyHostToDevice, stream));
            for (int i = 0; i < N; ++i) {
                checkCudaStatus(hipMemcpyAsync(alphaArrayHost[i], &alphaArray[i], sizeof(alphaArray[0]),
                                                hipMemcpyHostToDevice, stream));
                checkCudaStatus(hipMemcpyAsync(betaArrayHost[i], &betaArray[i], sizeof(betaArray[0]),
                                                hipMemcpyHostToDevice, stream));
            }

            // Copy per-group scale pointer arrays and data
            // Note: C, D scaling and amax are not supported for grouped GEMM
            if (!AscalePtrArrayHost.empty()) {
                checkCudaStatus(hipMemcpyAsync(AscalePtrArrayDev, AscalePtrArrayHost.data(),
                                                N * sizeof(AscalePtrArrayHost[0]), hipMemcpyHostToDevice, stream));
                checkCudaStatus(hipMemcpyAsync(BscalePtrArrayDev, BscalePtrArrayHost.data(),
                                                N * sizeof(BscalePtrArrayHost[0]), hipMemcpyHostToDevice, stream));

                // Copy scale data to per-group tensors
                for (int i = 0; i < N; ++i) {
                    int groupM = mArray[i];
                    int groupN = nArray[i];
                    int groupK = kArray[i];
                    int aInner = transa != HIPBLAS_OP_N ? groupK : groupM;
                    int aOuter = transa != HIPBLAS_OP_N ? groupM : groupK;
                    int bInner = transb != HIPBLAS_OP_N ? groupN : groupK;
                    int bOuter = transb != HIPBLAS_OP_N ? groupK : groupN;

                    size_t AscaleSize = std::max(getScaleTensorSize(aInner, aOuter, AScaleMode), size_t(1));
                    size_t BscaleSize = std::max(getScaleTensorSize(bInner, bOuter, BScaleMode), size_t(1));

                    // Fill scale data with values from the host arrays (or defaults)
                    ScaleType tempAscale = !AscaleHost.empty() ? AscaleHost[0] : ScaleType{2.0f};
                    ScaleType tempBscale = !BscaleHost.empty() ? BscaleHost[0] : ScaleType{0.5f};

                    // For simplicity, fill entire scale tensors with the same value
                    std::vector<ScaleType> tempAscaleData(AscaleSize, tempAscale);
                    std::vector<ScaleType> tempBscaleData(BscaleSize, tempBscale);

                    checkCudaStatus(hipMemcpyAsync(AscalePtrArrayHost[i], tempAscaleData.data(),
                                                    AscaleSize * sizeof(ScaleType), hipMemcpyHostToDevice, stream));
                    checkCudaStatus(hipMemcpyAsync(BscalePtrArrayHost[i], tempBscaleData.data(),
                                                    BscaleSize * sizeof(ScaleType), hipMemcpyHostToDevice, stream));
                }
            }
        }

        if (isPtrArray(ptrArrayBatch, groupedBatch)) {
            checkCudaStatus(hipMemcpyAsync(APtrArrayDev, APtrArrayHost.data(), N * sizeof(APtrArrayHost[0]),
                                            hipMemcpyHostToDevice, stream));
            checkCudaStatus(hipMemcpyAsync(BPtrArrayDev, BPtrArrayHost.data(), N * sizeof(BPtrArrayHost[0]),
                                            hipMemcpyHostToDevice, stream));
            checkCudaStatus(hipMemcpyAsync(CPtrArrayDev, CPtrArrayHost.data(), N * sizeof(CPtrArrayHost[0]),
                                            hipMemcpyHostToDevice, stream));
            checkCudaStatus(hipMemcpyAsync(BiasPtrArrayDev, BiasPtrArrayHost.data(), N * sizeof(BiasPtrArrayHost[0]),
                                            hipMemcpyHostToDevice, stream));
            if (outOfPlace)
                checkCudaStatus(hipMemcpyAsync(DPtrArrayDev, DPtrArrayHost.data(), N * sizeof(DPtrArrayHost[0]),
                                                hipMemcpyHostToDevice, stream));

            for (int i = 0; i < N; ++i) {
                checkCudaStatus(hipMemcpyAsync(APtrArrayHost[i], &Ahost[i * m * n],
                                                Ahost.size() / N * sizeof(Ahost[0]), hipMemcpyHostToDevice, stream));
                checkCudaStatus(hipMemcpyAsync(BPtrArrayHost[i], &Bhost[i * m * n],
                                                Bhost.size() / N * sizeof(Bhost[0]), hipMemcpyHostToDevice, stream));
                checkCudaStatus(hipMemcpyAsync(BiasPtrArrayHost[i], &biasHost[i * m],
                                                biasHost.size() / N * sizeof(biasHost[0]), hipMemcpyHostToDevice,
                                                stream));
            }
        } else {
            checkCudaStatus(
                hipMemcpyAsync(Adev, Ahost.data(), Ahost.size() * sizeof(Ahost[0]), hipMemcpyHostToDevice, stream));
            checkCudaStatus(
                hipMemcpyAsync(Bdev, Bhost.data(), Bhost.size() * sizeof(Bhost[0]), hipMemcpyHostToDevice, stream));
            checkCudaStatus(hipMemcpyAsync(biasDev, biasHost.data(), biasHost.size() * sizeof(biasHost[0]),
                                            hipMemcpyHostToDevice, stream));
        }
        checkCudaStatus(hipMemcpyAsync(AscaleDev, AscaleHost.data(), AscaleHost.size() * sizeof(AscaleHost[0]),
                                        hipMemcpyHostToDevice, stream));
        checkCudaStatus(hipMemcpyAsync(BscaleDev, BscaleHost.data(), BscaleHost.size() * sizeof(BscaleHost[0]),
                                        hipMemcpyHostToDevice, stream));
        checkCudaStatus(hipMemcpyAsync(CscaleDev, CscaleHost.data(), CscaleHost.size() * sizeof(CscaleHost[0]),
                                        hipMemcpyHostToDevice, stream));
        checkCudaStatus(hipMemcpyAsync(DscaleDev, DscaleHost.data(), DscaleHost.size() * sizeof(DscaleHost[0]),
                                        hipMemcpyHostToDevice, stream));
        checkCudaStatus(hipMemcpyAsync(DamaxDev, &DamaxHost, sizeof(DamaxHost), hipMemcpyHostToDevice, stream));

        // Additional per-tensor scaling copy logic (from second file)
        if (perTensorScalingEnabled && AscaleHost.empty()) {
            // For simple per-tensor scaling, copy individual scale values
            ScaleType tempAscale = ScaleType{2.0f}, tempBscale = ScaleType{0.5f}, tempCscale = ScaleType{1.0f};
            DScaleType tempDscale = DScaleType{1.0f};
            ComputeType tempDamax = ComputeType{0.0f};
            checkCudaStatus(hipMemcpyAsync(AscaleDev, &tempAscale, sizeof(tempAscale), hipMemcpyHostToDevice));
            checkCudaStatus(hipMemcpyAsync(BscaleDev, &tempBscale, sizeof(tempBscale), hipMemcpyHostToDevice));
            checkCudaStatus(hipMemcpyAsync(CscaleDev, &tempCscale, sizeof(tempCscale), hipMemcpyHostToDevice));
            checkCudaStatus(hipMemcpyAsync(DscaleDev, &tempDscale, sizeof(tempDscale), hipMemcpyHostToDevice));
            checkCudaStatus(hipMemcpyAsync(DamaxDev, &tempDamax, sizeof(tempDamax), hipMemcpyHostToDevice));
        }
    }

    void copyDataFromDevice() {
        if (isPtrArray(ptrArrayBatch, groupedBatch)) {
            for (int i = 0; i < N; ++i) {
                if (outOfPlace)
                    checkCudaStatus(hipMemcpyAsync(&Dhost[i * m * n], DPtrArrayHost[i],
                                                    Dhost.size() / N * sizeof(Dhost[0]), hipMemcpyDeviceToHost,
                                                    stream));
                else
                    checkCudaStatus(hipMemcpyAsync(&Chost[i * m * n], CPtrArrayHost[i],
                                                    Chost.size() / N * sizeof(Chost[0]), hipMemcpyDeviceToHost,
                                                    stream));
            }
        } else {
            if (outOfPlace)
                checkCudaStatus(hipMemcpyAsync(Dhost.data(), Ddev, Dhost.size() * sizeof(Dhost[0]),
                                                hipMemcpyDeviceToHost, stream));
            else
                checkCudaStatus(hipMemcpyAsync(Chost.data(), Cdev, Chost.size() * sizeof(Chost[0]),
                                                hipMemcpyDeviceToHost, stream));
        }

        checkCudaStatus(hipMemcpyAsync(DOutscaleHost.data(), DOutscaleDev,
                                        DOutscaleHost.size() * sizeof(DOutscaleHost[0]), hipMemcpyDeviceToHost,
                                        stream));
    }

    void streamSynchronize() {
        checkCudaStatus(hipStreamSynchronize(stream));
    }

    void run(const SampleRunner &runSample) {
        copyDataToDevice();

        runSample();

        copyDataFromDevice();
        streamSynchronize();
        // MIGRATION_OBSERVE_LT: output only, after synchronization.
        migration_observer::emit("A",Ahost.data(),Ahost.size());
        migration_observer::emit("B",Bhost.data(),Bhost.size());
        migration_observer::emit("C",Chost.data(),Chost.size());
        if(outOfPlace)migration_observer::emit("D",Dhost.data(),Dhost.size());
    }

    bool outOfPlace;
    bool ptrArrayBatch;
    bool perTensorScalingEnabled;
    hipblasOperation_t transa, transb;
    int m, n, k, N;
    int lda, ldb, ldc, ldd;
    ComputeType alpha, beta;

    hipStream_t stream;
    hipblasLtHandle_t ltHandle;

    void *workspace;
    size_t workspaceSize;

    std::vector<typename StorageType<InTypeAB>::type> Ahost, Bhost;
    std::vector<typename StorageType<InTypeC>::type> Chost;
    std::vector<typename StorageType<OutType>::type> Dhost, biasHost;

    typename StorageType<InTypeAB>::type *Adev, *Bdev;
    typename StorageType<InTypeC>::type *Cdev;
    typename StorageType<OutType>::type *Ddev, *biasDev;

    std::vector<typename StorageType<InTypeAB>::type *> APtrArrayHost, BPtrArrayHost;
    std::vector<typename StorageType<InTypeC>::type *> CPtrArrayHost;
    std::vector<typename StorageType<OutType>::type *> DPtrArrayHost;
    std::vector<typename StorageType<OutType>::type *> BiasPtrArrayHost;

    typename StorageType<InTypeAB>::type **APtrArrayDev, **BPtrArrayDev;
    typename StorageType<InTypeC>::type **CPtrArrayDev;
    typename StorageType<OutType>::type **DPtrArrayDev;
    typename StorageType<OutType>::type **BiasPtrArrayDev;

    hipblasLtMatmulMatrixScale_t AScaleMode, BScaleMode, CScaleMode, DScaleMode, DOutScaleMode;

    std::vector<ScaleType> AscaleHost, BscaleHost, CscaleHost, DOutscaleHost;
    std::vector<DScaleType> DscaleHost;

    ScaleType *AscaleDev, *BscaleDev, *CscaleDev, *DOutscaleDev;
    DScaleType *DscaleDev;

    ComputeType DamaxHost;
    ComputeType *DamaxDev;

    // Grouped GEMM
    bool groupedBatch;
    std::vector<int> mArray;
    std::vector<int> nArray;
    std::vector<int> kArray;
    int64_t avgM, avgN, avgK;
    void *mArrayDev, *nArrayDev, *kArrayDev;
    std::vector<int> ldaArray;
    std::vector<int> ldbArray;
    std::vector<int> ldcArray;
    std::vector<int> lddArray;
    void *ldaArrayDev, *ldbArrayDev, *ldcArrayDev, *lddArrayDev;
    std::vector<ComputeType> alphaArray;
    std::vector<ComputeType> betaArray;
    typename StorageType<ComputeType>::type **alphaArrayDev, **betaArrayDev;
    std::vector<typename StorageType<ComputeType>::type *> alphaArrayHost, betaArrayHost;

    // Grouped GEMM scale pointer arrays (for narrow precision types)
    // Note: C, D scaling and amax are not supported for grouped GEMM
    std::vector<ScaleType *> AscalePtrArrayHost, BscalePtrArrayHost;
    ScaleType **AscalePtrArrayDev, **BscalePtrArrayDev;
};

template <> inline void TestBench<__half, __half, float>::fillData() {
    for (size_t i = 0; i < Ahost.size(); i++) Ahost[i] = __float2half_rn(float(i));
    for (size_t i = 0; i < Bhost.size(); i++) Bhost[i] = __float2half_rn(float(i));
    for (size_t i = 0; i < Chost.size(); i++) Chost[i] = __float2half_rn(float(i));
    for (size_t i = 0; i < biasHost.size(); i++) biasHost[i] = __float2half_rn(float(i + 1));
}

template <> inline void TestBench<__half, __half, hipComplex>::fillData() {
    for (size_t i = 0; i < Ahost.size(); i++) Ahost[i] = __float2half_rn(i / 100.f);
    for (size_t i = 0; i < Bhost.size(); i++) Bhost[i] = __float2half_rn(i / 100.f);
    for (size_t i = 0; i < Chost.size(); i++) Chost[i] = __float2half_rn(i / 100.f);
    for (size_t i = 0; i < biasHost.size(); i++) biasHost[i] = __float2half_rn(float(i + 1));
}

template <>
inline void TestBench<__hip_fp4_e2m1, __hip_fp4_e2m1, float, __hip_fp8_e4m3_fnuz, float, __hip_bfloat16>::fillData() {
    for (size_t i = 0; i < Ahost.size(); i++) Ahost[i] = __hip_fp4x2_e2m1{float2{float(i % 5), float(i % 5) + 1}};
    for (size_t i = 0; i < Bhost.size(); i++) Bhost[i] = __hip_fp4x2_e2m1{float2{float(i % 5), float(i % 5) + 1}};
    for (size_t i = 0; i < Chost.size(); i++) Chost[i] = __hip_bfloat16(float(i % 5));
    for (size_t i = 0; i < biasHost.size(); i++) biasHost[i] = __hip_fp4x2_e2m1{float2{float(i % 5), float(i % 5) + 1}};
}

template <>
inline void TestBench<__hip_fp4_e2m1, __hip_bfloat16, float, __hip_fp8_e4m3_fnuz, float, __hip_bfloat16>::fillData() {
    for (size_t i = 0; i < Ahost.size(); i++) Ahost[i] = __hip_fp4x2_e2m1{float2{float(i % 5), float(i % 5) + 1}};
    for (size_t i = 0; i < Bhost.size(); i++) Bhost[i] = __hip_fp4x2_e2m1{float2{float(i % 5), float(i % 5) + 1}};
    for (size_t i = 0; i < Chost.size(); i++) Chost[i] = __hip_bfloat16(float(i % 5));
    for (size_t i = 0; i < biasHost.size(); i++) biasHost[i] = __hip_bfloat16(float(i % 5) + 1);
}

#ifdef MIGRATION_CUBLASLT_TILE_NAME_API_AVAILABLE
const char *tileToString(cublasLtMatmulTile_t tile);
#endif
