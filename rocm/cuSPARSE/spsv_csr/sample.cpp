// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuSPARSE/spsv_csr; calls remain explicit for comparison.
#include "check.hpp"
#include <hipsparse/hipsparse.h>
using namespace sample;
int main(){return run([]{
hipsparseHandle_t h;CHECK(hipsparseCreate(&h));Stream stream;CHECK(hipsparseSetStream(h,stream.p));
for(int profile:{0,1}) for(int base:{0,1}) {
 if(profile==0&&base!=0)continue;
 int n=4;std::vector<int> rp={0,3,4,7,9},ci={0,2,3,1,0,2,3,1,3};std::vector<float> av={1,2,3,4,5,6,7,8,9};
 for(auto& v:rp)v+=base;for(auto& v:ci)v+=base;
 Device<int> dr(rp),di(ci);Device<float> da(av);hipsparseSpMatDescr_t a;
 CHECK(hipsparseCreateCsr(&a,n,n,av.size(),dr.p,di.p,da.p,HIPSPARSE_INDEX_32I,HIPSPARSE_INDEX_32I,base?HIPSPARSE_INDEX_BASE_ONE:HIPSPARSE_INDEX_BASE_ZERO,HIP_R_32F));
auto x=input<float>(n,128),ref=x;float alpha=1;if(profile==0){x={1,8,23,52};ref=x;}
 for(int i=0;i<n;i++){float diag=0;for(int q=rp[i]-base;q<rp[i+1]-base;q++){int col=ci[q]-base;if(col<i)ref[i]-=av[q]*ref[col];if(col==i)diag=av[q];}ref[i]/=diag;}
 Device<float> dx(x),dy(n);hipsparseDnVecDescr_t xd,yd;CHECK(hipsparseCreateDnVec(&xd,n,dx.p,HIP_R_32F));CHECK(hipsparseCreateDnVec(&yd,n,dy.p,HIP_R_32F));
 auto fill=HIPSPARSE_FILL_MODE_LOWER;auto diag=HIPSPARSE_DIAG_TYPE_NON_UNIT;CHECK(hipsparseSpMatSetAttribute(a,HIPSPARSE_SPMAT_FILL_MODE,&fill,sizeof(fill)));CHECK(hipsparseSpMatSetAttribute(a,HIPSPARSE_SPMAT_DIAG_TYPE,&diag,sizeof(diag)));
 hipsparseSpSVDescr_t solve;CHECK(hipsparseSpSV_createDescr(&solve));size_t bytes=0;
 CHECK(hipsparseSpSV_bufferSize(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,yd,HIP_R_32F,HIPSPARSE_SPSV_ALG_DEFAULT,solve,&bytes));Device<unsigned char> work(bytes);
 CHECK(hipsparseSpSV_analysis(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,yd,HIP_R_32F,HIPSPARSE_SPSV_ALG_DEFAULT,solve,work.p));
 CHECK(hipsparseSpSV_solve(h,HIPSPARSE_OPERATION_NON_TRANSPOSE,&alpha,a,xd,yd,HIP_R_32F,HIPSPARSE_SPSV_ALG_DEFAULT,solve));CHECK(hipStreamSynchronize(stream.p));report(profile==0?"original_profile":"base"+std::to_string(base),dy.get(),ref,1e-6,1e-5);
 CHECK(hipsparseSpSV_destroyDescr(solve));CHECK(hipsparseDestroyDnVec(xd));CHECK(hipsparseDestroyDnVec(yd));
CHECK(hipsparseDestroySpMat(a));}
CHECK(hipsparseDestroy(h));
});}
