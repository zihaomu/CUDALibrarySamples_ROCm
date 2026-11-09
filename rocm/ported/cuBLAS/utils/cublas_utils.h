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
#pragma once

#include <cmath>
#include <functional>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

#include <hip/hip_complex.h>
#include <hipblas.h>
#include <hip/hip_runtime_api.h>
#include <hip/library_types.h>

// CUDA API error checking
#define CUDA_CHECK(err)                                                                            \
    do {                                                                                           \
        hipError_t err_ = (err);                                                                  \
        if (err_ != hipSuccess) {                                                                 \
            std::printf("CUDA error %d at %s:%d\n", err_, __FILE__, __LINE__);                     \
            throw std::runtime_error("CUDA error");                                                \
        }                                                                                          \
    } while (0)

// hipblas API error checking
#define CUBLAS_CHECK(err)                                                                          \
    do {                                                                                           \
        hipblasStatus_t err_ = (err);                                                               \
        if (err_ != HIPBLAS_STATUS_SUCCESS) {                                                       \
            std::printf("hipblas error %d at %s:%d\n", err_, __FILE__, __LINE__);                   \
            throw std::runtime_error("hipblas error");                                              \
        }                                                                                          \
    } while (0)

// memory alignment
#define ALIGN_TO(A, B) (((A + B - 1) / B) * B)

// device memory pitch alignment
static const size_t device_alignment = 32;

// type traits
template <typename T> struct traits;

template <> struct traits<float> {
    // scalar type
    typedef float T;
    typedef T S;

    static constexpr T zero = 0.f;
    static constexpr hipDataType cuda_data_type = HIP_R_32F;

    inline static S abs(T val) { return fabs(val); }

    template <typename RNG> inline static T rand(RNG &gen) { return (S)gen(); }

    inline static T add(T a, T b) { return a + b; }

    inline static T mul(T v, double f) { return v * f; }
};

template <> struct traits<double> {
    // scalar type
    typedef double T;
    typedef T S;

    static constexpr T zero = 0.;
    static constexpr hipDataType cuda_data_type = HIP_R_64F;

    inline static S abs(T val) { return fabs(val); }

    template <typename RNG> inline static T rand(RNG &gen) { return (S)gen(); }

    inline static T add(T a, T b) { return a + b; }

    inline static T mul(T v, double f) { return v * f; }
};

template <> struct traits<hipFloatComplex> {
    // scalar type
    typedef float S;
    typedef hipFloatComplex T;

    static constexpr T zero = {0.f, 0.f};
    static constexpr hipDataType cuda_data_type = HIP_C_32F;

    inline static S abs(T val) { return hipCabsf(val); }

    template <typename RNG> inline static T rand(RNG &gen) {
        return make_hipFloatComplex((S)gen(), (S)gen());
    }

    inline static T add(T a, T b) { return hipCaddf(a, b); }
    inline static T add(T a, S b) { return hipCaddf(a, make_hipFloatComplex(b, 0.f)); }

    inline static T mul(T v, double f) { return make_hipFloatComplex(v.x * f, v.y * f); }
};

template <> struct traits<hipDoubleComplex> {
    // scalar type
    typedef double S;
    typedef hipDoubleComplex T;

    static constexpr T zero = {0., 0.};
    static constexpr hipDataType cuda_data_type = HIP_C_64F;

    inline static S abs(T val) { return hipCabs(val); }

    template <typename RNG> inline static T rand(RNG &gen) {
        return make_hipDoubleComplex((S)gen(), (S)gen());
    }

    inline static T add(T a, T b) { return hipCadd(a, b); }
    inline static T add(T a, S b) { return hipCadd(a, make_hipDoubleComplex(b, 0.)); }

    inline static T mul(T v, double f) { return make_hipDoubleComplex(v.x * f, v.y * f); }
};

template <typename T> void print_matrix(const int &m, const int &n, const T *A, const int &lda);

template <> void print_matrix(const int &m, const int &n, const float *A, const int &lda) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            std::printf("%0.2f ", A[j * lda + i]);
        }
        std::printf("\n");
    }
}

template <> void print_matrix(const int &m, const int &n, const double *A, const int &lda) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            std::printf("%0.2f ", A[j * lda + i]);
        }
        std::printf("\n");
    }
}

template <> void print_matrix(const int &m, const int &n, const hipComplex *A, const int &lda) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            std::printf("%0.2f + %0.2fj ", A[j * lda + i].x, A[j * lda + i].y);
        }
        std::printf("\n");
    }
}

template <>
void print_matrix(const int &m, const int &n, const hipDoubleComplex *A, const int &lda) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            std::printf("%0.2f + %0.2fj ", A[j * lda + i].x, A[j * lda + i].y);
        }
        std::printf("\n");
    }
}

template <typename T> void print_packed_matrix(hipblasFillMode_t uplo, const int &n, const T *A);

template <> void print_packed_matrix(hipblasFillMode_t uplo, const int &n, const float *A) {
    size_t off = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if ((uplo == HIPBLAS_FILL_MODE_UPPER && j >= i) ||
                (uplo == HIPBLAS_FILL_MODE_LOWER && j <= i)) {
                std::printf("%6.2f ", A[off++]);
            } else if (uplo == HIPBLAS_FILL_MODE_UPPER) {
                std::printf("       ");
            }
        }
        std::printf("\n");
    }
}

template <> void print_packed_matrix(hipblasFillMode_t uplo, const int &n, const double *A) {
    size_t off = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if ((uplo == HIPBLAS_FILL_MODE_UPPER && j >= i) ||
                (uplo == HIPBLAS_FILL_MODE_LOWER && j <= i)) {
                std::printf("%6.2f ", A[off++]);
            } else if (uplo == HIPBLAS_FILL_MODE_UPPER) {
                std::printf("       ");
            }
        }
        std::printf("\n");
    }
}

template <> void print_packed_matrix(hipblasFillMode_t uplo, const int &n, const hipComplex *A) {
    size_t off = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if ((uplo == HIPBLAS_FILL_MODE_UPPER && j >= i) ||
                (uplo == HIPBLAS_FILL_MODE_LOWER && j <= i)) {
                std::printf("%6.2f + %6.2fj ", A[off].x, A[off].y);
                off++;
            } else if (uplo == HIPBLAS_FILL_MODE_UPPER) {
                std::printf("                 ");
            }
        }
        std::printf("\n");
    }
}

template <> void print_packed_matrix(hipblasFillMode_t uplo, const int &n, const hipDoubleComplex *A) {
    size_t off = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if ((uplo == HIPBLAS_FILL_MODE_UPPER && j >= i) ||
                (uplo == HIPBLAS_FILL_MODE_LOWER && j <= i)) {
                std::printf("%6.2f + %6.2fj ", A[off].x, A[off].y);
                off++;
            } else if (uplo == HIPBLAS_FILL_MODE_UPPER) {
                std::printf("                 ");
            }
        }
        std::printf("\n");
    }
}

template <typename T> void print_vector(const int &m, const T *A);

template <> void print_vector(const int &m, const float *A) {
    for (int i = 0; i < m; i++) {
        std::printf("%0.2f ", A[i]);
    }
    std::printf("\n");
}

template <> void print_vector(const int &m, const double *A) {
    for (int i = 0; i < m; i++) {
        std::printf("%0.2f ", A[i]);
    }
    std::printf("\n");
}

template <> void print_vector(const int &m, const hipComplex *A) {
    for (int i = 0; i < m; i++) {
        std::printf("%0.2f + %0.2fj ", A[i].x, A[i].y);
    }
    std::printf("\n");
}

template <> void print_vector(const int &m, const hipDoubleComplex *A) {
    for (int i = 0; i < m; i++) {
        std::printf("%0.2f + %0.2fj ", A[i].x, A[i].y);
    }
    std::printf("\n");
}

template <typename T> void generate_random_matrix(int m, int n, T **A, int *lda) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<typename traits<T>::S> dis(-1.0, 1.0);
    auto rand_gen = std::bind(dis, gen);

    *lda = n;

    size_t matrix_mem_size = static_cast<size_t>(*lda * m * sizeof(T));
    // suppress gcc 7 size warning
    if (matrix_mem_size <= PTRDIFF_MAX)
        *A = (T *)malloc(matrix_mem_size);
    else
        throw std::runtime_error("Memory allocation size is too large");

    if (*A == NULL)
        throw std::runtime_error("Unable to allocate host matrix");

    // random matrix and accumulate row sums
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n; ++j) {
            T *A_row = (*A) + *lda * i;
            A_row[j] = traits<T>::rand(rand_gen);
        }
    }
}

// Makes a diagonally dominant matrix A of size mxn and leading dimension lda
template <typename T> void make_diag_dominant_matrix(int m, int n, T *A, int lda) {
    for (int i = 0; i < std::min(m, n); ++i) {
        T *A_row = A + lda * i;
        auto row_sum = traits<typename traits<T>::S>::zero;
        for (int j = 0; j < n; ++j) {
            row_sum += traits<T>::abs(A_row[j]);
        }
        A_row[i] = traits<T>::add(A_row[i], row_sum);
    }
}

// Returns cudaDataType value as defined in library_types.h for the string
// containing type name
hipDataType get_cuda_library_type(std::string type_string) {
    if (type_string.compare("HIP_R_16F") == 0)
        return HIP_R_16F;
    else if (type_string.compare("HIP_C_16F") == 0)
        return HIP_C_16F;
    else if (type_string.compare("HIP_R_32F") == 0)
        return HIP_R_32F;
    else if (type_string.compare("HIP_C_32F") == 0)
        return HIP_C_32F;
    else if (type_string.compare("HIP_R_64F") == 0)
        return HIP_R_64F;
    else if (type_string.compare("HIP_C_64F") == 0)
        return HIP_C_64F;
    else if (type_string.compare("HIP_R_8I") == 0)
        return HIP_R_8I;
    else if (type_string.compare("HIP_C_8I") == 0)
        return HIP_C_8I;
    else if (type_string.compare("HIP_R_8U") == 0)
        return HIP_R_8U;
    else if (type_string.compare("HIP_C_8U") == 0)
        return HIP_C_8U;
    else if (type_string.compare("HIP_R_32I") == 0)
        return HIP_R_32I;
    else if (type_string.compare("HIP_C_32I") == 0)
        return HIP_C_32I;
    else if (type_string.compare("HIP_R_32U") == 0)
        return HIP_R_32U;
    else if (type_string.compare("HIP_C_32U") == 0)
        return HIP_C_32U;
    else
        throw std::runtime_error("Unknown CUDA datatype");
}

static inline int ceildiv(int a, int b) {
    return (a + b - 1) / b;
}

// This function provides the workspace size for a given problem shape and emulation configuration
#if defined(MIGRATION_CUBLAS_EMULATION_API_AVAILABLE)
size_t getFixedPointWorkspaceSizeInBytes(int m, int n, int k, int batchCount, bool isComplex,
                                        cudaEmulationMantissaControl mantissaControl, int maxMantissaBitCount) {

    constexpr double MULTIPLIER = 1.25;

    int mult = isComplex ? 2 : 1;
    int numSlices = ceildiv(maxMantissaBitCount + 1, 8);

    int padded_m = ceildiv(m, 1024) * 1024;
    int padded_n = ceildiv(n, 1024) * 1024;
    int padded_k = ceildiv(k, 128) * 128;
    int num_blocks_k = ceildiv(k, 64);

    size_t gemm_workspace = sizeof(int8_t) *
        ((size_t)padded_m * padded_k + (size_t)padded_n * padded_k) * mult * numSlices;

    gemm_workspace += sizeof(int32_t) * ((size_t)padded_m + padded_n) * mult;
    if (isComplex) {
        gemm_workspace += sizeof(double) * (size_t)m * n * mult * mult;
    }

    size_t adp_workspace = 0;
    if (mantissaControl == CUDA_EMULATION_MANTISSA_CONTROL_DYNAMIC) {
        adp_workspace = sizeof(int32_t) * ((size_t)m * num_blocks_k + (size_t)n * num_blocks_k +
                        (size_t)m * n) * mult;
    }

    constexpr size_t CONSTANT_SIZE = 128 * 1024 * 1024;
    return (size_t)(std::max(gemm_workspace, adp_workspace) * batchCount * MULTIPLIER) + CONSTANT_SIZE;
}


#endif // Isolate CUDA-only emulation helper from conventional BLAS ports.
