// SPDX-License-Identifier: Apache-2.0
// CPU-only nearest-upsampled YCbCr reference for explicit reconstruction modes.
#include <cstdio>
#include <jpeglib.h>
#include <fstream>
#include <iostream>
#include <vector>
#include <stdexcept>
#include <dlfcn.h>

int main(int argc,char**argv) {
    try {
        if(argc!=3)throw std::runtime_error("usage: JPEG output-YCbCr");
        Dl_info library{};
        if(!dladdr(reinterpret_cast<void*>(jpeg_std_error),&library)||!library.dli_fname)
            throw std::runtime_error("cannot resolve actual libjpeg");
        std::cerr<<"JPEG_LIBRARY="<<library.dli_fname<<'\n';
        FILE* input=std::fopen(argv[1],"rb");if(!input)throw std::runtime_error("missing JPEG input");
        jpeg_decompress_struct jpeg{};jpeg_error_mgr errors{};jpeg.err=jpeg_std_error(&errors);jpeg_create_decompress(&jpeg);
        jpeg_stdio_src(&jpeg,input);jpeg_read_header(&jpeg,TRUE);
        if(jpeg.num_components!=3||jpeg.comp_info[0].h_samp_factor!=2||jpeg.comp_info[0].v_samp_factor!=2||
           jpeg.comp_info[1].h_samp_factor!=1||jpeg.comp_info[1].v_samp_factor!=1||
           jpeg.comp_info[2].h_samp_factor!=1||jpeg.comp_info[2].v_samp_factor!=1)throw std::runtime_error("reference requires 3-component 420 JPEG");
        jpeg.out_color_space=JCS_YCbCr;jpeg.do_fancy_upsampling=FALSE;jpeg.dct_method=JDCT_ISLOW;
        jpeg_start_decompress(&jpeg);const unsigned width=jpeg.output_width,height=jpeg.output_height;
        if(jpeg.output_components!=3)throw std::runtime_error("reference component mismatch");
        std::vector<unsigned char> row(size_t(width)*3);std::ofstream output(argv[2],std::ios::binary);
        while(jpeg.output_scanline<height) {JSAMPROW pointer=row.data();if(jpeg_read_scanlines(&jpeg,&pointer,1)!=1)throw std::runtime_error("short CPU scanline");output.write(reinterpret_cast<char*>(row.data()),row.size());}
        jpeg_finish_decompress(&jpeg);jpeg_destroy_decompress(&jpeg);std::fclose(input);if(!output)throw std::runtime_error("CPU YCbCr output failed");
        std::cout<<"{\"width\":"<<width<<",\"height\":"<<height<<",\"components\":3,\"fancy\":false,\"YCC_bytes\":"<<size_t(width)*height*3<<"}\n";return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
