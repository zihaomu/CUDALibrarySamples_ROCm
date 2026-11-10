// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batches_runtime.hpp"
#include "batch5_io.hpp"
#include <rocblas/rocblas.h>
#include <hiptensor/hiptensor.h>
#include <memory>
namespace migration_batch {
template<class T>struct TensorBuffer{
 T*p=nullptr;size_t n;explicit TensorBuffer(size_t count):n(count){auto rc=hipMalloc(reinterpret_cast<void**>(&p),std::max(size_t(1),n*sizeof(T)));if(rc){size_t f=0,t=0;hipMemGetInfo(&f,&t);throw std::runtime_error("tensor allocation bytes="+std::to_string(n*sizeof(T))+" free="+std::to_string(f)+" total="+std::to_string(t)+" status="+std::to_string(int(rc)));}}
 explicit TensorBuffer(const std::vector<T>&v):TensorBuffer(v.size()){put(v);}~TensorBuffer(){if(p)hipFree(p);}void put(const std::vector<T>&v){MB_CHECK(hipMemcpy(p,v.data(),v.size()*sizeof(T),hipMemcpyHostToDevice));}std::vector<T>get()const{std::vector<T>v(n);MB_CHECK(hipMemcpy(v.data(),p,n*sizeof(T),hipMemcpyDeviceToHost));return v;}
};
using Extents=std::unordered_map<int,int64_t>;
inline size_t elements(const std::string&m,const Extents&e){size_t n=1;for(char c:m)n*=e.at(c);return n;}
inline std::vector<int64_t> strides(const std::string&m,const Extents&e){std::vector<int64_t>s;int64_t n=1;for(char c:m){s.push_back(n);n*=e.at(c);}return s;}
inline std::vector<float> tensor_input(const char* name,size_t n){std::vector<float>v(n);batch5::input(name,v.data(),v.size());return v;}
struct TensorMap{int rank=0;uint64_t total=0;int64_t dim[12]={},stride[12]={};};
inline TensorMap mapping(const std::string&ordered,const std::string&physical,const Extents&e){TensorMap m;m.rank=ordered.size();m.total=elements(ordered,e);auto s=strides(physical,e);for(int i=0;i<m.rank;++i){m.dim[i]=e.at(ordered[i]);m.stride[i]=s.at(physical.find(ordered[i]));}return m;}
__global__ void tensor_pack(const float* in,float* out,TensorMap m,bool inverse){uint64_t i=uint64_t(blockIdx.x)*blockDim.x+threadIdx.x;if(i>=m.total)return;uint64_t q=i,offset=0;for(int a=0;a<m.rank;++a){offset+=(q%m.dim[a])*m.stride[a];q/=m.dim[a];}if(inverse)out[offset]=in[i];else out[i]=in[offset];}
struct ContractPlan{
 std::string left,right,reduction;TensorMap a,b,c;int m,n,k;std::string key;
 ContractPlan(const std::string&A,const std::string&B,const std::string&C,const Extents&e){
  for(char x:A){if(C.find(x)!=std::string::npos)left+=x;else if(B.find(x)!=std::string::npos)reduction+=x;else throw std::runtime_error("unsupported implicit contraction");}
  for(char x:B)if(C.find(x)!=std::string::npos)right+=x;
  m=elements(left,e);n=elements(right,e);k=elements(reduction,e);a=mapping(left+reduction,A,e);b=mapping(reduction+right,B,e);c=mapping(left+right,C,e);
  char version[128]={};MB_CHECK(rocblas_get_version_string(version,sizeof(version)));key="fp32:gfx1201:"+std::string(version)+":"+(std::getenv("DEEPINFER_IMAGE_ID")?std::getenv("DEEPINFER_IMAGE_ID"):"unknown")+":"+A+":"+B+":"+C;for(auto pair:std::map<int,int64_t>(e.begin(),e.end()))key+=":"+std::string(1,char(pair.first))+"="+std::to_string(pair.second);
 }
};
// Bound packed workspace without shrinking the original tensor dimensions.
__global__ void tensor_tile(const float*in,float*out,TensorMap map,int64_t rows,int64_t first,int64_t count,bool inverse){uint64_t t=uint64_t(blockIdx.x)*blockDim.x+threadIdx.x,total=uint64_t(count)*(map.total/rows);if(t>=total)return;uint64_t canonical=first+t%count+(t/count)*rows,q=canonical,offset=0;for(int a=0;a<map.rank;++a){offset+=(q%map.dim[a])*map.stride[a];q/=map.dim[a];}if(inverse)out[offset]=in[t];else out[t]=in[offset];}
struct PreparedContract{
 ContractPlan plan;int capacity;TensorBuffer<float>pa,pb,pc;rocblas_handle h;
 PreparedContract(const float*A,const float*B,const ContractPlan&p):plan(p),capacity(std::min(p.m,65536)),pa(size_t(capacity)*p.k),pb(size_t(p.k)*p.n),pc(size_t(capacity)*p.n),inputA(A){MB_CHECK(rocblas_create_handle(&h));tensor_pack<<<(p.b.total+255)/256,256>>>(B,pb.p,p.b,false);MB_CHECK(hipGetLastError());}
 const float*inputA;
 ~PreparedContract(){rocblas_destroy_handle(h);}
 void execute(const float*initial,float*output,float alpha,float beta,int row_block=0){
  int step=row_block>0?std::min(row_block,capacity):capacity;
  for(int i=0;i<plan.m;i+=step){int count=std::min(step,plan.m-i);uint64_t na=uint64_t(count)*plan.k,nc=uint64_t(count)*plan.n;
   tensor_tile<<<(na+255)/256,256>>>(inputA,pa.p,plan.a,plan.m,i,count,false);
   if(beta!=0)tensor_tile<<<(nc+255)/256,256>>>(initial,pc.p,plan.c,plan.m,i,count,false);else MB_CHECK(hipMemset(pc.p,0,nc*sizeof(float)));
   MB_CHECK(rocblas_sgemm(h,rocblas_operation_none,rocblas_operation_none,count,plan.n,plan.k,&alpha,pa.p,count,pb.p,plan.k,&beta,pc.p,count));
   tensor_tile<<<(nc+255)/256,256>>>(pc.p,output,plan.c,plan.m,i,count,true);MB_CHECK(hipGetLastError());
  }
 }
};
inline void contract(const float*A,const std::string&am,const float*B,const std::string&bm,const float*C,float*D,const std::string&cm,const Extents&e,float alpha,float beta){PreparedContract p(A,B,ContractPlan(am,bm,cm,e));p.execute(C,D,alpha,beta);}
inline void unary_tensor(const float*A,float*C,const std::string&am,const std::string&cm,const Extents&e){
 hiptensorHandle_t h;MB_CHECK(hiptensorCreate(&h));hiptensorTensorDescriptor_t da,dc;std::vector<int64_t>ad,cd;for(char c:am)ad.push_back(e.at(c));for(char c:cm)cd.push_back(e.at(c));auto av=batch5::modes(am),cv=batch5::modes(cm);
 MB_CHECK(hiptensorCreateTensorDescriptor(h,&da,ad.size(),ad.data(),nullptr,HIPTENSOR_R_32F,128));MB_CHECK(hiptensorCreateTensorDescriptor(h,&dc,cd.size(),cd.data(),nullptr,HIPTENSOR_R_32F,128));hiptensorOperationDescriptor_t op;
 bool reduction=am.size()!=cm.size();
 if(reduction)MB_CHECK(hiptensorCreateReduction(h,&op,da,av.data(),HIPTENSOR_OP_IDENTITY,dc,cv.data(),HIPTENSOR_OP_IDENTITY,dc,cv.data(),HIPTENSOR_OP_ADD,HIPTENSOR_COMPUTE_DESC_32F));
 else MB_CHECK(hiptensorCreatePermutation(h,&op,da,av.data(),HIPTENSOR_OP_IDENTITY,dc,cv.data(),HIPTENSOR_COMPUTE_DESC_32F));
 hiptensorPlanPreference_t pref;MB_CHECK(hiptensorCreatePlanPreference(h,&pref,HIPTENSOR_ALGO_DEFAULT,HIPTENSOR_JIT_MODE_NONE));uint64_t bytes=0;MB_CHECK(hiptensorEstimateWorkspaceSize(h,op,pref,HIPTENSOR_WORKSPACE_DEFAULT,&bytes));hiptensorPlan_t plan;MB_CHECK(hiptensorCreatePlan(h,&plan,op,pref,bytes));Buffer<unsigned char>workspace(bytes);float alpha=1,beta=0;
 if(reduction)MB_CHECK(hiptensorReduce(h,plan,&alpha,A,&beta,C,C,workspace.p,bytes,0));else MB_CHECK(hiptensorPermute(h,plan,&alpha,A,C,0));
 MB_CHECK(hipDeviceSynchronize());hiptensorDestroyPlan(plan);hiptensorDestroyPlanPreference(pref);hiptensorDestroyOperationDescriptor(op);hiptensorDestroyTensorDescriptor(da);hiptensorDestroyTensorDescriptor(dc);hiptensorDestroy(h);
}
struct PadMap{int64_t dim[4],strideA[4],strideC[4],left[4],right[4];uint64_t total;};
__global__ void padded_permutation(const float*A,float*C,PadMap m){uint64_t idx=uint64_t(blockIdx.x)*blockDim.x+threadIdx.x;if(idx>=m.total)return;uint64_t q=idx,a=0,c=0;bool inside=true;
 for(int i=0;i<4;++i){int64_t size=m.dim[i]+m.left[i]+m.right[i],coordinate=q%size;q/=size;c+=coordinate*m.strideC[i];coordinate-=m.left[i];if(coordinate<0||coordinate>=m.dim[i])inside=false;else a+=coordinate*m.strideA[i];}C[c]=inside?A[a]:0.f;
}
inline uint64_t cache_hash(const std::string&s){uint64_t h=1469598103934665603ull;for(unsigned char c:s)h=(h^c)*1099511628211ull;return h;}
inline void write_cache(const std::string&file,const ContractPlan&p,int block){std::string payload=p.key+" "+std::to_string(block);std::ofstream f(file);f<<"ROCM_CONTRACT_PLAN_V1 "<<cache_hash(payload)<<"\n"<<payload<<"\n";if(!f)throw std::runtime_error("cache write");}
inline int read_cache(const std::string&file,const ContractPlan&p,int&block){std::ifstream f(file);if(!f)return 1;std::string magic,payload;uint64_t checksum;f>>magic>>checksum;std::getline(f,payload);std::getline(f,payload);if(magic!="ROCM_CONTRACT_PLAN_V1"||checksum!=cache_hash(payload))return 2;auto split=payload.rfind(' ');if(split==std::string::npos)return 2;block=std::stoi(payload.substr(split+1));if(payload.substr(0,split)!=p.key||block<1||block>p.m)return 3;return 0;}
inline int tensor_main(const std::string&kind){
 const std::string c=selected_case();bool original=c=="original";
 if(kind=="einsum"){
  int I=c=="non-square"?3:2,J=c=="non-square"?5:4,N=c=="non-square"?7:5,M=c=="non-square"?4:8,K=c=="non-square"?3:7;
  std::vector<std::string>am={"ijn","ijn","nij","nij","nij"},bm={"jmk","jmk","","",""},cm={"inkm","ikmn","ijn","ijn","ji"};
  for(int op=0;op<5;++op){Extents e=op<2?Extents{{'i',I},{'j',J},{'n',N},{'m',M},{'k',K}}:Extents{{'n',I},{'i',J},{'j',N}};std::reverse(am[op].begin(),am[op].end());std::reverse(bm[op].begin(),bm[op].end());std::reverse(cm[op].begin(),cm[op].end());std::string aName="A"+std::to_string(op),bName="B"+std::to_string(op);auto a=tensor_input(aName.c_str(),elements(am[op],e));auto b=tensor_input(bName.c_str(),bm[op].empty()?1:elements(bm[op],e));TensorBuffer<float>A(a),B(b),C(elements(cm[op],e));
   if(bm[op].empty())unary_tensor(A.p,C.p,am[op],cm[op],e);else contract(A.p,am[op],B.p,bm[op],C.p,C.p,cm[op],e,1,0);
   auto out=C.get();batch5::snapshot("output"+std::to_string(op),out);
   batch5::config("einsum",batch5::modes(am[op]),batch5::modes(bm[op]),batch5::modes(cm[op]),{},e,1,0,",\"operation\":"+std::to_string(op));
   std::string src=batch2_tensor::output_path("tensor5.json"),dst=batch2_tensor::output_path("tensor5-"+std::to_string(op)+".json");std::ifstream in(src);std::ofstream of(dst);of<<in.rdbuf();
  }return 0;
 }
 if(kind=="elementwise_permute_padding"){
  Extents e=original?Extents{{'h',128},{'w',32},{'c',128},{'n',128}}:Extents{{'h',3},{'w',5},{'c',7},{'n',2}};std::string am="whcn",cm="cwhn";auto as=strides(am,e);std::vector<int64_t>left={0,1,1,0},right={0,0,0,0};if(!original){left={0,1,2,0};right={0,2,1,0};}
  if(c=="small-strided"){as[0]=2;for(int i=1;i<4;++i)as[i]=as[i-1]*e.at(am[i-1])+3;}
  std::vector<int64_t>cs(4);int64_t size=1;for(int i=0;i<4;++i){cs[i]=size;size*=e.at(cm[i])+left[i]+right[i];}
  size_t na=1,nc=1;for(int i=0;i<4;++i){na+=(e.at(am[i])-1)*as[i];nc+=(e.at(cm[i])+left[i]+right[i]-1)*cs[i];}
  auto a=tensor_input("A",na);std::vector<float>initial(nc,-97.);TensorBuffer<float>A(a),C(initial);PadMap map;map.total=1;for(int i=0;i<4;++i){map.dim[i]=e.at(cm[i]);map.strideA[i]=as.at(am.find(cm[i]));map.strideC[i]=cs[i];map.left[i]=left[i];map.right[i]=right[i];map.total*=map.dim[i]+left[i]+right[i];}
  padded_permutation<<<(map.total+255)/256,256>>>(A.p,C.p,map);MB_CHECK(hipGetLastError());batch5::snapshot("output",C.get());batch5::config(kind,batch5::modes(am),{},batch5::modes(cm),{},e,1,0,",\"stridesA\":"+batch5::numbers(as)+",\"stridesC\":"+batch5::numbers(cs)+",\"left\":"+batch5::numbers(left)+",\"right\":"+batch5::numbers(right));return 0;
 }
 bool tri=kind=="contraction_trinary";Extents e=tri?(original?Extents{{'m',256},{'a',32},{'b',32},{'n',64},{'r',64},{'k',8},{'i',8},{'j',64}}:Extents{{'m',5},{'a',3},{'b',2},{'n',4},{'r',3},{'k',2},{'i',3},{'j',7}}):(original?Extents{{'m',96},{'n',96},{'u',96},{'v',64},{'h',64},{'k',64}}:Extents{{'m',5},{'n',3},{'u',4},{'v',2},{'h',7},{'k',2}});
 std::string am=tri?"mkajbi":"mhkn",bm=tri?"kni":"ukvh",cm=tri?"rj":"munv",dm=tri?"mnbra":"";float alpha=tri&&c=="small-zero-alpha"?0.f:original?1.1f:-.75f,beta=original?0.f:0.5f;
 auto a=tensor_input("A",elements(am,e));auto b=tensor_input("B",elements(bm,e));auto cv=tensor_input("C",elements(cm,e));TensorBuffer<float>A(a),B(b),C(cv);
 if(tri){auto dv=tensor_input("D",elements(dm,e));TensorBuffer<float>D(dv),mid(elements("majbn",e));
  contract(A.p,am,B.p,bm,mid.p,mid.p,"majbn",e,1,0);for(int repeat=0;repeat<3;++repeat)contract(mid.p,"majbn",C.p,cm,D.p,D.p,dm,e,alpha,beta);batch5::snapshot("output",D.get());
 }else{
  ContractPlan plan(am,bm,cm,e);PreparedContract prepared(A.p,B.p,plan);std::string file=batch2_tensor::output_path("planCache.bin");int block=0;int load=read_cache(file,plan,block);scalar("cache_read_status",load);int candidates=0;
  if(load!=0){float best=1e30;for(int divisor:{1,2,4}){int candidate=(plan.m+divisor-1)/divisor;hipEvent_t start,stop;MB_CHECK(hipEventCreate(&start));MB_CHECK(hipEventCreate(&stop));MB_CHECK(hipEventRecord(start));prepared.execute(C.p,C.p,alpha,beta,candidate);MB_CHECK(hipEventRecord(stop));MB_CHECK(hipEventSynchronize(stop));float ms;MB_CHECK(hipEventElapsedTime(&ms,start,stop));hipEventDestroy(start);hipEventDestroy(stop);if(ms<best){best=ms;block=candidate;}C.put(cv);++candidates;}
   write_cache(file,plan,block);
  }
  scalar("cache_candidate_runs",candidates);scalar("cached_row_block",block);C.put(cv);prepared.execute(C.p,C.p,alpha,beta,block);batch5::snapshot("output",C.get());scalar("cache_write_status",0);
 }
 batch5::config(kind,batch5::modes(am),batch5::modes(bm),batch5::modes(cm),batch5::modes(dm),e,alpha,beta);return 0;
}
}
