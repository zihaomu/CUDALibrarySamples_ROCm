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
    show("default-stream",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,count,nullptr),count,peaks,capacity,nullptr);
    std::vector<uint8_t> before_edge(w*h),before_peaks(size_t(capacity)*sizeof(*peaks)),before_count(sizeof(*count));
    check(hipMemcpy(before_edge.data(),edge,before_edge.size(),hipMemcpyDeviceToHost),"before-edge");
    check(hipMemcpy(before_peaks.data(),peaks,before_peaks.size(),hipMemcpyDeviceToHost),"before-peaks");
    check(hipMemcpy(before_count.data(),count,before_count.size(),hipMemcpyDeviceToHost),"before-count");
    show("null-input",rocm_image_hough_peaks(nullptr,w,h,8,peaks,capacity,count,stream));
    show("zero-threshold",rocm_image_hough_peaks(edge,w,h,0,peaks,capacity,count,stream));
    show("wrong-capacity",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity-1,count,stream));
    show("host-input",rocm_image_hough_peaks(host,w,h,8,peaks,capacity,count,stream));
    uint8_t*short_edge=nullptr;check(hipMalloc(&short_edge,w*h-1),"short-input");
    show("short-physical-allocation",rocm_image_hough_peaks(short_edge,w,h,8,peaks,capacity,count,stream));
    show("overlap-count-and-peaks",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,reinterpret_cast<int*>(peaks),stream));
    show("overlap-input-and-output",rocm_image_hough_peaks(edge,w,h,8,reinterpret_cast<RocmHoughPeak*>(edge),capacity,count,stream));
    int host_count=0;show("host-count",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,&host_count,stream));
    const size_t mis_peak_bytes=size_t(capacity)*sizeof(*peaks)+alignof(RocmHoughPeak);
    const size_t mis_count_bytes=sizeof(*count)+alignof(int);
    uint8_t *mis_peaks=nullptr,*mis_count=nullptr;
    check(hipMalloc(&mis_peaks,mis_peak_bytes),"misaligned-peaks-allocation");
    check(hipMalloc(&mis_count,mis_count_bytes),"misaligned-count-allocation");
    check(hipMemset(mis_peaks,0xa5,mis_peak_bytes),"misaligned-peaks-sentinel");
    check(hipMemset(mis_count,0x5a,mis_count_bytes),"misaligned-count-sentinel");
    void *peak_base=nullptr,*count_base=nullptr;size_t peak_span=0,count_span=0;
    check(hipMemGetAddressRange(&peak_base,&peak_span,mis_peaks+1),"misaligned-peaks-range");
    check(hipMemGetAddressRange(&count_base,&count_span,mis_count+1),"misaligned-count-range");
    const bool peak_full=peak_base==mis_peaks&&peak_span>=size_t(capacity)*sizeof(*peaks)+1;
    const bool count_full=count_base==mis_count&&count_span>=sizeof(*count)+1;
    std::fprintf(stderr,"alignment-spans-proven|%d|%d\n",int(peak_full),int(count_full));
    if(!peak_full||!count_full)return 4;
    show("misaligned-peaks",rocm_image_hough_peaks(edge,w,h,8,reinterpret_cast<RocmHoughPeak*>(mis_peaks+1),capacity,count,stream));
    show("misaligned-count",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,reinterpret_cast<int*>(mis_count+1),stream));
    hipStream_t dead{};check(hipStreamCreate(&dead),"create-dead");check(hipStreamDestroy(dead),"destroy-dead");
    show("destroyed-stream",rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,count,dead));
    std::vector<uint8_t> after_edge(w*h),after_peaks(size_t(capacity)*sizeof(*peaks)),after_count(sizeof(*count));
    check(hipMemcpy(after_edge.data(),edge,after_edge.size(),hipMemcpyDeviceToHost),"after-edge");
    check(hipMemcpy(after_peaks.data(),peaks,after_peaks.size(),hipMemcpyDeviceToHost),"after-peaks");
    check(hipMemcpy(after_count.data(),count,after_count.size(),hipMemcpyDeviceToHost),"after-count");
    std::vector<uint8_t> after_mis_peaks(mis_peak_bytes),after_mis_count(mis_count_bytes);
    check(hipMemcpy(after_mis_peaks.data(),mis_peaks,mis_peak_bytes,hipMemcpyDeviceToHost),"after-misaligned-peaks");
    check(hipMemcpy(after_mis_count.data(),mis_count,mis_count_bytes,hipMemcpyDeviceToHost),"after-misaligned-count");
    const bool mis_preserved=std::all_of(after_mis_peaks.begin(),after_mis_peaks.end(),[](uint8_t b){return b==0xa5;})&&
                             std::all_of(after_mis_count.begin(),after_mis_count.end(),[](uint8_t b){return b==0x5a;});
    std::printf("invalid-storage-preserved|0|%d\n",before_edge==after_edge&&before_peaks==after_peaks&&before_count==after_count&&mis_preserved?1:0);
    // Clear the expected invalid-handle status before the next valid launch.
    hipGetLastError();
    std::printf("large-grid-plan|0|%d\n",rocm_image_hough_vote_grid_x(16384,16384));
    constexpr int large=8192;const int largecap=rocm_image_hough_accumulator_height(large,large)*180;
    uint8_t*large_edges=nullptr;RocmHoughPeak*large_peaks=nullptr;
    check(hipMalloc(&large_edges,size_t(large)*large),"large-edges");
    check(hipMalloc(&large_peaks,size_t(largecap)*sizeof(*large_peaks)),"large-peaks");
    check(hipMemsetAsync(large_edges,0,size_t(large)*large,stream),"large-zero-input");
    show("large-zero-8192",rocm_image_hough_peaks(large_edges,large,large,1,large_peaks,largecap,count,stream),count,large_peaks,largecap,stream);
    check(hipFree(large_edges),"free-large-edges");check(hipFree(large_peaks),"free-large-peaks");
    constexpr int fpw=256;const int fpcap=rocm_image_hough_accumulator_height(fpw,fpw)*180;
    uint8_t*fp_edges=nullptr;RocmHoughPeak*fp_peaks=nullptr;
    check(hipMalloc(&fp_edges,fpw*fpw),"fp32-edges");
    check(hipMalloc(&fp_peaks,size_t(fpcap)*sizeof(*fp_peaks)),"fp32-peaks");
    uint8_t fp_host[fpw*fpw]{};fp_host[164*fpw+34]=255;fp_host[100*fpw+108]=255;
    check(hipMemcpyAsync(fp_edges,fp_host,sizeof(fp_host),hipMemcpyHostToDevice,stream),"fp32-input");
    show("fp32-half-grid",rocm_image_hough_peaks(fp_edges,fpw,fpw,2,fp_peaks,fpcap,count,stream),count,fp_peaks,fpcap,stream);
    check(hipFree(fp_edges),"free-fp32-edges");check(hipFree(fp_peaks),"free-fp32-peaks");
    check(hipFree(short_edge),"free-short");
    check(hipFree(mis_peaks),"free-misaligned-peaks");check(hipFree(mis_count),"free-misaligned-count");
    check(hipFree(edge),"free-edge");check(hipFree(peaks),"free-peaks");check(hipFree(count),"free-count");
    check(hipStreamDestroy(stream),"destroy-stream");
}
