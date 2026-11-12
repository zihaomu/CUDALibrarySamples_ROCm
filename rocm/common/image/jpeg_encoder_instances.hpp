// SPDX-License-Identifier: Apache-2.0
// I5 multi-instance adapter: HIP baseline JPEG; optimized DHT still uses libjpeg.
#pragma once
#include "jpeg_encoder_gpu.hpp"
#include "jpeg_full_gpu.hpp"
#include <atomic>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <mutex>
#include <string_view>
#include <thread>
namespace image_jpeg_instances {
namespace fs=std::filesystem;
struct Args {fs::path input,output;int images=0,states=0,threads=-1,runs=1,quality=80;bool write=false,optimize=false,sampling420=true,gpu=true,hardware=false;};
inline int number(const char*s,const char*name,int lo,int hi){
 try{size_t end=0;long long v=std::stoll(s,&end);if(end!=std::string(s).size()||v<lo||v>hi)throw std::runtime_error("range");return int(v);}
 catch(...){throw std::runtime_error(std::string("invalid ")+name);}}
inline Args parse(int argc,const char*argv[]){Args a;for(int i=1;i<argc;++i){std::string k=argv[i];
 if(k=="-i"||k=="-o"||k=="-n"||k=="-s"||k=="-j"||k=="-r"||k=="-q"){
  if(++i==argc)throw std::runtime_error("missing value after "+k);
  if(k=="-i")a.input=argv[i];else if(k=="-o"){a.output=argv[i];a.write=true;}
  else if(k=="-n")a.images=number(argv[i],"image count",0,100000000);
  else if(k=="-s")a.states=number(argv[i],"state count",0,256);
  else if(k=="-j")a.threads=number(argv[i],"thread count",0,256);
  else if(k=="-r")a.runs=number(argv[i],"run count",1,10000);
  else a.quality=number(argv[i],"quality",1,100);
 }else if(k=="-d"){}else if(k=="-f")a.optimize=true;else if(k=="-p")a.sampling420=false;
 else if(k=="-b"){a.gpu=a.hardware=false;int count=0;while(i+1<argc&&argv[i+1][0]!='-'){
  std::string v=argv[++i];if(v=="gpu")a.gpu=true;else if(v=="hardware")a.hardware=true;
  else throw std::runtime_error("unknown backend "+v);++count;}
  if(!count)throw std::runtime_error("missing backend after -b");}
 else throw std::runtime_error("unknown argument "+k);}
 if(a.input.empty())throw std::runtime_error("input BMP directory required (-i)");
 if(!a.gpu)throw std::runtime_error("AMD hardware JPEG encode backend unavailable; select -b gpu");return a;}
inline unsigned le16(const std::vector<unsigned char>&b,size_t o){if(o+2>b.size())throw std::runtime_error("truncated BMP header");return unsigned(b[o])|(unsigned(b[o+1])<<8);}
inline unsigned le32(const std::vector<unsigned char>&b,size_t o){return le16(b,o)|(le16(b,o+2)<<16);}
struct Image{int w,h;std::vector<unsigned char>rgb;};
inline Image bmp(const fs::path&p){auto b=image_jpeg_encoder::read_binary(p.c_str());
 if(b.size()<54||b[0]!='B'||b[1]!='M'||le32(b,14)<40||le16(b,26)!=1||le16(b,28)!=24||le32(b,30)!=0)
  throw std::runtime_error("unsupported/corrupt 24-bit BMP: "+p.string());
 unsigned off=le32(b,10);int w=int(le32(b,18)),signed_h=int(le32(b,22)),h=signed_h<0?-signed_h:signed_h;
 if(w<=0||h<=0||w>16384||h>16384)throw std::runtime_error("invalid BMP dimensions");
 size_t stride=(size_t(w)*3+3)&~size_t(3);
 if(off>b.size()||size_t(h)>(b.size()-off)/stride)throw std::runtime_error("truncated BMP pixels");
 Image out{w,h,std::vector<unsigned char>(size_t(w)*h*3)};
 for(int y=0;y<h;++y)for(int x=0;x<w;++x){int sy=signed_h<0?y:h-1-y;
  auto*q=out.rgb.data()+(size_t(y)*w+x)*3;auto*p=b.data()+off+size_t(sy)*stride+x*3;
  q[0]=p[2];q[1]=p[1];q[2]=p[0];}return out;}
inline bool natural_less(const fs::path&a,const fs::path&b){std::string x=a.string(),y=b.string();size_t i=0,j=0;
 while(i<x.size()&&j<y.size()){
  if(std::isdigit((unsigned char)x[i])&&std::isdigit((unsigned char)y[j])){
   size_t p=i,q=j;while(i<x.size()&&std::isdigit((unsigned char)x[i]))++i;
   while(j<y.size()&&std::isdigit((unsigned char)y[j]))++j;
   auto s=std::string_view(x).substr(p,i-p),t=std::string_view(y).substr(q,j-q);
   while(s.size()>1&&s.front()=='0')s.remove_prefix(1);
   while(t.size()>1&&t.front()=='0')t.remove_prefix(1);
   if(s.size()!=t.size())return s.size()<t.size();if(s!=t)return s<t;
  }else{if(x[i]!=y[j])return x[i]<y[j];++i;++j;}}
 return i==x.size()&&j!=y.size();}
inline std::vector<fs::path> files(const fs::path&dir){if(!fs::is_directory(dir))throw std::runtime_error("input BMP directory missing");
 std::vector<fs::path>v;for(const auto&e:fs::recursive_directory_iterator(dir)){
  auto ext=e.path().extension().string();if(e.is_regular_file()&&(ext==".bmp"||ext==".BMP"))v.push_back(e.path());}
 std::sort(v.begin(),v.end(),natural_less);if(v.empty())throw std::runtime_error("No BMP files in input directory");return v;}
inline int run(int argc,const char*argv[]){
 if(argc==1||(argc==2&&std::string(argv[1])=="-h")){
  std::cout<<"Usage: "<<argv[0]<<" -i indir [-n nimages] [-s nstates] [-j nthreads] [-b gpu|hardware] [-r nruns] [-d] [-o outdir] [-q quality] [-f] [-p]\n";return 0;}
 try{auto a=parse(argc,argv);image_jpeg_encoder::check(hipSetDevice(0),"select AMD GPU");
 hipDeviceProp_t prop{};image_jpeg_encoder::check(hipGetDeviceProperties(&prop,0),"get AMD GPU");
 auto input=files(a.input);if(!a.images)a.images=input.size();
 if(a.threads==0)a.threads=std::max(1u,std::thread::hardware_concurrency());
 if(a.threads<0)a.threads=std::min(2,a.images);if(!a.states)a.states=a.threads;
 a.states=std::max(a.states,a.threads);a.images=std::max(a.images,a.states);
 if(a.write)fs::create_directories(a.output);
 double best=0,latency=0;for(int rep=0;rep<a.runs;++rep){
  std::atomic<int>next{0},completed{0};std::mutex lock;std::string failure;
  auto start=std::chrono::steady_clock::now();std::vector<std::thread>workers;
  for(int tid=0;tid<a.threads;++tid)workers.emplace_back([&,tid]{try{
   image_jpeg_encoder::check(hipSetDevice(0),"worker GPU");std::vector<hipStream_t>streams;
   for(int state=tid;state<a.states;state+=a.threads){hipStream_t stream=nullptr;
    image_jpeg_encoder::check(hipStreamCreateWithFlags(&stream,hipStreamNonBlocking),"state stream");streams.push_back(stream);}
   for(int i=next.fetch_add(1),slot=0;i<a.images;i=next.fetch_add(1),++slot){auto pic=bmp(input[i%input.size()]);
    fs::path out=a.write?a.output/(std::to_string(i)+".jpg"):
      fs::temp_directory_path()/("rocm-jpeg-"+std::to_string(rep)+"-"+std::to_string(tid)+"-"+std::to_string(i)+".jpg");
    auto stream=streams[slot%streams.size()];
    if(a.optimize){
     image_jpeg_encoder::encode(pic.rgb,pic.w,pic.h,a.quality,a.sampling420?2:1,
       out.c_str(),true,stream);
    }else{
     auto jpeg=image_jpeg_full::encode(pic.rgb,pic.w,pic.h,a.quality,
       a.sampling420?2:1,stream);
     image_jpeg_encoder::write_binary(out.c_str(),jpeg.data(),jpeg.size());
    }
    if(!a.write)fs::remove(out);++completed;}
   for(auto stream:streams)image_jpeg_encoder::check(hipStreamDestroy(stream),"destroy state stream");
  }catch(const std::exception&e){std::lock_guard<std::mutex>guard(lock);if(failure.empty())failure=e.what();}});
  for(auto&worker:workers)worker.join();if(!failure.empty())throw std::runtime_error(failure);
  if(completed!=a.images)throw std::runtime_error("incomplete multi-instance encode");
  double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
  if(ms<=0)throw std::runtime_error("invalid elapsed time");best=std::max(best,completed*1000.0/ms);latency=ms/completed;}
 std::cout<<"GPU: "<<prop.name<<"\nNum hardware encode engines: 0\nInput: "<<a.input
 <<"\nEnabled backends: gpu\nSubsampling 420: "<<(a.sampling420?"on":"off")
 <<"\nOptimized Huffman: "<<(a.optimize?"on":"off")<<"\nQuality: "<<a.quality
 <<"\nThroughput: "<<best<<" images/s\nLatency: "<<latency<<" ms\nPercentage: 100, 0 %\nNum threads: "
 <<a.threads<<"\nNum states: "<<a.states<<"\nNum runs: "<<a.runs
 <<"\nRESULT status=PASS encoded="<<a.images<<" cpu_entropy="<<(a.optimize?1:0)
 <<" gpu_full_encode="<<(a.optimize?0:1)<<" gpu_fdct=1 hardware_encoder=0\n";return 0;
 }catch(const std::exception&e){std::cerr<<"RESULT status=FAIL reason="<<e.what()<<'\n';return 1;}}
} // namespace image_jpeg_instances
