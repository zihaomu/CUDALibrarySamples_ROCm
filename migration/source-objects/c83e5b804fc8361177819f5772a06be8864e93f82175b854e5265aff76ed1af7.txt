// SPDX-License-Identifier: Apache-2.0
// Original cuDSS simple SPD input; CPU sparse symbolic graph + GPU CSRRF numeric work.
#include "../common/sparse_chol.hpp"
using namespace sample;
int main(){return run([]{const std::vector<int>row={0,2,4,6,7,8},col={0,2,1,2,2,4,3,4};const std::vector<double>values={4,1,3,2,5,1,1,2},rhs={7,12,25,4,13};for(double scale:{1.,2.}){auto a=values;for(auto&z:a)z*=scale;auto x=migration_sparse::solve(5,row,col,a,rhs);std::vector<double>ref={1/scale,2/scale,3/scale,4/scale,5/scale};report("original-spd-sparse-solve-scale"+std::to_string(scale),x,ref,2e-15,0);std::vector<double>ax(5);for(int i=0;i<5;++i)for(int q=row[i];q<row[i+1];++q){int j=col[q];ax[i]+=a[q]*x[j];if(i!=j)ax[j]+=a[q]*x[i];}report("original-spd-sparse-residual-scale"+std::to_string(scale),ax,rhs,1e-11,0);}});}
