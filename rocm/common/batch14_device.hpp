// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batches_runtime.hpp"
#ifdef __HIP_PLATFORM_AMD__
#include <rocrand/rocrand_philox4x32_10.h>
#define R14_STATE rocrand_state_philox4x32_10
#define R14_INIT rocrand_init
#define R14_RAW rocrand4

#else
#include <curand_kernel.h>
#define R14_STATE curandStatePhilox4_32_10_t
#define R14_INIT curand_init
#define R14_RAW curand4

#endif
namespace migration_device {
using namespace migration_batch;
template<class T>void bin14(const std::string&name,const std::vector<T>&v){migration_binary::emit((name+".bin").c_str(),v.data(),v.size()*sizeof(T));}
__device__ double sqrt14(double x){
#ifdef __HIP_PLATFORM_AMD__
 return __builtin_sqrt(x);
#else
 return sqrt(x);
#endif
}
__device__ void trig14(float a,float&s,float&c){
#ifdef __HIP_PLATFORM_AMD__
 s=__builtin_sinf(a);c=__builtin_cosf(a);
#else
 sincosf(a,&s,&c);
#endif
}
struct Complex14{double x,y;};
__device__ Complex14 add14(Complex14 a,Complex14 b){return {a.x+b.x,a.y+b.y};}
__device__ Complex14 mul14(Complex14 a,Complex14 b){return {a.x*b.x-a.y*b.y,a.x*b.y+a.y*b.x};}
__device__ Complex14 conjugate14(Complex14 a){return {a.x,-a.y};}
__device__ void gemm_device14(const double*a,const double*b,double*c,int n,int mode,int*trace){for(int t=threadIdx.x;t<n*n;t+=blockDim.x){int i=t%n,j=t/n;double acc=0;for(int k=0;k<n;++k)acc+=a[i*n+k]*b[k+j*n];c[t]=mode==2?acc:acc+c[t];}__syncthreads();if(!threadIdx.x)atomicAdd(trace+mode,1);}
__global__ void gemm_block14(const double*a,const double*b,double*c,int n,int mode,int*trace){__shared__ double shared[32*32*3];double*aa=shared,*bb=aa+32*32,*cc=bb+32*32;for(int t=threadIdx.x;t<n*n;t+=blockDim.x){aa[t]=a[t];bb[t]=b[t];cc[t]=c[t];}__syncthreads();gemm_device14(aa,bb,cc,n,mode,trace);for(int t=threadIdx.x;t<n*n;t+=blockDim.x)c[t]=cc[t];if(!threadIdx.x){trace[3]=blockDim.x;trace[4]=warpSize;}}
__device__ void fft_device14(float2*data,int n,int batch,int*trace){int stages=0;for(int v=n;v>1;v>>=1)++stages;for(int t=threadIdx.x;t<n*batch;t+=blockDim.x){int i=t%n,reverse=0;for(int b=0;b<stages;++b)reverse=reverse*2+((i>>b)&1);if(i<reverse){float2 temp=data[t];data[t]=data[t-i+reverse];data[t-i+reverse]=temp;}}__syncthreads();for(int len=2;len<=n;len*=2){for(int t=threadIdx.x;t<batch*n/2;t+=blockDim.x){int fft=t/(n/2),j=t%(len/2),base=(t%(n/2))/(len/2)*len,first=fft*n+base+j,second=first+len/2;float s,c;trig14(-6.283185307179586f*j/len,s,c);auto u=data[first],v=data[second];float2 w={v.x*c-v.y*s,v.x*s+v.y*c};data[first]={u.x+w.x,u.y+w.y};data[second]={u.x-w.x,u.y-w.y};}__syncthreads();}if(!threadIdx.x)atomicAdd(trace,1);}
__global__ void fft_block14(float2*data,int n,int batch,int*trace){__shared__ float2 shared[3*128];for(int t=threadIdx.x;t<n*batch;t+=blockDim.x)shared[t]=data[t];__syncthreads();fft_device14(shared,n,batch,trace);for(int t=threadIdx.x;t<n*batch;t+=blockDim.x)data[t]=shared[t];if(!threadIdx.x){trace[3]=blockDim.x;trace[4]=warpSize;}}
__device__ void chol_device14(Complex14*a,int n,int lda,int*info,int*trace){for(int j=0;j<n;++j){if(!threadIdx.x&&!*info){double diag=a[j+j*lda].x;for(int k=0;k<j;++k){auto v=a[k+j*lda];diag-=v.x*v.x+v.y*v.y;}if(diag<=0)*info=j+1;else a[j+j*lda]={sqrt14(diag),0};}__syncthreads();if(!*info)for(int col=j+1+threadIdx.x;col<n;col+=blockDim.x){auto v=a[j+col*lda];for(int k=0;k<j;++k){auto term=mul14(conjugate14(a[k+j*lda]),a[k+col*lda]);v.x-=term.x;v.y-=term.y;}double diag=a[j+j*lda].x;a[j+col*lda]={v.x/diag,v.y/diag};}__syncthreads();}if(!threadIdx.x)atomicAdd(trace,1);}
__global__ void chol_block14(Complex14*data,int n,int*info,int*trace){__shared__ Complex14 shared[33*32];__shared__ int code;for(int t=threadIdx.x;t<33*n;t+=blockDim.x)shared[t]={-97,13};for(int t=threadIdx.x;t<n*n;t+=blockDim.x)shared[t%n+(t/n)*33]=data[t];if(!threadIdx.x)code=0;__syncthreads();chol_device14(shared,n,33,&code,trace);for(int t=threadIdx.x;t<n*n;t+=blockDim.x)data[t]=shared[t%n+(t/n)*33];if(!threadIdx.x){*info=code;trace[3]=blockDim.x;trace[4]=warpSize;int okay=1;for(int j=0;j<n;++j)for(int i=n;i<33;++i)okay&=shared[i+j*33].x==-97&&shared[i+j*33].y==13;trace[5]=okay;}}
__device__ double log14(double v){
#ifdef __HIP_PLATFORM_AMD__
return __ocml_log_f64(v);
#else
return log(v);
#endif
}
__device__ double exp14(double v){
#ifdef __HIP_PLATFORM_AMD__
return __ocml_exp_f64(v);
#else
return exp(v);
#endif
}
__device__ void trig_double14(double a,double&s,double&c){
#ifdef __HIP_PLATFORM_AMD__
s=__ocml_sin_f64(a);c=__ocml_cos_f64(a);
#else
sincos(a,&s,&c);
#endif
}
__global__ void rng_thread14(double*out,unsigned int*raw,int n,unsigned long long seed,unsigned long long offset,int*trace){int group=blockIdx.x*blockDim.x+threadIdx.x;if(group<n/4){unsigned long long sequence=(offset+group)%65536,skip=(offset+group)/65536;R14_STATE state;R14_INIT(seed,sequence,skip,&state);uint4 first=R14_RAW(&state),second=R14_RAW(&state);unsigned int words[8]={first.x,first.y,first.z,first.w,second.x,second.y,second.z,second.w};for(int j=0;j<8;++j)raw[group*8+j]=words[j];for(int pair=0;pair<2;++pair){int j=pair*4;double u=((double)(words[j]>>5)*67108864.+(words[j+1]>>6)+.5)/9007199254740992.;double v=((double)(words[j+2]>>5)*67108864.+(words[j+3]>>6)+.5)/9007199254740992.;double r=sqrt14(-2.*log14(u)),sn,cs;trig_double14(6.2831853071795864769*v,sn,cs);out[group*4+2*pair]=exp14(1.+.5*r*sn);out[group*4+2*pair+1]=exp14(1.+.5*r*cs);}atomicAdd(trace,1);}if(!group){trace[3]=blockDim.x;trace[4]=warpSize;}}
inline int main14(const std::string&kind){try{auto cas=selected_case();int n=32,threads=256,repeat=cas=="repeat"?3:1;if(cas=="irregular"){n=17;threads=128;}if(cas=="boundary"){n=8;threads=64;}Buffer<int>trace(std::vector<int>(6,0));
 if(kind=="introduction_example") {std::vector<double>a(n*n),b(n*n),c(n*n);for(int i=0;i<n*n;++i){a[i]=double(i%17+1)/17;b[i]=double(i%13+1)/13;c[i]=double(i%11+1)/11;if(cas=="changed-values")a[i]=-.5*a[i];if(cas=="singular-or-empty")a[i]=0;}bin14("input_A",a);bin14("input_B",b);bin14("input_C",c);Buffer<double>aa(a),bb(b),cc(c);for(int r=0;r<repeat;++r){cc.put(c);for(int mode=0;mode<3;++mode){gemm_block14<<<1,threads>>>(aa.p,bb.p,cc.p,n,mode,trace.p);MB_CHECK(MB_RT(DeviceSynchronize)());if(!r)bin14("phase"+std::to_string(mode),cc.get());}}bin14("output",cc.get());bin14("config",std::vector<int>{n,threads,repeat});}
 else if(kind=="simple_fft_block"){n=cas=="irregular"?64:cas=="boundary"?8:128;threads=cas=="boundary"?64:32;int batch=cas=="irregular"?3:2;std::vector<float2>in(n*batch);for(int i=0;i<n*batch;++i){float v=cas=="changed-values"?float((i*7)%19-9):cas=="singular-or-empty"?0:float(i);in[i]={v,-v};}Buffer<float2>x(in);bin14("input",in);for(int r=0;r<repeat;++r){x.put(in);fft_block14<<<1,threads>>>(x.p,n,batch,trace.p);MB_CHECK(MB_RT(DeviceSynchronize)());}bin14("output",x.get());bin14("config",std::vector<int>{n,batch,threads,repeat});}
 else if(kind=="potrf_block"){std::vector<Complex14>a(n*n);for(int j=0;j<n;++j)for(int i=0;i<n;++i)a[i+j*n]=i==j?Complex14{double(n*4+(cas=="changed-values"?3:0)),0}:Complex14{double((i*7+j*3)%13-6)/8,double((i*5+j*11)%17-8)/8};if(cas=="singular-or-empty")a[0].x=-1;bin14("input_A",a);Buffer<Complex14>x(a);Buffer<int>info(1);for(int r=0;r<repeat;++r){x.put(a);chol_block14<<<1,threads>>>(x.p,n,info.p,trace.p);MB_CHECK(MB_RT(DeviceSynchronize)());}bin14("output",x.get());bin14("info",info.get());bin14("config",std::vector<int>{n,33,threads,repeat});}
 else {n=cas=="boundary"?20:cas=="irregular"?5004:cas=="singular-or-empty"?0:5000;int seed=cas=="changed-values"?6789:1234,offset=cas=="boundary"?65535:1;Buffer<double>x(n);Buffer<unsigned int>raw(n*2);for(int r=0;r<repeat;++r){if(n)rng_thread14<<<(n/4+255)/256,256>>>(x.p,raw.p,n,seed,offset,trace.p);MB_CHECK(MB_RT(DeviceSynchronize)());if(!r)bin14("first",x.get());}bin14("output",x.get());bin14("raw",raw.get());bin14("config",std::vector<int>{n,seed,offset,256,repeat});}
 bin14("trace",trace.get());return 0;}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
}
