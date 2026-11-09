// SPDX-License-Identifier: Apache-2.0
#include "check.hpp"
#include <rocjpeg/rocjpeg.h>
#include <iterator>
using namespace sample;
int main(int argc,char**argv){return run([&]{
 if(argc<2)throw std::runtime_error("provide JPEG input path");std::ifstream f(argv[1],std::ios::binary);std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(f)),{});if(bytes.empty())throw std::runtime_error("empty JPEG input");RocJpegStreamHandle stream=nullptr;CHECK(rocJpegStreamCreate(&stream));CHECK(rocJpegStreamParse(bytes.data(),bytes.size(),stream));RocJpegHandle handle=nullptr;
 CHECK(rocJpegCreate(ROCJPEG_BACKEND_HARDWARE,0,&handle));uint8_t nc=0;RocJpegChromaSubsampling css;uint32_t w[4]={},h[4]={};CHECK(rocJpegGetImageInfo(handle,stream,&nc,&css,w,h));Device<unsigned char> output(w[0]*h[0]*3);RocJpegImage image{};image.channel[0]=output.p;image.pitch[0]=w[0]*3;RocJpegDecodeParams params{};params.output_format=ROCJPEG_OUTPUT_RGB;CHECK(rocJpegDecode(handle,stream,&params,&image));CHECK(hipDeviceSynchronize());auto pixels=output.get();std::ofstream dst("build/rocjpeg-rgb.bin",std::ios::binary);dst.write((char*)pixels.data(),pixels.size());std::cout<<"{\"width\":"<<w[0]<<",\"height\":"<<h[0]<<",\"components\":"<<int(nc)<<"}"<<std::endl;CHECK(rocJpegDestroy(handle));CHECK(rocJpegStreamDestroy(stream));
});}
