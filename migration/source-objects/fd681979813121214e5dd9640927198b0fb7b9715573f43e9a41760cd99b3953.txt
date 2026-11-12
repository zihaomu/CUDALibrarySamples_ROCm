// SPDX-License-Identifier: Apache-2.0
// Baseline JPEG core on HIP. CPU constructs only standard markers and tables.
#pragma once
#include "jpeg_entropy_gpu.hpp"
#include <array>
#include <vector>

namespace image_jpeg_full {
using image_jpeg_encoder::check;

__global__ static void gather_mcu_coefficients(const short*y,const short*cb,const short*cr,
    short*scan,int*previous,unsigned char*component,int blocks_x_y,int blocks_y_y,
    int blocks_x_c,int blocks_y_c,int mcus_x,int mcu_count,int sampling){
 int id=blockIdx.x*blockDim.x+threadIdx.x;
 int per_mcu=sampling==2?6:3,block_count=mcu_count*per_mcu;
 if(id>=block_count*64)return;
 int block=id/64,frequency=id%64,mcu=block/per_mcu,slot=block%per_mcu;
 int mx=mcu%mcus_x,my=mcu/mcus_x,channel=0,bx=0,by=0;
 if(sampling==2){
  if(slot<4){bx=mx*2+(slot&1);by=my*2+(slot>>1);}
  else{channel=slot-3;bx=mx;by=my;}
 }else{channel=slot;bx=mx;by=my;}
 const short*source=channel==0?y:channel==1?cb:cr;
 int width=channel==0?blocks_x_y:blocks_x_c;
 int height=channel==0?blocks_y_y:blocks_y_c;
 scan[id]=(bx<width&&by<height)?source[(size_t(by)*width+bx)*64+frequency]:0;
 if(!frequency){component[block]=channel;
  if(sampling==2){previous[block]=(slot==0)?(mcu?block-3:-1):
    (slot<4?block-1:(mcu?block-6:-1));}
  else previous[block]=mcu?block-3:-1;}
}

inline void marker(std::vector<unsigned char>&out,unsigned char id,
                   const std::vector<unsigned char>&payload){
 if(payload.size()>65533)throw std::runtime_error("JPEG marker payload too long");
 out.push_back(0xff);out.push_back(id);unsigned length=payload.size()+2;
 out.push_back(length>>8);out.push_back(length&255);
 out.insert(out.end(),payload.begin(),payload.end());
}
inline std::vector<unsigned char> header(jpeg_compress_struct&jpeg,int width,int height,int sampling){
 const int zigzag[64]={0,1,8,16,9,2,3,10,17,24,32,25,18,11,4,5,12,19,26,33,40,48,41,34,27,20,13,6,7,14,21,28,35,42,49,56,57,50,43,36,29,22,15,23,30,37,44,51,58,59,52,45,38,31,39,46,53,60,61,54,47,55,62,63};
 std::vector<unsigned char>out={0xff,0xd8};
 marker(out,0xe0,{'J','F','I','F',0,1,1,0,0,1,0,1,0,0});
 for(int index=0;index<2;++index){auto*table=jpeg.quant_tbl_ptrs[index];
  if(!table)throw std::runtime_error("missing JPEG quant table");
  std::vector<unsigned char>payload={static_cast<unsigned char>(index)};
  for(int k:zigzag){if(table->quantval[k]>255)throw std::runtime_error("nonbaseline quant table");
   payload.push_back(table->quantval[k]);}
  marker(out,0xdb,payload);}
 std::vector<unsigned char>sof={8,static_cast<unsigned char>(height>>8),
  static_cast<unsigned char>(height),static_cast<unsigned char>(width>>8),
  static_cast<unsigned char>(width),3};
 for(int c=0;c<3;++c){const auto&info=jpeg.comp_info[c];
  sof.push_back(info.component_id);sof.push_back((info.h_samp_factor<<4)|info.v_samp_factor);
  sof.push_back(info.quant_tbl_no);}
 marker(out,0xc0,sof);
 for(int index=0;index<2;++index)for(int kind=0;kind<2;++kind){
  auto*table=kind?jpeg.ac_huff_tbl_ptrs[index]:jpeg.dc_huff_tbl_ptrs[index];
  if(!table)throw std::runtime_error("missing baseline Huffman table");
  std::vector<unsigned char>payload={static_cast<unsigned char>((kind<<4)|index)};
  unsigned symbols=0;for(int length=1;length<=16;++length){payload.push_back(table->bits[length]);symbols+=table->bits[length];}
  payload.insert(payload.end(),table->huffval,table->huffval+symbols);
  marker(out,0xc4,payload);}
 std::vector<unsigned char>sos={3};for(int c=0;c<3;++c){const auto&info=jpeg.comp_info[c];
  sos.push_back(info.component_id);sos.push_back((info.dc_tbl_no<<4)|info.ac_tbl_no);}
 sos.insert(sos.end(),{0,63,0});marker(out,0xda,sos);
 return out;
}

inline std::vector<unsigned char> encode(const std::vector<unsigned char>&rgb,
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
 gather_mcu_coefficients<<<(size_t(block_count)*64+255)/256,256,0,stream>>>(
  coeff[0],coeff[1],coeff[2],scan,previous,component,block_x[0],block_y[0],
  block_x[1],block_y[1],mcus_x,mcus_x*mcus_y,sampling);
 check(hipGetLastError(),"GPU MCU gather");
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
 auto output=header(jpeg,width,height,sampling);
 size_t entropy_start=output.size();output.resize(entropy_start+stuffed_bytes);
 check(hipMemcpyAsync(output.data()+entropy_start,stuffed,stuffed_bytes,hipMemcpyDeviceToHost,stream),"copy GPU entropy");
 check(hipStreamSynchronize(stream),"wait GPU entropy copy");
 output.push_back(0xff);output.push_back(0xd9);
 for(auto*p:allocations)check(hipFree(p),"free GPU JPEG allocation");
 jpeg_destroy_compress(&jpeg);
 return output;
}
} // namespace image_jpeg_full
