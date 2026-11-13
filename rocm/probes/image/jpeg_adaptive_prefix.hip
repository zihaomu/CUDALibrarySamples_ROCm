// SPDX-License-Identifier: Apache-2.0
#include "image/jpeg_adaptive_prefix.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <cstring>
#include <vector>
#include <algorithm>

static void check(hipError_t c,const char* name) {if(c!=hipSuccess)throw std::runtime_error(std::string(name)+": "+hipGetErrorString(c));}
struct Memory {
    std::vector<void*> pointers;
    ~Memory() {hipDeviceSynchronize();for(auto p:pointers)hipFree(p);}
    template<class T>T* make(size_t count) {T* p=nullptr;check(hipMalloc(&p,count*sizeof(T)),"allocate adaptive probe");pointers.push_back(p);return p;}
};
template<class T>static void write(const std::filesystem::path& path,const std::vector<T>& values) {
    std::ofstream file(path,std::ios::binary);file.write(reinterpret_cast<const char*>(values.data()),values.size()*sizeof(T));
    if(!file)throw std::runtime_error("adaptive output failed");
}
template<class T,bool Stuff>static unsigned guards() {
    Memory m;const unsigned threshold=Stuff?image_jpeg_adaptive_prefix::stuff_serial_threshold:image_jpeg_adaptive_prefix::bit_serial_threshold;
    auto* input=m.make<T>(threshold+1);auto* offsets=m.make<unsigned>(threshold+1);auto* sums=m.make<unsigned>(1);auto* bases=m.make<unsigned>(1);auto* result=m.make<image_jpeg_checked_prefix::Result>(1);
    unsigned checked=0;
    if(image_jpeg_adaptive_prefix::launch<T,Stuff>(input,offsets,sums,bases,result,0)!=hipErrorInvalidValue)throw std::runtime_error("zero count accepted");++checked;
    for(unsigned count:{1U,threshold+1})for(unsigned absent=0;absent<5;++absent) {
        auto rc=image_jpeg_adaptive_prefix::launch<T,Stuff>(absent==0?nullptr:input,absent==1?nullptr:offsets,absent==2?nullptr:sums,absent==3?nullptr:bases,absent==4?nullptr:result,count);
        if(rc!=hipErrorInvalidValue)throw std::runtime_error("missing pointer accepted");++checked;
    }
    return checked;
}
template<class T,bool Stuff>static void run(const char* input_path,const char* output) {
    std::ifstream file(input_path,std::ios::binary);if(!file)throw std::runtime_error("missing input");
    std::vector<unsigned char> raw{std::istreambuf_iterator<char>(file),{}};
    if(raw.size()%sizeof(T)||raw.size()/sizeof(T)>1048576)throw std::runtime_error("invalid adaptive probe size");
    unsigned count=raw.size()/sizeof(T);std::filesystem::path folder=output;std::filesystem::create_directories(folder);
    Memory m;auto* input=m.make<T>(std::max(1U,count));auto* offsets=m.make<unsigned>(std::max(1U,count));
    const unsigned tiles=std::max(1U,image_jpeg_checked_prefix::tile_count(count));auto* sums=m.make<unsigned>(tiles);auto* bases=m.make<unsigned>(tiles);auto* result=m.make<image_jpeg_checked_prefix::Result>(1);
    if(count)check(hipMemcpy(input,raw.data(),raw.size(),hipMemcpyHostToDevice),"upload adaptive input");
    auto rc=image_jpeg_adaptive_prefix::launch<T,Stuff>(input,offsets,sums,bases,result,count);
    if(!count) {
        if(rc!=hipErrorInvalidValue)throw std::runtime_error("empty prefix not rejected");
        std::cout<<"{\"count\":0,\"host_invalid\":true}\n";return;
    }
    check(rc,"adaptive launch");std::vector<unsigned> positions(count);image_jpeg_checked_prefix::Result metadata{};
    check(hipMemcpy(positions.data(),offsets,count*sizeof(unsigned),hipMemcpyDeviceToHost),"copy adaptive offsets");check(hipMemcpy(&metadata,result,sizeof(metadata),hipMemcpyDeviceToHost),"copy adaptive metadata");
    write(folder/"offsets.u32",positions);write(folder/"result.u32",std::vector<unsigned>{metadata.total,metadata.errors});
    std::cout<<"{\"count\":"<<count<<",\"total\":"<<metadata.total<<",\"errors\":"<<metadata.errors<<",\"serial\":"<<(image_jpeg_adaptive_prefix::use_serial<Stuff>(count)?"true":"false")<<"}\n";
}
int main(int argc,char** argv) {
    try {
        check(hipSetDevice(0),"adaptive probe device");
        if(argc==2&&std::string(argv[1])=="guards") {unsigned count=guards<unsigned short,false>()+guards<unsigned char,true>();std::cout<<"{\"rejected_host_contracts\":"<<count<<"}\n";return 0;}
        if(argc!=4)throw std::runtime_error("usage: bits|stuff input output-dir");
        if(std::string(argv[1])=="bits")run<unsigned short,false>(argv[2],argv[3]);
        else if(std::string(argv[1])=="stuff")run<unsigned char,true>(argv[2],argv[3]);else throw std::runtime_error("invalid mode");return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
