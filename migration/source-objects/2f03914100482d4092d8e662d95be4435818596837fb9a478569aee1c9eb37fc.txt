// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
// Pitches and capacities are bytes. Optional outputs require a zero pitch
// when absent. All present spans, including workspace, must be disjoint.
typedef struct rocm_image_distance_descriptor {
 const void* input; uint64_t input_pitch;
 double* distance; uint64_t distance_pitch;
 uint16_t* visualization; uint64_t visualization_pitch;
 int16_t* indices; uint64_t indices_pitch;
 int16_t* relative; uint64_t relative_pitch;
 uint64_t* site_ids; uint64_t site_ids_pitch;
 double* sites_xy; uint64_t sites_xy_pitch;
 void* workspace; uint64_t workspace_bytes;
 double cutoff;
 int32_t width,height;
 uint32_t mode,input_type,remap_circle,reserved;
} rocm_image_distance_descriptor;
// mode:0 unsigned zero sites,1 signed linear threshold-crossing point set.
// input_type:0 uint8,1 float32,2 float64. Unsigned requires uint8;
// remap_circle requires signed float64 and computes (input-.5)*2 on GPU.
uint32_t rocm_image_distance_abi_version(void);
int rocm_image_distance_workspace_size(int width,int height,uint64_t* bytes);
int rocm_image_distance_run(const rocm_image_distance_descriptor*,void* stream);
#ifdef __cplusplus
}
#endif
