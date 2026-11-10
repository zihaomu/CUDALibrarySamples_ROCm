// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batches_runtime.hpp"
namespace migration_batch {
__global__ void pack_triangle(const double* A,double* AP,int n,int lda,bool upper,bool unpack){
 int row=blockIdx.x*blockDim.x+threadIdx.x,col=blockIdx.y*blockDim.y+threadIdx.y;
 if(row>=n||col>=n)return;
 if((upper&&row>col)||(!upper&&row<col))return;
 int k=upper?col*(col+1)/2+row:col*n-col*(col-1)/2+row-col;
 if(unpack)const_cast<double*>(A)[col*lda+row]=AP[k];else AP[k]=A[col*lda+row];
}
inline int packed_main(bool unpack){
 std::string c=selected_case();int n=c=="odd-size"?5:2,lda=c=="padded-lda"?n+3:n;bool upper=c!="lower";
 // Preserve the original unused trailing packed element too, initialized here.
 std::vector<double>A(lda*n,-97),AP(n*n,0);
 if(c=="original"){A={1,3,2,4};AP={1,3,2,4};}
 else{for(int j=0;j<n;++j)for(int i=0;i<n;++i)A[j*lda+i]=1+i+3*j;for(size_t i=0;i<AP.size();++i)AP[i]=i+1;}
 emit("input_A",A);emit("input_AP",AP);scalar("input_n",n);scalar("input_lda",lda);scalar("input_upper",int(upper));
 if(unpack)std::fill(A.begin(),A.end(),-97.);else std::fill(AP.begin(),AP.end(),-97.);
 Buffer<double>dA(A),dP(AP);
#ifdef __HIP_PLATFORM_AMD__
 pack_triangle<<<dim3((n+15)/16,(n+15)/16),dim3(16,16)>>>(dA.p,dP.p,n,lda,upper,unpack);
 MB_CHECK(hipGetLastError());
#else
 Blas b;auto u=upper?CUBLAS_FILL_MODE_UPPER:CUBLAS_FILL_MODE_LOWER;
 if(unpack)MB_CHECK(cublasDtpttr(b.h,u,n,dP.p,dA.p,lda));else MB_CHECK(cublasDtrttp(b.h,u,n,dA.p,lda,dP.p));
#endif
 emit("A",dA.get());emit("AP",dP.get());return 0;
}
}
