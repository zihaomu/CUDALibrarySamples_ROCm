// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuFFT/1d_c2c; calls remain explicit for comparison.
#include "check.hpp"
#include "scaling.hpp"
#include <hipfft/hipfft.h>
using namespace sample;
int main(){return run([]{
Stream stream;
for(int profile:{0,1})for(int n:{8,15}){if(profile==0&&n!=8)continue;int batch=2;hipfftHandle forward,backward;
 auto raw=input<float>(n*batch*2);if(profile==0)for(int z=0;z<n*batch;z++){raw[2*z]=float(z);raw[2*z+1]=float(-z);}std::vector<hipfftComplex>x(n*batch);for(int i=0;i<n*batch;i++)x[i]={raw[2*i],raw[2*i+1]};Device<hipfftComplex> dx(x);
 CHECK(hipfftPlan1d(&forward,n,HIPFFT_C2C,batch));CHECK(hipfftPlan1d(&backward,n,HIPFFT_C2C,batch));CHECK(hipfftSetStream(forward,stream.p));CHECK(hipfftSetStream(backward,stream.p));
 CHECK(hipfftExecC2C(forward,dx.p,dx.p,HIPFFT_FORWARD));CHECK(hipStreamSynchronize(stream.p));auto y=dx.get();std::vector<float> flat(n*batch*2),ref(flat.size());
 for(int z=0;z<batch;z++)for(int k=0;k<n;k++){std::complex<double> sum=0.;for(int j=0;j<n;j++)sum+=std::complex<double>(x[z*n+j].x,x[z*n+j].y)*std::polar(1.,-2*std::acos(-1.)*j*k/n);flat[2*(z*n+k)]=y[z*n+k].x;flat[2*(z*n+k)+1]=y[z*n+k].y;ref[2*(z*n+k)]=sum.real();ref[2*(z*n+k)+1]=sum.imag();}report(profile==0?"original_forward":"forward_n"+std::to_string(n),flat,ref,2e-5,1e-5);
 CHECK(migration_scale_complex(dx.p,n*batch,1.f/n,stream.p));CHECK(hipfftExecC2C(backward,dx.p,dx.p,HIPFFT_BACKWARD));CHECK(hipStreamSynchronize(stream.p));y=dx.get();for(int i=0;i<n*batch;i++){flat[2*i]=y[i].x;flat[2*i+1]=y[i].y;}report(profile==0?"original_profile":"roundtrip_n"+std::to_string(n),flat,raw,2e-6,1e-5);
 CHECK(hipfftDestroy(forward));CHECK(hipfftDestroy(backward));}

});}
