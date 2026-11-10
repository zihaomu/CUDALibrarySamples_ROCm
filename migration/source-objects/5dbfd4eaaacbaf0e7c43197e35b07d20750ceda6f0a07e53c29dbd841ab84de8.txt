// SPDX-License-Identifier: Apache-2.0
#pragma once
// Project implementation of the two NCC operations used by the teaching sample.
// This header supplies sample-local types; no NPP binary or SDK is loaded.
#include <hip/hip_runtime.h>
#include <cfloat>
using Npp8u=unsigned char;
using Npp32f=float;
using NppStatus=int;
constexpr int NPP_SUCCESS=0;
struct NppiSize{int width,height;};
struct NppStreamContext{
 hipStream_t hStream;int nCudaDeviceId,nMultiProcessorCount,nMaxThreadsPerMultiProcessor,nMaxThreadsPerBlock;
 size_t nSharedMemPerBlock;int nCudaDevAttrComputeCapabilityMajor,nCudaDevAttrComputeCapabilityMinor;unsigned nStreamFlags;
};
namespace project_ncc {
__global__ void correlate(const unsigned char*src,int stride,const unsigned char*tpl,int tplstride,float*out,int outstride,int w,int h,int tw,int th){
 int t=blockIdx.x*blockDim.x+threadIdx.x,ow=w-tw+1,oh=h-th+1;
 if(t>=ow*oh)return;int x=t%ow,y=t/ow;long long sa=0,sb=0,saa=0,sbb=0,sab=0;
 for(int j=0;j<th;++j)for(int i=0;i<tw;++i){int a=src[(y+j)*stride+x+i],b=tpl[j*tplstride+i];sa+=a;sb+=b;saa+=a*a;sbb+=b*b;sab+=a*b;}
 double count=tw*th,aa=count*saa-double(sa)*sa,bb=count*sbb-double(sb)*sb;
 // The fixed original image profile uses NPP's large-image path: undefined
 // template energy yields FLT_MAX; a constant image patch has zero correlation.
 out[y*outstride+x]=bb<=0?FLT_MAX:aa<=0?0:float((count*sab-double(sa)*sb)/__builtin_sqrt(aa*bb));
}
__global__ void maximum(const float*src,int stride,int w,int h,float*value,int*x,int*y){
 if(threadIdx.x||blockIdx.x)return;int best=0;float score=src[0];
 for(int t=1;t<w*h;++t){float v=src[(t/w)*stride+t%w];if(v>score){score=v;best=t;}}
 *value=score;*x=best%w;*y=best/w;
}
}
inline int nppiValidNormLevelGetBufferHostSize_8u32f_C1R_Ctx(NppiSize,size_t*size,NppStreamContext){*size=1;return 0;}
inline int nppiMaxIndxGetBufferHostSize_32f_C1R_Ctx(NppiSize,size_t*size,NppStreamContext){*size=1;return 0;}
inline int nppiCrossCorrValid_NormLevel_8u32f_C1R_Ctx(const Npp8u*src,int stride,NppiSize image,const Npp8u*tpl,int tplstride,NppiSize pattern,Npp32f*out,int outstride,Npp8u*,NppStreamContext ctx){
 int w=image.width-pattern.width+1,h=image.height-pattern.height+1;
 if(image.width!=2048||image.height!=1024)return -1;
 if(w<=0||h<=0||stride<image.width||tplstride<pattern.width||outstride<int(w*sizeof(float)))return -1;
 project_ncc::correlate<<<(w*h+127)/128,128,0,ctx.hStream>>>(src,stride,tpl,tplstride,out,outstride/sizeof(float),image.width,image.height,pattern.width,pattern.height);return hipGetLastError()==hipSuccess?0:-1;
}
inline int nppiMaxIndx_32f_C1R_Ctx(const Npp32f*src,int stride,NppiSize image,Npp8u*,Npp32f*value,int*x,int*y,NppStreamContext ctx){
 if(image.width<=0||image.height<=0||stride<int(image.width*sizeof(float)))return -1;
 project_ncc::maximum<<<1,1,0,ctx.hStream>>>(src,stride/sizeof(float),image.width,image.height,value,x,y);return hipGetLastError()==hipSuccess?0:-1;
}
