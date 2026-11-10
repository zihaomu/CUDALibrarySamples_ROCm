#pragma once
#include "rewrite_runtime.hpp"
namespace rewrite {
__global__ void split_complex(const C32*a,float*r,float*i,float*s,int rows,int cols,int ld,int op){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=rows*cols)return;int row=t%rows,col=t/rows;
 C32 v=op?a[col+row*ld]:a[row+col*ld];if(op==2)v.y=-v.y;r[t]=v.x;i[t]=v.y;s[t]=v.x+v.y;
}
__global__ void finish_complex(C32*c,const float*p,const float*q,const float*r,int m,int n,int ldc,C32 alpha,C32 beta,int triangle,int hermitian){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=m*n)return;int i=t%m,j=t/m;
 if((triangle==1&&i>j)||(triangle==2&&i<j))return;
 C32 value=mul(alpha,C32{p[t]-q[t],r[t]-p[t]-q[t]});
 if(beta.x!=0||beta.y!=0){C32 old=c[i+j*ldc];if(hermitian&&i==j)old.y=0;value=add(value,mul(beta,old));}
 if(hermitian&&i==j)value.y=0;c[i+j*ldc]=value;
}
inline void complex3m(Blas&b,const C32*a,const C32*bb,C32*c,int m,int n,int k,int lda,int ldb,int ldc,int opa,int opb,C32 alpha,C32 beta,int triangle,int hermitian){
 Buffer<float> ar(m*k),ai(m*k),as(m*k),br(k*n),bi(k*n),bs(k*n),p(m*n),q(m*n),r(m*n);
 split_complex<<<(m*k+255)/256,256,0,b.stream>>>(a,ar.p,ai.p,as.p,m,k,lda,opa);
 split_complex<<<(k*n+255)/256,256,0,b.stream>>>(bb,br.p,bi.p,bs.p,k,n,ldb,opb);
 float one=1,zero=0;
 RW_CHECK(RW_BLAS(Sgemm)(b.h,RW_N,RW_N,m,n,k,&one,ar.p,m,br.p,k,&zero,p.p,m));
 RW_CHECK(RW_BLAS(Sgemm)(b.h,RW_N,RW_N,m,n,k,&one,ai.p,m,bi.p,k,&zero,q.p,m));
 RW_CHECK(RW_BLAS(Sgemm)(b.h,RW_N,RW_N,m,n,k,&one,as.p,m,bs.p,k,&zero,r.p,m));
 finish_complex<<<(m*n+255)/256,256,0,b.stream>>>(c,p.p,q.p,r.p,m,n,ldc,alpha,beta,triangle,hermitian);
 RW_CHECK(RW_RT(StreamSynchronize)(b.stream));
}
__global__ void unpack_planar(const __half*a,C32*out,int rows,int cols,int ld){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<rows*cols){int at=t%rows+(t/rows)*ld;out[at]={__half2float(a[ld*cols+at]),__half2float(a[at])};}}
__global__ void pack_planar(const C32*a,__half*out,int m,int n,int ld){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<m*n){int at=t%m+(t/m)*ld;out[at]=__float2half(a[at].y);out[ld*n+at]=__float2half(a[at].x);}}
inline int blas_main(const std::string&kind){try{
 Config cfg;identity();int m=cfg.get("m"),n=cfg.get("n"),k=cfg.get("k"),lda=cfg.get("lda"),ldb=cfg.get("ldb"),ldc=cfg.get("ldc"),opa=cfg.get("opa"),opb=cfg.get("opb"),repeat=cfg.get("repeat",1),tri=cfg.get("triangle");
 C32 alpha{float(cfg.get("alpha_r",1)),float(cfg.get("alpha_i"))},beta{float(cfg.get("beta_r")),float(cfg.get("beta_i"))};Blas handle;
 int ac=opa?m:k,bc=opb?k:n;bool rank=kind=="herk3m"||kind=="syrk3m";
 if(rank){n=m;ac=opa?m:k;bc=ac;opb=opa?0:kind=="herk3m"?2:1;ldb=lda;}
 if(kind=="planar"){
  auto av=read<__half>("A",2*lda*k),bv=read<__half>("B",2*ldb*n),cv=read<__half>("C",2*ldc*n);
  Buffer<__half>a(av),b(bv),c(cv);Buffer<C32>aa(lda*k),bb(ldb*n),cc(ldc*n);
  for(int run=0;run<repeat;++run){c.put(cv);unpack_planar<<<(m*k+255)/256,256,0,handle.stream>>>(a.p,aa.p,m,k,lda);unpack_planar<<<(k*n+255)/256,256,0,handle.stream>>>(b.p,bb.p,k,n,ldb);unpack_planar<<<(m*n+255)/256,256,0,handle.stream>>>(c.p,cc.p,m,n,ldc);RW_CHECK(RW_RT(StreamSynchronize)(handle.stream));complex3m(handle,aa.p,bb.p,cc.p,m,n,k,lda,ldb,ldc,0,0,alpha,beta,0,0);pack_planar<<<(m*n+255)/256,256>>>(cc.p,c.p,m,n,ldc);sync();}
  emit("output",c.get());
 }else{
  auto av=read<C32>("A",lda*ac),bv=rank?av:read<C32>("B",ldb*bc),cv=read<C32>("C",ldc*n);Buffer<C32>a(av),b(bv),c(cv);
  for(int run=0;run<repeat;++run){c.put(cv);complex3m(handle,a.p,b.p,c.p,m,n,k,lda,ldb,ldc,opa,opb,alpha,beta,tri,kind=="herk3m");}emit("output",c.get());
 }
 emit("trace",std::vector<int>{3*repeat,repeat,0,0});return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
}
