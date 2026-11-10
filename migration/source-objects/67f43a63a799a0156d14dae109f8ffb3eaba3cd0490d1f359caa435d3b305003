// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batches_runtime.hpp"
#include <memory>
#include <limits>
#ifdef __HIP_PLATFORM_AMD__
#include <hipblaslt/hipblaslt.h>
#include <hip/hip_fp16.h>
#define T7_LT(x) hipblasLt##x
#define T7_ATTR(x) HIPBLASLT_##x
#define T7_F32 HIP_R_32F
#define T7_F16 HIP_R_16F
#define T7_COMPUTE HIPBLAS_COMPUTE_32F
#else
#include <cublasLt.h>
#include <cuda_fp16.h>
#define T7_LT(x) cublasLt##x
#define T7_ATTR(x) CUBLASLT_##x
#define T7_F32 CUDA_R_32F
#define T7_F16 CUDA_R_16F
#define T7_COMPUTE CUBLAS_COMPUTE_32F
#endif
namespace migration_batch {
template<class T>void bin7(const std::string&name,const std::vector<T>&v){migration_binary::emit((name+".bin").c_str(),v.data(),v.size()*sizeof(T));}
template<class T>std::vector<T> fixture7(size_t n,int offset){std::vector<T>v(n);for(size_t i=0;i<n;++i)v[i]=T(float(int((i*13+offset)%29)-14)/32);return v;}
inline void grouped_float7(){
 Blas h;auto cas=selected_case();int count=3;bool heterogeneous=cas=="heterogeneous-groups";int groups=heterogeneous?3:2;std::vector<int>sizes=heterogeneous?std::vector<int>{1,1,1}:std::vector<int>{2,1};std::vector<int>dims=heterogeneous?std::vector<int>{3,4,5}:std::vector<int>{2,3};std::vector<MB_BLAS(Operation_t)>ta(groups,MB_CONST(OP_N)),tb(groups,MB_CONST(OP_N));if(heterogeneous)ta[1]=MB_CONST(OP_T);std::vector<float>alpha(groups,cas=="negative-alpha"?-.75f:1.f),beta(groups,heterogeneous?.5f:0.f);
 std::vector<std::unique_ptr<Buffer<float>>>aa,bb,cc;std::vector<float*>ap,bp,cp;scalar("input_count",count);emit("input_group_sizes",sizes);
 for(int i=0;i<count;++i){int group=heterogeneous?i:i==2?1:0,n=dims[group];std::vector<float>A,B,C(n*n,0);
  if(n==2){A=i==1?std::vector<float>{5,7,6,8}:std::vector<float>{1,3,2,4};B=i==1?std::vector<float>{9,11,10,12}:std::vector<float>{5,7,6,8};}else if(n==3){A={1,4,7,2,5,8,3,6,9};B={4,7,10,5,8,11,6,9,12};}else{A=fixture7<float>(n*n,11);B=fixture7<float>(n*n,21);}if(heterogeneous)C=fixture7<float>(n*n,7);
  std::string p="g"+std::to_string(i);scalar(("input_n_"+p).c_str(),n);scalar(("input_trans_"+p).c_str(),int(ta[group]==MB_CONST(OP_T)));scalar(("input_alpha_"+p).c_str(),alpha[group]);scalar(("input_beta_"+p).c_str(),beta[group]);emit(("input_A_"+p).c_str(),A);emit(("input_B_"+p).c_str(),B);emit(("input_C_"+p).c_str(),C);aa.emplace_back(new Buffer<float>(A));bb.emplace_back(new Buffer<float>(B));cc.emplace_back(new Buffer<float>(C));ap.push_back(aa.back()->p);bp.push_back(bb.back()->p);cp.push_back(cc.back()->p);
 }
 Buffer<float*>da(ap),db(bp),dc(cp);
#ifdef __HIP_PLATFORM_AMD__
 int first=0;for(int group=0;group<groups;++group){int n=dims[group];MB_CHECK(hipblasSgemmBatched(h.h,ta[group],tb[group],n,n,n,&alpha[group],(const float*const*)da.p+first,n,(const float*const*)db.p+first,n,&beta[group],dc.p+first,n,sizes[group]));first+=sizes[group];}
#else
 MB_CHECK(cublasGemmGroupedBatchedEx(h.h,ta.data(),tb.data(),dims.data(),dims.data(),dims.data(),alpha.data(),(const void*const*)da.p,CUDA_R_32F,dims.data(),(const void*const*)db.p,CUDA_R_32F,dims.data(),beta.data(),(void*const*)dc.p,CUDA_R_32F,dims.data(),groups,sizes.data(),CUBLAS_COMPUTE_32F));
#endif
 for(int i=0;i<count;++i){std::string p="g"+std::to_string(i);emit(("candidate_"+p+"_0").c_str(),cc[i]->get());emit(("output_"+p).c_str(),cc[i]->get());scalar(("candidates_"+p).c_str(),1);scalar(("selected_"+p).c_str(),0);scalar(("workspace_"+p).c_str(),0);}
}
inline void double7(bool grouped){Blas b;auto c=selected_case();int count=grouped?3:1;scalar("input_count",count);
 for(int g=0;g<count;++g){int n=grouped&&g==2?3:2;if(c=="heterogeneous-groups")n+=g+1;bool tr=c=="heterogeneous-groups"&&g==1;double alpha=c=="negative-alpha"?-.75:1,beta=c=="heterogeneous-groups"?.5:0;std::vector<double>A,B,C(n*n,0);
  if(n==2){A=g==1?std::vector<double>{5,7,6,8}:std::vector<double>{1,3,2,4};B=g==1?std::vector<double>{9,11,10,12}:std::vector<double>{5,7,6,8};}else if(n==3){A={1,4,7,2,5,8,3,6,9};B={4,7,10,5,8,11,6,9,12};}else{A=fixture7<double>(n*n,11);B=fixture7<double>(n*n,21);}if(c=="changed-values"){for(auto&x:A)x=-.5*x+.125;beta=.25;C=fixture7<double>(n*n,7);}
  std::string pre="g"+std::to_string(g);scalar(("input_n_"+pre).c_str(),n);scalar(("input_trans_"+pre).c_str(),int(tr));scalar(("input_alpha_"+pre).c_str(),alpha);scalar(("input_beta_"+pre).c_str(),beta);emit(("input_A_"+pre).c_str(),A);emit(("input_B_"+pre).c_str(),B);emit(("input_C_"+pre).c_str(),C);Buffer<double>a(A),bb(B),cc(C);
  // Project autotuning candidates are real row-dispatch policies, not vendor algorithm IDs.
  int best=0;float bestms=std::numeric_limits<float>::max();int policies=grouped?1:2;
  for(int policy=0;policy<policies;++policy){cc.put(C);MB_RT(Event_t)start,stop;MB_CHECK(MB_RT(EventCreate)(&start));MB_CHECK(MB_RT(EventCreate)(&stop));MB_CHECK(MB_RT(EventRecord)(start));
   if(policy==0||tr){MB_CHECK(MB_BLAS(Dgemm)(b.h,tr?MB_CONST(OP_T):MB_CONST(OP_N),MB_CONST(OP_N),n,n,n,&alpha,a.p,n,bb.p,n,&beta,cc.p,n));}
   else for(int row=0;row<n;++row)MB_CHECK(MB_BLAS(Dgemm)(b.h,MB_CONST(OP_N),MB_CONST(OP_N),1,n,n,&alpha,a.p+row,n,bb.p,n,&beta,cc.p+row,n));
   MB_CHECK(MB_RT(EventRecord)(stop));MB_CHECK(MB_RT(EventSynchronize)(stop));float ms=0;MB_CHECK(MB_RT(EventElapsedTime)(&ms,start,stop));MB_RT(EventDestroy)(start);MB_RT(EventDestroy)(stop);if(ms<bestms){bestms=ms;best=policy;}emit(("candidate_"+pre+"_"+std::to_string(policy)).c_str(),cc.get());
  }
  cc.put(C);if(best==0||tr)MB_CHECK(MB_BLAS(Dgemm)(b.h,tr?MB_CONST(OP_T):MB_CONST(OP_N),MB_CONST(OP_N),n,n,n,&alpha,a.p,n,bb.p,n,&beta,cc.p,n));else for(int row=0;row<n;++row)MB_CHECK(MB_BLAS(Dgemm)(b.h,MB_CONST(OP_N),MB_CONST(OP_N),1,n,n,&alpha,a.p+row,n,bb.p,n,&beta,cc.p+row,n));emit(("output_"+pre).c_str(),cc.get());scalar(("candidates_"+pre).c_str(),policies);scalar(("selected_"+pre).c_str(),best);scalar(("workspace_"+pre).c_str(),0);
 }
}
template<class T>void lt7(int group,int m,int n,int k,float alpha,float beta,bool bias,size_t budget){
 auto c=selected_case();std::string pre="g"+std::to_string(group);auto A=fixture7<T>(size_t(m)*k,c=="changed-values"?23:3),B=fixture7<T>(size_t(k)*n,5),C=fixture7<T>(size_t(m)*n,7),Bias=fixture7<T>(m,9);Buffer<T>a(A),b(B),cc(C),d(C),bd(Bias);bin7("input_A_"+pre,A);bin7("input_B_"+pre,B);bin7("input_C_"+pre,C);bin7("input_bias_"+pre,Bias);
 scalar(("input_m_"+pre).c_str(),m);scalar(("input_n_"+pre).c_str(),n);scalar(("input_k_"+pre).c_str(),k);scalar(("input_alpha_"+pre).c_str(),alpha);scalar(("input_beta_"+pre).c_str(),beta);scalar(("input_bias_enabled_"+pre).c_str(),int(bias));scalar(("input_half_"+pre).c_str(),int(sizeof(T)==2));scalar(("input_workspace_limit_"+pre).c_str(),budget);
 if(m==0||n==0){bin7("output_"+pre,std::vector<T>{});scalar(("candidates_"+pre).c_str(),0);scalar(("selected_"+pre).c_str(),-1);scalar(("workspace_"+pre).c_str(),0);return;}
 T7_LT(Handle_t)h;T7_LT(MatmulDesc_t)op;T7_LT(MatrixLayout_t)ad,bdesc,cd;T7_LT(MatmulPreference_t)pref;
 MB_CHECK(T7_LT(Create)(&h));MB_CHECK(T7_LT(MatmulDescCreate)(&op,T7_COMPUTE,T7_F32));auto type=sizeof(T)==2?T7_F16:T7_F32;
 MB_CHECK(T7_LT(MatrixLayoutCreate)(&ad,type,m,k,m));MB_CHECK(T7_LT(MatrixLayoutCreate)(&bdesc,type,k,n,k));MB_CHECK(T7_LT(MatrixLayoutCreate)(&cd,type,m,n,m));
 if(bias){auto ep=T7_ATTR(EPILOGUE_BIAS);void*ptr=bd.p;MB_CHECK(T7_LT(MatmulDescSetAttribute)(op,T7_ATTR(MATMUL_DESC_EPILOGUE),&ep,sizeof(ep)));MB_CHECK(T7_LT(MatmulDescSetAttribute)(op,T7_ATTR(MATMUL_DESC_BIAS_POINTER),&ptr,sizeof(ptr)));}
 MB_CHECK(T7_LT(MatmulPreferenceCreate)(&pref));MB_CHECK(T7_LT(MatmulPreferenceSetAttribute)(pref,T7_ATTR(MATMUL_PREF_MAX_WORKSPACE_BYTES),&budget,sizeof(budget)));Buffer<unsigned char>work(budget);
 T7_LT(MatmulHeuristicResult_t)algorithms[8];int found=0;MB_CHECK(T7_LT(MatmulAlgoGetHeuristic)(h,op,ad,bdesc,cd,cd,pref,8,algorithms,&found));if(std::getenv("MIGRATION_NO_CANDIDATES"))found=0;if(!found)throw std::runtime_error("no algorithms satisfy dtype/layout/workspace");
 int best=-1,executed=0;float bestms=std::numeric_limits<float>::max();
 for(int i=0;i<found;++i){if(algorithms[i].state!=0||algorithms[i].workspaceSize>budget)continue;d.put(C);MB_RT(Event_t)start,stop;MB_CHECK(MB_RT(EventCreate)(&start));MB_CHECK(MB_RT(EventCreate)(&stop));MB_CHECK(MB_RT(EventRecord)(start));auto rc=T7_LT(Matmul)(h,op,&alpha,a.p,ad,b.p,bdesc,&beta,cc.p,cd,d.p,cd,&algorithms[i].algo,work.p,budget,0);if(rc){MB_RT(EventDestroy)(start);MB_RT(EventDestroy)(stop);continue;}MB_CHECK(MB_RT(EventRecord)(stop));MB_CHECK(MB_RT(EventSynchronize)(stop));float ms;MB_CHECK(MB_RT(EventElapsedTime)(&ms,start,stop));MB_RT(EventDestroy)(start);MB_RT(EventDestroy)(stop);if(ms<bestms){bestms=ms;best=i;}bin7("candidate_"+pre+"_"+std::to_string(executed),d.get());scalar(("candidate_workspace_"+pre+"_"+std::to_string(executed)).c_str(),algorithms[i].workspaceSize);++executed;}
 if(best<0)throw std::runtime_error("all candidate executions failed");d.put(C);MB_CHECK(T7_LT(Matmul)(h,op,&alpha,a.p,ad,b.p,bdesc,&beta,cc.p,cd,d.p,cd,&algorithms[best].algo,work.p,budget,0));bin7("output_"+pre,d.get());scalar(("candidates_"+pre).c_str(),executed);scalar(("selected_"+pre).c_str(),best);scalar(("workspace_"+pre).c_str(),algorithms[best].workspaceSize);
 T7_LT(MatmulPreferenceDestroy)(pref);T7_LT(MatrixLayoutDestroy)(ad);T7_LT(MatrixLayoutDestroy)(bdesc);T7_LT(MatrixLayoutDestroy)(cd);T7_LT(MatmulDescDestroy)(op);T7_LT(Destroy)(h);
}
inline int gemm7_main(const std::string&kind){try{auto c=selected_case();if(kind=="GemmGroupedBatchedEx"||kind=="GemmExAutoTuning"){if(kind=="GemmGroupedBatchedEx")grouped_float7();else double7(false);return 0;}
 bool grouped=kind=="LtHSHgemmGroupedSimple";int count=grouped?2:1;scalar("input_count",count);
 if(grouped){std::srand(42);int ms[2],ns[2],ks[2];for(int i=0;i<2;++i){ms[i]=(std::rand()%9)*8;ns[i]=(std::rand()%13)*8;ks[i]=(std::rand()%17)*8;}for(int i=0;i<2;++i){int m=ms[i],n=ns[i],k=ks[i];if(c=="heterogeneous-groups"){m=24+16*i;n=16+24*i;k=32+8*i;}lt7<__half>(i,m,n,k,c=="negative-alpha"?-.75f:2.f,c=="heterogeneous-groups"?.5f:0.f,true,8*1024*1024);}}
 else{int m=1024,n=kind=="LtSgemmCustomFind"?512:1024,k=kind=="LtSgemmCustomFind"?4096:1024;size_t bytes=c=="limited-workspace"?0:kind=="LtSgemmCustomFind"?16*1024*1024:4*1024*1024;lt7<float>(0,m,n,k,2,c=="changed-values"?.5f:0.f,false,bytes);}MB_CHECK(MB_RT(DeviceSynchronize)());return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
}
