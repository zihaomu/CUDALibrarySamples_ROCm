// SPDX-License-Identifier: Apache-2.0
// Checked JPEG entropy prefixes. Callers must inspect status before packing.
#pragma once
#include <hip/hip_runtime.h>
#include <cstdint>
#include <stdexcept>

namespace image_jpeg_checked_prefix {
constexpr unsigned tile_size = 256;
enum : unsigned { invalid_length = 1, offset_overflow = 2 };
struct Result { unsigned total; unsigned errors; };

template<class T, bool Stuff>
__global__ void tiles(const T* input, unsigned* offsets, unsigned* sums,
                      Result* result, unsigned count) {
    __shared__ unsigned values[tile_size], temporary[tile_size];
    const unsigned lane = threadIdx.x;
    const unsigned index = blockIdx.x * tile_size + lane;
    unsigned value = 0;
    if (index < count) {
        if constexpr (Stuff) value = input[index] == 0xff;
        else {
            value = input[index];
            if (!value || value > 4096) atomicOr(&result->errors, invalid_length);
        }
    }
    values[lane] = value;
    __syncthreads();
    for (unsigned distance = 1; distance < tile_size; distance <<= 1) {
        temporary[lane] = values[lane] + (lane >= distance ? values[lane-distance] : 0);
        __syncthreads();
        values[lane] = temporary[lane];
        __syncthreads();
    }
    if (index < count) offsets[index] = values[lane] - value;
    if (lane == tile_size - 1) sums[blockIdx.x] = values[lane];
}

template<bool Stuff>
__global__ void bases(const unsigned* sums, unsigned* tile_bases, Result* result,
                      unsigned tile_count, unsigned count) {
    if (threadIdx.x || blockIdx.x) return;
    uint64_t sum = 0;
    for (unsigned i = 0; i < tile_count; ++i) {
        tile_bases[i] = static_cast<unsigned>(sum);
        sum += sums[i];
    }
    if constexpr (Stuff) sum += count;
    // Reserve seven bits for the rounded byte count used by the packer.
    const uint64_t limit = Stuff ? uint64_t(UINT32_MAX) : uint64_t(UINT32_MAX) - 7;
    if (sum > limit) {
        atomicOr(&result->errors, offset_overflow);
        result->total = 0;
    } else result->total = static_cast<unsigned>(sum);
}

template<bool Stuff>
__global__ void finish(unsigned* offsets, const unsigned* tile_bases,
                       const Result* result, unsigned count) {
    const unsigned index = blockIdx.x * tile_size + threadIdx.x;
    if (index < count && !result->errors)
        offsets[index] += tile_bases[blockIdx.x] + (Stuff ? index : 0);
}

inline unsigned tile_count(unsigned count) {
    return count / tile_size + (count % tile_size != 0);
}

template<class T, bool Stuff>
inline hipError_t launch(const T* input, unsigned* offsets, unsigned* sums,
                         unsigned* tile_bases, Result* result, unsigned count,
                         hipStream_t stream = nullptr) {
    if (!count || !input || !offsets || !sums || !tile_bases || !result)
        return hipErrorInvalidValue;
    auto error = hipMemsetAsync(result, 0, sizeof(Result), stream);
    if (error != hipSuccess) return error;
    const auto n = tile_count(count);
    tiles<T, Stuff><<<n, tile_size, 0, stream>>>(input, offsets, sums, result, count);
    if ((error = hipGetLastError()) != hipSuccess) return error;
    bases<Stuff><<<1, 1, 0, stream>>>(sums, tile_bases, result, n, count);
    if ((error = hipGetLastError()) != hipSuccess) return error;
    finish<Stuff><<<n, tile_size, 0, stream>>>(offsets, tile_bases, result, count);
    return hipGetLastError();
}
} // namespace image_jpeg_checked_prefix
