// SPDX-License-Identifier: Apache-2.0
#include "sparse_chol.hpp"
extern "C" int rocm_sparse_chol(int n,int nnz,const int* rows,const int* cols,const double* vals,int base,const double* rhs,double* output){try{if(n<=0||nnz<n||!rows||!cols||!vals||!rhs||!output)return 1;std::vector<int>r(rows,rows+n+1),j(cols,cols+nnz);for(auto&v:r)v-=base;for(auto&v:j)v-=base;auto x=migration_sparse::solve(n,r,j,std::vector<double>(vals,vals+nnz),std::vector<double>(rhs,rhs+n));std::copy(x.begin(),x.end(),output);return 0;}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 2;}}
