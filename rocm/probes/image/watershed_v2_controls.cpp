// SPDX-License-Identifier: Apache-2.0
#include <hip/hip_runtime.h>
#include <cstdint>
#include <cstdio>
#include <set>
#include <stdexcept>
#include <vector>
static unsigned calls=0,fail_at=0;static std::set<void*> live;
static hipError_t observed_malloc(void**p,size_t n){
 ++calls;if(fail_at&&calls==fail_at)return hipErrorOutOfMemory;
 auto result=hipMalloc(p,n);if(result==hipSuccess)live.insert(*p);return result;
}
static hipError_t observed_free(void*p){
 if(p){if(!live.erase(p))return hipErrorInvalidValue;}
 return hipFree(p);
}
#define hipMalloc observed_malloc
#define hipFree observed_free
#include "image/watershed_v2.hpp"
#undef hipMalloc
#undef hipFree
namespace ws=image_watershed_v2;
static void checked(hipError_t e){if(e!=hipSuccess)throw std::runtime_error(hipGetErrorString(e));}
int main(){try{
 checked(hipSetDevice(0));char pci[32]{};checked(hipDeviceGetPCIBusId(pci,sizeof(pci),0));std::printf("DEVICE PCI=%s\n",pci);
 std::vector<void*> storage;auto allocate=[&](){void*p=nullptr;checked(hipMalloc(&p,4096));storage.push_back(p);checked(hipMemset(p,0xa5,4096));return p;};
 struct Guard{std::vector<void*>&v;~Guard(){for(void*p:v)hipFree(p);}}guard{storage};
 auto*input=static_cast<uint8_t*>(allocate());ws::Outputs base;
 base.segments={static_cast<uint8_t*>(allocate()),16};base.labels={static_cast<uint32_t*>(allocate()),64};base.compact={static_cast<uint32_t*>(allocate()),64};
 base.boundaries={static_cast<uint8_t*>(allocate()),16};base.contrast={static_cast<uint8_t*>(allocate()),16};
 auto unchanged=[&](){std::vector<uint8_t>host(4096);for(void*p:storage){checked(hipMemcpy(host.data(),p,host.size(),hipMemcpyDeviceToHost));for(auto b:host)if(b!=0xa5)throw std::runtime_error("rejected call wrote to caller memory");}};
 for(int test=0;test<18;++test){
  ws::Outputs out=base;const uint8_t*src=input;size_t pitch=16;int w=8,h=8;
  switch(test){
   case 0:src=nullptr;break;case 1:out.segments.data=nullptr;break;
   case 2:w=0;break;case 3:h=-1;break;case 4:w=INT_MAX;h=2;break;
   case 5:pitch=7;break;case 6:out.segments.pitch=7;break;
   case 7:out.labels.pitch=31;break;case 8:out.labels.pitch=33;break;
   case 9:out.labels.data=reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(out.labels.data)+1);break;
   case 10:out.compact.pitch=28;break;
   case 11:out.compact=out.labels;break;case 12:out.boundaries=out.segments;break;
   case 13:pitch=SIZE_MAX;break;case 14:out.segments.pitch=SIZE_MAX;break;
   case 15:src=reinterpret_cast<const uint8_t*>(UINTPTR_MAX-4);break;
   case 16:out.segments.data=reinterpret_cast<uint8_t*>(UINTPTR_MAX-4);break;
   case 17:out.black=out.contrast;break;
  }
  calls=0;auto result=ws::run(src,pitch,out,w,h);
  if(result!=hipErrorInvalidValue||calls||!live.empty())throw std::runtime_error("invalid view accepted or allocated");unchanged();
  std::printf("INVALID %d status=%d no_allocations=1 unchanged=1\n",test,int(result));
 }
 hipStream_t stream=nullptr;checked(hipStreamCreate(&stream));struct StreamGuard{hipStream_t s;~StreamGuard(){hipStreamDestroy(s);}}sg{stream};
 for(unsigned position=1;position<=9;++position){
  calls=0;fail_at=position;auto result=ws::run(input,16,base,8,8,stream);
  if(result!=hipErrorOutOfMemory||calls!=position||!live.empty())throw std::runtime_error("workspace allocation failure leaked or continued");unchanged();
  std::printf("ALLOCATION_FAILURE %u status=%d live=0 unchanged=1\n",position,int(result));
 }
 calls=0;fail_at=0;checked(ws::run(input,16,base,8,8,stream));
 if(!live.empty()||calls!=9)throw std::runtime_error("successful call leaked");
 std::vector<uint8_t>gray(64),boundary(64),contrast(64);std::vector<uint32_t>labels(64),compact(64);
 checked(hipMemcpy2D(gray.data(),8,base.segments.data,16,8,8,hipMemcpyDeviceToHost));checked(hipMemcpy2D(boundary.data(),8,base.boundaries.data,16,8,8,hipMemcpyDeviceToHost));checked(hipMemcpy2D(contrast.data(),8,base.contrast.data,16,8,8,hipMemcpyDeviceToHost));
 checked(hipMemcpy2D(labels.data(),32,base.labels.data,64,32,8,hipMemcpyDeviceToHost));checked(hipMemcpy2D(compact.data(),32,base.compact.data,64,32,8,hipMemcpyDeviceToHost));
 for(unsigned i=0;i<64;++i)if(gray[i]!=0xa5||boundary[i]!=255||contrast[i]!=0xa5||labels[i]||compact[i])throw std::runtime_error("post-failure recovery result");
 std::printf("RECOVERY successful=1 live=0 pixels=64\n");return 0;
}catch(const std::exception&e){std::fprintf(stderr,"%s\n",e.what());return 1;}}
