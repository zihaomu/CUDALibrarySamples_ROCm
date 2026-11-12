// SPDX-License-Identifier: Apache-2.0
// Complete original four-operation benchmark using HIP kernels and OpenCV CPU.
#include "../../../common/image/benchmark.h"
#include "../../../common/image/canny.h"
#include <hip/hip_runtime.h>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <functional>
#include <string>
#include <vector>

#define CHECK_HIP(call) do { hipError_t e=(call); if(e!=hipSuccess) { \
    std::fprintf(stderr,"HIP error %s at %s:%d\n",hipGetErrorString(e),__FILE__,__LINE__); \
    std::exit(EXIT_FAILURE); } } while(0)

static double median(std::vector<double> values){
    std::sort(values.begin(),values.end());return values[values.size()/2];
}
static double timeCpu(const std::function<void()>&fn,int iters){
    fn();std::vector<double> times;
    for(int r=0;r<5;++r){
        auto start=std::chrono::steady_clock::now();
        for(int i=0;i<iters;++i)fn();
        auto end=std::chrono::steady_clock::now();
        times.push_back(std::chrono::duration<double,std::milli>(end-start).count()/iters);
    }
    return median(times);
}
static double timeGpu(const std::function<void()>&fn,hipStream_t stream,int iters){
    hipEvent_t start{},end{};CHECK_HIP(hipEventCreate(&start));CHECK_HIP(hipEventCreate(&end));
    fn();CHECK_HIP(hipStreamSynchronize(stream));std::vector<double> times;
    for(int r=0;r<5;++r){
        CHECK_HIP(hipEventRecord(start,stream));
        for(int i=0;i<iters;++i)fn();
        CHECK_HIP(hipEventRecord(end,stream));CHECK_HIP(hipEventSynchronize(end));
        float ms=0;CHECK_HIP(hipEventElapsedTime(&ms,start,end));times.push_back(ms/iters);
    }
    CHECK_HIP(hipEventDestroy(start));CHECK_HIP(hipEventDestroy(end));return median(times);
}
static double meanAbsDiff(const cv::Mat&a,const cv::Mat&b){
    cv::Mat difference;cv::absdiff(a,b,difference);return cv::mean(difference.reshape(1))[0];
}
static void save(const char*name,const cv::Mat&image){
    std::ofstream out(name,std::ios::binary);out.write(reinterpret_cast<const char*>(image.data),image.total());
    if(!out)throw std::runtime_error(std::string("Cannot save ")+name);
}
struct Result {const char*name;double gpuKernel,gpuE2E,cpu1,cpuN,diff;};

int main(int argc,char**argv){
    std::string imagePath="../images/CircuitBoard_2048x1024_8u.raw";
    int W=4096,H=2048,iters=20;
    for(int i=1;i<argc;++i){
        if(!std::strcmp(argv[i],"-i")&&i+1<argc)imagePath=argv[++i];
        else if(!std::strcmp(argv[i],"-w")&&i+1<argc)W=std::atoi(argv[++i]);
        else if(!std::strcmp(argv[i],"-h")&&i+1<argc)H=std::atoi(argv[++i]);
        else if(!std::strcmp(argv[i],"-n")&&i+1<argc)iters=std::atoi(argv[++i]);
        else {std::printf("Usage: %s [-i 2048x1024.raw] [-w width] [-h height] [-n iterations]\n",argv[0]);
              std::puts("The 2048x1024 input image is tiled to width x height (default 4096x2048).");return 1;}
    }
    if(W<16||H<16||W>16384||H>16384||iters<1){
        std::fprintf(stderr,"Invalid option: need 16 <= -w/-h <= 16384 and -n >= 1\n");return 1;
    }
    constexpr int SW=2048,SH=1024;std::vector<uint8_t> raw(size_t(SW)*SH);
    std::ifstream input(imagePath,std::ios::binary);
    if(!input.read(reinterpret_cast<char*>(raw.data()),raw.size())){
        std::fprintf(stderr,"Cannot read %zu bytes from %s\n",raw.size(),imagePath.c_str());return 1;
    }
    cv::Mat base(SH,SW,CV_8UC1,raw.data()),gray(H,W,CV_8UC1);
    for(int y=0;y<H;++y){int sy=(y/SH)%2?SH-1-y%SH:y%SH;
        for(int x=0;x<W;++x){int sx=(x/SW)%2?SW-1-x%SW:x%SW;
            gray.at<uint8_t>(y,x)=base.at<uint8_t>(sy,sx);}}
    cv::Mat rgb;{cv::Mat planes[3]={gray,255-gray,gray/2+40};cv::merge(planes,3,rgb);}
    int OW=W/2,OH=H/2,hwThreads=cv::getNumThreads();
    if(hwThreads<2)std::printf("Warning: this OpenCV build reports only %d thread; the multi-thread column will not be meaningful.\n\n",hwThreads);
    hipStream_t stream{};CHECK_HIP(hipStreamCreate(&stream));
    hipDeviceProp_t prop{};CHECK_HIP(hipGetDeviceProperties(&prop,0));
    std::printf("Image %dx%d, %d iterations per timing, median of 5\n",W,H,iters);
    std::printf("GPU: %s | OpenCV %s, %d CPU threads\n\n",prop.name,CV_VERSION,hwThreads);
    size_t grayBytes=size_t(W)*H,rgbBytes=grayBytes*3,halfBytes=size_t(OW)*OH,workspaceBytes=0;
    uint8_t *d_gray=nullptr,*d_rgb=nullptr,*d_out=nullptr,*d_half=nullptr,*workspace=nullptr;
    uint8_t *h_in=nullptr,*h_out=nullptr,*h_rgbIn=nullptr;
    CHECK_HIP(hipMalloc(&d_gray,grayBytes));CHECK_HIP(hipMalloc(&d_rgb,rgbBytes));
    CHECK_HIP(hipMalloc(&d_out,grayBytes));CHECK_HIP(hipMalloc(&d_half,halfBytes));
    uint64_t required=0;CHECK_HIP(rocm_image_canny_workspace_size(W,H,&required));workspaceBytes=size_t(required);
    CHECK_HIP(hipMalloc(&workspace,workspaceBytes));
    CHECK_HIP(hipHostMalloc(&h_in,rgbBytes));CHECK_HIP(hipHostMalloc(&h_out,grayBytes));
    CHECK_HIP(hipHostMalloc(&h_rgbIn,rgbBytes));
    std::memcpy(h_in,gray.data,grayBytes);std::memcpy(h_rgbIn,rgb.data,rgbBytes);
    CHECK_HIP(hipMemcpy(d_gray,gray.data,grayBytes,hipMemcpyHostToDevice));
    CHECK_HIP(hipMemcpy(d_rgb,rgb.data,rgbBytes,hipMemcpyHostToDevice));
    auto gauss=[&]{CHECK_HIP(rocm_image_benchmark_gauss5(d_gray,d_out,W,H,stream));};
    auto canny=[&]{CHECK_HIP(rocm_image_canny_local(d_gray,grayBytes,W,W,H,1,60,120,d_out,grayBytes,W,
                                                    workspace,workspaceBytes,stream));};
    auto resize=[&]{CHECK_HIP(rocm_image_benchmark_resize_half(d_gray,d_half,W,H,stream));};
    auto color=[&]{CHECK_HIP(rocm_image_benchmark_rgb_gray(d_rgb,d_out,W,H,stream));};
    auto e2e=[&](const std::function<void()>&op,const uint8_t*hostIn,uint8_t*devIn,size_t inBytes,
                 const uint8_t*devOut,size_t outBytes){return [&,op,hostIn,devIn,inBytes,devOut,outBytes]{
        CHECK_HIP(hipMemcpyAsync(devIn,hostIn,inBytes,hipMemcpyHostToDevice,stream));op();
        CHECK_HIP(hipMemcpyAsync(h_out,devOut,outBytes,hipMemcpyDeviceToHost,stream));
        CHECK_HIP(hipStreamSynchronize(stream));};};
    cv::Mat cvOut,cvHalf,cvGrayFromRgb;
    struct Op {const char*name;std::function<void()>gpu,cpu;const uint8_t*hostIn;uint8_t*devIn;
               size_t inBytes;const uint8_t*devOut;size_t outBytes;int outW,outH;cv::Mat*cvResult;const char*file;};
    std::vector<Op> ops={{"Gaussian 5x5",gauss,[&]{cv::GaussianBlur(gray,cvOut,cv::Size(5,5),0);},
                          h_in,d_gray,grayBytes,d_out,grayBytes,W,H,&cvOut,"gauss.raw"},
                         {"Canny 3x3 L2",canny,[&]{cv::Canny(gray,cvOut,60,120,3,true);},
                          h_in,d_gray,grayBytes,d_out,grayBytes,W,H,&cvOut,"canny.raw"},
                         {"Resize 1/2 bilinear",resize,[&]{cv::resize(gray,cvHalf,cv::Size(OW,OH),0,0,cv::INTER_LINEAR);},
                          h_in,d_gray,grayBytes,d_half,halfBytes,OW,OH,&cvHalf,"resize.raw"},
                         {"RGB to gray",color,[&]{cv::cvtColor(rgb,cvGrayFromRgb,cv::COLOR_RGB2GRAY);},
                          h_rgbIn,d_rgb,rgbBytes,d_out,grayBytes,W,H,&cvGrayFromRgb,"color.raw"}};
    std::vector<Result> results;
    for(auto&op:ops){
        Result r={op.name,0,0,0,0,0};
        r.gpuKernel=timeGpu(op.gpu,stream,iters);
        r.gpuE2E=timeGpu(e2e(op.gpu,op.hostIn,op.devIn,op.inBytes,op.devOut,op.outBytes),stream,iters);
        cv::setNumThreads(1);r.cpu1=timeCpu(op.cpu,std::max(1,iters/4));
        cv::setNumThreads(hwThreads);r.cpuN=timeCpu(op.cpu,iters);
        op.gpu();CHECK_HIP(hipStreamSynchronize(stream));
        cv::Mat gpuResult(op.outH,op.outW,CV_8UC1);
        CHECK_HIP(hipMemcpy(gpuResult.data,op.devOut,op.outBytes,hipMemcpyDeviceToHost));
        op.cpu();r.diff=meanAbsDiff(gpuResult,*op.cvResult);results.push_back(r);save(op.file,gpuResult);
        if(!std::strcmp(op.name,"Canny 3x3 L2"))
            std::printf("Canny edge pixels: ROCm %d, OpenCV %d (algorithm variant; counts may differ)\n\n",
                        cv::countNonZero(gpuResult),cv::countNonZero(*op.cvResult));
    }
    std::printf("%-22s %11s %11s %11s %11s | %9s %9s %9s | %s\n","operation","ROCm kernel","ROCm e2e","CV 1 thr","CV N thr","kernel","e2e","e2e","mean abs");
    for(const auto&r:results)std::printf("%-22s %11.3f %11.3f %11.3f %11.3f | %8.1fx %8.1fx %8.1fx | %.2f\n",
            r.name,r.gpuKernel,r.gpuE2E,r.cpu1,r.cpuN,r.cpu1/r.gpuKernel,r.cpu1/r.gpuE2E,r.cpuN/r.gpuE2E,r.diff);
    CHECK_HIP(hipFree(workspace));CHECK_HIP(hipFree(d_gray));CHECK_HIP(hipFree(d_rgb));
    CHECK_HIP(hipFree(d_out));CHECK_HIP(hipFree(d_half));
    CHECK_HIP(hipHostFree(h_in));CHECK_HIP(hipHostFree(h_out));CHECK_HIP(hipHostFree(h_rgbIn));
    CHECK_HIP(hipStreamDestroy(stream));return 0;
}
