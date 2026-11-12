// SPDX-License-Identifier: Apache-2.0
#include "../../rocm/common/image/hough.h"
#include <hip/hip_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
static void check(hipError_t rc){if(rc!=hipSuccess){std::fprintf(stderr,"HIP %d\n",int(rc));std::exit(2);}}
int main(){
    int count_devices=0;check(hipGetDeviceCount(&count_devices));
    if(count_devices!=2){std::fprintf(stderr,"two visible physical GPUs required\n");return 2;}
    check(hipSetDevice(0));hipStream_t foreign{};check(hipStreamCreate(&foreign));
    check(hipSetDevice(1));hipStream_t own{};check(hipStreamCreate(&own));
    constexpr int w=16,h=16;const int capacity=rocm_image_hough_accumulator_height(w,h)*180;
    uint8_t*edge=nullptr;RocmHoughPeak*peaks=nullptr;int*count=nullptr;
    check(hipMalloc(&edge,w*h));check(hipMalloc(&peaks,size_t(capacity)*sizeof(*peaks)));check(hipMalloc(&count,sizeof(int)));
    check(hipMemsetAsync(edge,19,w*h,own));check(hipMemsetAsync(peaks,37,size_t(capacity)*sizeof(*peaks),own));check(hipMemsetAsync(count,53,sizeof(int),own));check(hipStreamSynchronize(own));
    auto rc=rocm_image_hough_peaks(edge,w,h,8,peaks,capacity,count,foreign);
    std::vector<uint8_t> a(w*h),b(size_t(capacity)*sizeof(*peaks)),c(sizeof(int));
    check(hipMemcpy(a.data(),edge,a.size(),hipMemcpyDeviceToHost));
    check(hipMemcpy(b.data(),peaks,b.size(),hipMemcpyDeviceToHost));
    check(hipMemcpy(c.data(),count,c.size(),hipMemcpyDeviceToHost));
    bool unchanged=true;for(auto v:a)unchanged&=v==19;for(auto v:b)unchanged&=v==37;for(auto v:c)unchanged&=v==53;
    std::printf("foreign-device-stream|%d|%d\n",int(rc),unchanged?1:0);
    check(hipFree(edge));check(hipFree(peaks));check(hipFree(count));check(hipStreamDestroy(own));
    check(hipSetDevice(0));check(hipStreamDestroy(foreign));
    return rc==hipErrorInvalidDevice&&unchanged?0:1;
}
