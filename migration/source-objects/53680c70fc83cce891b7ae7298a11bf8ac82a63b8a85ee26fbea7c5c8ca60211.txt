// SPDX-License-Identifier: Apache-2.0
// Original API semantic observations; this probe is not a ROCm implementation.
#include <cuda_runtime.h>
#ifdef IMAGE_NPP_PLUS
#define NPP_PLUS_ENABLE
#include <nppPlus/nppPlus.h>
using namespace nppPlusV;
#else
#include <npp.h>
#endif
#include <nppi.h>
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
static void check(cudaError_t e){if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}
static void save(const std::string& p,const void* v,size_t n){std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(v),n);if(!f)throw std::runtime_error("write failed");}
int main(int argc,char** argv){try{
 if(argc!=3)throw std::runtime_error("input and output directories required");
 check(cudaSetDevice(0));cudaDeviceProp device{};check(cudaGetDeviceProperties(&device,0));char pci[32]{};check(cudaDeviceGetPCIBusId(pci,sizeof(pci),0));
 NppStreamContext ctx{};check(cudaStreamCreate(&ctx.hStream));ctx.nCudaDeviceId=0;
 ctx.nMultiProcessorCount=device.multiProcessorCount;ctx.nMaxThreadsPerMultiProcessor=device.maxThreadsPerMultiProcessor;
 ctx.nMaxThreadsPerBlock=device.maxThreadsPerBlock;ctx.nSharedMemPerBlock=device.sharedMemPerBlock;
 ctx.nCudaDevAttrComputeCapabilityMajor=device.major;ctx.nCudaDevAttrComputeCapabilityMinor=device.minor;
 check(cudaStreamGetFlags(ctx.hStream,&ctx.nStreamFlags));
 const NppLibraryVersion* version=nppGetLibVersion();std::cout<<"DEVICE "<<device.name<<" PCI "<<pci<<" NPP "<<version->major<<'.'<<version->minor<<'.'<<version->build<<'\n';
 std::filesystem::create_directories(argv[2]);std::ifstream list(std::string(argv[1])+"/cases.txt");std::string name;int w,h;
 while(list>>name>>w>>h){
  if(w<1||h<1||w>2048||h>2048)throw std::runtime_error("probe shape");
  std::vector<uint8_t> input(size_t(w)*h);std::ifstream f(std::string(argv[1])+"/"+name+".raw",std::ios::binary);f.read(reinterpret_cast<char*>(input.data()),input.size());if(f.gcount()!=std::streamsize(input.size())||f.peek()!=EOF)throw std::runtime_error("input extent");
  const int pitch=w+7,lpitch=(w+5)*4;NppiSize roi{w,h};size_t scratch_bytes=0;
  NppStatus bs=nppiSegmentWatershedGetBufferSize_8u_C1R(roi,&scratch_bytes);
  if(bs!=NPP_SUCCESS){std::cout<<"SIZE_REJECTION "<<name<<' '<<int(bs)<<'\n';continue;}
  Npp8u* image=nullptr;Npp32u* labels=nullptr;Npp8u* scratch=nullptr;
  check(cudaMalloc(&image,size_t(pitch)*h));check(cudaMalloc(&labels,size_t(lpitch)*h));check(cudaMalloc(&scratch,std::max(size_t(1),scratch_bytes)));
  for(int norm: {4,8})for(int mode=0;mode<5;++mode)for(int repeat=0;repeat<3;++repeat){
   check(cudaMemset(image,0xa5,size_t(pitch)*h));check(cudaMemset(labels,0xa5,size_t(lpitch)*h));check(cudaMemset(scratch,repeat==0?0:repeat==1?127:255,std::max(size_t(1),scratch_bytes)));
   check(cudaMemcpy2D(image,pitch,input.data(),w,w,h,cudaMemcpyHostToDevice));
   NppStatus status=nppiSegmentWatershed_8u_C1IR_Ctx(image,pitch,labels,lpitch,norm==4?nppiNormL1:nppiNormInf,static_cast<NppiWatershedSegmentBoundaryType>(mode),roi,scratch,ctx);
   check(cudaStreamSynchronize(ctx.hStream));std::string key=name+"-n"+std::to_string(norm)+"-m"+std::to_string(mode)+"-r"+std::to_string(repeat);
   if(status<0){std::cout<<"API_REJECTION "<<key<<' '<<int(status)<<'\n';continue;}
   std::vector<uint8_t> padded(size_t(pitch)*h),lpadded(size_t(lpitch)*h),seg(size_t(w)*h);std::vector<uint32_t> lab(size_t(w)*h);
   check(cudaMemcpy(padded.data(),image,padded.size(),cudaMemcpyDeviceToHost));check(cudaMemcpy(lpadded.data(),labels,lpadded.size(),cudaMemcpyDeviceToHost));bool guard=true;
   for(int y=0;y<h;++y){std::copy_n(padded.data()+size_t(y)*pitch,w,seg.data()+size_t(y)*w);std::copy_n(lpadded.data()+size_t(y)*lpitch,w*4,reinterpret_cast<uint8_t*>(lab.data()+size_t(y)*w));for(int x=w;x<pitch;++x)guard&=padded[size_t(y)*pitch+x]==0xa5;for(int x=w*4;x<lpitch;++x)guard&=lpadded[size_t(y)*lpitch+x]==0xa5;}
   save(std::string(argv[2])+"/"+key+".segments",seg.data(),seg.size());save(std::string(argv[2])+"/"+key+".labels",lab.data(),lab.size()*4);
   std::cout<<"RESULT "<<key<<" status="<<int(status)<<" padding="<<guard<<" scratch="<<scratch_bytes<<'\n';
  }
  check(cudaFree(scratch));check(cudaFree(labels));check(cudaFree(image));
 }
 if(!list.eof())throw std::runtime_error("case manifest read");check(cudaStreamDestroy(ctx.hStream));return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
