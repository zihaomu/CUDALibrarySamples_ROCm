// SPDX-License-Identifier: Apache-2.0
// Project-only GPU correction for repeated rescaling of BLAS modified Givens H.
// The immutable rocBLAS remains unchanged. Ordinary inputs use hipBLAS directly.
#include <hip/hip_runtime.h>
#include <cmath>
#include <stdexcept>
namespace {
__device__ double magnitude(double x){return x<0?-x:x;}
__global__ void corrected_rotation(double* v){
 double d1=v[0],d2=v[1],x=v[2],y=v[3],f=-1,h11=0,h21=0,h12=0,h22=0;
 constexpr double g=4096,g2=g*g,ig2=1/g2;
 if(d1<0){d1=d2=x=0;}
 else if(d2*y==0){v[4]=-2;return;}
 else{
  double p1=d1*x,p2=d2*y,q1=p1*x,q2=p2*y;
  if(magnitude(q1)>magnitude(q2)){h21=-y/x;h12=p2/p1;double u=1-h12*h21;if(u>0){f=0;d1/=u;d2/=u;x*=u;}}
  else if(q2<0){d1=d2=x=0;}
  else{f=1;h11=p1/p2;h22=x/y;double u=1+h11*h22,t=d2/u;d2=d1/u;d1=t;x=y*u;}
  if(d1!=0)while(d1<=ig2||d1>=g2){
   if(f==0){h11=h22=1;f=-1;}else if(f==1){h21=-1;h12=1;f=-1;}
   if(d1<=ig2){d1*=g2;x/=g;h11/=g;h12/=g;}else{d1/=g2;x*=g;h11*=g;h12*=g;}
  }
  if(d2!=0)while(magnitude(d2)<=ig2||magnitude(d2)>=g2){
   if(f==0){h11=h22=1;f=-1;}else if(f==1){h21=-1;h12=1;f=-1;}
   if(magnitude(d2)<=ig2){d2*=g2;h21/=g;h22/=g;}else{d2/=g2;h21*=g;h22*=g;}
  }
 }
 v[0]=d1;v[1]=d2;v[2]=x;v[4]=f;
 if(f<0){v[5]=h11;v[6]=h21;v[7]=h12;v[8]=h22;}
 else if(f==0){v[6]=h21;v[7]=h12;}else{v[5]=h11;v[8]=h22;}
}
void checked(hipError_t e){if(e!=hipSuccess)throw std::runtime_error(hipGetErrorString(e));}
}
extern "C" void migration_rotmg_scale_fix(double original_d1,double original_d2,double original_x,double y,double* d1,double* d2,double* x,double* param){
 double host[9]={original_d1,original_d2,original_x,y,param[0],param[1],param[2],param[3],param[4]};double* device=nullptr;
 checked(hipMalloc(&device,sizeof(host)));checked(hipMemcpy(device,host,sizeof(host),hipMemcpyHostToDevice));corrected_rotation<<<1,1>>>(device);checked(hipGetLastError());checked(hipMemcpy(host,device,sizeof(host),hipMemcpyDeviceToHost));checked(hipFree(device));
 *d1=host[0];*d2=host[1];*x=host[2];for(int i=0;i<5;++i)param[i]=host[i+4];
}
