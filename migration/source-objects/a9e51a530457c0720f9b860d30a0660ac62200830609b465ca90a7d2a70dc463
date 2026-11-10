// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batches_runtime.hpp"
namespace migration_batch {
__global__ void sell_rows(const int* offsets,const int* columns,int* rows,int n,int slice){
 if(blockIdx.x||threadIdx.x)return;int total=0;rows[0]=0;
 for(int r=0;r<n;++r){int s=r/slice,l=r%slice;for(int q=offsets[s]+l;q<offsets[s+1];q+=slice)if(columns[q]>=0)++total;rows[r+1]=total;}
}
__global__ void sell_values(const int* offsets,const int* columns,const float* values,const int* rows,int* out_cols,float* out_values,int n,int slice){
 int r=blockIdx.x*blockDim.x+threadIdx.x;if(r>=n)return;int s=r/slice,l=r%slice,k=rows[r];
 for(int q=offsets[s]+l;q<offsets[s+1];q+=slice)if(columns[q]>=0){out_cols[k]=columns[q];out_values[k++]=values[q];}
}
__global__ void bsr_expand(const int* offsets,const int* columns,const float* values,int* rows,int* cols,float* out,int* mapping,int n,int block,bool column_order){
 if(blockIdx.x||threadIdx.x)return;int k=0;rows[0]=0;
 for(int r=0;r<n;++r){int br=r/block,ir=r%block;
  for(int b=offsets[br];b<offsets[br+1];++b)for(int j=0;j<block;++j){int p=b*block*block+(column_order?j*block+ir:ir*block+j);cols[k]=columns[b]*block+j;out[k]=values[p];mapping[k++]=p;}
  rows[r+1]=k;
 }
}
__global__ void bsr_restore(const float* values,const int* mapping,float* result,int n){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)result[mapping[i]]=values[i];}
inline int sparse_main(bool bsr){
 const std::string c=selected_case();
#ifdef __HIP_PLATFORM_AMD__
 constexpr auto f32=HIP_R_32F;constexpr auto i32=HIPSPARSE_INDEX_32I;constexpr auto zero=HIPSPARSE_INDEX_BASE_ZERO;constexpr auto row=HIPSPARSE_ORDER_ROW;constexpr auto col=HIPSPARSE_ORDER_COL;constexpr auto op=HIPSPARSE_OPERATION_NON_TRANSPOSE;
#else
 constexpr auto f32=CUDA_R_32F;constexpr auto i32=CUSPARSE_INDEX_32I;constexpr auto zero=CUSPARSE_INDEX_BASE_ZERO;constexpr auto row=CUSPARSE_ORDER_ROW;constexpr auto col=CUSPARSE_ORDER_COL;constexpr auto op=CUSPARSE_OPERATION_NON_TRANSPOSE;
#endif
 MB_SPARSE(Handle_t) h;MB_CHECK(MB_SPARSE(Create)(&h));
 if(!bsr){
  int n=4,slice=2,nnz=9;std::vector<int>offset={0,6,12},columns={0,1,2,-1,3,-1,0,1,2,3,3,-1};
  std::vector<float>values={1,4,2,0,3,0,5,8,6,9,7,0},x={1,8,23,52},y(n);float alpha=1;
  if(c=="changed-values"){alpha=-.5;for(float&v:values)v*=1.25f;}
  bool upper=c=="upper",unit=c=="unit-diagonal";
  emit("input_offsets",offset);emit("input_columns",columns);emit("input_values",values);emit("input_X",x);scalar("input_alpha",alpha);scalar("input_upper",int(upper));scalar("input_unit",int(unit));
  Buffer<int>dO(offset),dC(columns),csrO(n+1),csrC(nnz);Buffer<float>dV(values),dX(x),dY(y),csrV(nnz);
  MB_SPARSE(SpMatDescr_t) A;
#ifdef __HIP_PLATFORM_AMD__
  sell_rows<<<1,1>>>(dO.p,dC.p,csrO.p,n,slice);sell_values<<<1,64>>>(dO.p,dC.p,dV.p,csrO.p,csrC.p,csrV.p,n,slice);MB_CHECK(hipGetLastError());
  MB_CHECK(hipsparseCreateCsr(&A,n,n,nnz,csrO.p,csrC.p,csrV.p,i32,i32,zero,f32));
  emit("bridge_rows",csrO.get());emit("bridge_columns",csrC.get());emit("bridge_values",csrV.get());
  auto fill=upper?HIPSPARSE_FILL_MODE_UPPER:HIPSPARSE_FILL_MODE_LOWER;auto diag=unit?HIPSPARSE_DIAG_TYPE_UNIT:HIPSPARSE_DIAG_TYPE_NON_UNIT;
  auto fill_attr=HIPSPARSE_SPMAT_FILL_MODE,diag_attr=HIPSPARSE_SPMAT_DIAG_TYPE;auto alg=HIPSPARSE_SPSV_ALG_DEFAULT;
#else
  MB_CHECK(cusparseCreateSlicedEll(&A,n,n,nnz,values.size(),slice,dO.p,dC.p,dV.p,i32,i32,zero,f32));
  auto fill=upper?CUSPARSE_FILL_MODE_UPPER:CUSPARSE_FILL_MODE_LOWER;auto diag=unit?CUSPARSE_DIAG_TYPE_UNIT:CUSPARSE_DIAG_TYPE_NON_UNIT;
  auto fill_attr=CUSPARSE_SPMAT_FILL_MODE,diag_attr=CUSPARSE_SPMAT_DIAG_TYPE;auto alg=CUSPARSE_SPSV_ALG_DEFAULT;
#endif
  MB_CHECK(MB_SPARSE(SpMatSetAttribute)(A,fill_attr,&fill,sizeof(fill)));MB_CHECK(MB_SPARSE(SpMatSetAttribute)(A,diag_attr,&diag,sizeof(diag)));
  MB_SPARSE(DnVecDescr_t) X,Y;MB_CHECK(MB_SPARSE(CreateDnVec)(&X,n,dX.p,f32));MB_CHECK(MB_SPARSE(CreateDnVec)(&Y,n,dY.p,f32));
  MB_SPARSE(SpSVDescr_t) desc;MB_CHECK(MB_SPARSE(SpSV_createDescr)(&desc));size_t bytes=0;
  MB_CHECK(MB_SPARSE(SpSV_bufferSize)(h,op,&alpha,A,X,Y,f32,alg,desc,&bytes));Buffer<unsigned char>work(bytes);
  MB_CHECK(MB_SPARSE(SpSV_analysis)(h,op,&alpha,A,X,Y,f32,alg,desc,work.p));MB_CHECK(MB_SPARSE(SpSV_solve)(h,op,&alpha,A,X,Y,f32,alg,desc));
  emit("Y",dY.get());MB_CHECK(MB_SPARSE(SpSV_destroyDescr)(desc));MB_CHECK(MB_SPARSE(DestroyDnVec)(X));MB_CHECK(MB_SPARSE(DestroyDnVec)(Y));MB_CHECK(MB_SPARSE(DestroySpMat)(A));
 }else{
  int n=8,block=4,bnnz=2,nnz=32;bool column_order=c=="block-column-order";
  std::vector<int>offset={0,1,2},columns=c=="changed-pattern"?std::vector<int>{1,0}:std::vector<int>{0,1};
  std::vector<float>A(n*n),B(n*n),C(nnz,0);
  for(int i=0;i<n*n;++i){A[i]=B[i]=i%n+1;if(c=="changed-pattern")A[i]=float(i%13-6)/4.;}
  float alpha=c=="nonzero-beta"?-.75f:1.f,beta=c=="nonzero-beta"||column_order?.25f:0.f;
  if(beta!=0)for(int i=0;i<nnz;++i)C[i]=float(i%7-3)/4.;
  emit("input_A",A);emit("input_B",B);emit("input_C",C);emit("input_offsets",offset);emit("input_columns",columns);scalar("input_alpha",alpha);scalar("input_beta",beta);scalar("input_column_order",int(column_order));
  Buffer<float>dA(A),dB(B),dC(C),csrV(nnz);Buffer<int>dO(offset),dI(columns),csrO(n+1),csrI(nnz),mapping(nnz);
  MB_SPARSE(DnMatDescr_t) matA,matB;MB_SPARSE(SpMatDescr_t) matC;
  MB_CHECK(MB_SPARSE(CreateDnMat)(&matA,n,n,n,dA.p,f32,row));MB_CHECK(MB_SPARSE(CreateDnMat)(&matB,n,n,n,dB.p,f32,row));
#ifdef __HIP_PLATFORM_AMD__
  bsr_expand<<<1,1>>>(dO.p,dI.p,dC.p,csrO.p,csrI.p,csrV.p,mapping.p,n,block,column_order);MB_CHECK(hipGetLastError());
  MB_CHECK(hipsparseCreateCsr(&matC,n,n,nnz,csrO.p,csrI.p,csrV.p,i32,i32,zero,f32));
  emit("bridge_rows",csrO.get());emit("bridge_columns",csrI.get());emit("bridge_values",csrV.get());auto alg=HIPSPARSE_SDDMM_ALG_DEFAULT;
#else
  MB_CHECK(cusparseCreateBsr(&matC,n/block,n/block,bnnz,block,block,dO.p,dI.p,dC.p,i32,i32,zero,f32,column_order?col:row));auto alg=CUSPARSE_SDDMM_ALG_DEFAULT;
#endif
  size_t bytes=0;MB_CHECK(MB_SPARSE(SDDMM_bufferSize)(h,op,op,&alpha,matA,matB,&beta,matC,f32,alg,&bytes));Buffer<unsigned char>work(bytes);
  MB_CHECK(MB_SPARSE(SDDMM_preprocess)(h,op,op,&alpha,matA,matB,&beta,matC,f32,alg,work.p));MB_CHECK(MB_SPARSE(SDDMM)(h,op,op,&alpha,matA,matB,&beta,matC,f32,alg,work.p));
#ifdef __HIP_PLATFORM_AMD__
  bsr_restore<<<1,64>>>(csrV.p,mapping.p,dC.p,nnz);MB_CHECK(hipGetLastError());
#endif
  emit("C",dC.get());MB_CHECK(MB_SPARSE(DestroyDnMat)(matA));MB_CHECK(MB_SPARSE(DestroyDnMat)(matB));MB_CHECK(MB_SPARSE(DestroySpMat)(matC));
 }
 MB_CHECK(MB_SPARSE(Destroy)(h));return 0;
}
}
