// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batches_runtime.hpp"
#include <climits>
#ifdef __HIP_PLATFORM_AMD__
#include <rocsolver/rocsolver.h>
#endif
namespace migration_batch {
inline int checked_solver_dimension(int64_t x){if(x<0||x>INT_MAX)throw std::runtime_error("rocSOLVER typed SVD/eigen dimension exceeds INT_MAX; no truncation");return int(x);}
struct NativeSolver {
#ifndef __HIP_PLATFORM_AMD__
 cusolverDnHandle_t h;cusolverDnParams_t params;NativeSolver(){MB_CHECK(cusolverDnCreate(&h));MB_CHECK(cusolverDnCreateParams(&params));}~NativeSolver(){cusolverDnDestroyParams(params);cusolverDnDestroy(h);}
#endif
};
#ifdef __HIP_PLATFORM_AMD__
__global__ void singular_diagonal(const double*A,int64_t n,int64_t lda,int*info){int64_t i=int64_t(blockIdx.x)*blockDim.x+threadIdx.x;if(i<n&&A[i+i*lda]==0)atomicMin(info,int(i+1));}
#endif
inline int solver_main(const std::string& kind){try{
 const auto c=selected_case();NativeSolver solver;Blas blas;
#ifdef __HIP_PLATFORM_AMD__
rocblas_handle rh;MB_CHECK(rocblas_create_handle(&rh));
#endif
 if(kind=="Xgetrf"){
  int64_t n=3;bool pivot=c!="no-pivot";std::vector<double>A={1,4,7,2,5,8,3,6,10},B={1,2,3};if(c=="singular-info")for(int i=0;i<3;++i)A[i+6]=0;
  emit("input_A",A);emit("input_B",B);scalar("input_pivot",int(pivot));scalar("input_legacy",int(c=="legacy-algorithm"));Buffer<double>a(A),b(B);Buffer<int64_t>p(std::vector<int64_t>{1,2,3});int64_t info=0;
#ifdef __HIP_PLATFORM_AMD__
  Buffer<int64_t>fi(1);
  if(pivot){if(c=="legacy-algorithm")MB_CHECK(rocsolver_dgetf2_64(rh,n,n,a.p,n,p.p,fi.p));else MB_CHECK(rocsolver_dgetrf_64(rh,n,n,a.p,n,p.p,fi.p));}
  else MB_CHECK(rocsolver_dgetrf_npvt_64(rh,n,n,a.p,n,fi.p));
  info=fi.get()[0];emit("LU",a.get());emit("pivots",p.get());scalar("factor_info",info);
  if(!info)MB_CHECK(rocsolver_dgetrs_64(rh,rocblas_operation_none,n,1,a.p,n,p.p,b.p,n));
#else
  if(c=="legacy-algorithm")MB_CHECK(cusolverDnSetAdvOptions(solver.params,CUSOLVERDN_GETRF,CUSOLVER_ALG_1));
  size_t ds=0,hs=0;MB_CHECK(cusolverDnXgetrf_bufferSize(solver.h,solver.params,n,n,CUDA_R_64F,a.p,n,CUDA_R_64F,&ds,&hs));Buffer<unsigned char>w(ds);std::vector<unsigned char>hw(hs);Buffer<int>fi(1);
  MB_CHECK(cusolverDnXgetrf(solver.h,solver.params,n,n,CUDA_R_64F,a.p,n,pivot?p.p:nullptr,CUDA_R_64F,w.p,ds,hw.data(),hs,fi.p));info=fi.get()[0];emit("LU",a.get());emit("pivots",p.get());scalar("factor_info",info);
  if(!info)MB_CHECK(cusolverDnXgetrs(solver.h,solver.params,MB_CONST(OP_N),n,1,CUDA_R_64F,a.p,n,pivot?p.p:nullptr,CUDA_R_64F,b.p,n,fi.p));
#endif
  if(!info)emit("X",b.get());
 }else if(kind=="Xtrtri"){
  int64_t n=c=="original"?1000:7,lda=n+1;bool upper=c!="lower",unit=c=="unit-diagonal";std::vector<double>A(lda*n,-97),I(lda*n,-97);
  for(int64_t j=0;j<n;++j)for(int64_t i=0;i<n;++i){A[i+j*lda]=(upper?i<=j:i>=j)?(i==j?double(n+1):double((i*13+j*7)%19-9)/100.):0.;I[i+j*lda]=double(i==j);}
  if(c=="singular-info")A[3+3*lda]=0;
  emit("input_A",A);scalar("input_n",n);scalar("input_lda",lda);scalar("input_upper",int(upper));scalar("input_unit",int(unit));Buffer<double>a(A),inv(I);Buffer<int>fi(std::vector<int>{int(n+1)});int info=0;
#ifdef __HIP_PLATFORM_AMD__
  if(!unit){singular_diagonal<<<(n+255)/256,256>>>(a.p,n,lda,fi.p);MB_CHECK(hipGetLastError());info=fi.get()[0];if(info==n+1)info=0;}
  if(!info){double one=1;MB_CHECK(hipblasDtrsm_64(blas.h,HIPBLAS_SIDE_LEFT,upper?HIPBLAS_FILL_MODE_UPPER:HIPBLAS_FILL_MODE_LOWER,HIPBLAS_OP_N,unit?HIPBLAS_DIAG_UNIT:HIPBLAS_DIAG_NON_UNIT,n,n,&one,a.p,lda,inv.p,lda));auto result=inv.get();for(int64_t j=0;j<n;++j)for(int64_t i=0;i<n;++i)if(!(upper?i<=j:i>=j))result[i+j*lda]=A[i+j*lda];emit("inverse",result);}
#else
  size_t ds=0,hs=0;auto u=upper?CUBLAS_FILL_MODE_UPPER:CUBLAS_FILL_MODE_LOWER;auto d=unit?CUBLAS_DIAG_UNIT:CUBLAS_DIAG_NON_UNIT;
  MB_CHECK(cusolverDnXtrtri_bufferSize(solver.h,u,d,n,CUDA_R_64F,a.p,lda,&ds,&hs));Buffer<unsigned char>w(ds);std::vector<unsigned char>hw(hs);MB_CHECK(cusolverDnXtrtri(solver.h,u,d,n,CUDA_R_64F,a.p,lda,w.p,ds,hw.data(),hs,fi.p));info=fi.get()[0];if(!info)emit("inverse",a.get());
#endif
  scalar("factor_info",info);
 }else if(kind=="Xsyevdx"){
  int64_t n=3,meig=0;std::vector<double>A={3.5,.5,0,.5,3.5,0,0,0,2};bool value=c=="value-range"||c=="empty-range";double vl=c=="empty-range"?10:2.5,vu=c=="empty-range"?11:4.5;
  emit("input_A",A);scalar("input_value_range",int(value));scalar("input_vl",vl);scalar("input_vu",vu);Buffer<double>a(A),w(3),z(9);Buffer<int>fi(1);std::vector<double>vectors;
#ifdef __HIP_PLATFORM_AMD__
  const int ni=checked_solver_dimension(n);Buffer<int>nev(1),fail(ni);
  MB_CHECK(rocsolver_dsyevx(rh,rocblas_evect_original,value?rocblas_erange_value:rocblas_erange_all,rocblas_fill_lower,ni,a.p,ni,vl,vu,1,ni,0,nev.p,w.p,z.p,ni,fail.p,fi.p));meig=nev.get()[0];vectors=z.get();
#else
  auto range=value?CUSOLVER_EIG_RANGE_V:CUSOLVER_EIG_RANGE_ALL;size_t ds=0,hs=0;
  MB_CHECK(cusolverDnXsyevdx_bufferSize(solver.h,solver.params,CUSOLVER_EIG_MODE_VECTOR,range,CUBLAS_FILL_MODE_LOWER,n,CUDA_R_64F,a.p,n,&vl,&vu,1L,n,&meig,CUDA_R_64F,w.p,CUDA_R_64F,&ds,&hs));Buffer<unsigned char>work(ds);std::vector<unsigned char>host(hs);
  MB_CHECK(cusolverDnXsyevdx(solver.h,solver.params,CUSOLVER_EIG_MODE_VECTOR,range,CUBLAS_FILL_MODE_LOWER,n,CUDA_R_64F,a.p,n,&vl,&vu,1L,n,&meig,CUDA_R_64F,w.p,CUDA_R_64F,work.p,ds,host.data(),hs,fi.p));vectors=a.get();
#endif
  scalar("factor_info",fi.get()[0]);scalar("meig",meig);auto values=w.get();values.resize(meig);vectors.resize(n*meig);emit("eigenvalues",values);emit("vectors",vectors);
 }else if(kind=="Xgesvd"){
  int64_t m=c=="rectangular"?5:3,n=c=="rectangular"?3:2;std::vector<double>A={1,4,2,2,5,1};if(c=="rectangular"){A.resize(m*n);for(int j=0;j<n;++j)for(int i=0;i<m;++i)A[i+j*m]=double((i*7+j*13)%17-8)/3.;}if(c=="rank-deficient")for(int i=0;i<m;++i)A[i+m]=2*A[i];
  emit("input_A",A);scalar("input_m",m);scalar("input_n",n);Buffer<double>a(A),s(n),u(m*m),vt(n*n);Buffer<int>fi(1);
#ifdef __HIP_PLATFORM_AMD__
  int mi=checked_solver_dimension(m),ni=checked_solver_dimension(n);Buffer<double>e(n);
  MB_CHECK(rocsolver_dgesvd(rh,rocblas_svect_all,rocblas_svect_all,mi,ni,a.p,mi,s.p,u.p,mi,vt.p,ni,e.p,rocblas_outofplace,fi.p));
#else
  size_t ds=0,hs=0;MB_CHECK(cusolverDnXgesvd_bufferSize(solver.h,solver.params,'A','A',m,n,CUDA_R_64F,a.p,m,CUDA_R_64F,s.p,CUDA_R_64F,u.p,m,CUDA_R_64F,vt.p,n,CUDA_R_64F,&ds,&hs));Buffer<unsigned char>work(ds);std::vector<unsigned char>host(hs);
  MB_CHECK(cusolverDnXgesvd(solver.h,solver.params,'A','A',m,n,CUDA_R_64F,a.p,m,CUDA_R_64F,s.p,CUDA_R_64F,u.p,m,CUDA_R_64F,vt.p,n,CUDA_R_64F,work.p,ds,host.data(),hs,fi.p));
#endif
  scalar("factor_info",fi.get()[0]);emit("S",s.get());emit("U",u.get());emit("VT",vt.get());
 }else throw std::runtime_error("unknown solver");MB_CHECK(MB_RT(DeviceSynchronize)());return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
}
