// SPDX-License-Identifier: Apache-2.0
#include "flood.h"
#include "connectivity.h"
#include "image_memory.hpp"
#include <cstddef>
#include <limits>
static_assert(sizeof(rocm_image_flood_descriptor)==160,"flood descriptor ABI");
namespace image_flood {
using rocm_image::inactive_component;
inline bool shape(int w,int h,uint64_t&n,uint64_t&bytes){
 if(w<=0||h<=0||w>32768||h>32768)return false;
 n=uint64_t(w)*uint64_t(h);if(n>(uint64_t(1)<<26))return false;
 bytes=((3*n+3)&~uint64_t(3))+4*n+4;return true;
}
inline bool row_span(uint64_t pitch,uint64_t row,int h,uint64_t&bytes){
 if(pitch<row||uint64_t(h-1)>(UINT64_MAX-row)/pitch)return false;
 bytes=uint64_t(h-1)*pitch+row;return true;
}
__global__ void prepare(rocm_image_flood_descriptor d,uint8_t*original,uint32_t*parents){
 int t=blockIdx.x*blockDim.x+threadIdx.x,n=d.width*d.height;if(t>=n)return;
 int x=t%d.width,y=t/d.width;const uint8_t*p=d.input+uint64_t(y)*d.input_pitch+3*x;
 const uint8_t*seed=d.input+uint64_t(d.seed_y)*d.input_pitch+3*d.seed_x;bool allowed=true;
 for(int c=0;c<3;++c){
  original[3*t+c]=p[c];int lo=0,hi=255;
  if(d.mode==0)lo=hi=int(seed[c]);
  else if(d.mode<3){lo=int(seed[c])-int(d.lower[c]);hi=int(seed[c])+int(d.upper[c]);lo=lo<0?0:lo;hi=hi>255?255:hi;}
  else{lo=int(d.lower[c]);hi=int(d.upper[c]);}
  allowed=allowed&&int(p[c])>=lo&&int(p[c])<=hi;
 }
 parents[t]=allowed?uint32_t(t):inactive_component;
 if(t==0){d.region[0]=d.width;d.region[1]=d.height;d.region[2]=d.region[3]=d.region[4]=0;for(int c=0;c<3;++c)d.region[5+c]=seed[c];}
}
__global__ void output(rocm_image_flood_descriptor d,const uint8_t*original,const uint32_t*parents){
 int t=blockIdx.x*blockDim.x+threadIdx.x,n=d.width*d.height;if(t>=n)return;
 int x=t%d.width,y=t/d.width;uint32_t root=parents[d.seed_y*d.width+d.seed_x];
 bool selected=root!=inactive_component&&parents[t]==root,border=false;
 if(selected&&(d.mode==2||d.mode==4)){
  for(int oy=-1;oy<=1;++oy)for(int ox=-1;ox<=1;++ox){
   int xx=x+ox,yy=y+oy;
   if(xx<0||yy<0||xx>=d.width||yy>=d.height||parents[yy*d.width+xx]!=root)border=true;
  }
 }
 for(int c=0;c<3;++c)d.output[uint64_t(y)*d.output_pitch+3*x+c]=selected?uint8_t(border?d.boundary[c]:d.fill[c]):original[3*t+c];
 if(d.mask)d.mask[uint64_t(y)*d.mask_pitch+x]=selected?255:0;
 if(selected){atomicMin(d.region+0,uint32_t(x));atomicMin(d.region+1,uint32_t(y));atomicMax(d.region+2,uint32_t(x));atomicMax(d.region+3,uint32_t(y));atomicAdd(d.region+4,1u);}
}
__global__ void finish(uint32_t*region){if(!region[4])for(int i=0;i<4;++i)region[i]=0;}
}
extern "C" uint32_t rocm_image_flood_abi_version(){return 1;}
extern "C" int rocm_image_flood_workspace_size(int w,int h,uint64_t*bytes){
 if(!bytes)return int(hipErrorInvalidValue);*bytes=0;uint64_t n,size;
 if(!image_flood::shape(w,h,n,size))return int(hipErrorInvalidValue);*bytes=size;return 0;
}
extern "C" int rocm_image_flood_run(const rocm_image_flood_descriptor*pointer,void*stream_pointer){
 if(!pointer)return int(hipErrorInvalidValue);auto d=*pointer;uint64_t n,required;
 if(d.version!=1||d.descriptor_bytes!=sizeof(d)||d.reserved||d.reserved_tail||!image_flood::shape(d.width,d.height,n,required)||d.mode>4||d.seed_x<0||d.seed_y<0||d.seed_x>=d.width||d.seed_y>=d.height||!d.input||!d.output||!d.region||!d.workspace||d.workspace_bytes<required||uintptr_t(d.region)%4||uintptr_t(d.workspace)%4)return int(hipErrorInvalidValue);
 for(int c=0;c<3;++c)if(d.lower[c]>255||d.upper[c]>255||d.fill[c]>255||d.boundary[c]>255||(d.mode>=3&&d.lower[c]>d.upper[c]))return int(hipErrorInvalidValue);
 uint64_t in_bytes,out_bytes,mask_bytes=0;
 if(!image_flood::row_span(d.input_pitch,3*uint64_t(d.width),d.height,in_bytes)||!image_flood::row_span(d.output_pitch,3*uint64_t(d.width),d.height,out_bytes)||(!d.mask&&d.mask_pitch)||(d.mask&&!image_flood::row_span(d.mask_pitch,d.width,d.height,mask_bytes)))return int(hipErrorInvalidValue);
 if(d.input==d.output&&d.input_pitch!=d.output_pitch)return int(hipErrorInvalidValue);
 struct Span{const void*pointer;uint64_t bytes;};Span spans[]={{d.input,in_bytes},{d.output,out_bytes},{d.mask,mask_bytes},{d.region,32},{d.workspace,d.workspace_bytes}};
 for(int i=0;i<5;++i)for(int j=i+1;j<5;++j)if(spans[i].pointer&&spans[j].pointer&&!(i==0&&j==1&&d.input==d.output&&d.input_pitch==d.output_pitch)&&rocm_image::spans_overlap(spans[i].pointer,spans[i].bytes,spans[j].pointer,spans[j].bytes))return int(hipErrorInvalidValue);
 int current=-1,owner=-1;hipError_t status=hipGetDevice(&current);if(status!=hipSuccess)return int(status);
 for(auto s:spans)if(s.pointer){status=rocm_image::device_span(s.pointer,s.bytes,current);if(status!=hipSuccess)return int(status);}
 hipStream_t stream=reinterpret_cast<hipStream_t>(stream_pointer);status=hipStreamGetDevice(stream,&owner);if(status!=hipSuccess)return int(status);if(owner!=current)return int(hipErrorInvalidDevice);
 auto original=static_cast<uint8_t*>(d.workspace);auto parents=reinterpret_cast<uint32_t*>(original+((3*n+3)&~uint64_t(3)));uint32_t*changed=parents+n;
 image_flood::prepare<<<(n+255)/256,256,0,stream>>>(d,original,parents);status=hipGetLastError();if(status!=hipSuccess)return int(status);
 status=rocm_image::converge_components8(parents,nullptr,0,d.width,d.height,changed,stream);if(status!=hipSuccess)return int(status);
 image_flood::output<<<(n+255)/256,256,0,stream>>>(d,original,parents);status=hipGetLastError();if(status!=hipSuccess)return int(status);
 image_flood::finish<<<1,1,0,stream>>>(d.region);return int(hipGetLastError());
}
