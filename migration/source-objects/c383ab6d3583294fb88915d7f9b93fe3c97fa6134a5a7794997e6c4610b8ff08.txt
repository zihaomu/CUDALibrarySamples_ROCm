// SPDX-License-Identifier: Apache-2.0
#include "benchmark.h"
#include <hip/hip_runtime.h>
#include <climits>

namespace {
__device__ int clamp(int x,int n){return x<0?0:x>=n?n-1:x;}
__global__ void gauss5(const uint8_t*src,uint8_t*dst,int w,int h){
    int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=w*h)return;
    int x=t%w,y=t/w,sum=0;const int weight[5]={1,4,6,4,1};
    for(int dy=-2;dy<=2;++dy)for(int dx=-2;dx<=2;++dx)
        sum+=weight[dy+2]*weight[dx+2]*src[clamp(y+dy,h)*w+clamp(x+dx,w)];
    dst[t]=uint8_t((sum+128)>>8);
}
__global__ void resize_half(const uint8_t*src,uint8_t*dst,int w,int h,int ow,int oh){
    int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=ow*oh)return;
    int x=t%ow,y=t/ow;
    float sx=(float(x)+0.5f)*float(w)/float(ow)-0.5f;
    float sy=(float(y)+0.5f)*float(h)/float(oh)-0.5f;
    int x0=__float2int_rd(sx),y0=__float2int_rd(sy);
    float fx=sx-float(x0),fy=sy-float(y0);
    int ax=clamp(x0,w),bx=clamp(x0+1,w),ay=clamp(y0,h),by=clamp(y0+1,h);
    float value=(1.f-fy)*((1.f-fx)*src[ay*w+ax]+fx*src[ay*w+bx])+
                fy*((1.f-fx)*src[by*w+ax]+fx*src[by*w+bx]);
    dst[t]=uint8_t(__float2int_rn(value));
}
__global__ void rgb_gray(const uint8_t*src,uint8_t*dst,int w,int h){
    int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=w*h)return;
    int r=src[3*t],g=src[3*t+1],b=src[3*t+2];
    dst[t]=uint8_t((19595*r+38470*g+7471*b+32768)>>16);
}
bool overlaps(const void*a,size_t an,const void*b,size_t bn){
    uintptr_t x=reinterpret_cast<uintptr_t>(a),y=reinterpret_cast<uintptr_t>(b);
    return an>UINTPTR_MAX-x||bn>UINTPTR_MAX-y||(x<y+bn&&y<x+an);
}
hipError_t span(const void*pointer,size_t bytes,int current){
    hipPointerAttribute_t attr{};hipError_t rc=hipPointerGetAttributes(&attr,pointer);
    if(rc!=hipSuccess||attr.type!=hipMemoryTypeDevice)return hipErrorInvalidValue;
    if(attr.device!=current)return hipErrorInvalidDevice;
    hipDeviceptr_t base{};size_t allocation=0;
    rc=hipMemGetAddressRange(&base,&allocation,reinterpret_cast<hipDeviceptr_t>(const_cast<void*>(pointer)));
    if(rc!=hipSuccess)return rc;
    uintptr_t start=reinterpret_cast<uintptr_t>(pointer),origin=reinterpret_cast<uintptr_t>(base);
    if(start<origin||start-origin>allocation||bytes>allocation-(start-origin))return hipErrorInvalidValue;
    return hipSuccess;
}
hipError_t validate(const uint8_t*src,size_t input,uint8_t*dst,size_t output,int w,int h,hipStream_t stream){
    if(!src||!dst||w<16||h<16||w>16384||h>16384||overlaps(src,input,dst,output))return hipErrorInvalidValue;
    int device=0;hipDevice_t stream_device{};hipError_t rc=hipGetDevice(&device);if(rc!=hipSuccess)return rc;
    rc=hipStreamGetDevice(stream,&stream_device);if(rc!=hipSuccess)return rc;
    if(stream_device!=device)return hipErrorInvalidDevice;
    rc=span(src,input,device);if(rc!=hipSuccess)return rc;
    return span(dst,output,device);
}
}
extern "C" hipError_t rocm_image_benchmark_gauss5(const uint8_t*src,uint8_t*dst,int w,int h,hipStream_t stream){
    hipError_t rc=validate(src,size_t(w)*h,dst,size_t(w)*h,w,h,stream);if(rc!=hipSuccess)return rc;
    // A prior rejected HIP call can leave a thread-local last error. Report this launch only.
    hipGetLastError();
    gauss5<<<(w*h+255)/256,256,0,stream>>>(src,dst,w,h);return hipGetLastError();
}
extern "C" hipError_t rocm_image_benchmark_resize_half(const uint8_t*src,uint8_t*dst,int w,int h,hipStream_t stream){
    hipError_t rc=validate(src,size_t(w)*h,dst,size_t(w/2)*(h/2),w,h,stream);if(rc!=hipSuccess)return rc;
    hipGetLastError();
    resize_half<<<((w/2)*(h/2)+255)/256,256,0,stream>>>(src,dst,w,h,w/2,h/2);return hipGetLastError();
}
extern "C" hipError_t rocm_image_benchmark_rgb_gray(const uint8_t*src,uint8_t*dst,int w,int h,hipStream_t stream){
    hipError_t rc=validate(src,size_t(w)*h*3,dst,size_t(w)*h,w,h,stream);if(rc!=hipSuccess)return rc;
    hipGetLastError();
    rgb_gray<<<(w*h+255)/256,256,0,stream>>>(src,dst,w,h);return hipGetLastError();
}
