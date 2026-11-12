// SPDX-License-Identifier: Apache-2.0
// Isolated optimized baseline JPEG prototype; reuses frozen baseline GPU stages.
#pragma once
#include "jpeg_optimal_huffman.hpp"
namespace image_jpeg_opt {
using image_jpeg_full::check;
inline std::vector<unsigned char> encode_optimized(const std::vector<unsigned char>&rgb,
                                         int width,int height,int quality,int sampling,
                                         hipStream_t stream=nullptr){
 if(width<=0||height<=0||width>65535||height>65535||quality<1||quality>100||
    (sampling!=1&&sampling!=2)||rgb.size()!=size_t(width)*height*3)
  throw std::runtime_error("invalid full-GPU JPEG input");
 jpeg_compress_struct jpeg{};jpeg_error_mgr errors{};jpeg.err=jpeg_std_error(&errors);
 jpeg_create_compress(&jpeg);jpeg.image_width=width;jpeg.image_height=height;
 jpeg.input_components=3;jpeg.in_color_space=JCS_RGB;
 jpeg_set_defaults(&jpeg);jpeg_set_quality(&jpeg,quality,TRUE);
 jpeg.comp_info[0].h_samp_factor=sampling;jpeg.comp_info[0].v_samp_factor=sampling;
 for(int c=1;c<3;++c){jpeg.comp_info[c].h_samp_factor=1;jpeg.comp_info[c].v_samp_factor=1;}
 check(hipSetDevice(0),"select AMD GPU");
 std::vector<void*>allocations;auto allocate=[&](size_t bytes){void*p=nullptr;
  check(hipMalloc(&p,bytes),"GPU JPEG allocation");allocations.push_back(p);return p;};
 auto*device_rgb=static_cast<unsigned char*>(allocate(rgb.size()));
 check(hipMemcpyAsync(device_rgb,rgb.data(),rgb.size(),hipMemcpyHostToDevice,stream),"copy RGB");
 float cosine[64];for(int x=0;x<8;++x)for(int u=0;u<8;++u)
  cosine[x*8+u]=std::cos(float((2*x+1)*u)*3.14159265358979323846f/16.0f);
 auto*device_cosine=static_cast<float*>(allocate(sizeof(cosine)));
 check(hipMemcpyAsync(device_cosine,cosine,sizeof(cosine),hipMemcpyHostToDevice,stream),"copy cosine");
 std::array<short*,3>coeff{};std::array<int,3>block_x{},block_y{};
 for(int c=0;c<3;++c){int scale=c?sampling:1;
  int pw=(width+scale-1)/scale,ph=(height+scale-1)/scale;
  block_x[c]=(pw+7)/8;block_y[c]=(ph+7)/8;
  size_t pixels=size_t(pw)*ph,terms=size_t(block_x[c])*block_y[c]*64;
  auto*plane=static_cast<unsigned char*>(allocate(pixels));
  auto*quant=static_cast<unsigned short*>(allocate(64*sizeof(unsigned short)));
  coeff[c]=static_cast<short*>(allocate(terms*sizeof(short)));
  auto*table=jpeg.quant_tbl_ptrs[jpeg.comp_info[c].quant_tbl_no];
  if(!table)throw std::runtime_error("missing quant table for component");
  check(hipMemcpyAsync(quant,table->quantval,64*sizeof(unsigned short),hipMemcpyHostToDevice,stream),"copy quant table");
  image_jpeg_encoder::rgb_to_plane<<<(pixels+255)/256,256,0,stream>>>(device_rgb,plane,width,height,pw,ph,c,sampling);
  check(hipGetLastError(),"GPU RGB and chroma");
  image_jpeg_encoder::forward_dct_quantize<<<(terms+255)/256,256,0,stream>>>(plane,quant,device_cosine,
    coeff[c],pw,ph,block_x[c],block_y[c]);
  check(hipGetLastError(),"GPU FDCT quant");}
 int mcus_x=(width+sampling*8-1)/(sampling*8),mcus_y=(height+sampling*8-1)/(sampling*8);
 int block_count=mcus_x*mcus_y*(sampling==2?6:3);
 auto*scan=static_cast<short*>(allocate(size_t(block_count)*64*sizeof(short)));
 auto*previous=static_cast<int*>(allocate(size_t(block_count)*sizeof(int)));
 auto*component=static_cast<unsigned char*>(allocate(block_count));
 image_jpeg_full::gather_mcu_coefficients<<<(size_t(block_count)*64+255)/256,256,0,stream>>>(
  coeff[0],coeff[1],coeff[2],scan,previous,component,block_x[0],block_y[0],
  block_x[1],block_y[1],mcus_x,mcus_x*mcus_y,sampling);
 check(hipGetLastError(),"GPU MCU gather");
 auto*hist=static_cast<unsigned*>(allocate(4*256*sizeof(unsigned)));
 auto*invalid=static_cast<unsigned*>(allocate(sizeof(unsigned)));
 check(hipMemsetAsync(hist,0,4*256*sizeof(unsigned),stream),"clear optimized Huffman histogram");
 check(hipMemsetAsync(invalid,0,sizeof(unsigned),stream),"clear optimized Huffman guard");
 histogram<<<(block_count+127)/128,128,0,stream>>>(scan,previous,component,hist,invalid,block_count);
 check(hipGetLastError(),"GPU optimized Huffman symbol histogram");
 std::array<unsigned,4*256> host_hist{};unsigned invalid_symbols=0;
 check(hipMemcpyAsync(host_hist.data(),hist,host_hist.size()*sizeof(unsigned),hipMemcpyDeviceToHost,stream),"copy GPU symbol histogram");
 check(hipMemcpyAsync(&invalid_symbols,invalid,sizeof(unsigned),hipMemcpyDeviceToHost,stream),"copy symbol guard");
 check(hipStreamSynchronize(stream),"wait GPU optimized histogram");
 if(invalid_symbols)throw std::runtime_error("nonbaseline JPEG symbol in optimized histogram");
 for(int group=0;group<2;++group){
  make_table(jpeg.dc_huff_tbl_ptrs[group],host_hist.data()+group*256);
  make_table(jpeg.ac_huff_tbl_ptrs[group],host_hist.data()+(group+2)*256);
 }

 std::vector<Code>dc(3*256),ac(3*256);
 for(int c=0;c<3;++c){auto&info=jpeg.comp_info[c];auto d=make_codes(jpeg.dc_huff_tbl_ptrs[info.dc_tbl_no]);
  auto a=make_codes(jpeg.ac_huff_tbl_ptrs[info.ac_tbl_no]);
  std::copy(d.begin(),d.end(),dc.begin()+c*256);std::copy(a.begin(),a.end(),ac.begin()+c*256);}
 auto*device_dc=static_cast<Code*>(allocate(dc.size()*sizeof(Code)));
 auto*device_ac=static_cast<Code*>(allocate(ac.size()*sizeof(Code)));
 check(hipMemcpyAsync(device_dc,dc.data(),dc.size()*sizeof(Code),hipMemcpyHostToDevice,stream),"copy DC Huffman");
 check(hipMemcpyAsync(device_ac,ac.data(),ac.size()*sizeof(Code),hipMemcpyHostToDevice,stream),"copy AC Huffman");
 auto*bits=static_cast<unsigned char*>(allocate(size_t(block_count)*(MAX_BITS/8)));
 auto*lengths=static_cast<unsigned short*>(allocate(size_t(block_count)*sizeof(unsigned short)));
 check(hipMemsetAsync(bits,0,size_t(block_count)*(MAX_BITS/8),stream),"clear Huffman bits");
 encode_blocks<<<(block_count+127)/128,128,0,stream>>>(scan,previous,component,device_dc,device_ac,
  bits,lengths,block_count);
 check(hipGetLastError(),"GPU Huffman symbols and bits");
 auto*offsets=static_cast<unsigned*>(allocate(size_t(block_count)*sizeof(unsigned)));
 auto*total=static_cast<unsigned*>(allocate(sizeof(unsigned)));
 prefix_bits<<<1,1,0,stream>>>(lengths,offsets,total,block_count);
 check(hipGetLastError(),"GPU bit prefix");
 unsigned total_bits=0;check(hipMemcpyAsync(&total_bits,total,sizeof(unsigned),hipMemcpyDeviceToHost,stream),"copy total bits");
 check(hipStreamSynchronize(stream),"wait GPU bit prefix");
 if(!total_bits)throw std::runtime_error("empty GPU JPEG entropy");
 unsigned raw_bytes=(total_bits+7)/8;
 auto*packed=static_cast<unsigned char*>(allocate(raw_bytes));
 pack_bytes<<<(raw_bytes+255)/256,256,0,stream>>>(bits,offsets,packed,block_count,total_bits,raw_bytes);
 check(hipGetLastError(),"GPU bit pack");
 auto*positions=static_cast<unsigned*>(allocate(size_t(raw_bytes)*sizeof(unsigned)));
 auto*stuffed_total=static_cast<unsigned*>(allocate(sizeof(unsigned)));
 prefix_stuff<<<1,1,0,stream>>>(packed,positions,stuffed_total,raw_bytes);
 check(hipGetLastError(),"GPU stuffing prefix");
 unsigned stuffed_bytes=0;
 check(hipMemcpyAsync(&stuffed_bytes,stuffed_total,sizeof(unsigned),hipMemcpyDeviceToHost,stream),"copy stuffed bytes");
 check(hipStreamSynchronize(stream),"wait GPU stuffing prefix");
 auto*stuffed=static_cast<unsigned char*>(allocate(stuffed_bytes));
 scatter_stuff<<<(raw_bytes+255)/256,256,0,stream>>>(packed,positions,stuffed,raw_bytes);
 check(hipGetLastError(),"GPU byte stuffing scatter");
 auto output=image_jpeg_full::header(jpeg,width,height,sampling);
 size_t entropy_start=output.size();output.resize(entropy_start+stuffed_bytes);
 check(hipMemcpyAsync(output.data()+entropy_start,stuffed,stuffed_bytes,hipMemcpyDeviceToHost,stream),"copy GPU entropy");
 check(hipStreamSynchronize(stream),"wait GPU entropy copy");
 output.push_back(0xff);output.push_back(0xd9);
 for(auto*p:allocations)check(hipFree(p),"free GPU JPEG allocation");
 jpeg_destroy_compress(&jpeg);
 return output;
}
} // namespace image_jpeg_opt
