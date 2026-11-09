// SPDX-License-Identifier: Apache-2.0
// ROCm implementation of cuSOLVER/getrf; calls remain explicit for comparison.
#include "check.hpp"
#include <hipsolver/hipsolver.h>
using namespace sample;
int main(){return run([]{
hipsolverDnHandle_t h;CHECK(hipsolverDnCreate(&h));Stream stream;CHECK(hipsolverDnSetStream(h,stream.p));
for(bool pivot:{false,true}){
 int n=3;std::vector<double>a={1,4,7,2,5,8,3,6,10},b={1,2,3};Device<double> da(a),db(b);Device<int> piv(std::vector<int>{1,2,3}),info(1);int worksize=0;
 CHECK(hipsolverDnDgetrf_bufferSize(h,n,n,da.p,n,&worksize));Device<double> work(worksize);
 CHECK(hipsolverDnDgetrf(h,n,n,da.p,n,work.p,pivot?piv.p:nullptr,info.p));CHECK(hipStreamSynchronize(stream.p));if(info.get()[0]!=0)throw std::runtime_error("getrf info nonzero");
 auto lu=da.get();auto permutation=piv.get();auto permuted=a;
 if(pivot)for(int j=0;j<n;j++){int row=permutation[j]-1;if(row<0||row>=n)throw std::runtime_error("invalid pivot index");for(int col=0;col<n;col++)std::swap(permuted[j+col*n],permuted[row+col*n]);}
 std::vector<double> reconstructed(9,0);
 for(int col=0;col<n;col++)for(int row=0;row<n;row++)for(int q=0;q<n;q++){
 double l=row==q?1.:(row>q?lu[row+q*n]:0.);double u=q<=col?lu[q+col*n]:0.;reconstructed[row+col*n]+=l*u;}
 report("factorization_pivot"+std::to_string(pivot),reconstructed,permuted);
 // hipSOLVER getrs requires ipiv even after no-pivot LU: use identity pivots.
 CHECK(hipsolverDnDgetrs(h,HIPBLAS_OP_N,n,1,da.p,n,piv.p,db.p,n,info.p));CHECK(hipStreamSynchronize(stream.p));if(info.get()[0]!=0)throw std::runtime_error("getrs info nonzero");auto x=db.get();report("pivot"+std::to_string(pivot),x,std::vector<double>{-1./3,2./3,0});
 std::vector<double> ax(n,0);for(int i=0;i<n;i++)for(int j=0;j<n;j++)ax[i]+=a[i+j*n]*x[j];report("residual_pivot"+std::to_string(pivot),ax,b);
}CHECK(hipsolverDnDestroy(h));
});}
