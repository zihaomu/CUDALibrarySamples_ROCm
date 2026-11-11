// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
// RGB uint8, byte pitches, caller-owned device storage. Modes: 0 equal seed,
// 1 fixed seed gradient, 2 gradient with inner boundary, 3 absolute range,
// 4 range with inner boundary. Bounds are inclusive in all three channels.
typedef struct rocm_image_flood_descriptor {
 uint32_t version,descriptor_bytes;
 int32_t width,height;
 uint32_t mode; int32_t seed_x,seed_y; uint32_t reserved;
 const uint8_t* input; uint64_t input_pitch;
 uint8_t* output; uint64_t output_pitch;
 uint8_t* mask; uint64_t mask_pitch;
 uint32_t lower[3],upper[3],fill[3],boundary[3];
 // xmin,ymin,xmax,ymax inclusive, count, original RGB seed. Empty box is zero.
 uint32_t* region;
 void* workspace; uint64_t workspace_bytes,reserved_tail;
} rocm_image_flood_descriptor;
uint32_t rocm_image_flood_abi_version(void);
int rocm_image_flood_workspace_size(int width,int height,uint64_t* bytes);
int rocm_image_flood_run(const rocm_image_flood_descriptor*,void* stream);
#ifdef __cplusplus
}
#endif
