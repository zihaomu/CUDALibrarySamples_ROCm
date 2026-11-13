// SPDX-License-Identifier: Apache-2.0
#include "image/jpeg_frame_layout.hpp"
#include <hip/hip_runtime.h>
#include <fstream>
#include <iostream>

static void check(hipError_t c) {if(c!=hipSuccess)throw std::runtime_error(hipGetErrorString(c));}
int main(int argc,char**argv) {
    try {
        if(argc!=2)throw std::runtime_error("usage: frozen-geometry-input");
        check(hipSetDevice(0));size_t available=0,total=0;check(hipMemGetInfo(&available,&total));
        char pci[64]{};check(hipDeviceGetPCIBusId(pci,sizeof(pci),0));
        std::ifstream file(argv[1]);if(!file)throw std::runtime_error("missing geometry input");
        std::cout<<"{\"available_bytes\":"<<available<<",\"total_bytes\":"<<total<<",\"pci\":\""<<pci<<"\",\"rows\":[";
        int w,h,s,opt;bool first=true;
        while(file>>w>>h>>s>>opt) {
            if(!first)std::cout<<',';first=false;
            try {
                auto f=image_jpeg_layout::frame(w,h,s,opt!=0);bool rejected=false;
                try {image_jpeg_layout::require(f,available);}catch(const image_jpeg_layout::CapacityError&) {rejected=true;}
                std::cout<<"{\"valid\":true,\"minimum_bytes\":"<<f.minimum_bytes<<",\"blocks\":"<<f.blocks
                         <<",\"histogram_safe\":"<<(f.histogram_safe?"true":"false")<<",\"pixels\":[";
                for(unsigned c=0;c<3;++c)std::cout<<(c?",":"")<<f.pixels[c];std::cout<<"],\"coefficients\":[";
                for(unsigned c=0;c<3;++c)std::cout<<(c?",":"")<<f.coefficients[c];std::cout<<"],\"fits\":[";
                const bool fits[]={image_jpeg_layout::fits(f,available),image_jpeg_layout::fits(f,0),
                    image_jpeg_layout::fits(f,f.minimum_bytes-1),image_jpeg_layout::fits(f,f.minimum_bytes),
                    image_jpeg_layout::fits(f,f.minimum_bytes+1),image_jpeg_layout::fits(f,1,f.minimum_bytes-1),
                    image_jpeg_layout::fits(f,UINT64_MAX,f.minimum_bytes)};
                for(unsigned i=0;i<7;++i)std::cout<<(i?",":"")<<(fits[i]?"true":"false");
                std::cout<<"],\"actual_capacity_rejected\":"<<(rejected?"true":"false")<<'}';
            }catch(const std::invalid_argument&) {std::cout<<"{\"valid\":false}";}
        }
        std::cout<<"]}\n";return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
