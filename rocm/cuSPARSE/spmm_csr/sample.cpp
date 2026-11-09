// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuSPARSE/spmm_csr; calls remain explicit for comparison.
#include "check.hpp"
#include <hipsparse/hipsparse.h>
using namespace sample;
int main(){return run([]{
hipsparseHandle_t h;CHECK(hipsparseCreate(&h));Stream stream;CHECK(hipsparseSetStream(h,stream.p));
for(int profile:{0,1,2}) for(int base:{0,1}) {
 if(profile==0&&base!=0)continue;
 int n=4;std::vector<int> rp={0,3,4,7,9},ci={0,2,3,1,0,2,3,1,3};std::vector<float> av={1,2,3,4,5,6,7,8,9};
 if(profile==2){rp={0,2,2,5,7};ci={0,3,0,2,3,1,3};av={1,3,5,6,7,8,9};}
 for(auto& v:rp)v+=base;for(auto& v:ci)v+=base;
 Device<int> dr(rp),di(ci);Device<float> da(av);hipsparseSpMatDescr_t a;
 CHECK(hipsparseCreateCsr(&a,n,n,av.size(),dr.p,di.p,da.p,HIPSPARSE_INDEX_32I,HIPSPARSE_INDEX_32I,base?HIPSPARSE_INDEX_BASE_ONE:HIPSPARSE_INDEX_BASE_ZERO,HIP_R_32F));
for(float beta:{0.f,0.5f}){
 if(profile==0&&beta!=0)continue;
 int cols=3,ld=profile==0?4:6;auto x=input<float>(ld*cols,128),y=input<float>(ld*cols,256),ref=y;float alpha=profile==0?1.f:1.25f;if(profile==0){for(int z=0;z<12;z++)x[z]=float(z+1);y.assign(12,0);ref=y;}
 for(int j=0;j<cols;j++)for(int i=0;i<n;i++){float sum=0;for(int q=rp[i]-base;q<rp[i+1]-base;q++)sum+=av[q]*x[ci[q]-base+j*ld];ref[i+j*ld]=alpha*sum+beta*y[i+j*ld];}
 Device<float> dx(x),dy(y);hipsparseDnMatDescr_t xd,yd;CHECK(hipsparseCreateDnMat(&xd,n,cols,ld,dx.p,HIP_R_32F,HIPSPARSE_ORDER_COL));CHECK(hipsparseCreateDnMat(&yd,n,cols,ld,dy.p,HIP_R_32F,HIPSPARSE_ORDER_COL));size_t bytes=0;
 CHECK(hipsparseSpMM_bufferSize(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,&beta,yd,HIP_R_32F,HIPSPARSE_SPMM_ALG_DEFAULT,&bytes));Device<unsigned char> work(bytes);
 CHECK(hipsparseSpMM(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,&beta,yd,HIP_R_32F,HIPSPARSE_SPMM_ALG_DEFAULT,work.p));CHECK(hipStreamSynchronize(stream.p));report(profile==0?"original_profile":std::string(profile==2?"empty_":"")+"base"+std::to_string(base)+"_beta"+std::to_string(beta),dy.get(),ref,1e-6,1e-5);
 CHECK(hipsparseDestroyDnMat(xd));CHECK(hipsparseDestroyDnMat(yd));}
CHECK(hipsparseDestroySpMat(a));}
CHECK(hipsparseDestroy(h));
});}
