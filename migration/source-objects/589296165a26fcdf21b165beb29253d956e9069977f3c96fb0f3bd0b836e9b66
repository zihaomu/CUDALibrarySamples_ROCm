// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <hip/hip_runtime_api.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
// All image pointers refer to contiguous width*height device storage.
// Null optional outputs skip that product. At least segments and labels are required.
// This call synchronizes stream before releasing its private GPU workspace.
hipError_t rocm_image_watershed8(const uint8_t*input,uint8_t*segments,
    uint32_t*labels,uint32_t*compact,uint8_t*boundaries,uint8_t*contrast,
    int width,int height,hipStream_t stream);
#ifdef __cplusplus
}
#endif
