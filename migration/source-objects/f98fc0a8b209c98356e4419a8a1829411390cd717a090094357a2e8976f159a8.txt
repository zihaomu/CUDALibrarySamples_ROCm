// SPDX-License-Identifier: Apache-2.0
#include "canny_color.h"
#include "canny_stages.h"
#include "connectivity.h"
#include "image_memory.hpp"
#include <climits>
namespace {
__global__ void init(const uint16_t*nms,uint32_t*parent,uint32_t*strong,int n,int low){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<n){parent[t]=nms[t]>low?uint32_t(t):rocm_image::inactive_component;strong[t]=0;}
}
__global__ void seeds(const uint16_t*nms,const uint32_t*parent,uint32_t*strong,int n,int high){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<n&&parent[t]!=rocm_image::inactive_component&&nms[t]>high)atomicExch(strong+parent[t],1u);
}
__global__ void result(const uint32_t*parent,const uint32_t*strong,uint8_t*out,uint64_t pitch,int w,int h){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<w*h)out[uint64_t(t/w)*pitch+t%w]=parent[t]!=rocm_image::inactive_component&&strong[parent[t]]?255:0;
}
}
extern "C" uint32_t rocm_image_canny_color_abi_version(void){return 1;}
extern "C" hipError_t rocm_image_canny_color_workspace_size(int w,int h,uint64_t*bytes){
 if(!bytes||w<=0||h<=0||w>32768||h>32768||uint64_t(w)*h>INT_MAX-255)return hipErrorInvalidValue;
 *bytes=uint64_t(w)*h*16+4;return hipSuccess;
}
extern "C" hipError_t rocm_image_canny_color(const uint8_t*source,uint64_t source_bytes,uint64_t pitch,
 int w,int h,int low,int high,uint8_t*out,uint64_t out_bytes,uint64_t out_pitch,
 void*workspace,uint64_t workspace_bytes,hipStream_t stream){
 uint64_t needed=0;hipError_t status=rocm_image_canny_color_workspace_size(w,h,&needed);if(status!=hipSuccess)return status;
 if(!source||!out||!workspace||low<0||high<low||high>32767||pitch<uint64_t(w)*3||out_pitch<uint64_t(w)||pitch>UINT64_MAX/uint64_t(h)||out_pitch>UINT64_MAX/uint64_t(h)||source_bytes<uint64_t(h-1)*pitch+uint64_t(w)*3||out_bytes<uint64_t(h-1)*out_pitch+w||workspace_bytes<needed||reinterpret_cast<uintptr_t>(workspace)%alignof(uint32_t))return hipErrorInvalidValue;
 if(rocm_image::spans_overlap(source,source_bytes,out,out_bytes)||rocm_image::spans_overlap(source,source_bytes,workspace,workspace_bytes)||rocm_image::spans_overlap(out,out_bytes,workspace,workspace_bytes))return hipErrorInvalidValue;
 int device=0;hipDevice_t stream_device{};status=hipGetDevice(&device);if(status!=hipSuccess)return status;status=hipStreamGetDevice(stream,&stream_device);if(status!=hipSuccess)return status;if(stream_device!=device)return hipErrorInvalidDevice;
 for(int which=0;which<3;++which){
  const void*p=which==0?static_cast<const void*>(source):which==1?static_cast<const void*>(out):workspace;
  status=rocm_image::device_span(p,which==0?source_bytes:which==1?out_bytes:workspace_bytes,device);if(status!=hipSuccess)return status;
 }
 int n=w*h;auto*dx=static_cast<int16_t*>(workspace);auto*dy=dx+n;auto*mag=reinterpret_cast<uint16_t*>(dy+n);auto*nms=mag+n;auto*parent=reinterpret_cast<uint32_t*>(nms+n);auto*strong=parent+n;auto*changed=strong+n;
 status=rocm_image_canny_stages(source,pitch,w,h,3,dx,dy,mag,nms,stream);if(status!=hipSuccess)return status;
 init<<<(n+255)/256,256,0,stream>>>(nms,parent,strong,n,low);status=hipGetLastError();if(status!=hipSuccess)return status;
 status=rocm_image::converge_components8(parent,nullptr,0,w,h,changed,stream);if(status!=hipSuccess)return status;
 seeds<<<(n+255)/256,256,0,stream>>>(nms,parent,strong,n,high);status=hipGetLastError();if(status!=hipSuccess)return status;
 result<<<(n+255)/256,256,0,stream>>>(parent,strong,out,out_pitch,w,h);return hipGetLastError();
}
