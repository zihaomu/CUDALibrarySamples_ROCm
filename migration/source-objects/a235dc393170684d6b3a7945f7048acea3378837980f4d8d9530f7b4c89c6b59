// SPDX-License-Identifier: Apache-2.0
#include "rewrite_runtime.hpp"
#include <cusolverDn.h>
using namespace rewrite;
__global__ void extract_svd(const float*s,const float*u,const float*vt,float*so,float*uo,float*vo,int m,int n,int rank,int ldu,int ldv){int t=blockIdx.x*blockDim.x+threadIdx.x;if(t<rank)so[t]=s[t];if(t<m*rank)uo[t%m+(t/m)*ldu]=u[t];if(t<n*rank)vo[t%n+(t/n)*ldv]=vt[t/n+(t%n)*n];}
__global__ void residual_svd(const float*a,const float*s,const float*u,const float*v,double*out,int m,int n,int rank,int lda,int ldu,int ldv){if(threadIdx.x||blockIdx.x)return;double total=0;for(int j=0;j<n;++j)for(int i=0;i<m;++i){double value=a[i+j*lda];for(int k=0;k<rank;++k)value-=double(u[i+k*ldu])*s[k]*v[j+k*ldv];total+=value*value;}*out=sqrt(total);}
int main(int argc,char**argv){try{Config c;identity();std::string kind=argc>1?argv[1]:"svd";bool approximate=kind=="svd-native";int m=c.get("m"),n=c.get("n"),rank=c.get("rank"),batch=c.get("batch"),lda=c.get("lda"),ldu=c.get("ldu"),ldv=c.get("ldv"),sa=c.get("strideA"),ss=c.get("strideS"),su=c.get("strideU"),sv=c.get("strideV"),repeat=c.get("repeat",1);auto av=read<float>("A",batch*sa);Buffer<float>a(av),copy(av),s(n),u(m*n),vt(n*n),so(std::vector<float>(batch*ss,-97)),uo(std::vector<float>(batch*su,-97)),vo(std::vector<float>(batch*sv,-97));Buffer<int>info(batch);Buffer<double>norm(batch);cusolverDnHandle_t h;RW_CHECK(cusolverDnCreate(&h));int lwork=0;std::vector<double>native_norm(batch);
 if(approximate)RW_CHECK(cusolverDnSgesvdaStridedBatched_bufferSize(h,CUSOLVER_EIG_MODE_VECTOR,rank,m,n,a.p,lda,sa,so.p,ss,uo.p,ldu,su,vo.p,ldv,sv,&lwork,batch));
 else RW_CHECK(cusolverDnSgesvd_bufferSize(h,m,n,&lwork));Buffer<float>work(lwork),rwork(std::max(1,n-1));
 for(int rep=0;rep<repeat;++rep){copy.put(av);if(approximate){RW_CHECK(cusolverDnSgesvdaStridedBatched(h,CUSOLVER_EIG_MODE_VECTOR,rank,m,n,copy.p,lda,sa,so.p,ss,uo.p,ldu,su,vo.p,ldv,sv,work.p,lwork,info.p,native_norm.data(),batch));sync();}
 else for(int b=0;b<batch;++b){RW_CHECK(cusolverDnSgesvd(h,'S','A',m,n,copy.p+b*sa,lda,s.p,u.p,m,vt.p,n,work.p,lwork,rwork.p,info.p+b));extract_svd<<<(std::max(m,n)*rank+255)/256,256>>>(s.p,u.p,vt.p,so.p+b*ss,uo.p+b*su,vo.p+b*sv,m,n,rank,ldu,ldv);sync();}
 for(int b=0;b<batch;++b){residual_svd<<<1,1>>>(a.p+b*sa,so.p+b*ss,uo.p+b*su,vo.p+b*sv,norm.p+b,m,n,rank,lda,ldu,ldv);sync();}}
 RW_CHECK(cusolverDnDestroy(h));emit("S",so.get());emit("U",uo.get());emit("V",vo.get());emit("info",info.get());emit("A_after",a.get());emit("RnrmF",norm.get());if(approximate)emit("RnrmF_native",native_norm);return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
