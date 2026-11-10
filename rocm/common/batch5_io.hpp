// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "batch2_tensor_io.hpp"
#include <map>
namespace batch5 {
inline std::string selected_case(){return std::getenv("MIGRATION_CASE")?std::getenv("MIGRATION_CASE"):"original";}
inline bool replay(){return std::getenv("MIGRATION_CACHE_REPLAY")!=nullptr;}
inline void input(const std::string&name,float*data,size_t n){batch2_tensor::input(name,data,n);if(selected_case()=="changed-values"){for(size_t i=0;i<n;++i)data[i]=data[i]*-.5f+.125f;batch2_tensor::snapshot("input_"+name,data,n);}}
inline std::string output(const char* name){return batch2_tensor::output_path((replay()?"replay_":"")+std::string(name));}
inline void config(const std::string&kind,const std::vector<int>&a,const std::vector<int>&b,const std::vector<int>&c,const std::vector<int>&d,const std::unordered_map<int,int64_t>&e,double alpha,double beta,const std::string&extra=""){
 std::ofstream f(batch2_tensor::output_path("tensor5.json"));f<<std::setprecision(17)<<"{\"kind\":\""<<kind<<"\",\"alpha\":"<<alpha<<",\"beta\":"<<beta;
 auto modes=[&](const char*n,const std::vector<int>&m){f<<",\"mode"<<n<<"\":\"";for(int v:m)f<<char(v);f<<'"';};modes("A",a);modes("B",b);modes("C",c);modes("D",d);f<<",\"extents\":{";bool first=true;for(auto pair:std::map<int,int64_t>(e.begin(),e.end())){if(!first)f<<',';first=false;f<<'"'<<char(pair.first)<<"\":"<<pair.second;}f<<"}"<<extra<<"}\n";
}
template<class T>void snapshot(const std::string&name,const std::vector<T>&v){std::ofstream f(output((name+".bin").c_str()),std::ios::binary);f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T));if(!f)throw std::runtime_error("snapshot failed");}
inline std::vector<int> modes(const std::string&s){return {s.begin(),s.end()};}
inline std::string numbers(const std::vector<int64_t>&v){std::string s="[";for(size_t i=0;i<v.size();++i){if(i)s+=',';s+=std::to_string(v[i]);}return s+"]";}
}
