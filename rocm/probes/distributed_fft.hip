// SPDX-License-Identifier: Apache-2.0
// Two 128-point even/odd FFTs plus RCCL exchange and a GPU radix-2 merge.
#include "check.hpp"
#include "binary_observe.hpp"
#include <hipfft/hipfft.h>
#include <rccl/rccl.h>
#include <random>
using namespace sample;
__global__ void merge(const hipfftComplex* all,hipfftComplex* out,int rank){int k=threadIdx.x;if(k>=128)return;float angle=-2*3.14159265358979323846f*k/256;float co=__builtin_cosf(angle),si=__builtin_sinf(angle);auto e=all[k],o=all[128+k];float sign=rank? -1.f:1.f;out[k]={e.x+sign*(co*o.x-si*o.y),e.y+sign*(co*o.y+si*o.x)};}
int main(){return run([]{
 int count;CHECK(hipGetDeviceCount(&count));if(count!=2)throw std::runtime_error("requires exactly 2 allowed GPUs");std::mt19937 gen(3);std::uniform_real_distribution<float>dis(0,1);std::vector<hipfftComplex>input(256);for(auto&z:input){z.x=dis(gen);z.y=dis(gen);}std::vector<float>ref(512);for(int k=0;k<256;++k){std::complex<double>sum=0;for(int j=0;j<256;++j){double a=-2*3.14159265358979323846*j*k/256;sum+=std::complex<double>(input[j].x,input[j].y)*std::complex<double>(cos(a),sin(a));}ref[2*k]=sum.real();ref[2*k+1]=sum.imag();}
 ncclComm_t comm[2];int devices[2]={0,1};CHECK(ncclCommInitAll(comm,2,devices));hipfftHandle plan[2];hipStream_t streams[2];hipfftComplex *local[2],*all[2],*out[2];
 for(int r=0;r<2;++r){CHECK(hipSetDevice(r));CHECK(hipStreamCreate(&streams[r]));CHECK(hipfftPlan1d(&plan[r],128,HIPFFT_C2C,1));CHECK(hipfftSetStream(plan[r],streams[r]));CHECK(hipMalloc(&local[r],128*sizeof(hipfftComplex)));CHECK(hipMalloc(&all[r],256*sizeof(hipfftComplex)));CHECK(hipMalloc(&out[r],128*sizeof(hipfftComplex)));std::vector<hipfftComplex>x(128);for(int i=0;i<128;++i)x[i]=input[2*i+r];CHECK(hipMemcpy(local[r],x.data(),x.size()*sizeof(x[0]),hipMemcpyHostToDevice));CHECK(hipfftExecC2C(plan[r],local[r],local[r],HIPFFT_FORWARD));}
 CHECK(ncclGroupStart());for(int r=0;r<2;++r){CHECK(hipSetDevice(r));CHECK(ncclAllGather(local[r],all[r],256,ncclFloat,comm[r],streams[r]));}CHECK(ncclGroupEnd());
 std::vector<float>got(512);for(int r=0;r<2;++r){CHECK(hipSetDevice(r));merge<<<1,128,0,streams[r]>>>(all[r],out[r],r);CHECK(hipGetLastError());CHECK(hipStreamSynchronize(streams[r]));CHECK(hipMemcpy(got.data()+256*r,out[r],128*sizeof(hipfftComplex),hipMemcpyDeviceToHost));CHECK(hipfftDestroy(plan[r]));CHECK(ncclCommDestroy(comm[r]));CHECK(hipFree(local[r]));CHECK(hipFree(all[r]));CHECK(hipFree(out[r]));CHECK(hipStreamDestroy(streams[r]));}
 report("original-n256-seed3-two-gpu-fft-cpu-dft",got,ref,3e-5,3e-5);if(std::getenv("MIGRATION_OUTPUT_DIR")){migration_binary::emit("input.bin",input.data(),input.size()*sizeof(input[0]));migration_binary::emit("output.bin",got.data(),got.size()*sizeof(float));}
});}
