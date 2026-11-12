// SPDX-License-Identifier: Apache-2.0
#include "jpeg_full_gpu.hpp"
int main(int argc,char**argv){try{
 if(argc!=7)throw std::runtime_error("usage: input.rgb width height quality 420|444 output.jpg");
 auto rgb=image_jpeg_encoder::read_binary(argv[1]);int width=std::stoi(argv[2]),height=std::stoi(argv[3]),quality=std::stoi(argv[4]);
 std::string sampling=argv[5];if(sampling!="420"&&sampling!="444")throw std::runtime_error("sampling must be 420 or 444");
 auto jpeg=image_jpeg_full::encode(rgb,width,height,quality,sampling=="420"?2:1);
 image_jpeg_encoder::write_binary(argv[6],jpeg.data(),jpeg.size());
 std::cout<<"{\"width\":"<<width<<",\"height\":"<<height<<",\"quality\":"<<quality
  <<",\"sampling\":\""<<sampling<<"\",\"gpu_fdct\":true,\"gpu_huffman\":true,"
  <<"\"gpu_pack_stuff\":true,\"cpu_entropy\":false,\"cpu_header_tables\":true}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
