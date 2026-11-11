// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <hip/hip_runtime.h>
#include <cstdint>
namespace rocm_image {
constexpr uint32_t inactive_component=UINT32_MAX;
// Internal primitive. Parents contain self indices or inactive_component.
// Optional values constrain edges to equal byte values; null means binary.
// All buffers belong to the caller and kernels use its stream. Only the one
// convergence flag is read by the host; all component construction is on GPU.
hipError_t converge_components8(uint32_t*parents,const uint8_t*values,
 uint64_t pitch,int width,int height,uint32_t*changed,hipStream_t stream);
}
