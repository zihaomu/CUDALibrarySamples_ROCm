// SPDX-License-Identifier: Apache-2.0
#include "image/jpeg_serial_prefix.hpp"
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#include <cstring>

static void check(hipError_t code,const char* label) {
    if(code!=hipSuccess)throw std::runtime_error(std::string(label)+": "+hipGetErrorString(code));
}
struct Memory {
    std::vector<void*> pointers;
    ~Memory() {hipDeviceSynchronize();for(auto p:pointers)hipFree(p);}
    template<class T>T* make(size_t count) {
        T* p=nullptr;check(hipMalloc(&p,count*sizeof(T)),"allocate benchmark");pointers.push_back(p);return p;
    }
};
template<class T>static void write(const std::filesystem::path& path,const std::vector<T>& values) {
    std::ofstream file(path,std::ios::binary);file.write(reinterpret_cast<const char*>(values.data()),values.size()*sizeof(T));
    if(!file)throw std::runtime_error("benchmark output failed");
}
template<class T,bool Stuff>static void execute(const char* path,const char* output,bool timed) {
    std::ifstream file(path,std::ios::binary);std::vector<unsigned char> raw{std::istreambuf_iterator<char>(file),{}};
    if(raw.empty()||raw.size()%sizeof(T)||raw.size()/sizeof(T)>1048576)throw std::runtime_error("invalid benchmark byte count");
    const unsigned count=raw.size()/sizeof(T);std::vector<T> input(count);std::memcpy(input.data(),raw.data(),raw.size());
    const std::filesystem::path folder=output;std::filesystem::create_directories(folder);
    Memory memory;auto* values=memory.make<T>(count);auto* offsets=memory.make<unsigned>(count);
    const unsigned tiles=image_jpeg_checked_prefix::tile_count(count);auto* sums=memory.make<unsigned>(tiles);auto* bases=memory.make<unsigned>(tiles);
    auto* result=memory.make<image_jpeg_checked_prefix::Result>(1);
    check(hipMemcpy(values,input.data(),raw.size(),hipMemcpyHostToDevice),"upload benchmark input");
    std::vector<unsigned> expected(count),actual(count);uint64_t sum=0;unsigned errors=0;
    for(unsigned i=0;i<count;++i) {
        expected[i]=unsigned(sum+(Stuff?uint64_t(i):0));
        if constexpr(Stuff)sum+=input[i]==0xff;
        else {if(!input[i]||input[i]>4096)errors|=1;sum+=input[i];}
    }
    if constexpr(Stuff)sum+=count;
    const uint64_t limit=Stuff?uint64_t(UINT32_MAX):uint64_t(UINT32_MAX)-7;
    if(sum>limit)errors|=2;
    const unsigned total=sum>limit?0:unsigned(sum);
    auto launch=[&](bool parallel) {
        check(parallel?image_jpeg_checked_prefix::launch<T,Stuff>(values,offsets,sums,bases,result,count):
            image_jpeg_serial_prefix::launch<T,Stuff>(values,offsets,result,count),"launch checked prefix");
    };
    for(bool parallel:{false,true}) {
        launch(parallel);image_jpeg_checked_prefix::Result observed{};
        check(hipMemcpy(actual.data(),offsets,count*sizeof(unsigned),hipMemcpyDeviceToHost),"copy offsets");
        check(hipMemcpy(&observed,result,sizeof(observed),hipMemcpyDeviceToHost),"copy checked metadata");
        write(folder/(parallel?"tiled.u32":"serial.u32"),actual);
        write(folder/(parallel?"tiled-result.u32":"serial-result.u32"),std::vector<unsigned>{observed.total,observed.errors});
        if(observed.errors!=errors||observed.total!=total||(!errors&&actual!=expected))throw std::runtime_error("host reference mismatch before timing");
    }
    if(errors&&timed)throw std::runtime_error("invalid inputs cannot be timed");
    std::vector<float> serial_times,parallel_times;
    if(timed) {
        hipEvent_t start{},stop{};check(hipEventCreate(&start),"create event start");check(hipEventCreate(&stop),"create event stop");
        for(unsigned pair=0;pair<23;++pair)for(unsigned order=0;order<2;++order) {
            const bool parallel=(pair+order)%2;
            check(hipEventRecord(start),"record event start");launch(parallel);check(hipEventRecord(stop),"record event stop");check(hipEventSynchronize(stop),"wait event");
            float elapsed=0;check(hipEventElapsedTime(&elapsed,start,stop),"event duration");
            if(pair>=3)(parallel?parallel_times:serial_times).push_back(elapsed);
        }
        check(hipEventDestroy(start),"destroy event start");check(hipEventDestroy(stop),"destroy event stop");
    }
    auto print=[](const char* name,const std::vector<float>& times) {
        std::cout<<",\""<<name<<"\":[";for(size_t i=0;i<times.size();++i)std::cout<<(i?",":"")<<times[i];std::cout<<"]";
    };
    std::cout<<"{\"count\":"<<count<<",\"total\":"<<total<<",\"errors\":"<<errors<<",\"host_reference_passed\":true";
    print("serial_ms",serial_times);print("tiled_ms",parallel_times);std::cout<<"}\n";
}
int main(int argc,char** argv) {
    try {
        if(argc!=5)throw std::runtime_error("usage: bits|stuff input output-dir timed");check(hipSetDevice(0),"benchmark device");
        if(std::string(argv[1])=="bits")execute<unsigned short,false>(argv[2],argv[3],std::stoi(argv[4])!=0);
        else if(std::string(argv[1])=="stuff")execute<unsigned char,true>(argv[2],argv[3],std::stoi(argv[4])!=0);
        else throw std::runtime_error("invalid prefix mode");return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
