/* SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 * ROCm implementation of the original color-edge file/benchmark workflow.
 */
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/imgcodecs.hpp>
#include "canny_color.h"
#include <hip/hip_runtime.h>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {
void check(hipError_t s){if(s!=hipSuccess)throw std::runtime_error(hipGetErrorString(s));}
struct Buffer {
 void*p=nullptr;uint64_t bytes=0;
 explicit Buffer(uint64_t n):bytes(n){check(hipMalloc(&p,n));}
 ~Buffer(){if(p)hipFree(p);}
 Buffer(const Buffer&)=delete;Buffer&operator=(const Buffer&)=delete;
 Buffer(Buffer&&)=delete;Buffer&operator=(Buffer&&)=delete;
};
void raw(const std::string&name,const cv::Mat&a){std::ofstream f(name,std::ios::binary);for(int y=0;y<a.rows;++y)f.write(reinterpret_cast<const char*>(a.ptr(y)),a.cols*a.elemSize());if(!f)throw std::runtime_error("Audit file write failed");}
void save(const std::string&name,const cv::Mat&a){if(!cv::imwrite(name,a))throw std::runtime_error("Image output failed: "+name);}
double elapsed(std::chrono::steady_clock::time_point start){return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();}
uint64_t scratch(int w,int h){uint64_t n=0;check(rocm_image_canny_color_workspace_size(w,h,&n));return n;}
}
class NPPCanny {
 int width,height;Buffer workspace,source,output;
public:
 NPPCanny(int w,int h):width(w),height(h),workspace(scratch(w,h)),source(uint64_t(w)*h*3),output(uint64_t(w)*h){}
 ~NPPCanny(){hipStreamSynchronize(0);}
 cv::Mat detect(const cv::Mat&image,int low=50,int high=100){
  if(image.cols!=width||image.rows!=height||image.type()!=CV_8UC3)throw std::runtime_error("Image size/type mismatch");
  if(low<0||high<low||high>32767)throw std::runtime_error("Invalid thresholds");
  check(hipMemcpy2DAsync(source.p,width*3,image.data,image.step,width*3,height,hipMemcpyHostToDevice,0));
  check(rocm_image_canny_color(static_cast<uint8_t*>(source.p),source.bytes,width*3,width,height,low,high,static_cast<uint8_t*>(output.p),output.bytes,width,workspace.p,workspace.bytes,0));
  cv::Mat edges(height,width,CV_8UC1);check(hipMemcpy2DAsync(edges.data,edges.step,output.p,width,width,height,hipMemcpyDeviceToHost,0));check(hipStreamSynchronize(0));return edges;
 }
};
int main(int argc,char**argv){try{
 std::string path=argc>1?argv[1]:"image.jpg";cv::Mat image=cv::imread(path);
 if(image.empty())throw std::runtime_error("Could not read "+path);
 int count=0;check(hipGetDeviceCount(&count));if(!count)throw std::runtime_error("No HIP device");hipDeviceProp_t props{};int device=0;check(hipGetDevice(&device));check(hipGetDeviceProperties(&props,device));
 std::cout<<"Image: "<<image.cols<<"x"<<image.rows<<"\nGPU: "<<props.name<<"\nOpenCV: "<<CV_VERSION<<"\nBackend: Project HIP classical C3 Canny\n";
 NPPCanny detector(image.cols,image.rows);cv::Mat edges=detector.detect(image);std::vector<double>timings;
 for(int i=0;i<10;++i){auto start=std::chrono::steady_clock::now();edges=detector.detect(image);timings.push_back(elapsed(start));}
 cv::Mat gray,gray_edges;cv::cvtColor(image,gray,cv::COLOR_BGR2GRAY);auto start=std::chrono::steady_clock::now();for(int i=0;i<10;++i)cv::Canny(gray,gray_edges,50,100,3,true);double gray_ms=elapsed(start)/10;
 std::vector<cv::Mat>channels;cv::split(image,channels);cv::Mat b,g,r,merged;start=std::chrono::steady_clock::now();
 for(int i=0;i<10;++i){cv::Canny(channels[0],b,50,100,3,true);cv::Canny(channels[1],g,50,100,3,true);cv::Canny(channels[2],r,50,100,3,true);cv::bitwise_or(r,g,merged);cv::bitwise_or(merged,b,merged);}double color_ms=elapsed(start)/10;
 double hip_ms=0;for(double t:timings)hip_ms+=t/10;int hip_count=cv::countNonZero(edges),gray_count=cv::countNonZero(gray_edges),color_count=cv::countNonZero(merged);
 std::cout<<std::setprecision(17)<<"HIP 3-Channel: "<<hip_ms<<" ms ("<<hip_count<<" edges)\nOpenCV Grayscale: "<<gray_ms<<" ms ("<<gray_count<<" edges)\nOpenCV 3-Channel: "<<color_ms<<" ms ("<<color_count<<" edges)\n";
 if(hip_ms>0)std::cout<<"Gray/HIP elapsed ratio: "<<gray_ms/hip_ms<<"\n3-channel/HIP elapsed ratio: "<<color_ms/hip_ms<<"\n";
 if(gray_count)std::cout<<"Extra edges vs Gray (%): "<<100.*(hip_count-gray_count)/gray_count<<"\n";else std::cout<<"Extra edges vs Gray: undefined (no gray edges)\n";
 save("edges_npp.png",edges);save("edges_opencv_gray.png",gray_edges);save("edges_opencv_3ch.png",merged);
 if(const char*dir=std::getenv("MIGRATION_IMAGE_AUDIT_DIR")){
  std::string root=dir;raw(root+"/input.bin",image);raw(root+"/mask.bin",edges);std::ofstream f(root+"/workflow.json");f<<std::setprecision(17)<<"{\"width\":"<<image.cols<<",\"height\":"<<image.rows<<",\"warmup\":1,\"iterations\":10,\"gray_iterations\":10,\"color_iterations\":10,\"timings_ms\":[";for(size_t i=0;i<timings.size();++i)f<<(i?",":"")<<timings[i];f<<"],\"gray_ms\":"<<gray_ms<<",\"color_ms\":"<<color_ms<<",\"backend\":\"Project HIP classical C3 Canny\"}\n";if(!f)throw std::runtime_error("Audit metadata write failed");
 }
 return 0;
}catch(const std::exception&error){std::cerr<<"Error: "<<error.what()<<"\n";return 1;}}
