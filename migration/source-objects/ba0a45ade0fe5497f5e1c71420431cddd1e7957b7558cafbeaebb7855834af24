// SPDX-License-Identifier: Apache-2.0
// Independent CPU-only decoder; upstream source is pinned and unmodified.
#define STB_IMAGE_IMPLEMENTATION
#define STBI_ONLY_JPEG
#include <stb_image.h>
#include <fstream>
#include <iostream>
#include <stdexcept>

int main(int argc,char**argv) {
    try {
        if(argc!=3)throw std::runtime_error("usage: JPEG output-RGB");
        int width=0,height=0,components=0;
        auto* data=stbi_load(argv[1],&width,&height,&components,3);
        if(!data)throw std::runtime_error(stbi_failure_reason()?stbi_failure_reason():"CPU JPEG decode failed");
        const size_t bytes=size_t(width)*height*3;
        std::ofstream output(argv[2],std::ios::binary);output.write(reinterpret_cast<char*>(data),bytes);stbi_image_free(data);
        if(!output)throw std::runtime_error("CPU RGB output failed");
        std::cout<<"{\"width\":"<<width<<",\"height\":"<<height<<",\"source_components\":"<<components<<",\"RGB_bytes\":"<<bytes<<"}\n";
        return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
