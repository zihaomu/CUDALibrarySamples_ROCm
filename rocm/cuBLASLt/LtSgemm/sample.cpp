// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuBLASLt/LtSgemm; calls remain explicit for comparison.
#include "check.hpp"
#include <hipblaslt/hipblaslt.h>
using namespace sample;
int main(){return run([]{
hipblasLtHandle_t h;CHECK(hipblasLtCreate(&h));Stream stream;
{const bool tr=false;const float beta=0.f;
 int m=4,n=4,k=4,lda=4,ldb=4,ldc=4;float alpha=2.f;
 std::vector<float>a(16),b(16),c(16);for(int z=0;z<16;z++)a[z]=b[z]=c[z]=float(z);auto ref=c;
 for(int j=0;j<n;j++)for(int i=0;i<m;i++){float sum=0;for(int q=0;q<k;q++)sum+=(tr?a[q+i*lda]:a[i+q*lda])*b[q+j*ldb];ref[i+j*ldc]=alpha*sum+beta*c[i+j*ldc];}
 Device<float> da(a),db(b),dc(c);Device<unsigned char> work(4*1024*1024);
 hipblasLtMatmulDesc_t op;hipblasLtMatrixLayout_t ad,bd,cd;hipblasLtMatmulPreference_t pref;
 CHECK(hipblasLtMatmulDescCreate(&op,HIPBLAS_COMPUTE_32F,HIP_R_32F));auto trans=tr?HIPBLAS_OP_T:HIPBLAS_OP_N;
 CHECK(hipblasLtMatmulDescSetAttribute(op,HIPBLASLT_MATMUL_DESC_TRANSA,&trans,sizeof(trans)));
 CHECK(hipblasLtMatrixLayoutCreate(&ad,HIP_R_32F,tr?k:m,tr?m:k,lda));CHECK(hipblasLtMatrixLayoutCreate(&bd,HIP_R_32F,k,n,ldb));CHECK(hipblasLtMatrixLayoutCreate(&cd,HIP_R_32F,m,n,ldc));
 CHECK(hipblasLtMatmulPreferenceCreate(&pref));size_t bytes=work.n;CHECK(hipblasLtMatmulPreferenceSetAttribute(pref,HIPBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,&bytes,sizeof(bytes)));
 hipblasLtMatmulHeuristicResult_t algo{};int count=0;CHECK(hipblasLtMatmulAlgoGetHeuristic(h,op,ad,bd,cd,cd,pref,1,&algo,&count));if(count==0)throw std::runtime_error("no heuristic for required layout");
 CHECK(hipblasLtMatmul(h,op,&alpha,da.p,ad,db.p,bd,&beta,dc.p,cd,dc.p,cd,&algo.algo,work.p,work.n,stream.p));CHECK(hipStreamSynchronize(stream.p));
 report("original_profile",dc.get(),ref,1e-5,1e-5);
 CHECK(hipblasLtMatmulPreferenceDestroy(pref));CHECK(hipblasLtMatrixLayoutDestroy(ad));CHECK(hipblasLtMatrixLayoutDestroy(bd));CHECK(hipblasLtMatrixLayoutDestroy(cd));CHECK(hipblasLtMatmulDescDestroy(op));
}
for(bool tr:{false,true})for(float beta:{0.f,0.5f}){
 int m=5,n=3,k=7,lda=(tr?k:m)+2,ldb=k+1,ldc=m+3;float alpha=1.25f;
 auto a=input<float>(lda*(tr?m:k)),b=input<float>(ldb*n,512),c=input<float>(ldc*n,1024),ref=c;
 for(int j=0;j<n;j++)for(int i=0;i<m;i++){float sum=0;for(int q=0;q<k;q++)sum+=(tr?a[q+i*lda]:a[i+q*lda])*b[q+j*ldb];ref[i+j*ldc]=alpha*sum+beta*c[i+j*ldc];}
 Device<float> da(a),db(b),dc(c);Device<unsigned char> work(4*1024*1024);
 hipblasLtMatmulDesc_t op;hipblasLtMatrixLayout_t ad,bd,cd;hipblasLtMatmulPreference_t pref;
 CHECK(hipblasLtMatmulDescCreate(&op,HIPBLAS_COMPUTE_32F,HIP_R_32F));auto trans=tr?HIPBLAS_OP_T:HIPBLAS_OP_N;
 CHECK(hipblasLtMatmulDescSetAttribute(op,HIPBLASLT_MATMUL_DESC_TRANSA,&trans,sizeof(trans)));
 CHECK(hipblasLtMatrixLayoutCreate(&ad,HIP_R_32F,tr?k:m,tr?m:k,lda));CHECK(hipblasLtMatrixLayoutCreate(&bd,HIP_R_32F,k,n,ldb));CHECK(hipblasLtMatrixLayoutCreate(&cd,HIP_R_32F,m,n,ldc));
 CHECK(hipblasLtMatmulPreferenceCreate(&pref));size_t bytes=work.n;CHECK(hipblasLtMatmulPreferenceSetAttribute(pref,HIPBLASLT_MATMUL_PREF_MAX_WORKSPACE_BYTES,&bytes,sizeof(bytes)));
 hipblasLtMatmulHeuristicResult_t algo{};int count=0;CHECK(hipblasLtMatmulAlgoGetHeuristic(h,op,ad,bd,cd,cd,pref,1,&algo,&count));if(count==0)throw std::runtime_error("no heuristic for required layout");
 CHECK(hipblasLtMatmul(h,op,&alpha,da.p,ad,db.p,bd,&beta,dc.p,cd,dc.p,cd,&algo.algo,work.p,work.n,stream.p));CHECK(hipStreamSynchronize(stream.p));
 report("transpose"+std::to_string(tr)+"_beta"+std::to_string(beta),dc.get(),ref,1e-5,1e-5);
 CHECK(hipblasLtMatmulPreferenceDestroy(pref));CHECK(hipblasLtMatrixLayoutDestroy(ad));CHECK(hipblasLtMatrixLayoutDestroy(bd));CHECK(hipblasLtMatrixLayoutDestroy(cd));CHECK(hipblasLtMatmulDescDestroy(op));
}CHECK(hipblasLtDestroy(h));
});}
