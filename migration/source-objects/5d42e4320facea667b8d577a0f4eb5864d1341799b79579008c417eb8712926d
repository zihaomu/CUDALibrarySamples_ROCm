// SPDX-License-Identifier: Apache-2.0
#include "../../rocm/common/image/benchmark.h"
#include <hip/hip_runtime.h>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void check(hipError_t rc){if(rc!=hipSuccess){std::fprintf(stderr,"setup %s\n",hipGetErrorString(rc));std::exit(2);}}
using Function=hipError_t(*)(const uint8_t*,uint8_t*,int,int,hipStream_t);
static unsigned long long hash(const std::vector<uint8_t>&v){
    unsigned long long h=1469598103934665603ull;
    for(auto c:v){h^=c;h*=1099511628211ull;}return h;
}
static void row(const char*op,const char*name,bool good){std::printf("%s|%s|%d\n",op,name,good?1:0);}
static void exercise(const char*name,Function fn,int channels,bool half){
    constexpr int w=17,h=19;size_t in=size_t(w)*h*channels,out=half?size_t(w/2)*(h/2):size_t(w)*h;
    uint8_t *src=nullptr,*dst=nullptr,*shortSrc=nullptr,*shortDst=nullptr;
    check(hipMalloc(&src,in));check(hipMalloc(&dst,out));
    check(hipMalloc(&shortSrc,in-1));check(hipMalloc(&shortDst,out-1));
    hipStream_t stream{};check(hipStreamCreate(&stream));
    std::vector<uint8_t> input(in),result(out),again(out),zero(out),sentinel(out,173);
    for(size_t i=0;i<in;++i)input[i]=uint8_t((i*17+23)%251);
    check(hipMemcpy(src,input.data(),in,hipMemcpyHostToDevice));
    bool normal=fn(src,dst,w,h,stream)==hipSuccess;check(hipStreamSynchronize(stream));
    check(hipMemcpy(result.data(),dst,out,hipMemcpyDeviceToHost));row(name,"normal",normal&&hash(result)!=hash(sentinel));
    check(hipMemset(src,0,in));bool cleared=fn(src,dst,w,h,stream)==hipSuccess;check(hipStreamSynchronize(stream));
    check(hipMemcpy(zero.data(),dst,out,hipMemcpyDeviceToHost));
    row(name,"changed-to-zero",cleared&&std::all_of(zero.begin(),zero.end(),[](uint8_t x){return x==0;})&&result!=zero);
    check(hipMemcpy(src,input.data(),in,hipMemcpyHostToDevice));
    bool restored=fn(src,dst,w,h,stream)==hipSuccess;check(hipStreamSynchronize(stream));
    check(hipMemcpy(again.data(),dst,out,hipMemcpyDeviceToHost));row(name,"restored",restored&&again==result);
    bool defaultStream=fn(src,dst,w,h,nullptr)==hipSuccess;check(hipDeviceSynchronize());
    check(hipMemcpy(again.data(),dst,out,hipMemcpyDeviceToHost));row(name,"default-stream",defaultStream&&again==result);
    check(hipMemcpy(dst,sentinel.data(),out,hipMemcpyHostToDevice));
    bool invalid=fn(src,dst,0,h,stream)!=hipSuccess&&fn(src,dst,w,0,stream)!=hipSuccess
        &&fn(nullptr,dst,w,h,stream)!=hipSuccess&&fn(src,nullptr,w,h,stream)!=hipSuccess
        &&fn(shortSrc,dst,w,h,stream)!=hipSuccess&&fn(src,shortDst,w,h,stream)!=hipSuccess
        &&fn(src,src,w,h,stream)!=hipSuccess&&fn(input.data(),dst,w,h,stream)!=hipSuccess
        &&fn(src,again.data(),w,h,stream)!=hipSuccess;
    check(hipMemcpy(again.data(),dst,out,hipMemcpyDeviceToHost));
    row(name,"invalid-rejected-and-output-preserved",invalid&&again==sentinel);
    check(hipStreamDestroy(stream));row(name,"destroyed-stream-rejected",fn(src,dst,w,h,stream)!=hipSuccess);
    check(hipFree(src));check(hipFree(dst));check(hipFree(shortSrc));check(hipFree(shortDst));
}
int main(){
    exercise("gauss",rocm_image_benchmark_gauss5,1,false);
    exercise("resize",rocm_image_benchmark_resize_half,1,true);
    exercise("color",rocm_image_benchmark_rgb_gray,3,false);
}
