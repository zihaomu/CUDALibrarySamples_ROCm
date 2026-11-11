// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "ccl.h"
#include <array>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace rocm_image_ccl_sample {
inline void check(hipError_t s){if(s!=hipSuccess)throw std::runtime_error(hipGetErrorString(s));}
struct Device {void*p=nullptr;explicit Device(size_t n){check(hipMalloc(&p,n));}~Device(){if(p)hipFree(p);}Device(const Device&)=delete;Device&operator=(const Device&)=delete;};
struct Stream {hipStream_t s=nullptr;Stream(){check(hipStreamCreateWithFlags(&s,hipStreamNonBlocking));}~Stream(){if(s){hipStreamSynchronize(s);hipStreamDestroy(s);}}};
struct Image {
 int w,h;std::string prefix,shape;std::vector<uint8_t> host;std::vector<uint32_t> labels,compact;Device input,raw,comp,count,scratch;rocm_image_ccl8_descriptor descriptor{};
 static size_t work(int w,int h){uint64_t n=0;check(rocm_image_ccl8_workspace_size(w,h,&n));return n;}
 Image(int width,int height,const std::string&name,const std::string&file):w(width),h(height),prefix(name),shape(std::to_string(w)+"x"+std::to_string(h)),host(size_t(w)*h),labels(size_t(w)*h),compact(size_t(w)*h),input(host.size()),raw(host.size()*4),comp(host.size()*4),count(4),scratch(work(w,h)){
  std::ifstream f(file,std::ios::binary);if(!f)throw std::runtime_error("missing input: "+file);f.read(reinterpret_cast<char*>(host.data()),host.size());if(f.gcount()!=long(host.size())||f.peek()!=EOF)throw std::runtime_error("invalid raw input length: "+file);
  descriptor={static_cast<const uint8_t*>(input.p),uint64_t(w),static_cast<uint32_t*>(raw.p),uint64_t(w)*4,static_cast<uint32_t*>(comp.p),uint64_t(w)*4,static_cast<uint32_t*>(count.p),scratch.p,work(w,h),w,h};
 }
 void upload(hipStream_t s){check(hipMemcpyAsync(input.p,host.data(),host.size(),hipMemcpyHostToDevice,s));}
 void save(const std::string&out,bool batch,bool include_compact,hipStream_t s){
  check(hipMemcpyAsync(labels.data(),raw.p,labels.size()*4,hipMemcpyDeviceToHost,s));check(hipMemcpyAsync(compact.data(),comp.p,compact.size()*4,hipMemcpyDeviceToHost,s));uint32_t k=0;check(hipMemcpyAsync(&k,count.p,4,hipMemcpyDeviceToHost,s));check(hipStreamSynchronize(s));
  for(int c=0;c<(include_compact?2:1);++c){std::string n=out+"/"+prefix+"_"+(c?"CompressedMarkerLabels":"LabelMarkers")+(batch?"UFBatch":"UF")+"_8Way_"+shape+"_32u.raw";std::ofstream f(n,std::ios::binary|std::ios::trunc);if(!f)throw std::runtime_error("cannot create output: "+n);auto&v=c?compact:labels;f.write(reinterpret_cast<const char*>(v.data()),v.size()*4);f.close();if(!f)throw std::runtime_error("cannot write output: "+n);std::cout<<n<<" succeeded, compressed label count is "<<k<<"\n";}
 }
};
inline int application(int argc,char**argv,bool batch_compact){try{
 int n=5;bool seen=false;std::string in="../images",out="../images";
 for(int i=1;i<argc;++i){std::string a=argv[i];if(a=="-h"||a=="--help"){std::cout<<"Usage: "<<argv[0]<<" [-b number-of-batch] [--input-dir DIR] [--output-dir DIR]\nnumber-of-batch: 1..5 [default 5]\n";return 0;}
  if(a=="-b"){if(seen||i+1>=argc)throw std::runtime_error("invalid or duplicate -b");seen=true;std::string text=argv[++i];size_t used=0;n=std::stoi(text,&used);if(used!=text.size()||n<1||n>5)throw std::runtime_error("batch count must be 1..5");}
  else if(a=="--input-dir"||a=="--output-dir"){if(i+1>=argc)throw std::runtime_error("missing directory");(a=="--input-dir"?in:out)=argv[++i];}
  else throw std::runtime_error("unknown option: "+a);
 }
 int devices=0;check(hipGetDeviceCount(&devices));if(!devices)throw std::runtime_error("no HIP devices");
 const int widths[]={512,512,509,1024,1280},heights[]={512,512,335,683,720};const char*names[]={"lena","CT_skull","PCB_METAL","PCB2","PCB"};
 // Stream is destroyed first on both success and exception, before images and
 // their host buffers: queued copies never outlive source/destination storage.
 std::vector<std::unique_ptr<Image>>images;Stream stream;
 for(int i=0;i<n;++i){auto im=std::make_unique<Image>(widths[i],heights[i],i==0?"Lena":names[i],in+"/"+names[i]+"_"+std::to_string(widths[i])+"x"+std::to_string(heights[i])+"_8u.raw");images.push_back(std::move(im));images.back()->upload(stream.s);check(rocm_image_ccl8_run(&images.back()->descriptor,stream.s));images.back()->save(out,false,true,stream.s);}
 std::vector<rocm_image_ccl8_descriptor>batch;for(auto&im:images)batch.push_back(im->descriptor);check(rocm_image_ccl8_batch(batch.data(),n,stream.s));for(auto&im:images)im->save(out,true,batch_compact,stream.s);return 0;
 }catch(const std::exception&e){std::cerr<<"CCL error: "<<e.what()<<"\n";return 1;}}
}
