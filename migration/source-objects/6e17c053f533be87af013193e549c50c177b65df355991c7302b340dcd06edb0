// SPDX-License-Identifier: Apache-2.0
#ifndef ROCM_IMAGE_BENCHMARK_H
#define ROCM_IMAGE_BENCHMARK_H
#include <stdint.h>
#include <hip/hip_runtime_api.h>
#ifdef __cplusplus
extern "C" {
#endif
// Tightly packed 8-bit image operations. Device buffers must be disjoint and
// owned by the current device until work on stream completes.
hipError_t rocm_image_benchmark_gauss5(const uint8_t* source,uint8_t* output,int width,int height,hipStream_t stream);
hipError_t rocm_image_benchmark_resize_half(const uint8_t* source,uint8_t* output,int width,int height,hipStream_t stream);
hipError_t rocm_image_benchmark_rgb_gray(const uint8_t* source,uint8_t* output,int width,int height,hipStream_t stream);
#ifdef __cplusplus
}
#endif
#endif
