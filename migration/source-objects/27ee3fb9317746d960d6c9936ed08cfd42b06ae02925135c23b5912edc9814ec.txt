// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuSOLVER/potrfBatched; calls remain explicit for comparison.
#include "check.hpp"
#include <hipsolver/hipsolver.h>
using namespace sample;
int main(){return run([]{
hipsolverDnHandle_t h;CHECK(hipsolverDnCreate(&h));Stream stream;CHECK(hipsolverDnSetStream(h,stream.p));
{int n=3;std::vector<double>a={1,2,3,2,5,5,3,5,12,1,2,3,2,4,5,3,5,12},b={1,1,1};Device<double> da(a),db(b);Device<int> info(2);std::vector<double*> ap={da.p,da.p+9};Device<double*> dap(ap);CHECK(hipsolverDnDpotrfBatched(h,HIPBLAS_FILL_MODE_LOWER,n,dap.p,n,info.p,2));CHECK(hipStreamSynchronize(stream.p));report("original_non_spd_info",info.get(),std::vector<int>{0,2},0,0);auto lower=da.get();std::vector<double> rebuilt(9,0);for(int col=0;col<n;col++)for(int row=0;row<n;row++)for(int q=0;q<=std::min(row,col);q++)rebuilt[row+col*n]+=lower[row+q*n]*lower[col+q*n];report("original_factorization",rebuilt,std::vector<double>(a.begin(),a.begin()+9));std::vector<double*> bp={db.p};Device<double*> dbp(bp);CHECK(hipsolverDnDpotrsBatched(h,HIPBLAS_FILL_MODE_LOWER,n,1,dap.p,n,dbp.p,n,info.p,1));CHECK(hipStreamSynchronize(stream.p));report("original_profile",db.get(),std::vector<double>{10.5,-2.5,-1.5});}
for(auto fill:{HIPBLAS_FILL_MODE_LOWER,HIPBLAS_FILL_MODE_UPPER}){
 int n=3,count=2;std::vector<double>a={4,1,0,1,4,1,0,1,4,5,1,0,1,5,1,0,1,5},b={6,12,14,7,14,17};Device<double> da(a),db(b);Device<int> info(count);
 std::vector<double*>ap={da.p,da.p+9},bp={db.p,db.p+3};Device<double*> dap(ap),dbp(bp);
 CHECK(hipsolverDnDpotrfBatched(h,fill,n,dap.p,n,info.p,count));CHECK(hipStreamSynchronize(stream.p));for(int v:info.get())if(v)throw std::runtime_error("potrf info nonzero");
 CHECK(hipsolverDnDpotrsBatched(h,fill,n,1,dap.p,n,dbp.p,n,info.p,count));CHECK(hipStreamSynchronize(stream.p));for(int v:info.get())if(v)throw std::runtime_error("potrs info nonzero");
 auto x=db.get();report("uplo"+std::string(fill==HIPBLAS_FILL_MODE_LOWER?"lower":"upper"),x,std::vector<double>{1,2,3,1,2,3});
 std::vector<double> ax(6,0);for(int z=0;z<2;z++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)ax[z*n+i]+=a[z*9+i+j*n]*x[z*n+j];report("residual_uplo"+std::string(fill==HIPBLAS_FILL_MODE_LOWER?"lower":"upper"),ax,b);
}CHECK(hipsolverDnDestroy(h));
});}
