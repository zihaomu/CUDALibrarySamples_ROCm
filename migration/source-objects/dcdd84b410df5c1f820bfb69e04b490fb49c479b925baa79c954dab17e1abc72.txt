// SPDX-License-Identifier: Apache-2.0
// One 32-lane wave cooperates on the 25 lanes of the Keccak state.
#include "check.hpp"
#include <cstdint>
using namespace sample;
__device__ uint64_t rot(uint64_t x,unsigned r){return r?((x<<r)|(x>>(64-r))):x;}
__device__ uint64_t lane(uint64_t x,int src){return uint64_t(__shfl(uint32_t(x),src,32))|(uint64_t(__shfl(uint32_t(x>>32),src,32))<<32);}
__global__ void sha3(uint8_t* out,const uint8_t* msg,size_t n){
 int l=threadIdx.x,x=l%5,y=l/5;uint64_t a=0;
 const uint64_t rc[24]={0x0000000000000001ULL,0x0000000000008082ULL,0x800000000000808aULL,0x8000000080008000ULL,0x000000000000808bULL,0x0000000080000001ULL,0x8000000080008081ULL,0x8000000000008009ULL,0x000000000000008aULL,0x0000000000000088ULL,0x0000000080008009ULL,0x000000008000000aULL,0x000000008000808bULL,0x800000000000008bULL,0x8000000000008089ULL,0x8000000000008003ULL,0x8000000000008002ULL,0x8000000000000080ULL,0x000000000000800aULL,0x800000008000000aULL,0x8000000080008081ULL,0x8000000000008080ULL,0x0000000080000001ULL,0x8000000080008008ULL};
 const unsigned rotations[25]={0,1,62,28,27,36,44,6,55,20,3,10,43,25,39,41,45,15,21,8,18,2,61,56,14};
 size_t total=(n/136+1)*136;
 for(size_t base=0;base<total;base+=136){uint64_t v=0;if(l<17)for(int j=0;j<8;++j){size_t idx=base+l*8+j;uint8_t b=idx<n?msg[idx]:idx==n?6:0;if(idx==total-1)b^=0x80;v|=uint64_t(b)<<(8*j);}a^=v;
  for(int r=0;r<24;++r){uint64_t c[5];for(int i=0;i<5;++i)c[i]=lane(a,i)^lane(a,i+5)^lane(a,i+10)^lane(a,i+15)^lane(a,i+20);uint64_t t=rot(a^c[(x+4)%5]^rot(c[(x+1)%5],1),rotations[l<25?l:0]);uint64_t b=lane(t,(x+3*y)%5+5*x);uint64_t one=lane(b,(x+1)%5+5*(y%5)),two=lane(b,(x+2)%5+5*(y%5));a=b^((~one)&two);if(l==0)a^=rc[r];}
 }if(l<4)for(int j=0;j<8;++j)out[l*8+j]=a>>(8*j);
}
int main(int argc,char**argv){return run([&]{if(argc!=2)throw std::runtime_error("input file required");std::ifstream f(argv[1],std::ios::binary);std::vector<uint8_t> h((std::istreambuf_iterator<char>(f)),{});Device<uint8_t> msg(h),out(32);sha3<<<1,32>>>(out.p,msg.p,h.size());CHECK(hipGetLastError());CHECK(hipDeviceSynchronize());auto bytes=out.get();for(auto b:bytes)std::cout<<std::hex<<std::setw(2)<<std::setfill('0')<<int(b);std::cout<<std::endl;});}
