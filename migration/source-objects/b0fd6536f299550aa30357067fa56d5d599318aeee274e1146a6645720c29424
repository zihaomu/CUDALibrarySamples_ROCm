// SPDX-License-Identifier: Apache-2.0
#ifndef ROCM_IMAGE_CANNY_H
#define ROCM_IMAGE_CANNY_H
#include "canny_stages.h"
#ifdef __cplusplus
extern "C" {
#endif
uint32_t rocm_image_canny_abi_version(void);
hipError_t rocm_image_canny_workspace_size(int width,int height,uint64_t* bytes);
// Device-owned, disjoint spans. Caller retains all buffers until stream completion.
// C1/C3 Sobel/L2/NMS followed by the documented local threshold profile.
hipError_t rocm_image_canny_local(const uint8_t* source,uint64_t source_bytes,uint64_t source_pitch,
    int width,int height,int channels,int low,int high,uint8_t* output,uint64_t output_bytes,
    uint64_t output_pitch,void* workspace,uint64_t workspace_bytes,hipStream_t stream);
#ifdef __cplusplus
}
#endif
#endif
