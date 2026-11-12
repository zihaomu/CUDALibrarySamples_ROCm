// SPDX-License-Identifier: Apache-2.0
#include "watershed.h"
#include <hip/hip_runtime.h>
#include <limits.h>

namespace {
constexpr int B=256;
__global__ void select_parent(const uint8_t*image,uint32_t*parent,int w,int h){
 int i=blockIdx.x*blockDim.x+threadIdx.x,n=w*h;if(i>=n)return;
 int x=i%w,y=i/w;unsigned char value=image[i];uint32_t best=i;
 for(int dy=-1;dy<=1;++dy){int yy=y+dy;if(yy<0||yy>=h)continue;
  for(int dx=-1;dx<=1;++dx){int xx=x+dx;if(xx<0||xx>=w)continue;
   int j=yy*w+xx;unsigned char v=image[j];
   if(v<value||(v==value&&uint32_t(j)<best)){value=v;best=j;}
  }
 }
 parent[i]=best;
}
__global__ void jump(const uint32_t*parent,uint32_t*next,int n){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)next[i]=parent[parent[i]];
}
__global__ void render(const uint8_t*image,const uint32_t*roots,uint8_t*segments,
 uint32_t*labels,uint8_t*boundaries,uint8_t*contrast,int w,int h){
 int i=blockIdx.x*blockDim.x+threadIdx.x,n=w*h;if(i>=n)return;
 uint32_t root=roots[i];uint8_t value=image[root];segments[i]=value;labels[i]=root;
 if(!boundaries&&!contrast)return;
 int x=i%w,y=i/w;bool edge=false;
 for(int dy=-1;dy<=1&&!edge;++dy){int yy=y+dy;if(yy<0||yy>=h)continue;
  for(int dx=-1;dx<=1;++dx){int xx=x+dx;if(xx<0||xx>=w)continue;
   if(roots[yy*w+xx]!=root){edge=true;break;}
  }
 }
 if(boundaries)boundaries[i]=edge?0:255;
 if(contrast)contrast[i]=edge?255:value;
}
__global__ void mark_roots(const uint32_t*roots,uint32_t*flags,int n){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)flags[i]=roots[i]==uint32_t(i);
}
__global__ void block_scan(const uint32_t*flags,uint32_t*prefix,uint32_t*sums,int n){
 __shared__ uint32_t values[B];int t=threadIdx.x,i=blockIdx.x*B+t;
 values[t]=i<n?flags[i]:0;__syncthreads();
 for(int delta=1;delta<B;delta*=2){uint32_t add=t>=delta?values[t-delta]:0;
  __syncthreads();values[t]+=add;__syncthreads();}
 if(i<n)prefix[i]=values[t];if(t==B-1)sums[blockIdx.x]=values[t];
}
__global__ void scan_sums(uint32_t*sums,int blocks){
 if(blockIdx.x||threadIdx.x)return;uint32_t offset=0;
 for(int i=0;i<blocks;++i){uint32_t v=sums[i];sums[i]=offset;offset+=v;}
}
__global__ void compact_roots(const uint32_t*roots,const uint32_t*prefix,
 const uint32_t*offsets,uint32_t*compact,int n){
 int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;
 uint32_t root=roots[i];compact[i]=offsets[root/B]+prefix[root]-1;
}
}

extern "C" hipError_t rocm_image_watershed8(const uint8_t*input,uint8_t*segments,
 uint32_t*labels,uint32_t*compact,uint8_t*boundaries,uint8_t*contrast,
 int width,int height,hipStream_t stream){
 if(!input||!segments||!labels||width<=0||height<=0||
    width>INT_MAX/height)return hipErrorInvalidValue;
 const int n=width*height,blocks=(n+B-1)/B;
 uint32_t *a=nullptr,*b=nullptr,*flags=nullptr,*prefix=nullptr,*sums=nullptr;
 auto release=[&](){hipFree(a);hipFree(b);hipFree(flags);hipFree(prefix);hipFree(sums);};
 hipError_t err=hipMalloc((void**)&a,size_t(n)*4);
 if(err==hipSuccess)err=hipMalloc((void**)&b,size_t(n)*4);
 if(err==hipSuccess&&compact)err=hipMalloc((void**)&flags,size_t(n)*4);
 if(err==hipSuccess&&compact)err=hipMalloc((void**)&prefix,size_t(n)*4);
 if(err==hipSuccess&&compact)err=hipMalloc((void**)&sums,size_t(blocks)*4);
 if(err!=hipSuccess){release();return err;}
 hipGetLastError();
 select_parent<<<blocks,B,0,stream>>>(input,a,width,height);
 err=hipGetLastError();
 if(err==hipSuccess){
  for(unsigned span=1;span<unsigned(n);span*=2){
   jump<<<blocks,B,0,stream>>>(a,b,n);err=hipGetLastError();if(err!=hipSuccess)break;
   uint32_t*tmp=a;a=b;b=tmp;
  }
 }
 if(err==hipSuccess){render<<<blocks,B,0,stream>>>(input,a,segments,labels,boundaries,contrast,width,height);
  err=hipGetLastError();}
 if(err==hipSuccess&&compact){
  mark_roots<<<blocks,B,0,stream>>>(a,flags,n);err=hipGetLastError();
  if(err==hipSuccess){block_scan<<<blocks,B,0,stream>>>(flags,prefix,sums,n);err=hipGetLastError();}
  if(err==hipSuccess){scan_sums<<<1,1,0,stream>>>(sums,blocks);err=hipGetLastError();}
  if(err==hipSuccess){compact_roots<<<blocks,B,0,stream>>>(a,prefix,sums,compact,n);err=hipGetLastError();}
 }
 if(err==hipSuccess)err=hipStreamSynchronize(stream);
 release();return err;
}
