// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuBLAS/Level-2/gemv; calls remain explicit for comparison.
#include "check.hpp"
#include <hipblas/hipblas.h>
using namespace sample;
int main(){return run([]{
hipblasHandle_t h;CHECK(hipblasCreate(&h));Stream stream;CHECK(hipblasSetStream(h,stream.p));
{const bool tr=false;const double beta=0.;
 int m=2,n=2,ld=2,rows=tr?n:m,cols=tr?m:n;double alpha=1.0;
 std::vector<double>a={1,3,2,4},x={5,6},y(rows,0),ref=y;
 for(int i=0;i<rows;i++){double sum=0;for(int j=0;j<cols;j++)sum+=(tr?a[j+i*ld]:a[i+j*ld])*x[j];ref[i]=alpha*sum+beta*y[i];}
 Device<double> da(a),dx(x),dy(y);CHECK(hipblasDgemv(h,tr?HIPBLAS_OP_T:HIPBLAS_OP_N,m,n,&alpha,da.p,ld,dx.p,1,&beta,dy.p,1));CHECK(hipStreamSynchronize(stream.p));
 report("original_profile",dy.get(),ref);
}
for(bool tr:{false,true})for(double beta:{0.,0.5}){
 int m=5,n=3,ld=7,rows=tr?n:m,cols=tr?m:n;double alpha=1.25;
 auto a=input<double>(ld*n),x=input<double>(cols,128),y=input<double>(rows,256),ref=y;
 for(int i=0;i<rows;i++){double sum=0;for(int j=0;j<cols;j++)sum+=(tr?a[j+i*ld]:a[i+j*ld])*x[j];ref[i]=alpha*sum+beta*y[i];}
 Device<double> da(a),dx(x),dy(y);CHECK(hipblasDgemv(h,tr?HIPBLAS_OP_T:HIPBLAS_OP_N,m,n,&alpha,da.p,ld,dx.p,1,&beta,dy.p,1));CHECK(hipStreamSynchronize(stream.p));
 report("transpose"+std::to_string(tr)+"_beta"+std::to_string(beta),dy.get(),ref);
}CHECK(hipblasDestroy(h));
});}
