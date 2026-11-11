// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "crc_benchmark_observe.hpp"
#include <hiprand/hiprand.h>
#include <array>
#include <memory>
#include <algorithm>
#include <iostream>
#define CUDA_CHECK(x) do{cb_check(int(x));}while(0)
#define cudaError_t hipError_t
#define cudaStream_t hipStream_t
#define cudaEvent_t hipEvent_t
#define cudaSuccess hipSuccess
#define cudaMemGetInfo hipMemGetInfo
#define cudaMalloc hipMalloc
#define cudaFree hipFree
#define cudaHostAlloc hipHostAlloc
#define cudaHostAllocDefault hipHostMallocDefault
#define cudaFreeHost hipHostFree
#define cudaStreamCreate hipStreamCreate
#define cudaStreamDestroy hipStreamDestroy
#define cudaStreamSynchronize hipStreamSynchronize
#define cudaEventCreate hipEventCreate
#define cudaEventDestroy hipEventDestroy
#define cudaEventRecord hipEventRecord
#define cudaEventElapsedTime hipEventElapsedTime
#define cudaMemcpyAsync hipMemcpyAsync
#define cudaMemcpyHostToDevice hipMemcpyHostToDevice
#define curandStatus_t hiprandStatus_t
#define curandGenerator_t hiprandGenerator_t
#define CURAND_STATUS_SUCCESS HIPRAND_STATUS_SUCCESS
#define CURAND_RNG_PSEUDO_DEFAULT HIPRAND_RNG_PSEUDO_DEFAULT
#define curandCreateGenerator hiprandCreateGenerator
#define curandSetPseudoRandomGeneratorSeed hiprandSetPseudoRandomGeneratorSeed
#define curandGenerate hiprandGenerate
#define curandDestroyGenerator hiprandDestroyGenerator
namespace nvcomp {template<class T>inline hipError_t cudaMallocSafe(T**p,size_t n){return hipMalloc(reinterpret_cast<void**>(p),n);}}
namespace crc_benchmark {
inline uint32_t times(const uint32_t*matrix,uint32_t vector){uint32_t result=0;for(int i=0;vector;++i,vector>>=1)if(vector&1)result^=matrix[i];return result;}
inline void square(uint32_t*out,const uint32_t*in){for(int i=0;i<32;++i)out[i]=times(in,in[i]);}
inline uint32_t shift(uint32_t crc,size_t bytes){uint32_t odd[32],even[32];odd[0]=0xedb88320u;uint32_t row=1;for(int i=1;i<32;++i){odd[i]=row;row<<=1;}square(even,odd);square(odd,even);while(bytes){square(even,odd);if(bytes&1)crc=times(even,crc);bytes>>=1;if(!bytes)break;square(odd,even);if(bytes&1)crc=times(odd,crc);bytes>>=1;}return crc;}
struct Workspace {
 uint32_t *table=nullptr,*matrices=nullptr,*a=nullptr,*b=nullptr;size_t segments,count,size;int segment,threads;
 Workspace(size_t n,size_t bytes,int length,int block):segments((bytes+length-1)/length),count(n),size(bytes),segment(length),threads(block){
  std::vector<uint32_t>t(256);for(int i=0;i<256;++i){uint32_t c=i;for(int bit=0;bit<8;++bit)c=(c>>1)^((c&1)?0xedb88320u:0);t[i]=c;}
  std::vector<uint32_t>m;for(size_t width=1;width<segments;width*=2)for(int i=0;i<32;++i)m.push_back(shift(uint32_t(1)<<i,size_t(segment)*width));
  cb_check(hipMalloc(&table,t.size()*4));cb_check(hipMemcpy(table,t.data(),t.size()*4,hipMemcpyHostToDevice));if(!m.empty()){cb_check(hipMalloc(&matrices,m.size()*4));cb_check(hipMemcpy(matrices,m.data(),m.size()*4,hipMemcpyHostToDevice));}
  cb_check(hipMalloc(&a,count*segments*4));cb_check(hipMalloc(&b,count*segments*4));
 }
 ~Workspace(){if(table)hipFree(table);if(matrices)hipFree(matrices);if(a)hipFree(a);if(b)hipFree(b);}
};
__global__ void segments_kernel(const void*const*data,const size_t*sizes,size_t count,size_t segments,int length,const uint32_t*table,uint32_t*out){size_t id=size_t(blockIdx.x)*blockDim.x+threadIdx.x;if(id>=count*segments)return;size_t chunk=id/segments,start=id%segments*length,end=start+length;if(end>sizes[chunk])end=sizes[chunk];uint32_t crc=0xffffffffu;auto*p=(const unsigned char*)data[chunk];for(size_t i=start;i<end;++i)crc=table[(crc^p[i])&255]^(crc>>8);out[id]=crc^0xffffffffu;}
__global__ void combine_kernel(const uint32_t*input,uint32_t*out,size_t chunks,size_t current,const uint32_t*matrix){size_t id=size_t(blockIdx.x)*blockDim.x+threadIdx.x,next=current/2;if(id>=chunks*next)return;size_t chunk=id/next,index=id%next;uint32_t x=input[chunk*current+index*2],result=0;for(int bit=0;x;++bit,x>>=1)if(x&1)result^=matrix[bit];out[id]=result^input[chunk*current+index*2+1];}
inline void launch(Workspace&w,const void*const*data,const size_t*sizes,uint32_t*out,hipStream_t stream){size_t work=w.count*w.segments;segments_kernel<<<(work+w.threads-1)/w.threads,w.threads,0,stream>>>(data,sizes,w.count,w.segments,w.segment,w.table,w.a);cb_check(hipGetLastError());uint32_t*in=w.a,*other=w.b;int level=0;for(size_t n=w.segments;n>1;n/=2,++level){size_t total=w.count*(n/2);combine_kernel<<<(total+255)/256,256,0,stream>>>(in,other,w.count,n,w.matrices+level*32);cb_check(hipGetLastError());std::swap(in,other);}cb_check(hipMemcpyAsync(out,in,w.count*4,hipMemcpyDeviceToDevice,stream));}
}
enum {nvcompSuccess=0,nvcompCRC32=0,nvcompCRC32OnlySegment=0};
using nvcompStatus_t=int;
struct nvcompCRC32KernelConf_t {std::shared_ptr<crc_benchmark::Workspace>workspace;};
struct nvcompBatchedCRC32Opts_t {int kind;nvcompCRC32KernelConf_t config;std::array<int,2>reserved;};
inline int nvcompBatchedCRC32SearchConf(const void*const*data,const size_t*sizes,size_t count,uint32_t*out,int kind,nvcompCRC32KernelConf_t*conf,hipStream_t stream){
 if(!count||!conf||kind!=nvcompCRC32)return 1;std::vector<size_t>host(count);cb_check(hipMemcpyAsync(host.data(),sizes,count*sizeof(size_t),hipMemcpyDeviceToHost,stream));cb_check(hipStreamSynchronize(stream));size_t size=host[0];if(!size||(size&(size-1))||!std::all_of(host.begin(),host.end(),[&](size_t n){return n==size;}))return 1;
 float best=std::numeric_limits<float>::infinity();hipEvent_t start,end;cb_check(hipEventCreate(&start));cb_check(hipEventCreate(&end));std::ofstream log;if(!cb_root().empty())log.open(cb_root()+"/search.jsonl",std::ios::app);log.precision(17);
 for(int segment:{256,1024,4096}){auto w=std::make_shared<crc_benchmark::Workspace>(count,size,segment,segment==256?128:256);cb_check(hipEventRecord(start,stream));crc_benchmark::launch(*w,data,sizes,out,stream);cb_check(hipEventRecord(end,stream));cb_check(hipEventSynchronize(end));float ms=0;cb_check(hipEventElapsedTime(&ms,start,end));cb_values(size,count,out,"segment"+std::to_string(segment));if(log)log<<"{\"size\":"<<size<<",\"count\":"<<count<<",\"segment\":"<<segment<<",\"threads\":"<<w->threads<<",\"elapsed_ms\":"<<ms<<"}\n";if(ms<best){best=ms;conf->workspace=w;}}
 cb_check(hipEventDestroy(start));cb_check(hipEventDestroy(end));return conf->workspace?0:1;
}
inline int nvcompBatchedCRC32Async(const void*const*data,const size_t*sizes,size_t count,uint32_t*out,nvcompBatchedCRC32Opts_t opts,int segment_kind,void*,hipStream_t stream){if(!opts.config.workspace||opts.config.workspace->count!=count||opts.kind!=nvcompCRC32||segment_kind!=nvcompCRC32OnlySegment)return 1;crc_benchmark::launch(*opts.config.workspace,data,sizes,out,stream);return 0;}
inline void cb_cell(size_t size,size_t count,const uint32_t*values,float ms,const nvcompCRC32KernelConf_t&conf){cb_cell_base(size,count,values,ms,conf);if(cb_root().empty())return;std::ofstream f(cb_root()+"/cell_"+std::to_string(size)+"_"+std::to_string(count)+"_selected.json");f<<"{\"segment\":"<<conf.workspace->segment<<",\"threads\":"<<conf.workspace->threads<<"}\n";}
