// SPDX-License-Identifier: Apache-2.0
#include "sparse24.hpp"
int main(){using namespace rewrite_sparse24;Shape s{};s.m=4;s.k=4;s.batch=1;int cases=0;for(auto input:std::vector<std::vector<uint8_t>>{{4,4,14,14},{0,4,14,14},{4,4,4,4},{20,4,14,14}}){Buffer<uint8_t>metadata(input);Buffer<int>status(std::vector<int>{0});check24<<<1,32>>>(s,metadata.p,status.p);sync();int observed=status.get()[0],expected=cases++==0?0:1;std::cout<<"GPU metadata check "<<cases<<" observed="<<observed<<" expected="<<expected<<'\n';if(observed!=expected)return 1;}return cases==4?0:1;}
