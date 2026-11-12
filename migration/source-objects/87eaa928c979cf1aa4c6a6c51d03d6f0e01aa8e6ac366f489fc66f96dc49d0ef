// SPDX-License-Identifier: Apache-2.0
// Isolated one-level JPEG2000 reversible inverse 5/3 and inverse RCT stage.
#pragma once
#include <hip/hip_runtime.h>

namespace image_j2k_i53 {
__device__ inline int floor_power_two(int value, int shift) {
    const long long divisor = 1LL << shift;
    const long long x = value;
    return int(x >= 0 ? x / divisor : -((-x + divisor - 1) / divisor));
}

__device__ inline void inverse_line(const int* packed, int stride, int* output,
                                    int output_stride, int n) {
    int even[64], odd[64];
    int nl = (n + 1) / 2, nh = n / 2;
    if (nh == 0) { output[0] = packed[0]; return; }
    for (int i = 0; i < nl; ++i) {
        int left = packed[(nl + (i ? i - 1 : 0)) * stride];
        int right = packed[(nl + (i < nh ? i : nh - 1)) * stride];
        even[i] = packed[i * stride] - floor_power_two(left + right + 2, 2);
    }
    for (int i = 0; i < nh; ++i) {
        int right = even[i + 1 < nl ? i + 1 : nl - 1];
        odd[i] = packed[(nl + i) * stride] + floor_power_two(even[i] + right, 1);
    }
    for (int i = 0; i < n; ++i)
        output[i * output_stride] = i & 1 ? odd[i / 2] : even[i / 2];
}

__global__ void inverse_vertical(const int* coefficients, int* work,
                                 int width, int height) {
    int x = blockIdx.x * blockDim.x + threadIdx.x, component = blockIdx.y;
    if (x >= width) return;
    size_t offset = size_t(component) * width * height + x;
    inverse_line(coefficients + offset, width, work + offset, width, height);
}

__global__ void inverse_horizontal(const int* work, int* spatial,
                                   int width, int height) {
    int y = blockIdx.x * blockDim.x + threadIdx.x, component = blockIdx.y;
    if (y >= height) return;
    size_t offset = size_t(component) * width * height + size_t(y) * width;
    inverse_line(work + offset, 1, spatial + offset, 1, width);
}

__global__ void inverse_rct_rgb(const int* spatial, unsigned char* rgb,
                                int pixels) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= pixels) return;
    int y = spatial[i], cb = spatial[pixels + i], cr = spatial[2 * pixels + i];
    int g = y - floor_power_two(cb + cr, 2), r = cr + g, b = cb + g;
    rgb[3 * i] = static_cast<unsigned char>(r);
    rgb[3 * i + 1] = static_cast<unsigned char>(g);
    rgb[3 * i + 2] = static_cast<unsigned char>(b);
}
} // namespace image_j2k_i53
