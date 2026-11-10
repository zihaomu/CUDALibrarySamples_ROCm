// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batches_runtime.hpp"
#include <mpi.h>
#include <unistd.h>
#include <thread>
#include <mutex>
#include <memory>
#include <numeric>
#include <iomanip>
#ifdef __HIP_PLATFORM_AMD__
#include <rccl/rccl.h>
#include <hip/hip_fp16.h>
#define D12_F32 HIP_R_32F
#define D12_F16 HIP_R_16F
#define D12_COMPUTE HIPBLAS_COMPUTE_32F
#else
#include <nccl.h>
#include <cuda_fp16.h>
#define D12_F32 CUDA_R_32F
#define D12_F16 CUDA_R_16F
#define D12_COMPUTE CUBLAS_COMPUTE_32F
#endif
namespace migration_dist {
using namespace migration_batch;
inline std::mutex output_mutex;
struct Context {
 int rank,size,device;ncclComm_t comm;std::string directory;int ag=0,ar=0,rs=0,bc=0,kernels=0,blas=0;
 void sync(){MB_CHECK(MB_RT(DeviceSynchronize)());}
 template<class T>void save(const std::string&name,const std::vector<T>&v){std::ofstream f(directory+"/r"+std::to_string(rank)+"_"+name+".bin",std::ios::binary);f.write((const char*)v.data(),v.size()*sizeof(T));if(!f)throw std::runtime_error("evidence write");}
 void sum(const float*in,float*out,size_t n){MB_CHECK(ncclAllReduce(in,out,n,ncclFloat,ncclSum,comm,0));++ar;sync();}
 void broadcast(void*in,size_t n,ncclDataType_t type,int root){MB_CHECK(ncclBroadcast(in,in,n,type,root,comm,0));++bc;sync();}
 void finish(){sync();char bdf[64];MB_CHECK(MB_RT(DeviceGetPCIBusId)(bdf,64,device));std::ofstream f(directory+"/rank"+std::to_string(rank)+".json");f<<"{\"rank\":"<<rank<<",\"size\":"<<size<<",\"device\":"<<device<<",\"pci\":\""<<bdf<<"\",\"pid\":"<<getpid()<<",\"allgather\":"<<ag<<",\"allreduce\":"<<ar<<",\"reducescatter\":"<<rs<<",\"broadcast\":"<<bc<<",\"kernels\":"<<kernels<<",\"blas\":"<<blas<<"}\n";}
};
inline float value12(int i,int j,int salt){return float(((i*17+j*13+salt)%31)-15)/32;}
inline int owner12(int i,int j,int block,int p,int q){return (i/block%p)+(j/block%q)*p;}
__global__ void scatter12(const float*local,const int*index,float*global,int n){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<n)global[index[t]]=local[t];}
__global__ void select12(const float*global,const int*index,float*local,int n){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<n)local[t]=global[index[t]];}
__global__ void axpby12(const float*a,float*c,int m,int n,const int*index,int count,int cr,int ar,int ia,int ja,int ic,int jc,float alpha,float beta){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<count){int row=index[t]%cr-ic,col=index[t]/cr-jc;if(row>=0&&row<m&&col>=0&&col<n)c[t]=alpha*a[(row+ia)+(col+ja)*ar]+beta*c[t];}}
inline std::vector<int>indices12(int rows,int cols,int block,int p,int q,int rank){std::vector<int>v;for(int j=0;j<cols;++j)for(int i=0;i<rows;++i)if(owner12(i,j,block,p,q)==rank)v.push_back(i+j*rows);return v;}
inline std::vector<float>gather12(Context&c,const std::vector<float>&local,const std::vector<int>&idx,int total){Buffer<float>l(local),masked(std::vector<float>(total,0)),all(total);Buffer<int>ix(idx);if(!idx.empty()){scatter12<<<(idx.size()+255)/256,256>>>(l.p,ix.p,masked.p,idx.size());++c.kernels;}c.sum(masked.p,all.p,total);return all.get();}
inline void gemm12(Context&c,int m,int n,int k,const float*a,const float*b,float*out,float beta=0,bool half=false){Blas h;float alpha=1;
 if(!half)MB_CHECK(MB_BLAS(Sgemm)(h.h,MB_CONST(OP_N),MB_CONST(OP_N),m,n,k,&alpha,a,m,b,k,&beta,out,m));
 else {std::vector<float>ha(size_t(m)*k),hb(size_t(k)*n);MB_CHECK(MB_RT(Memcpy)(ha.data(),a,ha.size()*4,MB_RT(MemcpyDeviceToHost)));MB_CHECK(MB_RT(Memcpy)(hb.data(),b,hb.size()*4,MB_RT(MemcpyDeviceToHost)));std::vector<__half>ah(ha.begin(),ha.end()),bh(hb.begin(),hb.end());Buffer<__half>aa(ah),bb(bh);MB_CHECK(MB_BLAS(GemmEx)(h.h,MB_CONST(OP_N),MB_CONST(OP_N),m,n,k,&alpha,aa.p,D12_F16,m,bb.p,D12_F16,k,&beta,out,D12_F32,m,D12_COMPUTE,MB_CONST(GEMM_DEFAULT)));}
 ++c.blas;c.sync();}
__global__ void quantize12(float*v,int n){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<n)v[t]=__half2float(__float2half(v[t]));}
inline void basic12(Context&c,const std::string&kind){auto cas=selected_case();bool redist=kind=="gemr2d";int m=redist?1024:10,n=m,k=10;int block=redist?64:2,p=cas=="boundary"?1:2,q=2/p;int ia=redist?0:2,ja=redist?0:2,ic=0,jc=0;
 if(cas=="irregular"){m=13;n=11;k=7;block=3;}if(cas=="singular-or-empty"){m=1;n=1;k=1;}
 int ar=m+ia,ac=(kind=="gemm"?k:n)+ja,cr=m+ic,cc=n+jc;auto ai=indices12(ar,ac,block,p,q,c.rank),ci=indices12(cr,cc,redist?128:block,redist?q:p,redist?p:q,c.rank);std::vector<float>a(ai.size()),initial(ci.size());
 for(size_t t=0;t<ai.size();++t)a[t]=value12(ai[t]%ar,ai[t]/ar,cas=="changed-values"?9:3);for(size_t t=0;t<ci.size();++t)initial[t]=value12(ci[t]%cr,ci[t]/cr,7);
 c.save("A_local",a);c.save("A_indices",ai);c.save("C_initial",initial);c.save("C_indices",ci);auto full=gather12(c,a,ai,ar*ac);Buffer<float>all(full),out(initial);Buffer<int>idx(ci);int repeat=cas=="repeat"?3:1;
 if(kind=="gemm"){
  // Every device computes its own block-cyclic row/column intersection with native BLAS.
  std::vector<int>bi=indices12(k*n,1,2,p,q,c.rank);std::vector<float>b(bi.size());for(size_t t=0;t<bi.size();++t)b[t]=value12(bi[t]%k,bi[t]/k,5);auto B=gather12(c,b,bi,k*n);c.save("B_local",b);c.save("B_indices",bi);
  std::vector<int>rows,cols;for(int i=0;i<m;++i)if(owner12(i,0,block,p,1)==c.rank%p)rows.push_back(i);for(int j=0;j<n;++j)if((j/block)%q==c.rank/p)cols.push_back(j);std::vector<float>aa(rows.size()*k),bb(k*cols.size()),ccp(rows.size()*cols.size());for(int j=0;j<k;++j)for(size_t i=0;i<rows.size();++i)aa[i+j*rows.size()]=full[rows[i]+ia+(j+ja)*ar];for(size_t j=0;j<cols.size();++j)for(int i=0;i<k;++i)bb[i+j*k]=B[i+cols[j]*k];for(size_t j=0;j<cols.size();++j)for(size_t i=0;i<rows.size();++i)ccp[i+j*rows.size()]=value12(rows[i],cols[j],7);Buffer<float>ga(aa),gb(bb),gc(ccp);for(int rep=0;rep<repeat;++rep){gc.put(ccp);if(!rows.empty()&&!cols.empty())gemm12(c,rows.size(),cols.size(),k,ga.p,gb.p,gc.p,1);}auto answer=gc.get();for(size_t t=0;t<ci.size();++t){auto ri=std::find(rows.begin(),rows.end(),ci[t]%cr),co=std::find(cols.begin(),cols.end(),ci[t]/cr);initial[t]=answer[(ri-rows.begin())+(co-cols.begin())*rows.size()];}out.put(initial);
 }else if(redist){for(int rep=0;rep<repeat;++rep){if(!ci.empty())select12<<<(ci.size()+255)/256,256>>>(all.p,idx.p,out.p,ci.size());++c.kernels;}c.sync();auto back=gather12(c,out.get(),ci,ar*ac);Buffer<float>backgpu(back),restored(ai.size());Buffer<int>aidx(ai);if(!ai.empty())select12<<<(ai.size()+255)/256,256>>>(backgpu.p,aidx.p,restored.p,ai.size());++c.kernels;c.save("roundtrip",restored.get());}
 else for(int rep=0;rep<repeat;++rep){out.put(initial);if(!ci.empty())axpby12<<<(ci.size()+255)/256,256>>>(all.p,out.p,m,n,idx.p,ci.size(),cr,ar,ia,ja,ic,jc,1,1);++c.kernels;}
 c.sync();c.save("output",out.get());c.save("config",std::vector<int>{m,n,k,block,p,q,ar,ac,cr,cc,ia,ja,repeat});}
inline void collective12(Context&c,const std::string&kind){auto cas=selected_case();int m=1024,n=1024,k=1024;if(cas=="irregular"){m=13;n=11;k=9;}if(cas=="boundary"){m=3;n=5;k=2;}if(cas=="singular-or-empty"){m=2;n=2;k=1;}bool ag=kind=="matmul_ag",rs=kind=="matmul_rs";int count=(ag?m:k)+c.size-1;count/=c.size;int start=c.rank*count;int nc=(n+c.size-1)/c.size;int nstart=c.rank*nc;std::vector<float>a(ag?count*k:m*count,0),b(ag?k*nc:count*n,0);
 for(int j=0;j<(ag?k:count);++j)for(int i=0;i<(ag?count:m);++i){int row=ag?i+start:i,col=ag?j:j+start;if(row<m&&col<k)a[i+j*(ag?count:m)]=value12(row,col,cas=="changed-values"?11:3);}
 for(int j=0;j<(ag?nc:n);++j)for(int i=0;i<(ag?k:count);++i){int row=ag?i:i+start,col=ag?j+nstart:j;if(row<k&&col<n)b[i+j*(ag?k:count)]=value12(row,col,5);}
 c.save("A_local",a);c.save("B_local",b);Buffer<float>aa(a),bb(b),out(size_t(m)*(rs?nc:ag?nc:n));int repeat=cas=="repeat"?3:1;
 for(int rep=0;rep<repeat;++rep){
  if(ag){Buffer<float>gathered(size_t(count)*k*c.size);MB_CHECK(ncclAllGather(aa.p,gathered.p,count*k,ncclFloat,c.comm,0));++c.ag;c.sync();auto packed=gathered.get();std::vector<float>full(m*k);for(int j=0;j<k;++j)for(int i=0;i<m;++i)full[i+j*m]=packed[(i/count)*count*k+i%count+j*count];Buffer<float>complete(full);gemm12(c,m,nc,k,complete.p,bb.p,out.p,0,true);}
  else {Buffer<float>partial(size_t(m)*nc*c.size);MB_CHECK(MB_RT(Memset)(partial.p,0,partial.n*4));gemm12(c,m,n,count,aa.p,bb.p,partial.p,0,true);if(rs){MB_CHECK(ncclReduceScatter(partial.p,out.p,m*nc,ncclFloat,ncclSum,c.comm,0));++c.rs;c.sync();}else c.sum(partial.p,out.p,m*n);}
  quantize12<<<(out.n+255)/256,256>>>(out.p,out.n);++c.kernels;c.sync();
 }
 c.save("output",out.get());c.save("config",std::vector<int>{m,n,k,count,start,nc,nstart,repeat,ag,rs});}
inline int main12(const std::string&kind,int argc,char**argv){int initialized=0;MPI_Init(&argc,&argv);MPI_Initialized(&initialized);int rank,size;MPI_Comm_rank(MPI_COMM_WORLD,&rank);MPI_Comm_size(MPI_COMM_WORLD,&size);try{int count;MB_CHECK(MB_RT(GetDeviceCount)(&count));if(size!=2||count<size)throw std::runtime_error("requires two MPI ranks on two distinct visible GPUs");MB_CHECK(MB_RT(SetDevice)(rank));ncclUniqueId id;if(rank==0)MB_CHECK(ncclGetUniqueId(&id));MPI_Bcast(&id,sizeof(id),MPI_BYTE,0,MPI_COMM_WORLD);ncclComm_t comm;MB_CHECK(ncclCommInitRank(&comm,size,id,rank));const char*dir=std::getenv("MIGRATION_OUTPUT_DIR");if(!dir)throw std::runtime_error("MIGRATION_OUTPUT_DIR required");Context c{rank,size,rank,comm,dir};if(kind.rfind("matmul_",0)==0)collective12(c,kind);else basic12(c,kind);c.finish();MB_CHECK(ncclCommDestroy(comm));MPI_Finalize();return 0;}catch(const std::exception&e){std::cerr<<"rank "<<rank<<" "<<e.what()<<std::endl;MPI_Abort(MPI_COMM_WORLD,1);return 1;}}
}
