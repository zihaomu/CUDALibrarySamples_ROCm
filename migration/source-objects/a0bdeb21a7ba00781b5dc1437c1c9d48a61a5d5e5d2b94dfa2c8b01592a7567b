// SPDX-License-Identifier: Apache-2.0
// I5 entropy prototype: GPU Huffman, prefix scan, byte pack and byte stuffing.
#include <hip/hip_runtime.h>
#include <jpeglib.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

static constexpr int MAX_BITS=4096;
struct Code {unsigned short bits;unsigned char length;};
static void check(hipError_t r,const char*what){if(r!=hipSuccess)throw std::runtime_error(std::string(what)+": "+hipGetErrorString(r));}
static std::vector<unsigned char> read_file(const char*p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error("cannot open input");return {std::istreambuf_iterator<char>(f),{}};}
static void write_file(const char*p,const std::vector<unsigned char>&v){std::ofstream f(p,std::ios::binary);f.write((const char*)v.data(),v.size());if(!f)throw std::runtime_error("cannot write output");}
static std::array<Code,256> make_codes(JHUFF_TBL*table){if(!table)throw std::runtime_error("missing Huffman table");
 std::array<Code,256> result{};unsigned code=0,k=0;
 for(unsigned length=1;length<=16;++length){for(int n=0;n<table->bits[length];++n){
  unsigned symbol=table->huffval[k++];result[symbol]={static_cast<unsigned short>(code++),static_cast<unsigned char>(length)};}
  code<<=1;}return result;}

__device__ static void put_bits(unsigned char*out,int&n,unsigned value,int count){
 for(int bit=count-1;bit>=0;--bit){if(n<MAX_BITS && ((value>>bit)&1))out[n>>3]|=0x80u>>(n&7);++n;}}
__device__ static int category(int v){unsigned magnitude=v<0?-v:v;int n=0;while(magnitude){magnitude>>=1;++n;}return n;}
__device__ static unsigned amplitude(int v,int n){return v<0?unsigned((1<<n)-1+v):unsigned(v);}
__global__ static void encode_blocks(const short*coeff,const int*previous,const unsigned char*component,
 const Code*dc,const Code*ac,unsigned char*output,unsigned short*lengths,int blocks){
 int id=blockIdx.x*blockDim.x+threadIdx.x;if(id>=blocks)return;
 const short*c=coeff+size_t(id)*64;unsigned char*out=output+size_t(id)*(MAX_BITS/8);
 int comp=component[id],prev=previous[id];int value=int(c[0])-(prev<0?0:int(coeff[size_t(prev)*64]));
 int n=0,bits=category(value);Code h=dc[comp*256+bits];
 if(!h.length){lengths[id]=0;return;}put_bits(out,n,h.bits,h.length);put_bits(out,n,amplitude(value,bits),bits);
 const int zigzag[64]={0,1,8,16,9,2,3,10,17,24,32,25,18,11,4,5,12,19,26,33,40,48,41,34,27,20,13,6,7,14,21,28,35,42,49,56,57,50,43,36,29,22,15,23,30,37,44,51,58,59,52,45,38,31,39,46,53,60,61,54,47,55,62,63};
 int zeros=0;
 for(int k=1;k<64;++k){value=c[zigzag[k]];if(!value){++zeros;continue;}
  while(zeros>=16){h=ac[comp*256+0xf0];if(!h.length){lengths[id]=0;return;}
   put_bits(out,n,h.bits,h.length);zeros-=16;}
  bits=category(value);h=ac[comp*256+(zeros<<4)+bits];if(!h.length){lengths[id]=0;return;}
  put_bits(out,n,h.bits,h.length);put_bits(out,n,amplitude(value,bits),bits);zeros=0;}
 if(zeros){h=ac[comp*256];if(!h.length){lengths[id]=0;return;}put_bits(out,n,h.bits,h.length);}
 lengths[id]=n>MAX_BITS?0:static_cast<unsigned short>(n);
}

__global__ static void prefix_bits(const unsigned short*lengths,unsigned*offsets,
                                   unsigned*total,int blocks){
 if(blockIdx.x||threadIdx.x)return;
 unsigned sum=0;for(int i=0;i<blocks;++i){offsets[i]=sum;sum+=lengths[i];}
 total[0]=sum;
}
__global__ static void pack_bytes(const unsigned char*bits,const unsigned*offsets,
                                  unsigned char*packed,int blocks,unsigned total_bits,
                                  unsigned output_bytes){
 unsigned index=blockIdx.x*blockDim.x+threadIdx.x;if(index>=output_bytes)return;
 unsigned value=0;
 for(int slot=0;slot<8;++slot){unsigned bit_index=index*8+slot,bit=1;
  if(bit_index<total_bits){int low=0,high=blocks;
   while(low+1<high){int middle=(low+high)/2;if(offsets[middle]<=bit_index)low=middle;
    else high=middle;}
   unsigned local=bit_index-offsets[low];
   bit=(bits[size_t(low)*(MAX_BITS/8)+(local>>3)]>>(7-(local&7)))&1u;}
  value=(value<<1)|bit;}
 packed[index]=static_cast<unsigned char>(value);
}
__global__ static void prefix_stuff(const unsigned char*packed,unsigned*positions,
                                    unsigned*total,unsigned count){
 if(blockIdx.x||threadIdx.x)return;
 unsigned extra=0;for(unsigned i=0;i<count;++i){positions[i]=i+extra;
  if(packed[i]==0xff)++extra;}
 total[0]=count+extra;
}
__global__ static void scatter_stuff(const unsigned char*packed,const unsigned*positions,
                                     unsigned char*output,unsigned count){
 unsigned index=blockIdx.x*blockDim.x+threadIdx.x;if(index>=count)return;
 unsigned target=positions[index];output[target]=packed[index];
 if(packed[index]==0xff)output[target+1]=0;
}

static std::vector<unsigned char> original_entropy(const std::vector<unsigned char>&jpeg){
 if(jpeg.size()<8||jpeg[0]!=0xff||jpeg[1]!=0xd8)throw std::runtime_error("not baseline JPEG");
 size_t p=2;
 while(p+4<jpeg.size()){if(jpeg[p]!=0xff)throw std::runtime_error("invalid JPEG marker");
  unsigned marker=jpeg[p+1];if(marker==0xda){size_t length=(size_t(jpeg[p+2])<<8)|jpeg[p+3];
   size_t begin=p+2+length;if(begin+2>jpeg.size()||jpeg[jpeg.size()-2]!=0xff||jpeg.back()!=0xd9)
    throw std::runtime_error("missing EOI");return {jpeg.begin()+begin,jpeg.end()-2};}
  size_t length=(size_t(jpeg[p+2])<<8)|jpeg[p+3];if(length<2)throw std::runtime_error("invalid marker length");p+=length+2;}
 throw std::runtime_error("missing SOS");}

int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("usage: original.jpg gpu.entropy original.entropy");
 auto jpeg=read_file(argv[1]);jpeg_decompress_struct decoder{};jpeg_error_mgr err{};
 decoder.err=jpeg_std_error(&err);jpeg_create_decompress(&decoder);
 jpeg_mem_src(&decoder,jpeg.data(),jpeg.size());jpeg_read_header(&decoder,TRUE);
 if(decoder.progressive_mode||decoder.num_components!=3||decoder.restart_interval)
  throw std::runtime_error("prototype supports three-component baseline JPEG without restart");
 jvirt_barray_ptr*arrays=jpeg_read_coefficients(&decoder);
 int max_h=decoder.max_h_samp_factor,max_v=decoder.max_v_samp_factor;
 int mcus_x=(decoder.image_width+max_h*8-1)/(max_h*8),mcus_y=(decoder.image_height+max_v*8-1)/(max_v*8);
 std::vector<short>coeff;std::vector<int>previous;std::vector<unsigned char>components;
 std::array<int,3>last={-1,-1,-1};std::vector<Code>dc(3*256),ac(3*256);
 for(int c=0;c<3;++c){auto&info=decoder.comp_info[c];auto d=make_codes(decoder.dc_huff_tbl_ptrs[info.dc_tbl_no]);
  auto a=make_codes(decoder.ac_huff_tbl_ptrs[info.ac_tbl_no]);
  std::copy(d.begin(),d.end(),dc.begin()+c*256);std::copy(a.begin(),a.end(),ac.begin()+c*256);}
 for(int my=0;my<mcus_y;++my)for(int mx=0;mx<mcus_x;++mx)for(int c=0;c<3;++c){
  auto&info=decoder.comp_info[c];for(int v=0;v<info.v_samp_factor;++v)for(int h=0;h<info.h_samp_factor;++h){
   int row=my*info.v_samp_factor+v,col=mx*info.h_samp_factor+h;
   JBLOCKARRAY blocks=decoder.mem->access_virt_barray((j_common_ptr)&decoder,arrays[c],row,1,FALSE);
   int id=components.size();previous.push_back(last[c]);last[c]=id;components.push_back(c);
   coeff.insert(coeff.end(),blocks[0][col],blocks[0][col]+64);}}
 int count=components.size();if(!count)throw std::runtime_error("no scan blocks");
 check(hipSetDevice(0),"select AMD GPU");short*device_coeff=nullptr;int*device_prev=nullptr;
 unsigned char*device_comp=nullptr,*device_bits=nullptr;Code*device_dc=nullptr,*device_ac=nullptr;
 unsigned short*device_lengths=nullptr;
 check(hipMalloc(&device_coeff,coeff.size()*sizeof(short)),"coeff alloc");
 check(hipMalloc(&device_prev,previous.size()*sizeof(int)),"previous alloc");
 check(hipMalloc(&device_comp,components.size()),"component alloc");
 check(hipMalloc(&device_dc,dc.size()*sizeof(Code)),"DC table alloc");
 check(hipMalloc(&device_ac,ac.size()*sizeof(Code)),"AC table alloc");
 check(hipMalloc(&device_bits,size_t(count)*(MAX_BITS/8)),"bits alloc");
 check(hipMalloc(&device_lengths,size_t(count)*sizeof(unsigned short)),"length alloc");
 check(hipMemcpy(device_coeff,coeff.data(),coeff.size()*sizeof(short),hipMemcpyHostToDevice),"copy coeff");
 check(hipMemcpy(device_prev,previous.data(),previous.size()*sizeof(int),hipMemcpyHostToDevice),"copy prev");
 check(hipMemcpy(device_comp,components.data(),components.size(),hipMemcpyHostToDevice),"copy components");
 check(hipMemcpy(device_dc,dc.data(),dc.size()*sizeof(Code),hipMemcpyHostToDevice),"copy DC");
 check(hipMemcpy(device_ac,ac.data(),ac.size()*sizeof(Code),hipMemcpyHostToDevice),"copy AC");
 check(hipMemset(device_bits,0,size_t(count)*(MAX_BITS/8)),"clear GPU bits");
 encode_blocks<<<(count+127)/128,128>>>(device_coeff,device_prev,device_comp,device_dc,device_ac,
  device_bits,device_lengths,count);
 check(hipGetLastError(),"GPU Huffman kernel");check(hipDeviceSynchronize(),"GPU Huffman finish");
 std::vector<unsigned short>lengths(count);
 check(hipMemcpy(lengths.data(),device_lengths,count*sizeof(unsigned short),hipMemcpyDeviceToHost),"copy lengths");
 for(int id=0;id<count;++id)if(!lengths[id])throw std::runtime_error("missing/overflow GPU Huffman code");
 unsigned *device_offsets=nullptr,*device_total_bits=nullptr,*device_positions=nullptr,*device_stuffed_size=nullptr;
 unsigned char *device_packed=nullptr,*device_stuffed=nullptr;
 check(hipMalloc(&device_offsets,count*sizeof(unsigned)),"offset alloc");
 check(hipMalloc(&device_total_bits,sizeof(unsigned)),"total bits alloc");
 prefix_bits<<<1,1>>>(device_lengths,device_offsets,device_total_bits,count);
 check(hipGetLastError(),"launch GPU bit prefix scan");
 unsigned total_bits=0;check(hipMemcpy(&total_bits,device_total_bits,sizeof(unsigned),hipMemcpyDeviceToHost),"copy total bits");
 unsigned raw_bytes=(total_bits+7)/8;
 if(!raw_bytes)throw std::runtime_error("empty GPU entropy output");
 check(hipMalloc(&device_packed,raw_bytes),"packed byte alloc");
 pack_bytes<<<(raw_bytes+255)/256,256>>>(device_bits,device_offsets,device_packed,count,total_bits,raw_bytes);
 check(hipGetLastError(),"launch GPU byte bit packing");
 check(hipMalloc(&device_positions,raw_bytes*sizeof(unsigned)),"stuff offsets alloc");
 check(hipMalloc(&device_stuffed_size,sizeof(unsigned)),"stuffed size alloc");
 prefix_stuff<<<1,1>>>(device_packed,device_positions,device_stuffed_size,raw_bytes);
 check(hipGetLastError(),"launch GPU byte stuffing prefix scan");
 unsigned stuffed_size=0;check(hipMemcpy(&stuffed_size,device_stuffed_size,sizeof(unsigned),hipMemcpyDeviceToHost),"copy stuffed size");
 check(hipMalloc(&device_stuffed,stuffed_size),"stuffed entropy alloc");
 scatter_stuff<<<(raw_bytes+255)/256,256>>>(device_packed,device_positions,device_stuffed,raw_bytes);
 check(hipGetLastError(),"launch GPU byte stuffing scatter");
 std::vector<unsigned char>assembled(stuffed_size);
 check(hipMemcpy(assembled.data(),device_stuffed,stuffed_size,hipMemcpyDeviceToHost),"copy complete GPU entropy");
 for(auto*p:{(void*)device_coeff,(void*)device_prev,(void*)device_comp,(void*)device_dc,
             (void*)device_ac,(void*)device_bits,(void*)device_lengths})
  check(hipFree(p),"free GPU Huffman allocation");
 for(auto*p:{(void*)device_offsets,(void*)device_total_bits,(void*)device_positions,
             (void*)device_stuffed_size,(void*)device_packed,(void*)device_stuffed})
  check(hipFree(p),"free GPU packing allocation");
 auto expected=original_entropy(jpeg);write_file(argv[2],assembled);write_file(argv[3],expected);
 jpeg_finish_decompress(&decoder);jpeg_destroy_decompress(&decoder);
 std::cout<<"{\"blocks\":"<<count<<",\"total_bits\":"<<total_bits<<",\"gpu_huffman\":true,"
          <<"\"cpu_coefficient_extract\":true,\"gpu_prefix_pack_stuff\":true,"
          <<"\"cpu_bit_packing\":false,\"matches_original\":"
          <<(assembled==expected?"true":"false")<<"}\n";
 return assembled==expected?0:2;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
