// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <hip/hip_runtime_api.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct rocm_image_contour_info {
 uint32_t contour_pixels,edge_count,loop_count,min_x,min_y,max_x,max_y;
} rocm_image_contour_info;
typedef struct rocm_image_contour_edge {
 uint32_t component,loop_id,order,x0,y0,x1,y1,pixel_x,pixel_y;
} rocm_image_contour_edge;
typedef struct rocm_image_contour_descriptor {
 const uint8_t* input;uint64_t input_pitch;
 uint32_t* raw_labels;uint64_t raw_pitch;
 uint32_t* labels;uint64_t labels_pitch;
 uint8_t* mask;uint64_t mask_pitch;
 rocm_image_contour_info* info;uint64_t info_capacity;
 rocm_image_contour_edge* geometry;uint64_t geometry_capacity;
 uint32_t* totals;void* workspace;uint64_t workspace_bytes;
 int width,height;
} rocm_image_contour_descriptor;
uint32_t rocm_image_contour_abi_version(void);
// width,height 1..32768, at most 2^26 pixels. info_capacity >= pixel count,
// geometry_capacity >= 4*pixel count. Only actual prefixes are written.
// totals contains {component_count,edge_count,loop_count}. All storage is
// caller-owned device memory; workspace must be four-byte aligned.
hipError_t rocm_image_contour_workspace_size(int width,int height,uint64_t*bytes);
hipError_t rocm_image_contour_run(const rocm_image_contour_descriptor*image,hipStream_t stream);
// Rasterize supplied closed-cell geometry into the exact 0-boundary/255-other
// eight-neighbor mask. [start,stop) selects zero-based component IDs; regions
// with contour_pixels >= limit are bypassed unless stop-start<=1. A zero
// limit is legal (bypass all under a multi-ID range). Pixel flags require
// width*height uint32 values plus one uint32 validation flag. Synchronizes
// validation scalars; final pixel kernels remain queued on the caller stream.
hipError_t rocm_image_contour_reconstruct(const uint32_t*labels,uint64_t labels_pitch,
 const rocm_image_contour_info*info,uint32_t components,
 const rocm_image_contour_edge*geometry,uint32_t edge_count,
 uint32_t start,uint32_t stop,uint32_t limit,uint8_t*output,uint64_t output_pitch,
 void*workspace,uint64_t workspace_bytes,int width,int height,hipStream_t stream);
#ifdef __cplusplus
}
#endif
