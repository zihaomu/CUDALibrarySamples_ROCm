// SPDX-License-Identifier: Apache-2.0
#include "check.hpp"
#include <hiptensor/hiptensor.h>
using namespace sample;
int main(){return run([]{
 hiptensorHandle_t handle;CHECK(hiptensorCreate(&handle));
 for(int64_t n:{int64_t(16),int64_t(32)}){
  std::vector<float>a(n*n),b(n*n),c(n*n),ref(n*n);for(size_t i=0;i<a.size();++i){a[i]=int(i%11)-5;b[i]=int(i%7)-3;c[i]=int(i%5)-2;}
  for(int j=0;j<n;++j)for(int i=0;i<n;++i){float sum=0;for(int k=0;k<n;++k)sum+=a[i+n*k]*b[k+n*j];ref[i+n*j]=1.5f*sum+.25f*c[i+n*j];}
  Device<float>A(a),B(b),C(c);int64_t lengths[2]={n,n};int32_t ma[2]={'m','k'},mb[2]={'k','n'},mc[2]={'m','n'};hiptensorTensorDescriptor_t da,db,dc;CHECK(hiptensorCreateTensorDescriptor(handle,&da,2,lengths,nullptr,HIPTENSOR_R_32F,16));CHECK(hiptensorCreateTensorDescriptor(handle,&db,2,lengths,nullptr,HIPTENSOR_R_32F,16));CHECK(hiptensorCreateTensorDescriptor(handle,&dc,2,lengths,nullptr,HIPTENSOR_R_32F,16));hiptensorOperationDescriptor_t op;CHECK(hiptensorCreateContraction(handle,&op,da,ma,HIPTENSOR_OP_IDENTITY,db,mb,HIPTENSOR_OP_IDENTITY,dc,mc,HIPTENSOR_OP_IDENTITY,dc,mc,HIPTENSOR_COMPUTE_DESC_32F));hiptensorPlanPreference_t pref;CHECK(hiptensorCreatePlanPreference(handle,&pref,HIPTENSOR_ALGO_DEFAULT,HIPTENSOR_JIT_MODE_NONE));uint64_t bytes=0;CHECK(hiptensorEstimateWorkspaceSize(handle,op,pref,HIPTENSOR_WORKSPACE_DEFAULT,&bytes));Device<unsigned char>workspace(bytes);hiptensorPlan_t plan;CHECK(hiptensorCreatePlan(handle,&plan,op,pref,bytes));float alpha=1.5f,beta=.25f;CHECK(hiptensorContract(handle,plan,&alpha,A.p,B.p,&beta,C.p,C.p,workspace.p,bytes,0));CHECK(hipDeviceSynchronize());report("hiptensor-contraction-"+std::to_string(n),C.get(),ref,1e-4,1e-5);CHECK(hiptensorDestroyPlan(plan));CHECK(hiptensorDestroyPlanPreference(pref));CHECK(hiptensorDestroyOperationDescriptor(op));CHECK(hiptensorDestroyTensorDescriptor(da));CHECK(hiptensorDestroyTensorDescriptor(db));CHECK(hiptensorDestroyTensorDescriptor(dc));
 }CHECK(hiptensorDestroy(handle));
});}
