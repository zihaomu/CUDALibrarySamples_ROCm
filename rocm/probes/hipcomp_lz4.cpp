// SPDX-License-Identifier: Apache-2.0
#include "check.hpp"
#include <hipcomp/lz4.h>
using namespace sample;
int main(){return run([]{
 for(size_t count:{size_t(128),size_t(32768),size_t(65536)}){
  std::vector<unsigned char> h(count);for(size_t i=0;i<count;++i)h[i]=(i/17+i%5)%127;
  Device<unsigned char> input(h),output(count);size_t temp=0,maxout=0,dt=0;
  CHECK(hipcompBatchedLZ4CompressGetTempSize(1,count,hipcompBatchedLZ4DefaultOpts,&temp));
  CHECK(hipcompBatchedLZ4CompressGetMaxOutputChunkSize(count,hipcompBatchedLZ4DefaultOpts,&maxout));
  Device<unsigned char> workspace(temp),compressed(maxout);Device<const void*> ins(std::vector<const void*>{input.p});Device<void*> cs(std::vector<void*>{compressed.p}),outs(std::vector<void*>{output.p});Device<size_t> sizes(std::vector<size_t>{count}),compressed_sizes(1),actual(1);Device<hipcompStatus_t> status(1);
  CHECK(hipcompBatchedLZ4CompressAsync(ins.p,sizes.p,count,1,workspace.p,temp,cs.p,compressed_sizes.p,hipcompBatchedLZ4DefaultOpts,0));CHECK(hipDeviceSynchronize());
  CHECK(hipcompBatchedLZ4DecompressGetTempSize(1,count,&dt));Device<unsigned char> dw(dt);
  CHECK(hipcompBatchedLZ4DecompressAsync((const void* const*)cs.p,compressed_sizes.p,sizes.p,actual.p,1,dw.p,dt,outs.p,status.p,0));CHECK(hipDeviceSynchronize());
  if(int(status.get()[0])||actual.get()[0]!=count)throw std::runtime_error("LZ4 chunk status/size failure");
  report("lz4-roundtrip-"+std::to_string(count),output.get(),h,0,0);
 }
});}
