#include "rewrite_runtime.hpp"
#include <cublasLt.h>
#include <cusolverDn.h>
using namespace rewrite;
__global__ void direct_integer(const int8_t*a,const int8_t*b,int32_t*c,int m,int n,int k,int lda,int ldb,int ldc,int alpha,int beta){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<m*n){int row=i%m,col=i/m,v=0;for(int p=0;p<k;++p)v+=(int)a[row+p*lda]*(int)b[p+col*ldb];c[row+col*ldc]=alpha*v+(beta?beta*c[row+col*ldc]:0);}}
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("kind required");std::string kind=argv[1];Config cfg;identity();
 int m=cfg.get("m"),n=cfg.get("n"),k=cfg.get("k"),lda=cfg.get("lda"),ldb=cfg.get("ldb"),ldc=cfg.get("ldc"),repeat=cfg.get("repeat",1);
 cuComplex alpha=make_cuComplex(cfg.get("alpha_r",1),cfg.get("alpha_i")),beta=make_cuComplex(cfg.get("beta_r"),cfg.get("beta_i"));Blas h;
 auto op=[](int v){return v==2?CUBLAS_OP_C:v==1?CUBLAS_OP_T:CUBLAS_OP_N;};
 if(kind=="gemm3m"||kind=="herk3m"||kind=="syrk3m"){
  int opa=cfg.get("opa"),opb=cfg.get("opb");bool rank=kind!="gemm3m";auto av=read<cuComplex>("A",lda*(opa?m:k));auto bv=rank?av:read<cuComplex>("B",ldb*(opb?k:n));auto cv=read<cuComplex>("C",ldc*n);Buffer<cuComplex>a(av),b(bv),c(cv);
  for(int r=0;r<repeat;++r){c.put(cv);
   if(!rank)RW_CHECK(cublasCgemm3m(h.h,op(opa),op(opb),m,n,k,&alpha,a.p,lda,b.p,ldb,&beta,c.p,ldc));
   else if(kind=="herk3m")RW_CHECK(cublasCherk3mEx(h.h,cfg.get("triangle")==1?CUBLAS_FILL_MODE_UPPER:CUBLAS_FILL_MODE_LOWER,op(opa),n,k,&alpha.x,a.p,CUDA_C_32F,lda,&beta.x,c.p,CUDA_C_32F,ldc));
   else RW_CHECK(cublasCsyrk3mEx(h.h,cfg.get("triangle")==1?CUBLAS_FILL_MODE_UPPER:CUBLAS_FILL_MODE_LOWER,op(opa),n,k,&alpha,a.p,CUDA_C_32F,lda,&beta,c.p,CUDA_C_32F,ldc));
   RW_CHECK(cudaStreamSynchronize(h.stream));
  }emit("output",c.get());emit("trace",std::vector<int>{repeat,repeat});
 }else if(kind=="planar"){
  auto av=read<__half>("A",2*lda*k),bv=read<__half>("B",2*ldb*n),cv=read<__half>("C",2*ldc*n);Buffer<__half>a(av),b(bv),c(cv);
  cublasLtHandle_t lt;RW_CHECK(cublasLtCreate(&lt));cublasLtMatmulDesc_t desc;RW_CHECK(cublasLtMatmulDescCreate(&desc,CUBLAS_COMPUTE_32F,CUDA_C_32F));
  cublasLtMatrixLayout_t ad,bd,cd;RW_CHECK(cublasLtMatrixLayoutCreate(&ad,CUDA_C_16F,m,k,lda));RW_CHECK(cublasLtMatrixLayoutCreate(&bd,CUDA_C_16F,k,n,ldb));RW_CHECK(cublasLtMatrixLayoutCreate(&cd,CUDA_C_16F,m,n,ldc));
  int64_t ao=-2LL*lda*k,bo=-2LL*ldb*n,co=-2LL*ldc*n;
  RW_CHECK(cublasLtMatrixLayoutSetAttribute(ad,CUBLASLT_MATRIX_LAYOUT_PLANE_OFFSET,&ao,sizeof(ao)));RW_CHECK(cublasLtMatrixLayoutSetAttribute(bd,CUBLASLT_MATRIX_LAYOUT_PLANE_OFFSET,&bo,sizeof(bo)));RW_CHECK(cublasLtMatrixLayoutSetAttribute(cd,CUBLASLT_MATRIX_LAYOUT_PLANE_OFFSET,&co,sizeof(co)));
  for(int r=0;r<repeat;++r){c.put(cv);RW_CHECK(cublasLtMatmul(lt,desc,&alpha,a.p+lda*k,ad,b.p+ldb*n,bd,&beta,c.p+ldc*n,cd,c.p+ldc*n,cd,nullptr,nullptr,0,h.stream));RW_CHECK(cudaStreamSynchronize(h.stream));}
  emit("output",c.get());RW_CHECK(cublasLtMatrixLayoutDestroy(ad));RW_CHECK(cublasLtMatrixLayoutDestroy(bd));RW_CHECK(cublasLtMatrixLayoutDestroy(cd));RW_CHECK(cublasLtMatmulDescDestroy(desc));RW_CHECK(cublasLtDestroy(lt));
 }else if(kind=="igemm"){
  auto av=read<int8_t>("A",lda*k),bv=read<int8_t>("B",ldb*n);auto cv=read<int32_t>("C",ldc*n);Buffer<int8_t>a(av),b(bv);Buffer<int32_t>c(cv);
  for(int r=0;r<repeat;++r){c.put(cv);direct_integer<<<(m*n+255)/256,256>>>(a.p,b.p,c.p,m,n,k,lda,ldb,ldc,cfg.get("alpha_r",1),cfg.get("beta_r"));sync();}emit("output",c.get());
 }else{
  cusolverDnHandle_t solver;RW_CHECK(cusolverDnCreate(&solver));RW_CHECK(cusolverDnSetStream(solver,h.stream));
  if(kind=="lu"){
   auto av=read<cuComplex>("A",lda*n);Buffer<cuComplex>a(av);Buffer<int>piv(std::min(m,n)),info(1);int lwork;RW_CHECK(cusolverDnCgetrf_bufferSize(solver,m,n,a.p,lda,&lwork));Buffer<cuComplex>work(lwork);
   for(int r=0;r<repeat;++r){a.put(av);RW_CHECK(cusolverDnCgetrf(solver,m,n,a.p,lda,work.p,piv.p,info.p));RW_CHECK(cudaStreamSynchronize(h.stream));}emit("output",a.get());emit("pivots",piv.get());emit("info",info.get());
  }else if(kind=="posv"){
   int batch=cfg.get("batch"),nrhs=cfg.get("nrhs");auto av=read<cuDoubleComplex>("A",batch*lda*n),bv=read<cuDoubleComplex>("B",batch*ldb*nrhs);Buffer<cuDoubleComplex>a(av),b(bv);Buffer<int>info(batch);int lwork;RW_CHECK(cusolverDnZpotrf_bufferSize(solver,CUBLAS_FILL_MODE_LOWER,n,a.p,lda,&lwork));Buffer<cuDoubleComplex>work(lwork);
   for(int r=0;r<repeat;++r){a.put(av);b.put(bv);for(int j=0;j<batch;++j){RW_CHECK(cusolverDnZpotrf(solver,CUBLAS_FILL_MODE_LOWER,n,a.p+j*lda*n,lda,work.p,lwork,info.p+j));RW_CHECK(cudaStreamSynchronize(h.stream));if(info.get()[j]==0)RW_CHECK(cusolverDnZpotrs(solver,CUBLAS_FILL_MODE_LOWER,n,nrhs,a.p+j*lda*n,lda,b.p+j*ldb*nrhs,ldb,info.p+j));}RW_CHECK(cudaStreamSynchronize(h.stream));}emit("factor",a.get());emit("output",b.get());emit("info",info.get());
  }else{
   auto av=read<double>("A",lda*n),bv=read<double>("B",ldb*n);Buffer<double>a(av),b(bv);double one=1;
   for(int r=0;r<repeat;++r){b.put(bv);RW_CHECK(cublasDtrsm(h.h,CUBLAS_SIDE_RIGHT,CUBLAS_FILL_MODE_LOWER,CUBLAS_OP_N,CUBLAS_DIAG_NON_UNIT,m,n,&one,a.p,lda,b.p,ldb));RW_CHECK(cudaStreamSynchronize(h.stream));}emit("output",b.get());emit("A_after",a.get());
  }RW_CHECK(cusolverDnDestroy(solver));
 }return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
