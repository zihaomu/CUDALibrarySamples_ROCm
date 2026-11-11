// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "distance.h"
#include <hip/hip_runtime.h>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace image_distance_sample {
namespace fs=std::filesystem;
inline void check(int status,const char*operation){if(status)throw std::runtime_error(std::string(operation)+": "+hipGetErrorString(static_cast<hipError_t>(status)));}
struct Stream{
 hipStream_t value{};
 Stream(){check(hipStreamCreateWithFlags(&value,hipStreamNonBlocking),"create HIP stream");}
 ~Stream(){if(value){hipStreamSynchronize(value);hipStreamDestroy(value);}}
 Stream(const Stream&)=delete;Stream&operator=(const Stream&)=delete;
};
template<class T>struct Device{
 T*p{};explicit Device(size_t n){check(hipMalloc(reinterpret_cast<void**>(&p),n*sizeof(T)),"allocate HIP buffer");}
 ~Device(){if(p)hipFree(p);}Device(const Device&)=delete;Device&operator=(const Device&)=delete;
};
struct Fence{hipStream_t stream;~Fence(){hipStreamSynchronize(stream);}};
struct Job{const char*name;const char*input;const char*prefix;int width,height;uint32_t mode,type,remap;double cutoff;};
inline const std::array<Job,5> jobs={{
 {"unsigned-original","DistanceSampler_512x512_8u.raw","DistanceSamplerTransform_512x512",512,512,0,0,0,0.},
 {"unsigned-original-inverted","DistanceSampler_512x512_Inverted_8u.raw","DistanceSamplerTransform_512x512_Inverted",512,512,0,0,0,0.},
 {"signed-circle-original","SignedCircle_256x206_64f.raw","SignedDistanceCircleTransform_256x206",256,206,1,2,1,0.},
 {"signed-circle-original-inverted","SignedCircle_256x206_Inverted_64f.raw","SignedDistanceCircleTransform_256x206_Inverted",256,206,1,2,1,0.},
 {"signed-lith-original","SignedLith_554x554_32f.raw","SignedDistanceLithTransform_554x554",554,554,1,1,0,double(.1f)}
}};
inline std::vector<unsigned char> read(const fs::path&p,size_t bytes){
 std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("input file missing: "+p.string());std::vector<unsigned char>data((std::istreambuf_iterator<char>(f)),{});if(f.bad()||data.size()!=bytes)throw std::runtime_error("input file length mismatch: "+p.string());return data;
}
template<class T>inline void write(const fs::path&p,const std::vector<T>&data){
 std::ofstream f(p,std::ios::binary|std::ios::trunc);if(!f)throw std::runtime_error("output file open failed: "+p.string());f.write(reinterpret_cast<const char*>(data.data()),std::streamsize(data.size()*sizeof(T)));f.close();if(!f)throw std::runtime_error("output file write failed: "+p.string());
}
template<class T>inline void copy(std::vector<T>&host,const Device<T>&device,hipStream_t stream){check(hipMemcpyAsync(host.data(),device.p,host.size()*sizeof(T),hipMemcpyDeviceToHost,stream),"read back HIP output");}
struct Result{std::vector<double>distance,sites;std::vector<uint16_t>visual;std::vector<int16_t>indices,relative;std::vector<uint64_t>ids;};
inline Result compute(const Job&j,const std::vector<unsigned char>&input,hipStream_t stream){
 size_t n=size_t(j.width)*j.height;uint64_t bytes=0;check(rocm_image_distance_workspace_size(j.width,j.height,&bytes),"query distance workspace");Device<unsigned char>src(input.size()),work(bytes);Device<double>distance(n),sites(2*n);Device<uint16_t>visual(n);Device<int16_t>indices(2*n),relative(2*n);Device<uint64_t>ids(n);Result result;Fence fence{stream};result.distance.resize(n);result.visual.resize(n);result.indices.resize(2*n);result.relative.resize(2*n);result.ids.resize(n);result.sites.resize(2*n);check(hipMemcpyAsync(src.p,input.data(),input.size(),hipMemcpyHostToDevice,stream),"upload original image");rocm_image_distance_descriptor d{};d.input=src.p;d.input_pitch=uint64_t(j.width)*(j.type==0?1:j.type==1?4:8);d.distance=distance.p;d.distance_pitch=uint64_t(j.width)*8;d.visualization=visual.p;d.visualization_pitch=uint64_t(j.width)*2;d.indices=indices.p;d.indices_pitch=uint64_t(j.width)*4;d.relative=relative.p;d.relative_pitch=uint64_t(j.width)*4;d.site_ids=ids.p;d.site_ids_pitch=uint64_t(j.width)*8;d.sites_xy=sites.p;d.sites_xy_pitch=uint64_t(j.width)*16;d.workspace=work.p;d.workspace_bytes=bytes;d.cutoff=j.cutoff;d.width=j.width;d.height=j.height;d.mode=j.mode;d.input_type=j.type;d.remap_circle=j.remap;check(rocm_image_distance_run(&d,reinterpret_cast<void*>(stream)),"execute HIP distance transform");copy(result.distance,distance,stream);copy(result.visual,visual,stream);copy(result.indices,indices,stream);copy(result.relative,relative,stream);copy(result.ids,ids,stream);copy(result.sites,sites,stream);check(hipStreamSynchronize(stream),"complete distance workflow");return result;
}
inline void audit(const fs::path&base,const Job&j,const std::vector<unsigned char>&input,const Result&r){
 fs::path p=base/j.name;fs::create_directories(p);write(p/"input.bin",input);write(p/"distance.bin",r.distance);write(p/"visualization.bin",r.visual);write(p/"indices.bin",r.indices);write(p/"relative.bin",r.relative);write(p/"site_ids.bin",r.ids);write(p/"sites_xy.bin",r.sites);std::ofstream f(p/"workflow.json");if(!f)throw std::runtime_error("audit metadata open failed");f<<std::setprecision(17)<<"{\"case\":\""<<j.name<<"\",\"width\":"<<j.width<<",\"height\":"<<j.height<<",\"mode\":"<<j.mode<<",\"input_type\":"<<j.type<<",\"remap_circle\":"<<j.remap<<",\"cutoff\":"<<j.cutoff<<"}\n";f.close();if(!f)throw std::runtime_error("audit metadata write failed");
}
inline int main(int argc,char**argv){
 try{
  fs::path input="../images",output="../images";bool input_seen=false,output_seen=false;
  if(argc==2&&std::string(argv[1])=="--help"){std::cout<<"Usage: "<<argv[0]<<" [--input-dir DIR] [--output-dir DIR]\nRuns all five original inputs and writes twelve RAW outputs.\n";return 0;}
  for(int i=1;i<argc;++i){std::string key=argv[i];if(key!="--input-dir"&&key!="--output-dir")throw std::runtime_error("unknown option: "+key);if(i+1>=argc)throw std::runtime_error("missing option value: "+key);std::string value=argv[++i];if(value.empty()||value.rfind("--",0)==0)throw std::runtime_error("invalid option value: "+key);bool&seen=key=="--input-dir"?input_seen:output_seen;if(seen)throw std::runtime_error("duplicate option: "+key);seen=true;(key=="--input-dir"?input:output)=value;}
  std::array<std::vector<unsigned char>,5>inputs;for(size_t i=0;i<jobs.size();++i){const auto&j=jobs[i];inputs[i]=read(input/j.input,size_t(j.width)*j.height*(j.type==0?1:j.type==1?4:8));}
  fs::create_directories(output);Stream stream;std::array<Result,5>results;for(size_t i=0;i<jobs.size();++i)results[i]=compute(jobs[i],inputs[i],stream.value);
  const char*audit_dir=std::getenv("MIGRATION_IMAGE_DISTANCE_AUDIT_DIR");
  for(size_t i=0;i<jobs.size();++i){const auto&j=jobs[i];const auto&r=results[i];write(output/(std::string(j.prefix)+"_64f.raw"),r.distance);write(output/(std::string(j.prefix)+"_16u.raw"),r.visual);if(j.type==1){write(output/"SignedDistanceLithTransformVoronoiIndices_554x554_16s.raw",r.indices);write(output/"SignedDistanceLithTransformVoronoiRelativeManhattan_554x554_16s.raw",r.relative);}if(audit_dir&&*audit_dir)audit(audit_dir,j,inputs[i],r);std::cout<<"Distance GPU workflow complete: "<<j.name<<" "<<j.width<<"x"<<j.height<<" mode "<<j.mode<<" input_type "<<j.type<<"\n";}
  return 0;
 }catch(const std::exception&e){std::cerr<<"Distance error: "<<e.what()<<"\n";return 1;}
}
}
