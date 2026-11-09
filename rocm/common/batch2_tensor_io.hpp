// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <string>
#include <stdexcept>
#include <vector>
#include <unordered_map>
#include <cstdint>
namespace batch2_tensor {
inline std::string output_path(const std::string& n){const char* p=std::getenv("MIGRATION_OUTPUT_DIR");if(!p)throw std::runtime_error("MIGRATION_OUTPUT_DIR required");return std::string(p)+"/"+n;}
template<class T>void snapshot(const std::string& name,T* data,size_t n){std::ofstream f(output_path(name+".bin"),std::ios::binary);f.write(reinterpret_cast<const char*>(data),n*sizeof(T));if(!f)throw std::runtime_error("Tensor output write failed");}
template<class T>void input(const std::string& name,T* data,size_t n){
 if(const char* seed=std::getenv("MIGRATION_FIXTURE_SEED")){
  uint32_t base=uint32_t(std::strtoul(seed,nullptr,10))+uint32_t(name[0])*0x9e3779b9u;
  for(size_t i=0;i<n;++i){uint32_t x=uint32_t(i)+base;x^=x>>16;x*=0x7feb352du;x^=x>>15;x*=0x846ca68bu;x^=x>>16;data[i]=T(x>>8)*T(1.0/16777216.0);}
 }
 if(const char* p=std::getenv("MIGRATION_INPUT_FIXTURE_DIR")){std::ifstream f(std::string(p)+"/input_"+name+".bin",std::ios::binary);f.read(reinterpret_cast<char*>(data),n*sizeof(T));if(!f||f.peek()!=std::ifstream::traits_type::eof())throw std::runtime_error("Tensor fixture size/read mismatch");}
 snapshot("input_"+name,data,n);
}
template<class I>void config(const std::vector<I>& a,const std::vector<I>& b,const std::vector<I>& c,const std::unordered_map<I,int64_t>& extent,double alpha,double beta,double gamma){
 std::ofstream f(output_path("tensor.json"));f<<std::setprecision(17)<<"{\"alpha\":"<<alpha<<",\"beta\":"<<beta<<",\"gamma\":"<<gamma;
 auto modes=[&](const char* label,const std::vector<I>& v){f<<",\""<<label<<"\":\"";for(auto x:v)f<<char(x);f<<"\"";};modes("modeA",a);modes("modeB",b);modes("modeC",c);
 f<<",\"fixture_seed\":"<<(std::getenv("MIGRATION_FIXTURE_SEED")?std::getenv("MIGRATION_FIXTURE_SEED"):"null")<<",\"extents\":{";bool first=true;for(auto p:extent){if(!first)f<<',';first=false;f<<'"'<<char(p.first)<<"\":"<<p.second;}f<<"}}\n";
}
}
