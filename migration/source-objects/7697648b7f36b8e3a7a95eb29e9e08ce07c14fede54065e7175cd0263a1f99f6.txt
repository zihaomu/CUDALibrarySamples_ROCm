// SPDX-License-Identifier: Apache-2.0
// Three-stage tiled prefix prototype for JPEG block bits and FF byte stuffing.
#pragma once
#include <hip/hip_runtime.h>

namespace image_jpeg_parallel_prefix {
constexpr unsigned TILE = 256;

template<class T, bool STUFF>
__global__ void scan_tile(const T* input, unsigned* local, unsigned* sums, unsigned count) {
    __shared__ unsigned a[TILE], b[TILE];
    unsigned lane = threadIdx.x, index = blockIdx.x * TILE + lane;
    unsigned value = index < count ? (STUFF ? unsigned(input[index] == T(0xff)) : unsigned(input[index])) : 0;
    a[lane] = value;
    __syncthreads();
    for (unsigned step = 1; step < TILE; step <<= 1) {
        b[lane] = a[lane] + (lane >= step ? a[lane-step] : 0);
        __syncthreads();
        a[lane] = b[lane];
        __syncthreads();
    }
    if (index < count) local[index] = a[lane] - value;
    if (lane == TILE - 1) sums[blockIdx.x] = a[lane];
}

template<bool STUFF>
__global__ void scan_sums(const unsigned* sums, unsigned* bases, unsigned* total,
                          unsigned tiles, unsigned count) {
    if (threadIdx.x || blockIdx.x) return;
    unsigned sum = 0;
    for (unsigned tile = 0; tile < tiles; ++tile) {
        bases[tile] = sum;
        sum += sums[tile];
    }
    total[0] = STUFF ? count + sum : sum;
}

template<bool STUFF>
__global__ void add_bases(unsigned* output, const unsigned* bases, unsigned count) {
    unsigned index = blockIdx.x * TILE + threadIdx.x;
    if (index < count) output[index] += bases[blockIdx.x] + (STUFF ? index : 0);
}

template<class T, bool STUFF>
inline void launch(const T* input, unsigned* output, unsigned* sums,
                   unsigned* bases, unsigned* total, unsigned count,
                   hipStream_t stream = nullptr) {
    if (!count) return;
    unsigned tiles = (count + TILE - 1) / TILE;
    scan_tile<T, STUFF><<<tiles, TILE, 0, stream>>>(input, output, sums, count);
    scan_sums<STUFF><<<1, 1, 0, stream>>>(sums, bases, total, tiles, count);
    add_bases<STUFF><<<tiles, TILE, 0, stream>>>(output, bases, count);
}
} // namespace image_jpeg_parallel_prefix
