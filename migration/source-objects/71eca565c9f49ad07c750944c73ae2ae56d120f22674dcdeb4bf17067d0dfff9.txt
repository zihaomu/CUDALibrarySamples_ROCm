// SPDX-License-Identifier: Apache-2.0
#include "crc_benchmark_compat.hpp"
int main(){try{
 const uint64_t lengths[]={1,256,1024,(uint64_t(1)<<32)-1,uint64_t(1)<<32,uint64_t(1)<<35};uint32_t*a,*b,*m;cb_check(hipMalloc(&a,8));cb_check(hipMalloc(&b,4));cb_check(hipMalloc(&m,128));
 std::vector<uint64_t>observed;for(uint64_t length:lengths){uint32_t input[]={0x01234567u,0x89abcdefu},matrix[32],out;for(int i=0;i<32;++i)matrix[i]=crc_benchmark::shift(uint32_t(1)<<i,length);cb_check(hipMemcpy(a,input,8,hipMemcpyHostToDevice));cb_check(hipMemcpy(m,matrix,128,hipMemcpyHostToDevice));crc_benchmark::combine_kernel<<<1,1>>>(a,b,1,2,m);cb_check(hipGetLastError());cb_check(hipMemcpy(&out,b,4,hipMemcpyDeviceToHost));observed.insert(observed.end(),{length,input[0],input[1],out});}
 std::ofstream f(cb_root()+"/lengths.bin",std::ios::binary);f.write((char*)observed.data(),observed.size()*8);cb_check(hipFree(a));cb_check(hipFree(b));cb_check(hipFree(m));return f?0:1;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
