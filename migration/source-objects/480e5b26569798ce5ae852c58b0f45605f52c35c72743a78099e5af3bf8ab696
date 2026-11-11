// SPDX-License-Identifier: Apache-2.0
#include "ccl.h"
#include "connectivity.h"
#include "image_memory.hpp"
#include <vector>
namespace {
constexpr int threads=256;
bool shape(int w,int h){return w>0&&h>0&&w<=32768&&h<=32768&&uint64_t(w)*h<=(1u<<28);}
uint64_t scratch_words(uint64_t n){uint64_t words=2*n+1;while(n>256){n=(n+255)/256;words+=2*n;}return words;}
__global__ void initialize(uint32_t*parents,int n){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)parents[i]=i;}
__global__ void root_flags(const uint32_t*parents,uint32_t*flags,int n){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)flags[i]=(parents[i]==uint32_t(i));}
__global__ void block_scan(const uint32_t*in,uint32_t*out,uint32_t*sums,int n){
 __shared__ uint32_t v[threads];int t=threadIdx.x,i=blockIdx.x*threads+t;v[t]=i<n?in[i]:0;__syncthreads();
 for(int d=1;d<threads;d*=2){uint32_t add=t>=d?v[t-d]:0;__syncthreads();v[t]+=add;__syncthreads();}
 if(i<n)out[i]=v[t];if(sums&&t==threads-1)sums[blockIdx.x]=v[t];
}
__global__ void scan_offsets(uint32_t*out,const uint32_t*prefix,int n){int i=blockIdx.x*threads+threadIdx.x;if(i<n&&blockIdx.x)out[i]+=prefix[blockIdx.x-1];}
hipError_t scan(uint32_t*in,uint32_t*out,int n,uint32_t*scratch,hipStream_t stream){
 int blocks=(n+255)/256;block_scan<<<blocks,threads,0,stream>>>(in,out,blocks>1?scratch:nullptr,n);hipError_t s=hipGetLastError();if(s!=hipSuccess||blocks==1)return s;
 uint32_t*prefix=scratch+blocks;s=scan(scratch,prefix,blocks,scratch+2*blocks,stream);if(s!=hipSuccess)return s;
 scan_offsets<<<blocks,threads,0,stream>>>(out,prefix,n);return hipGetLastError();
}
__global__ void output(const uint32_t*parents,const uint32_t*ranks,uint32_t*labels,uint64_t lp,uint32_t*compact,uint64_t cp,uint32_t*count,int w,int n){
 int i=blockIdx.x*threads+threadIdx.x;if(i>=n)return;int x=i%w,y=i/w;uint32_t r=parents[i];reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(labels)+uint64_t(y)*lp)[x]=r+1;reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(compact)+uint64_t(y)*cp)[x]=ranks[r];if(i==n-1)*count=ranks[i];
}
struct Range{const void*pointer;uint64_t bytes;bool write;};
hipError_t validate(const rocm_image_ccl8_descriptor&d,int device,std::vector<Range>&ranges){
 if(!shape(d.width,d.height)||!d.input||!d.labels||!d.compact||!d.count||!d.workspace||d.input_pitch<uint64_t(d.width)||d.labels_pitch<uint64_t(d.width)*4||d.compact_pitch<uint64_t(d.width)*4||d.input_pitch>UINT64_MAX/uint64_t(d.height)||d.labels_pitch>UINT64_MAX/uint64_t(d.height)||d.compact_pitch>UINT64_MAX/uint64_t(d.height)||reinterpret_cast<uintptr_t>(d.workspace)%4||reinterpret_cast<uintptr_t>(d.labels)%4||reinterpret_cast<uintptr_t>(d.compact)%4||reinterpret_cast<uintptr_t>(d.count)%4||d.labels_pitch%4||d.compact_pitch%4)return hipErrorInvalidValue;
 uint64_t required=scratch_words(uint64_t(d.width)*d.height)*4;if(d.workspace_bytes<required)return hipErrorInvalidValue;
 Range add[]={{d.input,uint64_t(d.height-1)*d.input_pitch+uint64_t(d.width),false},{d.labels,uint64_t(d.height-1)*d.labels_pitch+uint64_t(d.width)*4,true},{d.compact,uint64_t(d.height-1)*d.compact_pitch+uint64_t(d.width)*4,true},{d.count,4,true},{d.workspace,required,true}};
 for(auto r:add){auto s=rocm_image::device_span(r.pointer,r.bytes,device);if(s!=hipSuccess)return s;for(auto p:ranges)if((r.write||p.write)&&rocm_image::spans_overlap(r.pointer,r.bytes,p.pointer,p.bytes))return hipErrorInvalidValue;ranges.push_back(r);}return hipSuccess;
}
hipError_t run(const rocm_image_ccl8_descriptor&d,hipStream_t stream){
 int n=d.width*d.height;auto*parents=static_cast<uint32_t*>(d.workspace);uint32_t*ranks=parents+n,*changed=ranks+n,*scratch=changed+1;
 initialize<<<(n+255)/256,threads,0,stream>>>(parents,n);auto s=hipGetLastError();if(s!=hipSuccess)return s;
 s=rocm_image::converge_components8(parents,d.input,d.input_pitch,d.width,d.height,changed,stream);if(s!=hipSuccess)return s;
 root_flags<<<(n+255)/256,threads,0,stream>>>(parents,ranks,n);s=hipGetLastError();if(s!=hipSuccess)return s;
 s=scan(ranks,ranks,n,scratch,stream);if(s!=hipSuccess)return s;
 output<<<(n+255)/256,threads,0,stream>>>(parents,ranks,d.labels,d.labels_pitch,d.compact,d.compact_pitch,d.count,d.width,n);return hipGetLastError();
}
}
extern "C" uint32_t rocm_image_ccl8_abi_version(){return 1;}
extern "C" hipError_t rocm_image_ccl8_workspace_size(int w,int h,uint64_t*bytes){if(!bytes)return hipErrorInvalidValue;*bytes=0;if(!shape(w,h))return hipErrorInvalidValue;*bytes=scratch_words(uint64_t(w)*h)*4;return hipSuccess;}
extern "C" hipError_t rocm_image_ccl8_run(const rocm_image_ccl8_descriptor*d,hipStream_t stream){return rocm_image_ccl8_batch(d,1,stream);}
extern "C" hipError_t rocm_image_ccl8_batch(const rocm_image_ccl8_descriptor*d,int count,hipStream_t stream){
 if(!d||count<=0||count>65536)return hipErrorInvalidValue;
 try{int device=-1;auto s=hipGetDevice(&device);if(s!=hipSuccess)return s;hipDevice_t stream_device=-1;s=hipStreamGetDevice(stream,&stream_device);if(s!=hipSuccess)return s;if(stream_device!=device)return hipErrorInvalidDevice;std::vector<Range>ranges;ranges.reserve(size_t(count)*5);
 for(int i=0;i<count;++i){s=validate(d[i],device,ranges);if(s!=hipSuccess)return s;}
 for(int i=0;i<count;++i){s=run(d[i],stream);if(s!=hipSuccess)return s;}return hipSuccess;
 }catch(...){return hipErrorOutOfMemory;}
}
