// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "watershed.h"
#include <hip/hip_runtime.h>
#include <array>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

namespace rocm_watershed_sample {
struct Image {const char*input;int width,height;const char*prefix;};
constexpr std::array<Image,5> npp_images{{
 {"Lena_512x512_8u_Gray.raw",512,512,"Lena"},
 {"CT_skull_512x512_8u_Gray.raw",512,512,"CT_skull"},
 {"Rocks_512x512_8u_Gray.raw",512,512,"Rocks"},
 {"coins_500x383_8u_Gray.raw",500,383,"coins"},
 {"coins_overlay_500x569_8u_Gray.raw",500,569,"coins_overlay"}}};
constexpr std::array<Image,3> plus_images{{
 {"CT_skull_512x512_8u_Gray.raw",512,512,"CT_skull"},
 {"Rocks_512x512_8u_Gray.raw",512,512,"Rocks"},
 {"Corn_614x461_8u_Gray.raw",614,461,"Corn"}}};
struct Device {
 uint8_t *input=nullptr,*segments=nullptr,*boundaries=nullptr,*contrast=nullptr;
 uint32_t *labels=nullptr,*compact=nullptr;
 ~Device(){hipFree(input);hipFree(segments);hipFree(boundaries);hipFree(contrast);
   hipFree(labels);hipFree(compact);}
};
inline bool save(const std::string&path,const void*data,size_t bytes){
 FILE*f=std::fopen(path.c_str(),"wb");if(!f)return false;
 bool ok=std::fwrite(data,1,bytes,f)==bytes;ok=std::fclose(f)==0&&ok;return ok;
}
inline bool load(const std::string&path,void*data,size_t bytes){
 FILE*f=std::fopen(path.c_str(),"rb");if(!f)return false;
 bool ok=std::fread(data,1,bytes,f)==bytes;std::fclose(f);return ok;
}
inline bool check(hipError_t code,const char*phase){
 if(code==hipSuccess)return true;
 std::cerr<<phase<<": "<<hipGetErrorString(code)<<"\n";return false;
}
inline bool process(const Image&image,bool plus,hipStream_t stream){
 const std::string base="../images/";size_t n=size_t(image.width)*image.height;
 std::vector<uint8_t> input(n),segments(n),boundaries(plus?n:0),contrast(plus?n:0);
 std::vector<uint32_t> labels(n),compact(plus?n:0);
 if(!load(base+image.input,input.data(),n)){
  std::cerr<<"Failed to load "<<image.input<<"\n";return false;
 }
 Device d;
 if(!check(hipMalloc((void**)&d.input,n),"allocate input")||
    !check(hipMalloc((void**)&d.segments,n),"allocate segments")||
    !check(hipMalloc((void**)&d.labels,4*n),"allocate labels"))return false;
 if(plus&&(!check(hipMalloc((void**)&d.compact,4*n),"allocate compact")||
    !check(hipMalloc((void**)&d.boundaries,n),"allocate boundaries")||
    !check(hipMalloc((void**)&d.contrast,n),"allocate contrast")))return false;
 if(!check(hipMemcpyAsync(d.input,input.data(),n,hipMemcpyHostToDevice,stream),"copy input")||
    !check(rocm_image_watershed8(d.input,d.segments,d.labels,d.compact,
      d.boundaries,d.contrast,image.width,image.height,stream),"watershed GPU"))return false;
 if(!check(hipMemcpyAsync(segments.data(),d.segments,n,hipMemcpyDeviceToHost,stream),"copy segments")||
    !check(hipMemcpyAsync(labels.data(),d.labels,4*n,hipMemcpyDeviceToHost,stream),"copy labels"))return false;
 if(plus&&(!check(hipMemcpyAsync(compact.data(),d.compact,4*n,hipMemcpyDeviceToHost,stream),"copy compact")||
    !check(hipMemcpyAsync(boundaries.data(),d.boundaries,n,hipMemcpyDeviceToHost,stream),"copy boundaries")||
    !check(hipMemcpyAsync(contrast.data(),d.contrast,n,hipMemcpyDeviceToHost,stream),"copy contrast")))return false;
 if(!check(hipStreamSynchronize(stream),"readback synchronize"))return false;
 if(plus){
  std::string suffix="_8Way_"+std::to_string(image.width)+"x"+std::to_string(image.height);
  if(!save(base+image.prefix+"_Segments"+suffix+"_8u.raw",segments.data(),n)||
     !save(base+image.prefix+"_CompressedSegmentLabels"+suffix+"_32u.raw",compact.data(),4*n)||
     !save(base+image.prefix+"_SegmentBoundaries"+suffix+"_8u.raw",boundaries.data(),n)||
     !save(base+image.prefix+"_SegmentsWithContrastingBoundaries"+suffix+"_8u.raw",contrast.data(),n)){
    std::cerr<<"Failed to save products for "<<image.input<<"\n";return false;
  }
 }else if(!save(base+"Segmented_"+image.input,segments.data(),n)||
           !save(base+"Labels_"+image.input,labels.data(),4*n)){
  std::cerr<<"Failed to save products for "<<image.input<<"\n";return false;
 }
 std::cout<<"Processed "<<image.input<<"\n";return true;
}
inline int run(bool plus){
 hipStream_t stream=nullptr;
 if(!check(hipStreamCreate(&stream),"create stream"))return 1;
 bool okay=true;
 if(plus){for(const auto&image:plus_images)if(!process(image,true,stream)){okay=false;break;}}
 else {for(const auto&image:npp_images)if(!process(image,false,stream)){okay=false;break;}}
 if(!check(hipStreamDestroy(stream),"destroy stream"))okay=false;
 return okay?0:1;
}
}
