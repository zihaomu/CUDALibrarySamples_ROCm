#pragma once
#include "rewrite_runtime.hpp"
namespace rewrite {
__host__ __device__ inline int col32(int row,int col,int ld){return col/32*ld+row*32+col%32;}
__host__ __device__ inline int col4(int row,int col,int ld){return col/32*ld+row/8*256+(row%2)*128+(row%8/2)*4+(col%32/4)*16+col%4;}
__global__ void pack_int8(const int8_t*a,const int8_t*b,int8_t*pa,int8_t*pb,int m,int n,int k,int lda,int ldb,int pald,int pbld){
 int t=blockIdx.x*blockDim.x+threadIdx.x;
 if(t<m*k){int i=t%m,j=t/m;pa[col32(i,j,pald)]=a[i+j*lda];}
 if(t<n*k){int i=t%n,j=t/n;pb[col4(i,j,pbld)]=b[j+i*ldb];}
}
__global__ void integer_product(const int8_t*a,const int8_t*b,const int32_t*old,int32_t*c,int m,int n,int k,int ald,int bld,int cld,int ldc,int alpha,int beta){
 int t=blockIdx.x*blockDim.x+threadIdx.x;if(t>=m*n)return;int i=t%m,j=t/m;int32_t v=0;
 for(int p=0;p<k;++p)v+=(int32_t)a[col32(i,p,ald)]*(int32_t)b[col4(j,p,bld)];
 c[col32(i,j,cld)]=alpha*v+(beta?beta*old[i+j*ldc]:0);
}
__global__ void unpack_int32(const int32_t*c,int32_t*out,int m,int n,int cld,int ldc){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<m*n)out[t%m+(t/m)*ldc]=c[col32(t%m,t/m,cld)];}
__global__ void unpack_for_native(const int8_t*pa,const int8_t*pb,int8_t*a,int8_t*b,int m,int n,int k,int mp,int np,int kp,int ald,int bld){
 int t=blockIdx.x*blockDim.x+threadIdx.x;
 if(t<mp*kp){int i=t%mp,j=t/mp;a[t]=(i<m&&j<k)?pa[col32(i,j,ald)]:0;}
 if(t<kp*np){int i=t%kp,j=t/kp;b[t]=(i<k&&j<n)?pb[col4(j,i,bld)]:0;}
}
__global__ void pack_native_result(const int32_t*value,const int32_t*old,int32_t*packed,int m,int n,int mp,int cld,int ldc,int alpha,int beta){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<m*n){int i=t%m,j=t/m;packed[col32(i,j,cld)]=alpha*value[i+j*mp]+(beta?beta*old[i+j*ldc]:0);}}
inline int int8_main(){try{
 Config cfg;identity();int m=cfg.get("m"),n=cfg.get("n"),k=cfg.get("k"),lda=cfg.get("lda"),ldb=cfg.get("ldb"),ldc=cfg.get("ldc"),repeat=cfg.get("repeat",1);
 auto av=read<int8_t>("A",lda*k),bv=read<int8_t>("B",ldb*n);auto cv=read<int32_t>("C",ldc*n);
 int ald=32*m,bld=32*((n+7)/8*8),cld=32*m,as=(k+31)/32*ald,bs=(k+31)/32*bld,cs=(n+31)/32*cld;
 Buffer<int8_t>a(av),b(bv),pa(std::vector<int8_t>(as+16,85)),pb(std::vector<int8_t>(bs+16,85));
 Buffer<int32_t>c(cv),pc(std::vector<int32_t>(cs+16,0x12345678));
 int mp=(m+3)/4*4,np=(n+3)/4*4,kp=(k+3)/4*4,native_calls=0,fallback_calls=0;
 Buffer<int8_t>na(mp*kp),nb(kp*np);Buffer<int32_t>nc(mp*np);Blas blas;
 for(int r=0;r<repeat;++r){c.put(cv);int count=std::max(m*k,n*k);pack_int8<<<(count+255)/256,256>>>(a.p,b.p,pa.p,pb.p,m,n,k,lda,ldb,ald,bld);
 int native_count=std::max(mp*kp,kp*np);unpack_for_native<<<(native_count+255)/256,256>>>(pa.p,pb.p,na.p,nb.p,m,n,k,mp,np,kp,ald,bld);sync();
 int one=1,zero=0;
#ifdef __HIP_PLATFORM_AMD__
 auto status=hipblasGemmEx(blas.h,HIPBLAS_OP_N,HIPBLAS_OP_N,mp,np,kp,&one,na.p,HIP_R_8I,mp,nb.p,HIP_R_8I,kp,&zero,nc.p,HIP_R_32I,mp,HIPBLAS_COMPUTE_32I,HIPBLAS_GEMM_DEFAULT);
#else
 auto status=cublasGemmEx(blas.h,CUBLAS_OP_N,CUBLAS_OP_N,mp,np,kp,&one,na.p,CUDA_R_8I,mp,nb.p,CUDA_R_8I,kp,&zero,nc.p,CUDA_R_32I,mp,CUBLAS_COMPUTE_32I,CUBLAS_GEMM_DEFAULT);
#endif
 RW_CHECK(RW_RT(StreamSynchronize)(blas.stream));
 if(status==0){++native_calls;pack_native_result<<<(m*n+255)/256,256>>>(nc.p,c.p,pc.p,m,n,mp,cld,ldc,cfg.get("alpha_r",1),cfg.get("beta_r"));}
 else{++fallback_calls;std::cout<<"native-int8-status="<<int(status)<<"; explicit HIP integer fallback\n";integer_product<<<(m*n+255)/256,256>>>(pa.p,pb.p,c.p,pc.p,m,n,k,ald,bld,cld,ldc,cfg.get("alpha_r",1),cfg.get("beta_r"));}
 unpack_int32<<<(m*n+255)/256,256>>>(pc.p,c.p,m,n,cld,ldc);sync();}
 emit("output",c.get());emit("packed_A",pa.get());emit("packed_B",pb.get());emit("packed_C",pc.get());
 emit("trace",std::vector<int>{repeat,repeat,ald,bld,cld,as,bs,cs,native_calls,fallback_calls});return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
}
