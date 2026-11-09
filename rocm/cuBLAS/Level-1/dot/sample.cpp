// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuBLAS/Level-1/dot; calls remain explicit for comparison.
#include "check.hpp"
#include <hipblas/hipblas.h>
using namespace sample;
int main(){return run([]{
hipblasHandle_t h;CHECK(hipblasCreate(&h));Stream stream;CHECK(hipblasSetStream(h,stream.p));
{std::vector<double> x={1,2,3,4},y={5,6,7,8};Device<double> dx(x),dy(y);double value=0;CHECK(hipblasDdot(h,4,dx.p,1,dy.p,1,&value));CHECK(hipStreamSynchronize(stream.p));report("original_profile",std::vector<double>{value},std::vector<double>{70});}
for(int n: {4,17}) for(int stride: {1,2}) {
 auto x=input<double>(n*stride,0),y=input<double>(n*stride,128);auto ref=y;Device<double> dx(x),dy(y);double alpha=2.1;
 double refdot=0;for(int i=0;i<n;i++)refdot+=x[i*stride]*y[i*stride];
 for(bool device_mode:{false,true}){double result=0;Device<double> dresult(1);
 CHECK(hipblasSetPointerMode(h,device_mode?HIPBLAS_POINTER_MODE_DEVICE:HIPBLAS_POINTER_MODE_HOST));
 CHECK(hipblasDdot(h,n,dx.p,stride,dy.p,stride,device_mode?dresult.p:&result));CHECK(hipStreamSynchronize(stream.p));
 if(device_mode)result=dresult.get()[0];report("n"+std::to_string(n)+"_stride"+std::to_string(stride)+"_mode"+std::to_string(device_mode),std::vector<double>{result},std::vector<double>{refdot});}
}
CHECK(hipblasDestroy(h));
});}
