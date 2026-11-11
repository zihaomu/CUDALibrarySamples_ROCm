// SPDX-License-Identifier: Apache-2.0
#include "connectivity.h"
namespace rocm_image {
namespace {
__device__ uint32_t root(uint32_t*parent,uint32_t x){
 uint32_t next=atomicAdd(parent+x,0u);
 while(next!=inactive_component&&next!=x){x=next;next=atomicAdd(parent+x,0u);}
 return next;
}
__global__ void hook(uint32_t*parent,const uint8_t*values,uint64_t pitch,int w,int h,uint32_t*changed){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=w*h||atomicAdd(parent+t,0u)==inactive_component)return;
 int x=t%w,y=t/w;
 for(int oy=-1;oy<=1;++oy)for(int ox=-1;ox<=1;++ox){
  int xx=x+ox,yy=y+oy;if(xx<0||yy<0||xx>=w||yy>=h||(!ox&&!oy))continue;
  int q=yy*w+xx;if(atomicAdd(parent+q,0u)==inactive_component)continue;
  if(values&&values[uint64_t(y)*pitch+x]!=values[uint64_t(yy)*pitch+xx])continue;
  uint32_t a=root(parent,t),b=root(parent,q);if(a==b)continue;
  uint32_t hi=a>b?a:b,lo=a>b?b:a;
  if(atomicMin(parent+hi,lo)>lo)atomicExch(changed,1u);
 }
}
__global__ void compress(uint32_t*parent,int n){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<n&&atomicAdd(parent+t,0u)!=inactive_component)atomicMin(parent+t,root(parent,t));
}
}
hipError_t converge_components8(uint32_t*parents,const uint8_t*values,uint64_t pitch,int w,int h,uint32_t*changed,hipStream_t stream){
 const int n=w*h;uint32_t host_changed=1;
 for(int round=0;round<=n;++round){
  hipError_t status=hipMemsetAsync(changed,0,sizeof(uint32_t),stream);if(status!=hipSuccess)return status;
  hook<<<(n+255)/256,256,0,stream>>>(parents,values,pitch,w,h,changed);status=hipGetLastError();if(status!=hipSuccess)return status;
  compress<<<(n+255)/256,256,0,stream>>>(parents,n);status=hipGetLastError();if(status!=hipSuccess)return status;
  status=hipMemcpyAsync(&host_changed,changed,sizeof(uint32_t),hipMemcpyDeviceToHost,stream);if(status!=hipSuccess)return status;
  status=hipStreamSynchronize(stream);if(status!=hipSuccess)return status;
  if(!host_changed)return hipSuccess;
 }
 return hipErrorUnknown;
}
}
