// SPDX-License-Identifier: Apache-2.0
// Independent CPU JPEG coefficient inspection; never a production encoder.
#include <cstdio>
#include <jpeglib.h>
#include <dlfcn.h>
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv) {
    try {
        if(argc!=2)throw std::runtime_error("usage: JPEG");
        Dl_info library{};if(!dladdr(reinterpret_cast<void*>(jpeg_std_error),&library)||!library.dli_fname)throw std::runtime_error("libjpeg identity unavailable");
        std::cerr<<"JPEG_LIBRARY="<<library.dli_fname<<'\n';
        FILE* input=std::fopen(argv[1],"rb");if(!input)throw std::runtime_error("missing JPEG");
        jpeg_decompress_struct d{};jpeg_error_mgr err{};d.err=jpeg_std_error(&err);jpeg_create_decompress(&d);
        jpeg_stdio_src(&d,input);jpeg_read_header(&d,TRUE);auto arrays=jpeg_read_coefficients(&d);
        std::cout<<"{\"width\":"<<d.image_width<<",\"height\":"<<d.image_height<<",\"components\":[";
        for(int c=0;c<d.num_components;++c) {
            auto& info=d.comp_info[c];if(c)std::cout<<',';
            std::cout<<"{\"width_blocks\":"<<info.width_in_blocks<<",\"height_blocks\":"<<info.height_in_blocks<<",\"quant\":[";
            for(int k=0;k<64;++k){if(k)std::cout<<',';std::cout<<d.quant_tbl_ptrs[info.quant_tbl_no]->quantval[k];}
            std::cout<<"],\"coefficients\":[";bool first=true;
            for(JDIMENSION y=0;y<info.height_in_blocks;++y) {
                JBLOCKARRAY row=(*d.mem->access_virt_barray)(reinterpret_cast<j_common_ptr>(&d),arrays[c],y,1,FALSE);
                for(JDIMENSION x=0;x<info.width_in_blocks;++x)for(int k=0;k<64;++k) {if(!first)std::cout<<',';first=false;std::cout<<row[0][x][k];}
            }
            std::cout<<"]}";
        }
        std::cout<<"]}\n";jpeg_finish_decompress(&d);jpeg_destroy_decompress(&d);std::fclose(input);return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
