// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuBLAS/Level-1/axpy; calls remain explicit for comparison.
#include "check.hpp"
#include <hipblas/hipblas.h>
using namespace sample;
int main(){return run([]{
hipblasHandle_t h;CHECK(hipblasCreate(&h));Stream stream;CHECK(hipblasSetStream(h,stream.p));
{std::vector<double> x={1,2,3,4},y={5,6,7,8};double alpha=2.1;Device<double> dx(x),dy(y);CHECK(hipblasDaxpy(h,4,&alpha,dx.p,1,dy.p,1));CHECK(hipStreamSynchronize(stream.p));report("original_profile",dy.get(),std::vector<double>{7.1,10.2,13.3,16.4});}
for(int n: {4,17}) for(int stride: {1,2}) {
 auto x=input<double>(n*stride,0),y=input<double>(n*stride,128);auto ref=y;Device<double> dx(x),dy(y);double alpha=2.1;
 for(int i=0;i<n;i++)ref[i*stride]+=alpha*x[i*stride];
 CHECK(hipblasDaxpy(h,n,&alpha,dx.p,stride,dy.p,stride));CHECK(hipStreamSynchronize(stream.p));
 report("n"+std::to_string(n)+"_stride"+std::to_string(stride),dy.get(),ref);
}
CHECK(hipblasDestroy(h));
});}
