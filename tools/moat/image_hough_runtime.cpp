// SPDX-License-Identifier: Apache-2.0
#include "../../rocm/common/image/hough.h"
#include <hip/hip_runtime.h>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static void check(hipError_t s,const char*where){
    if(s!=hipSuccess){std::fprintf(stderr,"%s: %s\n",where,hipGetErrorString(s));std::exit(3);}
}
static void show(const char*name,hipError_t rc,int*count=nullptr,RocmHoughPeak*peaks=nullptr,int n=0,hipStream_t stream=nullptr){
    std::printf("%s|%d",name,int(rc));
    if(rc==hipSuccess&&count){
        int found=-1;check(hipMemcpyAsync(&found,count,sizeof(found),hipMemcpyDeviceToHost,stream),"copy-count");
        check(hipStreamSynchronize(stream),"sync-count");
        std::printf("|%d",found);
        if(peaks&&found>=0&&found<n){
            std::vector<RocmHoughPeak> rows(found);
            if(found)check(hipMemcpy(rows.data(),peaks,found*sizeof(RocmHoughPeak),hipMemcpyDeviceToHost),"copy-peaks");
            std::sort(rows.begin(),rows.end(),[](auto&a,auto&b){return a.theta_degrees!=b.theta_degrees?a.theta_degrees<b.theta_degrees:a.rho_index<b.rho_index;});
            for(auto&p:rows)std::printf("|%d,%d,%d",p.rho_index,p.theta_degrees,p.votes);
        }
    }
    std::puts("");
}
int main(){
    constexpr int w=16,h=16;const int rows=rocm_image_hough_accumulator_height(w,h),capacity=rows*180;
    uint8_t*edge=nullptr;RocmHoughPeak*peaks=nullptr;int*count=nullptr;hipStream_t stream{};
    check(hipStreamCreate(&stream),"stream");
    check(hipMalloc(&edge,w*h),"edge");
    check(hipMalloc(&peaks,capacity*sizeof(*peaks)),"peaks");
    check(hipMalloc(&count,sizeof(*count)),"count");
    uint8_t host[w*h]{};for(int x=0;x<w;++x)host[8*w+x]=255;
    check(hipMemcpyAsync(edge,host,sizeof(host),hipMemcpyHostToDevice,stream),"input");
    show("normal",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,count,stream),count,peaks,capacity,stream);
    check(hipMemsetAsync(edge,0,sizeof(host),stream),"change-input");
    show("changed-to-zero",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,count,stream),count,peaks,capacity,stream);
    check(hipMemcpyAsync(edge,host,sizeof(host),hipMemcpyHostToDevice,stream),"restore-input");
    show("restore",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,count,stream),count,peaks,capacity,stream);
    show("null-input",rocm_image_hough_peaks(nullptr,w,h,8,peaks,capacity,count,stream));
    show("zero-threshold",rocm_image_hough_peaks(edge,w,h,0,peaks,capacity,count,stream));
    show("wrong-capacity",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity-1,count,stream));
    show("host-input",rocm_image_hough_peaks(host,w,h,8,peaks,capacity,count,stream));
    uint8_t*short_edge=nullptr;check(hipMalloc(&short_edge,w*h-1),"short-input");
    show("short-physical-allocation",rocm_image_hough_peaks(short_edge,w,h,8,peaks,capacity,count,stream));
    show("overlap-count-and-peaks",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,reinterpret_cast<int*>(peaks),stream));
    show("overlap-input-and-output",rocm_image_hough_peaks(edge,w,h,8,reinterpret_cast<RocmHoughPeak*>(edge),capacity,count,stream));
    int host_count=0;show("host-count",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,&host_count,stream));
    check(hipFree(short_edge),"free-short");
    check(hipFree(edge),"free-edge");check(hipFree(peaks),"free-peaks");check(hipFree(count),"free-count");
    check(hipStreamDestroy(stream),"destroy-stream");
}
