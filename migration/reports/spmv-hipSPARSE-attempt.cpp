// SPDX-License-Identifier: Apache-2.0
// ROCm implementation of cuSPARSE/spmv_csr; calls remain explicit for comparison.
#include "check.hpp"
#include <hipsparse/hipsparse.h>
using namespace sample;
int main(){return run([]{
hipsparseHandle_t h;CHECK(hipsparseCreate(&h));Stream stream;CHECK(hipsparseSetStream(h,stream.p));
for(int base:{0,1}) {
 int n=4;std::vector<int> rp={0,3,4,7,9},ci={0,2,3,1,0,2,3,1,3};std::vector<float> av={1,2,3,4,5,6,7,8,9};
 for(auto& v:rp)v+=base;for(auto& v:ci)v+=base;
 Device<int> dr(rp),di(ci);Device<float> da(av);hipsparseSpMatDescr_t a;
 CHECK(hipsparseCreateCsr(&a,n,n,av.size(),dr.p,di.p,da.p,HIPSPARSE_INDEX_32I,HIPSPARSE_INDEX_32I,base?HIPSPARSE_INDEX_BASE_ONE:HIPSPARSE_INDEX_BASE_ZERO,HIP_R_32F));
for(float beta:{0.f,0.5f}){
 auto x=input<float>(n,128),y=input<float>(n,256),ref=y;float alpha=1.25f;
 for(int i=0;i<n;i++){float sum=0;for(int q=rp[i]-base;q<rp[i+1]-base;q++)sum+=av[q]*x[ci[q]-base];ref[i]=alpha*sum+beta*y[i];}
 Device<float> dx(x),dy(y);hipsparseDnVecDescr_t xd,yd;CHECK(hipsparseCreateDnVec(&xd,n,dx.p,HIP_R_32F));CHECK(hipsparseCreateDnVec(&yd,n,dy.p,HIP_R_32F));size_t bytes=0;
 CHECK(hipsparseSpMV_bufferSize(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,&beta,yd,HIP_R_32F,HIPSPARSE_SPMV_CSR_ALG1,&bytes));Device<unsigned char> work(bytes);
 // ROCm backend requires analysis/preprocess before CSR SpMV.
 CHECK(hipsparseSpMV_preprocess(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,&beta,yd,HIP_R_32F,HIPSPARSE_SPMV_CSR_ALG1,work.p));
 CHECK(hipsparseSpMV(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,&beta,yd,HIP_R_32F,HIPSPARSE_SPMV_CSR_ALG1,work.p));CHECK(hipStreamSynchronize(stream.p));report("base"+std::to_string(base)+"_beta"+std::to_string(beta),dy.get(),ref,1e-6,1e-5);
 CHECK(hipsparseDestroyDnVec(xd));CHECK(hipsparseDestroyDnVec(yd));}
CHECK(hipsparseDestroySpMat(a));}
CHECK(hipsparseDestroy(h));
});}
