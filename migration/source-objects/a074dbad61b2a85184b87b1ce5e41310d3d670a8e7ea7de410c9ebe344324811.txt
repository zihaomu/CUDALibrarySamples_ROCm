// SPDX-License-Identifier: Apache-2.0
#include <cuda_runtime.h>
#if defined(USE_NPPPLUS)
#include <nppPlus/nppPlus.h>
#include <npp.h>
#define UF nppPlusV
#else
#include <npp.h>
#if __has_include(<nppworkspace.h>)
#include <nppworkspace.h>
#define USE_WORKSPACE
#endif
#endif
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>
static void ck(cudaError_t s){if(s!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(s));}
static void nk(NppStatus s,const char*n){if(s!=NPP_SUCCESS)throw std::runtime_error(std::string(n)+" status="+std::to_string(s));}
int main(int argc,char**argv){try{
 if(argc!=6)return 2;int w=std::stoi(argv[2]),h=std::stoi(argv[3]),pitch=std::stoi(argv[4]);std::string out=argv[5];NppiSize roi{w,h};
 std::vector<uint8_t>a(size_t(pitch)*h);std::ifstream in(argv[1],std::ios::binary);in.read(reinterpret_cast<char*>(a.data()),a.size());if(in.gcount()!=long(a.size())||in.peek()!=EOF)return 2;
 NppStreamContext ctx{};cudaDeviceProp p{};ck(cudaGetDevice(&ctx.nCudaDeviceId));ck(cudaGetDeviceProperties(&p,ctx.nCudaDeviceId));ctx.nMultiProcessorCount=p.multiProcessorCount;ctx.nMaxThreadsPerMultiProcessor=p.maxThreadsPerMultiProcessor;ctx.nMaxThreadsPerBlock=p.maxThreadsPerBlock;ctx.nSharedMemPerBlock=p.sharedMemPerBlock;ctx.nCudaDevAttrComputeCapabilityMajor=p.major;ctx.nCudaDevAttrComputeCapabilityMinor=p.minor;ck(cudaStreamCreate(&ctx.hStream));ck(cudaStreamGetFlags(ctx.hStream,&ctx.nStreamFlags));
#ifdef USE_WORKSPACE
 nk(nppiWorkspaceCreate(&ctx),"workspace");
#endif
 Npp8u *src=nullptr,*scratch=nullptr;Npp32u*labels=nullptr;ck(cudaMalloc(&src,a.size()));ck(cudaMalloc(&labels,size_t(w)*h*4));ck(cudaMemcpyAsync(src,a.data(),a.size(),cudaMemcpyHostToDevice,ctx.hStream));int bytes=0;nk(nppiLabelMarkersUFGetBufferSize_32u_C1R(roi,&bytes),"label-size");ck(cudaMalloc(&scratch,bytes));
#ifdef USE_NPPPLUS
 nk(UF::nppiLabelMarkersUF_8u32u_C1R_Ctx(src,pitch,labels,w*4,roi,nppiNormInf,scratch,ctx),"label");
#else
 nk(nppiLabelMarkersUF_8u32u_C1R_Ctx(src,pitch,labels,w*4,roi,nppiNormInf,
#ifdef USE_WORKSPACE
 nullptr,
#else
 scratch,
#endif
 ctx),"label");
#endif
 std::vector<uint32_t>b(size_t(w)*h);ck(cudaMemcpyAsync(b.data(),labels,b.size()*4,cudaMemcpyDeviceToHost,ctx.hStream));ck(cudaStreamSynchronize(ctx.hStream));std::ofstream(out+"/labels.bin",std::ios::binary).write(reinterpret_cast<char*>(b.data()),b.size()*4);ck(cudaFree(scratch));scratch=nullptr;
#ifdef USE_NPPPLUS
 nk(UF::nppiCompressMarkerLabelsGetBufferSize_32u_C1R(w*h,&bytes),"compact-size");
#else
 nk(nppiCompressMarkerLabelsGetBufferSize_32u_C1R(w*h,&bytes),"compact-size");
#endif
 ck(cudaMalloc(&scratch,bytes));int count=0;
#ifdef USE_NPPPLUS
 nk(UF::nppiCompressMarkerLabelsUF_32u_C1IR_Ctx(labels,w*4,roi,w*h,&count,scratch,ctx),"compact");
#else
 nk(nppiCompressMarkerLabelsUF_32u_C1IR_Ctx(labels,w*4,roi,w*h,&count,scratch,ctx),"compact");
#endif
 ck(cudaMemcpyAsync(b.data(),labels,b.size()*4,cudaMemcpyDeviceToHost,ctx.hStream));ck(cudaStreamSynchronize(ctx.hStream));std::ofstream(out+"/compact.bin",std::ios::binary).write(reinterpret_cast<char*>(b.data()),b.size()*4);std::ofstream(out+"/counts.json")<<"{\"reported_count\":"<<count<<"}\n";std::printf("GPU=%s labels-and-compression count=%d\n",p.name,count);ck(cudaFree(src));ck(cudaFree(labels));ck(cudaFree(scratch));
#ifdef USE_WORKSPACE
 nk(nppiWorkspaceDestroy(&ctx),"destroy-workspace");
#endif
 ck(cudaStreamDestroy(ctx.hStream));return 0;
 }catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());return 1;}}
