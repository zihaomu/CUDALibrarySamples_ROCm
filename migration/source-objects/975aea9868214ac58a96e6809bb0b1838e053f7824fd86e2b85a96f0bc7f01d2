// SPDX-License-Identifier: Apache-2.0
#include "jpeg_checked_prefix.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <vector>
using namespace image_jpeg_checked_prefix;
void check(hipError_t e) { if(e!=hipSuccess) throw std::runtime_error(hipGetErrorString(e)); }
template<class T> void load(const char* path,std::vector<T>& values) {
    std::ifstream file(path,std::ios::binary|std::ios::ate);
    if(!file || file.tellg()<=0 || size_t(file.tellg())%sizeof(T))throw std::runtime_error("bad input");
    if(size_t(file.tellg())/sizeof(T)>UINT32_MAX)throw std::runtime_error("prefix count exceeds uint32");
    values.resize(size_t(file.tellg())/sizeof(T));file.seekg(0);
    file.read(reinterpret_cast<char*>(values.data()),values.size()*sizeof(T));
    if(!file)throw std::runtime_error("short input");
}
template<class T,bool Stuff> void run(const char* input,const char* output) {
    std::vector<T> data;load(input,data);unsigned n=data.size(),nt=tile_count(n);
    T* din=nullptr;unsigned *offsets=nullptr,*sums=nullptr,*tb=nullptr;Result* result=nullptr;
    check(hipMalloc(&din,data.size()*sizeof(T)));check(hipMalloc(&offsets,size_t(n)*sizeof(unsigned)));
    check(hipMalloc(&sums,nt*sizeof(unsigned)));check(hipMalloc(&tb,nt*sizeof(unsigned)));check(hipMalloc(&result,sizeof(Result)));
    check(hipMemcpy(din,data.data(),data.size()*sizeof(T),hipMemcpyHostToDevice));
    check(launch<T,Stuff>(din,offsets,sums,tb,result,n));
    Result host{};check(hipMemcpy(&host,result,sizeof(host),hipMemcpyDeviceToHost));
    std::vector<unsigned> positions(n);check(hipMemcpy(positions.data(),offsets,n*sizeof(unsigned),hipMemcpyDeviceToHost));
    std::ofstream file(output,std::ios::binary);file.write(reinterpret_cast<char*>(positions.data()),n*sizeof(unsigned));
    if(!file)throw std::runtime_error("output failed");
    check(hipFree(din));check(hipFree(offsets));check(hipFree(sums));check(hipFree(tb));check(hipFree(result));
    std::cout<<"{\"total\":"<<host.total<<",\"errors\":"<<host.errors<<",\"count\":"<<n<<"}\n";
}
int main(int argc,char**argv) {
    try {
        if(argc!=4)throw std::runtime_error("usage: bits|stuff input output");
        check(hipSetDevice(0));
        if(std::string(argv[1])=="empty") {
            auto error=launch<unsigned short,false>(nullptr,nullptr,nullptr,nullptr,nullptr,0);
            if(error!=hipErrorInvalidValue)throw std::runtime_error("empty input accepted");
            std::cout<<"{\"empty_rejected\":true}\n";
        }
        else if(std::string(argv[1])=="bits")run<unsigned short,false>(argv[2],argv[3]);
        else if(std::string(argv[1])=="stuff")run<unsigned char,true>(argv[2],argv[3]);
        else throw std::runtime_error("unknown mode");
        return 0;
    } catch(const std::exception&e) {std::cerr<<e.what()<<'\n';return 1;}
}
