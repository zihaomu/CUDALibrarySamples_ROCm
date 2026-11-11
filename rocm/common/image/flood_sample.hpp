// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "flood.h"
#include <hip/hip_runtime.h>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace image_flood_sample {
namespace fs=std::filesystem;
inline void checked(hipError_t s){if(s!=hipSuccess)throw std::runtime_error(std::string("HIP: ")+hipGetErrorString(s));}
struct Stream {
 hipStream_t value{};Stream(){checked(hipStreamCreate(&value));}
 ~Stream(){if(value){hipStreamSynchronize(value);hipStreamDestroy(value);}}
 Stream(const Stream&)=delete;Stream&operator=(const Stream&)=delete;
};
struct Device {
 void*value{};explicit Device(size_t n){checked(hipMalloc(&value,n));}~Device(){if(value)hipFree(value);}
 Device(const Device&)=delete;Device&operator=(const Device&)=delete;
};
struct Fence {hipStream_t stream;~Fence(){hipStreamSynchronize(stream);}};
struct Case {const char*name;int mode,width,height,sx,sy;const char*input;const char*product;};
inline const std::array<Case,5>&cases(){
 static const std::array<Case,5>v={{
  {"exact-original",0,1024,445,327,426,"RainbowChart_RGB_C3_1024x445_8u.raw","RainbowChart_RGB_C3_Fill_8Way_1024x445_Dev_8u.raw"},
  {"gradient-original",1,1024,445,327,426,"RainbowChart_RGB_C3_1024x445_8u.raw","RainbowChart_RGB_C3_Fill_8Way_Gradient_1024x445_Dev_8u.raw"},
  {"gradient-boundary-original",2,1024,445,327,426,"RainbowChart_RGB_C3_1024x445_8u.raw","RainbowChart_RGB_C3_Fill_8Way_Gradient_Boundary_1024x445_Dev_8u.raw"},
  {"range-original",3,675,1024,20,24,"SeabedSampler_RGB_C3_675x1024_8u.raw","SeabedSampler_RGB_C3_Fill_8Way_Range_675x1024_Dev_8u.raw"},
  {"range-boundary-original",4,675,1024,20,24,"SeabedSampler_RGB_C3_675x1024_8u.raw","SeabedSampler_RGB_C3_Fill_8Way_Range_Boundary_675x1024_Dev_8u.raw"}}};return v;
}
inline std::vector<uint8_t>read(const fs::path&p,size_t n){
 if(!fs::is_regular_file(p)||fs::file_size(p)!=n)throw std::runtime_error("Input size or file invalid: "+p.string());
 std::ifstream f(p,std::ios::binary);std::vector<uint8_t>d(n);if(!f.read(reinterpret_cast<char*>(d.data()),n))throw std::runtime_error("Input read failed: "+p.string());return d;
}
inline void write(const fs::path&p,const void*data,size_t bytes){std::ofstream f(p,std::ios::binary|std::ios::trunc);if(!f||!f.write(static_cast<const char*>(data),bytes)||!f.flush())throw std::runtime_error("Output write failed: "+p.string());}
struct Result {std::vector<uint8_t>input,output,mask;std::array<uint32_t,8>region{};};
inline int main(int argc,char**argv){try{
 fs::path input_dir="../images",output_dir="../images";bool have_input=false,have_output=false;
 for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="--help"){std::puts("Usage: floodFill [--input-dir images] [--output-dir products]\nFive complete RGB flood workflows; default input/output ../images.");return 0;}
  if(a!="--input-dir"&&a!="--output-dir")throw std::runtime_error("Unknown option: "+a);
  bool&seen=a=="--input-dir"?have_input:have_output;if(seen)throw std::runtime_error("Duplicate option: "+a);seen=true;
  if(i+1>=argc||!argv[i+1][0]||std::string(argv[i+1]).rfind("--",0)==0)throw std::runtime_error("Missing option value: "+a);
  if(a=="--input-dir")input_dir=argv[++i];else output_dir=argv[++i];
 }
 std::array<Result,5>results;
 for(size_t i=0;i<cases().size();++i){auto&c=cases()[i];results[i].input=read(input_dir/c.input,size_t(c.width)*c.height*3);if(fs::exists(output_dir/c.product)&&!fs::is_regular_file(output_dir/c.product))throw std::runtime_error("Product path is not a file: "+(output_dir/c.product).string());}
 if(fs::exists(output_dir)&&!fs::is_directory(output_dir))throw std::runtime_error("Output directory is not a directory");
 int count=0;checked(hipGetDeviceCount(&count));if(count<=0)throw std::runtime_error("No HIP GPU available");Stream stream;
 for(size_t i=0;i<cases().size();++i){auto&c=cases()[i];auto&r=results[i];size_t n=size_t(c.width)*c.height;r.output.resize(3*n);r.mask.resize(n);uint64_t wb=0;checked(static_cast<hipError_t>(rocm_image_flood_workspace_size(c.width,c.height,&wb)));
  Device src(3*n),dst(3*n),mask(n),region(32),workspace(wb);Fence fence{stream.value};
  checked(hipMemcpyAsync(src.value,r.input.data(),3*n,hipMemcpyHostToDevice,stream.value));rocm_image_flood_descriptor d{};d.version=1;d.descriptor_bytes=sizeof(d);d.width=c.width;d.height=c.height;d.mode=c.mode;d.seed_x=c.sx;d.seed_y=c.sy;d.input=static_cast<const uint8_t*>(src.value);d.input_pitch=3*c.width;d.output=static_cast<uint8_t*>(dst.value);d.output_pitch=3*c.width;d.mask=static_cast<uint8_t*>(mask.value);d.mask_pitch=c.width;d.region=static_cast<uint32_t*>(region.value);d.workspace=workspace.value;d.workspace_bytes=wb;
  const uint32_t lo[3]={24,24,62},hi[3]={240,248,251},red[3]={255,0,0},green[3]={0,128,0},brown[3]={128,100,0},yellow[3]={255,255,0},purple[3]={255,0,255};
  for(int k=0;k<3;++k){d.lower[k]=c.mode<3?52:lo[k];d.upper[k]=c.mode<3?3:hi[k];d.fill[k]=c.mode<3?red[k]:c.mode==3?green[k]:brown[k];d.boundary[k]=c.mode<3?yellow[k]:purple[k];}
  checked(static_cast<hipError_t>(rocm_image_flood_run(&d,stream.value)));checked(hipMemcpyAsync(r.output.data(),dst.value,3*n,hipMemcpyDeviceToHost,stream.value));checked(hipMemcpyAsync(r.mask.data(),mask.value,n,hipMemcpyDeviceToHost,stream.value));checked(hipMemcpyAsync(r.region.data(),region.value,32,hipMemcpyDeviceToHost,stream.value));checked(hipStreamSynchronize(stream.value));
 }
 fs::create_directories(output_dir);const char*audit=std::getenv("MIGRATION_IMAGE_FLOOD_AUDIT_DIR");
 for(size_t i=0;i<cases().size();++i){auto&c=cases()[i];auto&r=results[i];write(output_dir/c.product,r.output.data(),r.output.size());
  if(audit&&audit[0]){fs::path d=fs::path(audit)/c.name;fs::create_directories(d);write(d/"input.bin",r.input.data(),r.input.size());write(d/"output.bin",r.output.data(),r.output.size());write(d/"mask.bin",r.mask.data(),r.mask.size());write(d/"region.bin",r.region.data(),32);std::string m="{\"case\":\""+std::string(c.name)+"\",\"mode\":"+std::to_string(c.mode)+",\"width\":"+std::to_string(c.width)+",\"height\":"+std::to_string(c.height)+",\"seed\":["+std::to_string(c.sx)+","+std::to_string(c.sy)+"]}\n";write(d/"workflow.json",m.data(),m.size());}
  std::printf("BoundsRect x %u y %u width %u height %u count %u seed0 %u seed1 %u seed2 %u.\n",r.region[0],r.region[1],r.region[2],r.region[3],r.region[4],r.region[5],r.region[6],r.region[7]);
 }
 return 0;
}catch(const std::exception&e){std::fprintf(stderr,"Flood fill error: %s\n",e.what());return 1;}}
}
