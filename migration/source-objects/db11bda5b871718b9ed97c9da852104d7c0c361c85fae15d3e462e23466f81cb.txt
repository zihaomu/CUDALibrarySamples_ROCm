// SPDX-License-Identifier: Apache-2.0
#include "image/jpeg_wide_transform.hpp"
#include "image/jpeg_full_gpu.hpp"
#include <filesystem>
#include <sstream>
#include <climits>

using image_jpeg_encoder::check;
struct Allocations {
    std::vector<void*> pointers;
    ~Allocations() {hipDeviceSynchronize();for(auto p:pointers)hipFree(p);}
    template<class T>T* make(size_t count) {
        if(count>SIZE_MAX/sizeof(T))throw std::runtime_error("probe allocation overflow");
        T* pointer=nullptr;check(hipMalloc(&pointer,count*sizeof(T)),"probe allocate");pointers.push_back(pointer);return pointer;
    }
};
template<class T>void output_pair(const std::filesystem::path& folder,const char* label,T* candidate,T* original,size_t count) {
    std::vector<T> wide(count),old(count);
    check(hipMemcpy(wide.data(),candidate,count*sizeof(T),hipMemcpyDeviceToHost),"copy wide array");
    check(hipMemcpy(old.data(),original,count*sizeof(T),hipMemcpyDeviceToHost),"copy original array");
    image_jpeg_encoder::write_binary((folder/(std::string(label)+"-wide.bin")).c_str(),reinterpret_cast<const unsigned char*>(wide.data()),count*sizeof(T));
    image_jpeg_encoder::write_binary((folder/(std::string(label)+"-original.bin")).c_str(),reinterpret_cast<const unsigned char*>(old.data()),count*sizeof(T));
}

__global__ void coordinates(const unsigned long long* input,unsigned long long* output,unsigned count) {
    const unsigned id=blockIdx.x*blockDim.x+threadIdx.x;if(id>=count)return;
    const auto* row=input+size_t(id)*4;auto* result=output+size_t(id)*13;
    const int width=row[0],height=row[1],sampling=row[2];const size_t index=row[3];
    const int bx=(width+7)/8,by=(height+7)/8,cx=((width+sampling-1)/sampling+7)/8,cy=((height+sampling-1)/sampling+7)/8;
    const int mx=(width+sampling*8-1)/(sampling*8),my=(height+sampling*8-1)/(sampling*8);
    const auto p=image_jpeg_wide::pixel_index(index,width,height);
    const auto d=image_jpeg_wide::dct_index(index,bx,by);
    const auto s=image_jpeg_wide::scan_index(index,bx,by,cx,cy,mx,my,sampling);
    result[0]=p.valid;result[1]=p.x;result[2]=p.y;result[3]=d.valid;result[4]=d.x;result[5]=d.y;
    result[6]=d.u;result[7]=d.v;result[8]=s.valid;result[9]=s.channel;result[10]=s.source_valid;
    result[11]=s.source;result[12]=s.previous<0?ULLONG_MAX:static_cast<unsigned long long>(s.previous);
}

int main(int argc,char** argv) {
    try {
        check(hipSetDevice(0),"probe device");Allocations memory;
        if(argc==4&&std::string(argv[1])=="coordinates") {
            std::ifstream file(argv[2]);std::vector<unsigned long long> input;unsigned long long v;
            while(file>>v)input.push_back(v);
            if(input.empty()||input.size()%4)throw std::runtime_error("invalid coordinate input");
            auto* device_in=memory.make<unsigned long long>(input.size());const unsigned count=input.size()/4;
            auto* device_out=memory.make<unsigned long long>(size_t(count)*13);
            check(hipMemcpy(device_in,input.data(),input.size()*sizeof(v),hipMemcpyHostToDevice),"copy coordinates");
            coordinates<<<(count+63)/64,64>>>(device_in,device_out,count);check(hipGetLastError(),"wide coordinate kernel");
            std::vector<unsigned long long> output(size_t(count)*13);
            check(hipMemcpy(output.data(),device_out,output.size()*sizeof(v),hipMemcpyDeviceToHost),"copy coordinate result");
            std::ofstream out(argv[3]);for(unsigned i=0;i<count;++i) {for(unsigned j=0;j<13;++j)out<<output[size_t(i)*13+j]<<' ';out<<'\n';}
            if(!out)throw std::runtime_error("coordinate write failed");return 0;
        }
        if(argc!=7)throw std::runtime_error("usage: RGB width height sampling quality output-dir");
        const int width=std::stoi(argv[2]),height=std::stoi(argv[3]),sampling=std::stoi(argv[4]),quality=std::stoi(argv[5]);
        if(width<=0||height<=0||width>65535||height>65535||(sampling!=1&&sampling!=2)||quality<1||quality>100)throw std::runtime_error("invalid probe shape/mode");
        auto rgb=image_jpeg_encoder::read_binary(argv[1]);if(rgb.size()!=size_t(width)*height*3)throw std::runtime_error("RGB byte count");
        const std::filesystem::path folder=argv[6];std::filesystem::create_directories(folder);
        auto* device_rgb=memory.make<unsigned char>(rgb.size());check(hipMemcpy(device_rgb,rgb.data(),rgb.size(),hipMemcpyHostToDevice),"copy probe RGB");
        float cosine[64];for(int x=0;x<8;++x)for(int u=0;u<8;++u)cosine[x*8+u]=std::cos(float((2*x+1)*u)*3.14159265358979323846f/16.0f);
        auto* device_cosine=memory.make<float>(64);check(hipMemcpy(device_cosine,cosine,sizeof(cosine),hipMemcpyHostToDevice),"copy cosine");
        jpeg_compress_struct jpeg{};jpeg_error_mgr errors{};jpeg.err=jpeg_std_error(&errors);jpeg_create_compress(&jpeg);
        jpeg.input_components=3;jpeg.in_color_space=JCS_RGB;jpeg_set_defaults(&jpeg);jpeg_set_quality(&jpeg,quality,TRUE);
        std::array<short*,3> wide{},original{};std::array<int,3> bx{},by{};
        for(int c=0;c<3;++c) {
            const int scale=c?sampling:1,pw=(width+scale-1)/scale,ph=(height+scale-1)/scale;
            bx[c]=(pw+7)/8;by[c]=(ph+7)/8;const size_t pixels=size_t(pw)*ph,terms=size_t(bx[c])*by[c]*64;
            if(pixels>INT_MAX||terms>INT_MAX)throw std::runtime_error("legacy comparison index range exceeded");
            auto* plane_wide=memory.make<unsigned char>(pixels);auto* plane_old=memory.make<unsigned char>(pixels);
            auto* quant=memory.make<unsigned short>(64);
            check(hipMemcpy(quant,jpeg.quant_tbl_ptrs[c?1:0]->quantval,64*sizeof(unsigned short),hipMemcpyHostToDevice),"copy quant");
            image_jpeg_wide::rgb_to_plane<<<(pixels+255)/256,256>>>(device_rgb,plane_wide,width,height,pw,ph,c,sampling);
            check(hipGetLastError(),"wide color");
            image_jpeg_encoder::rgb_to_plane<<<(pixels+255)/256,256>>>(device_rgb,plane_old,width,height,pw,ph,c,sampling);
            check(hipGetLastError(),"original color");
            wide[c]=memory.make<short>(terms);original[c]=memory.make<short>(terms);
            image_jpeg_wide::forward_dct_quantize<<<(terms+255)/256,256>>>(plane_wide,quant,device_cosine,wide[c],pw,ph,bx[c],by[c]);check(hipGetLastError(),"wide FDCT");
            image_jpeg_encoder::forward_dct_quantize<<<(terms+255)/256,256>>>(plane_old,quant,device_cosine,original[c],pw,ph,bx[c],by[c]);check(hipGetLastError(),"original FDCT");
            output_pair(folder,("color"+std::to_string(c)).c_str(),plane_wide,plane_old,pixels);
            output_pair(folder,("coeff"+std::to_string(c)).c_str(),wide[c],original[c],terms);
        }
        jpeg_destroy_compress(&jpeg);
        const int mx=(width+sampling*8-1)/(sampling*8),my=(height+sampling*8-1)/(sampling*8),blocks=mx*my*(sampling==2?6:3);
        if(size_t(blocks)*64>INT_MAX)throw std::runtime_error("legacy gather index range exceeded");
        auto* scan_wide=memory.make<short>(size_t(blocks)*64);auto* scan_old=memory.make<short>(size_t(blocks)*64);
        auto* prev_wide=memory.make<int>(blocks);auto* prev_old=memory.make<int>(blocks);
        auto* comp_wide=memory.make<unsigned char>(blocks);auto* comp_old=memory.make<unsigned char>(blocks);
        image_jpeg_wide::gather_mcu_coefficients<<<(size_t(blocks)*64+255)/256,256>>>(wide[0],wide[1],wide[2],scan_wide,prev_wide,comp_wide,bx[0],by[0],bx[1],by[1],mx,my,sampling);check(hipGetLastError(),"wide gather");
        image_jpeg_full::gather_mcu_coefficients<<<(size_t(blocks)*64+255)/256,256>>>(original[0],original[1],original[2],scan_old,prev_old,comp_old,bx[0],by[0],bx[1],by[1],mx,mx*my,sampling);check(hipGetLastError(),"original gather");
        output_pair(folder,"scan",scan_wide,scan_old,size_t(blocks)*64);
        output_pair(folder,"previous",prev_wide,prev_old,blocks);output_pair(folder,"component",comp_wide,comp_old,blocks);
        std::cout<<"{\"arrays\":9,\"width\":"<<width<<",\"height\":"<<height<<",\"sampling\":"<<sampling<<"}\n";return 0;
    }catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
