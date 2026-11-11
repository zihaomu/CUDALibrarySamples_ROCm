// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <hip/hip_runtime_api.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
// Eight-connected equal-byte components, including zero-valued regions.
// Raw IDs are minimum row-major pixel index+1; compact IDs are 1..K in
// increasing raw-root order. count is a device uint32 scalar. Labels are u32.
// Scratch must be 4-byte aligned. The caller owns every allocation and stream.
// A host convergence scalar is synchronized internally; final output kernels
// remain queued on stream. Synchronize before reading/releasing any buffer.
typedef struct rocm_image_ccl8_descriptor {
 const uint8_t* input; uint64_t input_pitch;
 uint32_t* labels; uint64_t labels_pitch;
 uint32_t* compact; uint64_t compact_pitch;
 uint32_t* count; void* workspace; uint64_t workspace_bytes;
 int width,height;
} rocm_image_ccl8_descriptor;
uint32_t rocm_image_ccl8_abi_version(void);
hipError_t rocm_image_ccl8_workspace_size(int width,int height,uint64_t*bytes);
hipError_t rocm_image_ccl8_run(const rocm_image_ccl8_descriptor* image,hipStream_t stream);
// descriptors is a host array, length 1..65536. All descriptors are validated
// before any pixel work. Each image has independent state; read-only inputs may
// be shared, writable ranges may not overlap another descriptor's buffers.
// The heterogeneous batch is processed in descriptor order on the given stream.
hipError_t rocm_image_ccl8_batch(const rocm_image_ccl8_descriptor*descriptors,int count,hipStream_t stream);
#ifdef __cplusplus
}
#endif
