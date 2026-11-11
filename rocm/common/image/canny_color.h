// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <hip/hip_runtime.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
uint32_t rocm_image_canny_color_abi_version(void);
hipError_t rocm_image_canny_color_workspace_size(int width,int height,uint64_t*bytes);
hipError_t rocm_image_canny_color(const uint8_t*source,uint64_t source_bytes,uint64_t source_pitch,
 int width,int height,int low,int high,uint8_t*output,uint64_t output_bytes,uint64_t output_pitch,
 void*workspace,uint64_t workspace_bytes,hipStream_t stream);
#ifdef __cplusplus
}
#endif
