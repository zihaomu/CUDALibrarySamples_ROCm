// SPDX-License-Identifier: Apache-2.0
#include "hough.h"
#include "hough_trig.h"
#include <cmath>
#include <climits>

namespace {
bool overlaps(const void*a,size_t an,const void*b,size_t bn){
    uintptr_t x=reinterpret_cast<uintptr_t>(a),y=reinterpret_cast<uintptr_t>(b);
    return an>UINTPTR_MAX-x||bn>UINTPTR_MAX-y||(x<y+bn&&y<x+an);
}
hipError_t device_span(const void*pointer,size_t bytes,int current){
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
__global__ void cast_votes(const uint8_t* edges,int w,int h,int rows,int* votes){
    unsigned long long pixel=static_cast<unsigned long long>(blockIdx.x)*blockDim.x+threadIdx.x;
    const unsigned long long stride=static_cast<unsigned long long>(gridDim.x)*blockDim.x;
    const unsigned long long total=static_cast<unsigned long long>(w)*h;
    const int theta=blockIdx.y;
    for(;pixel<total;pixel+=stride){
        if(!edges[pixel])continue;
        int x=int(pixel%w)-(w>>1),y=int(pixel/w)-(h>>1);
        int rho=__float2int_rn(float(x)*kHoughCos[theta]+float(y)*kHoughSin[theta])+(rows>>1);
        if(rho>=0&&rho<rows)atomicAdd(votes+theta*rows+rho,1);
    }
}
__global__ void extract_peaks(const int* votes,int rows,int threshold,
                              RocmHoughPeak* peaks,int* count){
    int t=blockIdx.x*blockDim.x+threadIdx.x,all=rows*180;
    if(t>=all)return;
    int rho=t%rows,theta=t/rows,v=votes[t];if(v<threshold)return;
    for(int dt=-1;dt<=1;++dt){
        int a=theta+dt;if(a<0||a>=180)continue;
        for(int dr=-1;dr<=1;++dr){
            if(!dt&&!dr)continue;
            int r=rho+dr;if(r<0||r>=rows)continue;
            int q=a*rows+r,w=votes[q];
            if(w>v||(w==v&&q<t))return;
        }
    }
    int place=atomicAdd(count,1);peaks[place]={rho,theta,v};
}
}
extern "C" int rocm_image_hough_accumulator_height(int w,int h){
    if(w<16||h<16||w>16384||h>16384)return 0;
    return int(std::ceil(std::sqrt(2.0)*double(w>h?w:h)));
}
extern "C" int rocm_image_hough_vote_grid_x(int w,int h){
    if(!rocm_image_hough_accumulator_height(w,h))return 0;
    unsigned long long blocks=(static_cast<unsigned long long>(w)*h+255)/256;
    return int(blocks<8192?blocks:8192);
}
extern "C" hipError_t rocm_image_hough_peaks(const uint8_t* edges,int w,int h,
        int threshold,RocmHoughPeak* peaks,int capacity,int* count,hipStream_t stream){
    int rows=rocm_image_hough_accumulator_height(w,h);
    if(!edges||!peaks||!count||!rows||threshold<1||capacity!=rows*180
       ||reinterpret_cast<uintptr_t>(peaks)%alignof(RocmHoughPeak)
       ||reinterpret_cast<uintptr_t>(count)%alignof(int))
        return hipErrorInvalidValue;
    size_t edge_bytes=size_t(w)*h,peak_bytes=size_t(capacity)*sizeof(RocmHoughPeak);
    if(overlaps(edges,edge_bytes,peaks,peak_bytes)||overlaps(edges,edge_bytes,count,sizeof(int))||
       overlaps(peaks,peak_bytes,count,sizeof(int)))return hipErrorInvalidValue;
    int current=0;hipDevice_t stream_device{};
    hipError_t rc=hipGetDevice(&current);if(rc!=hipSuccess)return rc;
    rc=hipStreamGetDevice(stream,&stream_device);if(rc!=hipSuccess)return rc;
    if(stream_device!=current)return hipErrorInvalidDevice;
    rc=device_span(edges,edge_bytes,current);if(rc!=hipSuccess)return rc;
    rc=device_span(peaks,peak_bytes,current);if(rc!=hipSuccess)return rc;
    rc=device_span(count,sizeof(int),current);if(rc!=hipSuccess)return rc;
    int* votes=nullptr;
    rc=hipMalloc(&votes,size_t(rows)*180*sizeof(int));if(rc!=hipSuccess)return rc;
    rc=hipMemsetAsync(votes,0,size_t(rows)*180*sizeof(int),stream);
    if(rc==hipSuccess)rc=hipMemsetAsync(count,0,sizeof(int),stream);
    if(rc==hipSuccess){
        cast_votes<<<dim3(rocm_image_hough_vote_grid_x(w,h),180,1),256,0,stream>>>(edges,w,h,rows,votes);
        rc=hipGetLastError();
    }
    if(rc==hipSuccess){
        extract_peaks<<<(rows*180+255)/256,256,0,stream>>>(votes,rows,threshold,peaks,count);
        rc=hipGetLastError();
    }
    // hipFreeAsync retains the caller's stream order while leaving the API asynchronous.
    hipError_t freed=hipFreeAsync(votes,stream);
    return rc==hipSuccess?freed:rc;
}
