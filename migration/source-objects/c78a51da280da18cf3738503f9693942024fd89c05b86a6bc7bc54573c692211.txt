// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuBLAS/Extensions/GemmEx; calls remain explicit for comparison.
#include "check.hpp"
#include <hipblas/hipblas.h>
using namespace sample;
int main(){return run([]{
hipblasHandle_t h;CHECK(hipblasCreate(&h));Stream stream;CHECK(hipblasSetStream(h,stream.p));
{const bool tr=false;const double beta=0.;
 int m=2,n=2,k=2,lda=2,ldb=2,ldc=2,batches=1;
 long long sa=lda*(tr?m:k) ,sb=ldb*n,sc=ldc*n;double alpha=1.;
 std::vector<double>a={1,3,2,4},b={5,7,6,8},c(sc*batches,0);if(batches==2){a={1,3,2,4,5,7,6,8};b={5,7,6,8,9,11,10,12};}auto ref=c;
 for(int z=0;z<batches;z++)for(int j=0;j<n;j++)for(int i=0;i<m;i++){
  double sum=0;for(int q=0;q<k;q++)sum+=(tr?a[z*sa+q+i*lda]:a[z*sa+i+q*lda])*b[z*sb+q+j*ldb];
  ref[z*sc+i+j*ldc]=alpha*sum+beta*c[z*sc+i+j*ldc];}
 Device<double> da(a),db(b),dc(c);
 CHECK(hipblasGemmEx(h,tr?HIPBLAS_OP_T:HIPBLAS_OP_N,HIPBLAS_OP_N,m,n,k,&alpha,da.p,HIP_R_64F,lda,db.p,HIP_R_64F,ldb,&beta,dc.p,HIP_R_64F,ldc,HIPBLAS_COMPUTE_64F,HIPBLAS_GEMM_DEFAULT));
 CHECK(hipStreamSynchronize(stream.p));report("original_profile",dc.get(),ref);
}
for(bool tr:{false,true})for(double beta:{0.,0.5}){
 int m=5,n=3,k=7,lda=(tr?k:m)+2,ldb=k+1,ldc=m+3,batches=1;
 long long sa=lda*(tr?m:k)+5,sb=ldb*n+5,sc=ldc*n+5;double alpha=1.25;
 auto a=input<double>(sa*batches),b=input<double>(sb*batches,512),c=input<double>(sc*batches,1024),ref=c;
 for(int z=0;z<batches;z++)for(int j=0;j<n;j++)for(int i=0;i<m;i++){
  double sum=0;for(int q=0;q<k;q++)sum+=(tr?a[z*sa+q+i*lda]:a[z*sa+i+q*lda])*b[z*sb+q+j*ldb];
  ref[z*sc+i+j*ldc]=alpha*sum+beta*c[z*sc+i+j*ldc];}
 Device<double> da(a),db(b),dc(c);
 CHECK(hipblasGemmEx(h,tr?HIPBLAS_OP_T:HIPBLAS_OP_N,HIPBLAS_OP_N,m,n,k,&alpha,da.p,HIP_R_64F,lda,db.p,HIP_R_64F,ldb,&beta,dc.p,HIP_R_64F,ldc,HIPBLAS_COMPUTE_64F,HIPBLAS_GEMM_DEFAULT));
 CHECK(hipStreamSynchronize(stream.p));report("transpose"+std::to_string(tr)+"_beta"+std::to_string(beta),dc.get(),ref);
}CHECK(hipblasDestroy(h));
});}
