// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuFFT/1d_r2c_c2r; calls remain explicit for comparison.
#include "check.hpp"
#include "scaling.hpp"
#include <hipfft/hipfft.h>
using namespace sample;
int main(){return run([]{
Stream stream;
for(int profile:{0,1})for(int n:{8,15}){if(profile==0&&n!=8)continue;int batch=2;hipfftHandle forward,backward;
 auto x=input<float>(n*batch);if(profile==0)for(int z=0;z<n*batch;z++)x[z]=float(z);Device<float> dx(x);int nf=n/2+1;Device<hipfftComplex> dy(nf*batch);
 CHECK(hipfftPlan1d(&forward,n,HIPFFT_R2C,batch));CHECK(hipfftPlan1d(&backward,n,HIPFFT_C2R,batch));CHECK(hipfftSetStream(forward,stream.p));CHECK(hipfftSetStream(backward,stream.p));
 CHECK(hipfftExecR2C(forward,dx.p,dy.p));CHECK(hipStreamSynchronize(stream.p));auto y=dy.get();std::vector<float>flat(nf*batch*2),ref(flat.size());
 for(int z=0;z<batch;z++)for(int k=0;k<nf;k++){std::complex<double>sum=0.;for(int j=0;j<n;j++)sum+=double(x[z*n+j])*std::polar(1.,-2*std::acos(-1.)*j*k/n);flat[2*(z*nf+k)]=y[z*nf+k].x;flat[2*(z*nf+k)+1]=y[z*nf+k].y;ref[2*(z*nf+k)]=sum.real();ref[2*(z*nf+k)+1]=sum.imag();}report(profile==0?"original_forward":"forward_n"+std::to_string(n),flat,ref,2e-5,1e-5);
 CHECK(migration_scale_complex(dy.p,nf*batch,1.f/n,stream.p));CHECK(hipfftExecC2R(backward,dy.p,dx.p));CHECK(hipStreamSynchronize(stream.p));auto back=dx.get();report(profile==0?"original_profile":"roundtrip_n"+std::to_string(n),back,x,2e-6,1e-5);
 CHECK(hipfftDestroy(forward));CHECK(hipfftDestroy(backward));}

});}
