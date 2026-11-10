// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "sparse_bridge.h"
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
namespace rewrite_sparse_cpp {
inline int run(){
 int r[]={0,2,4,6,7,8},c[]={0,2,1,2,2,4,3,4};double v[]={4,1,3,2,5,1,1,2},b[]={7,12,25,4,13},x[5]={};int rp[5],cp[5],info=0;size_t bytes=0;void*h=nullptr;
 auto check=[](int rc){if(rc)throw std::runtime_error("sparse C ABI status="+std::to_string(rc));};
 try{check(rw_sparse_create(5,8,r,c,v,0,1,1,&h));check(rw_sparse_analyze(h,rp,cp,&bytes));check(rw_sparse_solve(h,1,b,5,x,5,&info));check(rw_sparse_export(h,"b0"));check(rw_sparse_destroy(h));h=nullptr;bool numeric=info==0;for(int i=0;i<5;++i){std::cout<<"x["<<i<<"]="<<x[i]<<" expected="<<i+1<<'\n';numeric=numeric&&std::abs(x[i]-(i+1))<=2e-15;}
  // Preserve the original C++ sample's strict vendor ordering check. The
  // declared min-degree algorithm can solve correctly yet differ from METIS.
  int expected[]={4,3,1,0,2};bool identical=bytes==sizeof(rp);for(int i=0;i<5;++i)identical=identical&&rp[i]==expected[i]&&cp[i]==expected[i];std::cout<<"numeric="<<numeric<<" vendor-permutation-identical="<<identical<<'\n';return numeric&&identical?0:1;
 }catch(const std::exception&e){if(h)rw_sparse_destroy(h);std::cerr<<e.what()<<'\n';return 2;}
}
}
