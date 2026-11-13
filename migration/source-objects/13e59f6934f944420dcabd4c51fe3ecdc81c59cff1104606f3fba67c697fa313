// SPDX-License-Identifier: Apache-2.0
#include "image/jpeg_wide_transform.hpp"
#include <fstream>
#include <iostream>
#include <array>
#include <cmath>
int main(int argc,char**argv) {
    using image_jpeg_encoder::check;
    try {
        if(argc!=2)throw std::runtime_error("usage: frozen DC input pairs");
        std::ifstream input(argv[1]);if(!input)throw std::runtime_error("missing cases");
        unsigned char* plane=nullptr;short* coefficients=nullptr;unsigned short* quant=nullptr;float* cosines=nullptr;
        check(hipMalloc(&plane,64),"plane");check(hipMalloc(&coefficients,128),"coefficients");check(hipMalloc(&quant,128),"quant");check(hipMalloc(&cosines,256),"cosines");
        std::array<float,64> table{};for(int x=0;x<8;++x)for(int u=0;u<8;++u)table[x*8+u]=std::cos((2*x+1)*u*std::acos(-1.0)/16);
        check(hipMemcpy(cosines,table.data(),256,hipMemcpyHostToDevice),"upload cosines");
        int q,sum;bool first=true;std::cout<<"[";
        while(input>>q>>sum) {
            if(q<1||q>255||sum< -8192||sum>8128)throw std::runtime_error("invalid frozen DC input");
            std::array<unsigned char,64> pixels{};const int total=sum+8192;
            for(int i=0;i<64;++i)pixels[i]=total/64+(i<total%64);
            std::array<unsigned short,64> qt{};qt.fill(q);std::array<short,64> output{};
            check(hipMemcpy(plane,pixels.data(),64,hipMemcpyHostToDevice),"upload plane");check(hipMemcpy(quant,qt.data(),128,hipMemcpyHostToDevice),"upload quant");
            hipLaunchKernelGGL(image_jpeg_wide::forward_dct_quantize,dim3(1),dim3(64),0,0,plane,quant,cosines,coefficients,8,8,1,1);
            check(hipGetLastError(),"DC launch");check(hipMemcpy(output.data(),coefficients,128,hipMemcpyDeviceToHost),"read coefficients");
            if(!first)std::cout<<',';first=false;std::cout<<"{\"quant\":"<<q<<",\"sum\":"<<sum<<",\"DC\":"<<output[0]<<"}";
        }
        std::cout<<"]\n";check(hipFree(plane),"free plane");check(hipFree(coefficients),"free coefficients");check(hipFree(quant),"free quant");check(hipFree(cosines),"free cosine");return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
