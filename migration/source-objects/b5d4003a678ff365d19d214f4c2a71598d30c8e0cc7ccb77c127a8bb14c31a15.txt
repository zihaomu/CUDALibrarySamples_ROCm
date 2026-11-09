// SPDX-License-Identifier: Apache-2.0
// Educational SHA-256 device implementation; correctness is checked by hashlib.
#include "check.hpp"
#include <cstdint>
using namespace sample;
__device__ uint32_t rr(uint32_t x,unsigned r){return (x>>r)|(x<<(32-r));}
__global__ void sha256(uint8_t* out,const uint8_t* msg,size_t n){
 if(threadIdx.x)return;
 const uint32_t K[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
 uint32_t H[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};size_t total=((n+9+63)/64)*64;
 for(size_t base=0;base<total;base+=64){uint32_t w[64]={};for(int j=0;j<64;++j){size_t i=base+j;uint8_t byte=i<n?msg[i]:i==n?0x80:0;if(i>=total-8)byte=uint64_t(n*8)>>(8*(total-1-i));w[j/4]|=uint32_t(byte)<<(24-8*(j%4));}
 for(int t=16;t<64;++t){uint32_t x=w[t-15],y=w[t-2];w[t]=w[t-16]+(rr(x,7)^rr(x,18)^(x>>3))+w[t-7]+(rr(y,17)^rr(y,19)^(y>>10));}
 uint32_t a=H[0],b=H[1],c=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7];for(int t=0;t<64;++t){uint32_t z=h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^((~e)&g))+K[t]+w[t];uint32_t q=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c));h=g;g=f;f=e;e=d+z;d=c;c=b;b=a;a=z+q;}H[0]+=a;H[1]+=b;H[2]+=c;H[3]+=d;H[4]+=e;H[5]+=f;H[6]+=g;H[7]+=h;}
 for(int j=0;j<32;++j)out[j]=H[j/4]>>(24-8*(j%4));
}
int main(int argc,char**argv){return run([&]{if(argc!=2)throw std::runtime_error("input file required");std::ifstream f(argv[1],std::ios::binary);std::vector<uint8_t> h((std::istreambuf_iterator<char>(f)),{});Device<uint8_t> msg(h),out(32);sha256<<<1,32>>>(out.p,msg.p,h.size());CHECK(hipGetLastError());CHECK(hipDeviceSynchronize());auto bytes=out.get();for(auto b:bytes)std::cout<<std::hex<<std::setw(2)<<std::setfill('0')<<int(b);std::cout<<std::endl;});}
