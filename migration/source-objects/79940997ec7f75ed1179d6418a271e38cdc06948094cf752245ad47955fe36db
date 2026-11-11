// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <fstream>
#include <vector>
#include <string>
#include <cstdlib>
#include <stdexcept>
#include <limits>
#include <cstdint>
#ifdef RW_BENCH_NATIVE
#include <cuda_runtime.h>
#define CB_GPU(n) cuda##n
#else
#include <hip/hip_runtime.h>
#define CB_GPU(n) hip##n
#endif
inline std::string cb_root(){const char*p=std::getenv("REWRITE_OUTPUT");return p?p:"";}
inline void cb_check(int rc){if(rc)throw std::runtime_error("benchmark observation runtime status "+std::to_string(rc));}
inline void cb_input(void*device,size_t size){
 if(const char*name=std::getenv("REWRITE_BENCH_INPUT")){std::ifstream input(name,std::ios::binary);std::vector<unsigned char>part(std::min(size,size_t(1<<20)));size_t offset=0;while(offset<size){size_t n=std::min(part.size(),size-offset);input.read((char*)part.data(),n);if(!input)throw std::runtime_error("short frozen benchmark input");cb_check(CB_GPU(Memcpy)((char*)device+offset,part.data(),n,CB_GPU(MemcpyHostToDevice)));offset+=n;}if(input.peek()!=EOF)throw std::runtime_error("long frozen benchmark input");}
 if(cb_root().empty())return;std::ofstream file(cb_root()+"/input.bin",std::ios::binary);std::vector<unsigned char>part(std::min(size,size_t(1<<20)));for(size_t off=0;off<size;off+=part.size()){size_t n=std::min(part.size(),size-off);cb_check(CB_GPU(Memcpy)(part.data(),(char*)device+off,n,CB_GPU(MemcpyDeviceToHost)));file.write((char*)part.data(),n);}if(!file)throw std::runtime_error("cannot save benchmark input");
}
inline void cb_values(size_t size,size_t count,const uint32_t*values,const std::string&suffix){if(cb_root().empty())return;std::vector<uint32_t>host(count);cb_check(CB_GPU(Memcpy)(host.data(),values,count*4,CB_GPU(MemcpyDeviceToHost)));std::ofstream file(cb_root()+"/cell_"+std::to_string(size)+"_"+std::to_string(count)+"_"+suffix+".bin",std::ios::binary);file.write((char*)host.data(),count*4);if(!file)throw std::runtime_error("cannot save CRC values");}
template<class Conf>inline void cb_cell_base(size_t size,size_t count,const uint32_t*values,float ms,const Conf&conf){cb_values(size,count,values,"final");if(cb_root().empty())return;std::string base=cb_root()+"/cell_"+std::to_string(size)+"_"+std::to_string(count);std::ofstream timing(base+"_timing.json");timing.precision(17);timing<<"{\"size\":"<<size<<",\"count\":"<<count<<",\"elapsed_ms\":"<<ms<<",\"configuration_bytes\":"<<sizeof(conf)<<"}\n";}
template<class Conf>inline void cb_cell(size_t size,size_t count,const uint32_t*values,float ms,const Conf&conf){cb_cell_base(size,count,values,ms,conf);}
inline void cb_memory(size_t total,size_t free){if(cb_root().empty())return;std::ofstream f(cb_root()+"/memory.json");f<<"{\"total\":"<<total<<",\"free\":"<<free<<"}\n";}
template<class Args,class Table>inline void cb_config(const Args&a,const Table&t){if(cb_root().empty())return;std::ofstream f(cb_root()+"/grid.json");f<<"{\"storage\":"<<a.storage_size<<",\"min_size\":"<<a.min_buf_size<<",\"max_size\":"<<a.max_buf_size<<",\"min_count\":"<<a.min_buf_count<<",\"max_count\":"<<a.max_buf_count<<",\"step_shift\":"<<a.step_shift<<",\"sizes\":[";for(size_t i=0;i<t.buf_sizes.size();++i)f<<(i?",":"")<<t.buf_sizes[i];f<<"],\"counts\":[";for(size_t i=0;i<t.buf_counts.size();++i)f<<(i?",":"")<<t.buf_counts[i];f<<"]}\n";}
