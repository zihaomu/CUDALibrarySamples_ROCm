// SPDX-License-Identifier: Apache-2.0
#include <hip/hip_runtime.h>
__global__ void migration_scale_kernel(float2* data, int count, float factor) {
 for (int i=blockIdx.x*blockDim.x+threadIdx.x;i<count;i+=blockDim.x*gridDim.x) {
  data[i].x*=factor;data[i].y*=factor;
 }
}
extern "C" int migration_scale_complex(void* data,int count,float factor,hipStream_t stream) {
 migration_scale_kernel<<<(count+127)/128,128,0,stream>>>(static_cast<float2*>(data),count,factor);
 return int(hipGetLastError());
}
