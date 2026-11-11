// SPDX-License-Identifier: Apache-2.0
#ifndef ROCM_IMAGE_CANNY_STAGES_H
#define ROCM_IMAGE_CANNY_STAGES_H
#include <stdint.h>
#include <hip/hip_runtime_api.h>
#ifdef __cplusplus
extern "C" {
#endif
// Device buffers must belong to the current device and outlive stream completion.
// All four distinct output buffers contain width*height tightly packed elements.
// This API computes stages, not a final binary Canny mask.
hipError_t rocm_image_canny_stages(const uint8_t* source, uint64_t source_pitch,
    int width, int height, int channels, int16_t* dx, int16_t* dy,
    uint16_t* magnitude, uint16_t* suppressed, hipStream_t stream);
#ifdef __cplusplus
}
#endif
#endif
