// SPDX-License-Identifier: Apache-2.0
#include "canny.h"
#include <hip/hip_runtime.h>
#include <climits>
#include <cstdint>

namespace {
__device__ int clamp_coord(int x,int n){return x<0?0:x>=n?n-1:x;}
__device__ int direction(int gx,int gy){
    int ax=gx<0?-gx:gx,ay=gy<0?-gy:gy;
    if(ay*32768<ax*13573)return 0;
    if(ay*32768>ax*(13573+65536))return 2;
    return gx*gy>=0?1:3;
}
__global__ void local_threshold(const int16_t*dx,const int16_t*dy,const uint16_t*nms,
    uint8_t*out,uint64_t pitch,int w,int h,int low,int high){
    int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=w*h)return;
    int x=t%w,y=t/w,d=direction(dx[t],dy[t]);
    int ox=d==2?0:1,oy=d==0?0:d==3?-1:1;bool connected=false;
    for(int sign=-1;sign<=1;sign+=2){
        int q=clamp_coord(y+sign*oy,h)*w+clamp_coord(x+sign*ox,w);
        connected|=nms[q]==nms[t]&&direction(dx[q],dy[q])==d;
    }
    out[uint64_t(y)*pitch+x]=(nms[t]>high||(nms[t]>=low&&connected))?255:0;
}
bool overlaps(const void*a,uint64_t an,const void*b,uint64_t bn){
    uintptr_t aa=reinterpret_cast<uintptr_t>(a),bb=reinterpret_cast<uintptr_t>(b);
    return an>UINTPTR_MAX-aa||bn>UINTPTR_MAX-bb||(aa<bb+bn&&bb<aa+an);
}
hipError_t device_span(const void*pointer,uint64_t bytes,int current){
    hipPointerAttribute_t attr{};
    hipError_t status=hipPointerGetAttributes(&attr,pointer);
    if(status!=hipSuccess)return hipErrorInvalidValue;
    if(attr.type!=hipMemoryTypeDevice)return hipErrorInvalidValue;
    if(attr.device!=current)return hipErrorInvalidDevice;
    hipDeviceptr_t base{};size_t size=0;
    status=hipMemGetAddressRange(&base,&size,reinterpret_cast<hipDeviceptr_t>(const_cast<void*>(pointer)));
    if(status!=hipSuccess)return status;
    uintptr_t start=reinterpret_cast<uintptr_t>(pointer),origin=reinterpret_cast<uintptr_t>(base);
    if(start<origin||start-origin>size||bytes>size-(start-origin))return hipErrorInvalidValue;
    return hipSuccess;
}
}
extern "C" uint32_t rocm_image_canny_abi_version(void){return 1;}
extern "C" hipError_t rocm_image_canny_workspace_size(int w,int h,uint64_t*bytes){
    if(!bytes||w<=0||h<=0||w>32768||h>32768||uint64_t(w)*h>INT_MAX-255)return hipErrorInvalidValue;
    *bytes=uint64_t(w)*h*8;return hipSuccess;
}
extern "C" hipError_t rocm_image_canny_local(const uint8_t*source,uint64_t source_bytes,uint64_t pitch,
    int w,int h,int channels,int low,int high,uint8_t*out,uint64_t out_bytes,uint64_t out_pitch,
    void*workspace,uint64_t workspace_bytes,hipStream_t stream){
    uint64_t needed=0;hipError_t status=rocm_image_canny_workspace_size(w,h,&needed);
    if(status!=hipSuccess)return status;
    if(!source||!out||!workspace||(channels!=1&&channels!=3)||low<0||high<low||high>32767||
       pitch<uint64_t(w)*channels||out_pitch<uint64_t(w)||pitch>UINT64_MAX/uint64_t(h)||out_pitch>UINT64_MAX/uint64_t(h)||
       source_bytes<uint64_t(h-1)*pitch+uint64_t(w)*channels||out_bytes<uint64_t(h-1)*out_pitch+w||
       workspace_bytes<needed||reinterpret_cast<uintptr_t>(workspace)%alignof(int16_t))return hipErrorInvalidValue;
    if(overlaps(source,source_bytes,out,out_bytes)||overlaps(source,source_bytes,workspace,workspace_bytes)||
       overlaps(out,out_bytes,workspace,workspace_bytes))return hipErrorInvalidValue;
    int device=0;hipDevice_t stream_device{};status=hipGetDevice(&device);if(status!=hipSuccess)return status;
    status=hipStreamGetDevice(stream,&stream_device);if(status!=hipSuccess)return status;
    if(stream_device!=device)return hipErrorInvalidDevice;
    for(int which=0;which<3;++which){
        const void*p=which==0?static_cast<const void*>(source):which==1?static_cast<const void*>(out):workspace;
        uint64_t bytes=which==0?source_bytes:which==1?out_bytes:workspace_bytes;
        status=device_span(p,bytes,device);if(status!=hipSuccess)return status;
    }
    uint64_t n=uint64_t(w)*h;auto*dx=static_cast<int16_t*>(workspace);auto*dy=dx+n;
    auto*mag=reinterpret_cast<uint16_t*>(dy+n);auto*nms=mag+n;
    status=rocm_image_canny_stages(source,pitch,w,h,channels,dx,dy,mag,nms,stream);
    if(status!=hipSuccess)return status;
    local_threshold<<<(w*h+255)/256,256,0,stream>>>(dx,dy,nms,out,out_pitch,w,h,low,high);
    return hipGetLastError();
}
