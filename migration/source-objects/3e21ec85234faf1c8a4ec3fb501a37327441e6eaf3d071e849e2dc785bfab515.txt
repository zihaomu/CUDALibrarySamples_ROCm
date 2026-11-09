// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "check.hpp"
#include <rocsolver/rocsolver.h>
#include <map>
#include <set>
namespace migration_sparse {
// Host symbolic graph elimination; all numerical factorization/solve stays sparse on GPU.
inline std::vector<double> solve(int n,const std::vector<int>& r,const std::vector<int>& j,const std::vector<double>& v,const std::vector<double>& rhs){
 using namespace sample;std::vector<std::map<int,double>> rows(n);std::vector<std::set<int>> graph(n),lcols(n);
 for(int i=0;i<n;++i)for(int q=r[i];q<r[i+1];++q){int k=j[q];rows[i][k]=v[q];rows[k][i]=v[q];if(i!=k){graph[i].insert(k);graph[k].insert(i);}}
 for(int k=0;k<n;++k){lcols[k].insert(k);std::vector<int> higher;for(int i:graph[k])if(i>k){higher.push_back(i);lcols[i].insert(k);}for(int i:higher)for(int j:higher)if(i!=j)graph[i].insert(j);}
 std::vector<int>rp{0},ci,lr{0},lc,perm(n);std::vector<double>av,initial;
 for(int i=0;i<n;++i){perm[i]=i;for(auto [j,x]:rows[i]){ci.push_back(j);av.push_back(x);}rp.push_back(ci.size());for(int j:lcols[i]){lc.push_back(j);initial.push_back(i==j?1:0);}lr.push_back(lc.size());}
 Device<int>R(rp),J(ci),LR(lr),LC(lc),P(perm);std::vector<double> identity_values(av.size());for(int i=0;i<n;++i)for(int q=rp[i];q<rp[i+1];++q)if(ci[q]==i)identity_values[q]=1;
 Device<double>A(identity_values),L(initial),B(rhs);rocblas_handle handle;CHECK(rocblas_create_handle(&handle));rocsolver_rfinfo info;CHECK(rocsolver_create_rfinfo(&info,handle));CHECK(rocsolver_set_rfinfo_mode(info,rocsolver_rfinfo_mode_cholesky));CHECK(rocsolver_dcsrrf_analysis(handle,n,1,av.size(),R.p,J.p,A.p,initial.size(),LR.p,LC.p,L.p,P.p,P.p,B.p,n,info));// The prior matrix M0=I and its L0=I have the same stored pattern.
 CHECK(hipDeviceSynchronize());CHECK(hipMemcpy(A.p,av.data(),av.size()*sizeof(double),hipMemcpyHostToDevice));
 CHECK(rocsolver_dcsrrf_refactchol(handle,n,av.size(),R.p,J.p,A.p,initial.size(),LR.p,LC.p,L.p,P.p,info));CHECK(rocsolver_dcsrrf_solve(handle,n,1,initial.size(),LR.p,LC.p,L.p,P.p,P.p,B.p,n,info));CHECK(hipDeviceSynchronize());auto x=B.get();CHECK(rocsolver_destroy_rfinfo(info));CHECK(rocblas_destroy_handle(handle));return x;
}
}
