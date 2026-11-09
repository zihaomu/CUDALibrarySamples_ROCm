// SPDX-License-Identifier: Apache-2.0
// ROCm implementation of cuSPARSE/spmv_csr; calls remain explicit for comparison.
#include "check.hpp"
#include <cusparse.h>
using namespace sample;
int main(){return run([]{
cusparseHandle_t h;CHECK(cusparseCreate(&h));Stream stream;CHECK(cusparseSetStream(h,stream.p));
for(int base:{0,1}) {
 int n=4;std::vector<int> rp={0,3,4,7,9},ci={0,2,3,1,0,2,3,1,3};std::vector<float> av={1,2,3,4,5,6,7,8,9};
 for(auto& v:rp)v+=base;for(auto& v:ci)v+=base;
 Device<int> dr(rp),di(ci);Device<float> da(av);cusparseSpMatDescr_t a;
 CHECK(cusparseCreateCsr(&a,n,n,av.size(),dr.p,di.p,da.p,CUSPARSE_INDEX_32I,CUSPARSE_INDEX_32I,base?CUSPARSE_INDEX_BASE_ONE:CUSPARSE_INDEX_BASE_ZERO,CUDA_R_32F));
for(float beta:{0.f,0.5f}){
 auto x=input<float>(n,128),y=input<float>(n,256),ref=y;float alpha=1.25f;
 for(int i=0;i<n;i++){float sum=0;for(int q=rp[i]-base;q<rp[i+1]-base;q++)sum+=av[q]*x[ci[q]-base];ref[i]=alpha*sum+beta*y[i];}
 Device<float> dx(x),dy(y);cusparseDnVecDescr_t xd,yd;CHECK(cusparseCreateDnVec(&xd,n,dx.p,CUDA_R_32F));CHECK(cusparseCreateDnVec(&yd,n,dy.p,CUDA_R_32F));size_t bytes=0;
 CHECK(cusparseSpMV_bufferSize(h,CUSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,&beta,yd,CUDA_R_32F,CUSPARSE_SPMV_ALG_DEFAULT,&bytes));Device<unsigned char> work(bytes);
 CHECK(cusparseSpMV(h,CUSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,&beta,yd,CUDA_R_32F,CUSPARSE_SPMV_ALG_DEFAULT,work.p));CHECK(cudaStreamSynchronize(stream.p));report("base"+std::to_string(base)+"_beta"+std::to_string(beta),dy.get(),ref,1e-6,1e-5);
 CHECK(cusparseDestroyDnVec(xd));CHECK(cusparseDestroyDnVec(yd));}
CHECK(cusparseDestroySpMat(a));}
CHECK(cusparseDestroy(h));
});}
