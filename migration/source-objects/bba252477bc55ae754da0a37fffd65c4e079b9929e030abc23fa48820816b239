// SPDX-License-Identifier: Apache-2.0
#include <cuda_runtime.h>
#include <npp.h>
#include <vector>
#include <cstdio>
#include <algorithm>
int main(){
 NppStreamContext ctx{};cudaDeviceProp p{};cudaGetDeviceProperties(&p,0);ctx.nMultiProcessorCount=p.multiProcessorCount;ctx.nMaxThreadsPerMultiProcessor=p.maxThreadsPerMultiProcessor;ctx.nMaxThreadsPerBlock=p.maxThreadsPerBlock;ctx.nSharedMemPerBlock=p.sharedMemPerBlock;ctx.nCudaDevAttrComputeCapabilityMajor=p.major;ctx.nCudaDevAttrComputeCapabilityMinor=p.minor;
 constexpr int w=32,h=24,tw=8,th=8,size=(w-tw+1)*(h-th+1);size_t bytes=0;nppiValidNormLevelGetBufferHostSize_8u32f_C1R_Ctx({w,h},&bytes,ctx);
 unsigned char *a,*b,*scratch;float*c;cudaMalloc(&a,w*h);cudaMalloc(&b,tw*th);cudaMalloc(&c,size*sizeof(float));cudaMalloc(&scratch,std::max(size_t(1),bytes));
 for(int mode=0;mode<4;++mode){std::vector<unsigned char>image(w*h),tpl(tw*th);for(int i=0;i<w*h;++i)image[i]=(mode==1||mode==3)?13:(i*17+i/w*7)%251;for(int i=0;i<tw*th;++i)tpl[i]=(mode==2||mode==3)?13:(i*13+i/tw*9)%251;cudaMemcpy(a,image.data(),w*h,cudaMemcpyHostToDevice);cudaMemcpy(b,tpl.data(),tw*th,cudaMemcpyHostToDevice);
 int rc=nppiCrossCorrValid_NormLevel_8u32f_C1R_Ctx(a,w,{w,h},b,tw,{tw,th},c,(w-tw+1)*4,scratch,ctx);std::vector<float>out(size);cudaMemcpy(out.data(),c,size*4,cudaMemcpyDeviceToHost);
 printf("mode=%d status=%d min=%.9g max=%.9g first=%.9g\n",mode,rc,*std::min_element(out.begin(),out.end()),*std::max_element(out.begin(),out.end()),out[0]);if(rc)return 1;
 }
 cudaFree(a);cudaFree(b);cudaFree(c);cudaFree(scratch);return 0;
}
