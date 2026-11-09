// SPDX-License-Identifier: Apache-2.0
// Native rocSPARSE v2 route selected after the hipSPARSE route failed in this environment.
#include "check.hpp"
#include <rocsparse/rocsparse.h>
using namespace sample;
int main(){return run([]{
 rocsparse_handle h;CHECK(rocsparse_create_handle(&h));Stream stream;CHECK(rocsparse_set_stream(h,stream.p));
 for(int base:{0,1}){
  int n=4;std::vector<int> rp={0,3,4,7,9},ci={0,2,3,1,0,2,3,1,3};std::vector<float> av={1,2,3,4,5,6,7,8,9};
  for(auto& v:rp)v+=base;for(auto& v:ci)v+=base;
  Device<int> dr(rp),di(ci);Device<float> da(av);rocsparse_spmat_descr a;
  CHECK(rocsparse_create_csr_descr(&a,n,n,av.size(),dr.p,di.p,da.p,rocsparse_indextype_i32,rocsparse_indextype_i32,base?rocsparse_index_base_one:rocsparse_index_base_zero,rocsparse_datatype_f32_r));
  for(float beta:{0.f,0.5f}){
   auto x=input<float>(n,128),y=input<float>(n,256),ref=y;float alpha=1.25f;
   for(int i=0;i<n;i++){float sum=0;for(int q=rp[i]-base;q<rp[i+1]-base;q++)sum+=av[q]*x[ci[q]-base];ref[i]=alpha*sum+beta*y[i];}
   Device<float> dx(x),dy(y);rocsparse_dnvec_descr xd,yd;CHECK(rocsparse_create_dnvec_descr(&xd,n,dx.p,rocsparse_datatype_f32_r));CHECK(rocsparse_create_dnvec_descr(&yd,n,dy.p,rocsparse_datatype_f32_r));
   rocsparse_spmv_descr desc;CHECK(rocsparse_create_spmv_descr(&desc));
   auto dtype=rocsparse_datatype_f32_r;auto op=rocsparse_operation_none;auto alg=rocsparse_spmv_alg_csr_adaptive;
   CHECK(rocsparse_spmv_set_input(h,desc,rocsparse_spmv_input_scalar_datatype,&dtype,sizeof(dtype),nullptr));
   CHECK(rocsparse_spmv_set_input(h,desc,rocsparse_spmv_input_compute_datatype,&dtype,sizeof(dtype),nullptr));
   CHECK(rocsparse_spmv_set_input(h,desc,rocsparse_spmv_input_operation,&op,sizeof(op),nullptr));
   CHECK(rocsparse_spmv_set_input(h,desc,rocsparse_spmv_input_alg,&alg,sizeof(alg),nullptr));
   size_t analysis_size=0,compute_size=0;
   CHECK(rocsparse_v2_spmv_buffer_size(h,desc,a,xd,yd,rocsparse_v2_spmv_stage_analysis,&analysis_size,nullptr));
   std::cerr<<"analysis_size="<<analysis_size<<std::endl;Device<unsigned char> analysis(analysis_size);
   CHECK(rocsparse_v2_spmv(h,desc,&alpha,a,xd,&beta,yd,rocsparse_v2_spmv_stage_analysis,analysis_size,analysis_size?analysis.p:nullptr,nullptr));
   CHECK(rocsparse_v2_spmv_buffer_size(h,desc,a,xd,yd,rocsparse_v2_spmv_stage_compute,&compute_size,nullptr));
   Device<unsigned char> compute(compute_size);
   CHECK(rocsparse_v2_spmv(h,desc,&alpha,a,xd,&beta,yd,rocsparse_v2_spmv_stage_compute,compute_size,compute_size?compute.p:nullptr,nullptr));
   CHECK(hipStreamSynchronize(stream.p));report("base"+std::to_string(base)+"_beta"+std::to_string(beta),dy.get(),ref,1e-6,1e-5);
   CHECK(rocsparse_destroy_spmv_descr(desc));CHECK(rocsparse_destroy_dnvec_descr(xd));CHECK(rocsparse_destroy_dnvec_descr(yd));
  }
  CHECK(rocsparse_destroy_spmat_descr(a));
 }
 CHECK(rocsparse_destroy_handle(h));
});}
