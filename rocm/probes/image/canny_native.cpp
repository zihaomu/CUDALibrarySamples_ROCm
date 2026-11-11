// SPDX-License-Identifier: Apache-2.0
#include <cuda_runtime.h>
#ifdef IMAGE_NPP_PLUS
#define NPP_PLUS_ENABLE
#include <nppPlus/nppPlus.h>
#include <nppi.h>
using namespace nppPlusV;
#else
#include <npp.h>
#endif
#include <fstream>
#include <iostream>
#include <vector>
#include <stdexcept>
#include <cstdlib>
static void check(int status,const char* operation){if(status)throw std::runtime_error(std::string(operation)+" status="+std::to_string(status));}
static void emit(const std::string& p,const void* data,size_t n){std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),n);if(!f)throw std::runtime_error("output "+p);}
int main(int argc,char** argv){try{
 if(argc!=3)throw std::runtime_error("expected input/output directories");std::string in=argv[1],out=argv[2];int W,H,C,pitch,x,y,w,h,low,high,opitch;std::ifstream config(in+"/params.txt");if(!(config>>W>>H>>C>>pitch>>x>>y>>w>>h>>low>>high>>opitch))throw std::runtime_error("params");
 std::ifstream raw(in+"/input.bin",std::ios::binary);std::vector<unsigned char> input((std::istreambuf_iterator<char>(raw)),{}),output(size_t(opitch)*h,173);if(input.size()!=size_t(pitch)*H)throw std::runtime_error("input size");unsigned char *a=nullptr,*b=nullptr,*scratch=nullptr;cudaStream_t stream{};check(cudaStreamCreate(&stream),"stream-create");check(cudaMalloc(&a,input.size()),"allocate-input");check(cudaMalloc(&b,output.size()),"allocate-output");check(cudaMemcpyAsync(a,input.data(),input.size(),cudaMemcpyHostToDevice,stream),"input-copy");check(cudaMemcpyAsync(b,output.data(),output.size(),cudaMemcpyHostToDevice,stream),"output-sentinel");
 NppStreamContext ctx{};cudaDeviceProp prop{};check(cudaGetDevice(&ctx.nCudaDeviceId),"device");check(cudaGetDeviceProperties(&prop,ctx.nCudaDeviceId),"properties");ctx.hStream=stream;ctx.nMultiProcessorCount=prop.multiProcessorCount;ctx.nMaxThreadsPerMultiProcessor=prop.maxThreadsPerMultiProcessor;ctx.nMaxThreadsPerBlock=prop.maxThreadsPerBlock;ctx.nSharedMemPerBlock=prop.sharedMemPerBlock;ctx.nCudaDevAttrComputeCapabilityMajor=prop.major;ctx.nCudaDevAttrComputeCapabilityMinor=prop.minor;check(cudaStreamGetFlags(stream,&ctx.nStreamFlags),"stream-flags");
 int bytes=0;check(nppiFilterCannyBorderGetBufferSize(NppiSize{w,h},&bytes),"scratch-query");check(cudaMalloc(&scratch,bytes),"scratch-allocate");
 if(const char* fill=std::getenv("IMAGE_SCRATCH_FILL"))check(cudaMemsetAsync(scratch,std::atoi(fill),bytes,stream),"scratch-fill-investigation");
#ifdef IMAGE_NPP_PLUS
 if(C!=1)throw std::runtime_error("NPP+ sample uses C1");
 int status=nppiFilterCannyBorder_8u_C1R_Ctx(a,pitch,{W,H},{x,y},b,opitch,{w,h},NPP_FILTER_SOBEL,NPP_MASK_SIZE_3_X_3,(Npp16s)low,(Npp16s)high,nppiNormL2,NPP_BORDER_REPLICATE,scratch,ctx);
#else
 int status=C==1?nppiFilterCannyBorder_8u_C1R_Ctx(a,pitch,{W,H},{x,y},b,opitch,{w,h},NPP_FILTER_SOBEL,NPP_MASK_SIZE_3_X_3,(Npp16s)low,(Npp16s)high,nppiNormL2,NPP_BORDER_REPLICATE,scratch,ctx):nppiFilterCannyBorder_8u_C3C1R_Ctx(a,pitch,{W,H},{x,y},b,opitch,{w,h},NPP_FILTER_SOBEL,NPP_MASK_SIZE_3_X_3,(Npp16s)low,(Npp16s)high,nppiNormL2,NPP_BORDER_REPLICATE,scratch,ctx);
#endif
 check(status,"native-canny");check(cudaStreamSynchronize(stream),"decode-sync");check(cudaMemcpy(output.data(),b,output.size(),cudaMemcpyDeviceToHost),"output-copy");emit(out+"/output.bin",output.data(),output.size());char pci[64]{};check(cudaDeviceGetPCIBusId(pci,64,ctx.nCudaDeviceId),"PCI");std::ofstream meta(out+"/native.json");meta<<"{\"status\":"<<status<<",\"context_bytes\":"<<sizeof(ctx)<<",\"scratch_bytes\":"<<bytes<<",\"pci\":\""<<pci<<"\",\"device\":\""<<prop.name<<"\"}\n";
 if(std::getenv("IMAGE_GRADIENT_OUTPUT")){
  Npp16s *gx=nullptr,*gy=nullptr,*mag=nullptr;Npp32f* angle=nullptr;size_t count=size_t(w)*h;
  check(cudaMalloc(&gx,count*2),"gradient-x");check(cudaMalloc(&gy,count*2),"gradient-y");check(cudaMalloc(&mag,count*2),"gradient-mag");check(cudaMalloc(&angle,count*4),"gradient-angle");
#ifdef IMAGE_NPP_PLUS
  int gs=nppiGradientVectorSobelBorder_Ctx(NPP_8U,NPP_16S,NPP_CH_1,a,pitch,{W,H},{x,y},gx,w*2,gy,w*2,mag,w*2,angle,w*4,{w,h},NPP_MASK_SIZE_3_X_3,nppiNormL2,NPP_BORDER_REPLICATE,ctx);
#else
  int gs=C==1?nppiGradientVectorSobelBorder_8u16s_C1R_Ctx(a,pitch,{W,H},{x,y},gx,w*2,gy,w*2,mag,w*2,angle,w*4,{w,h},NPP_MASK_SIZE_3_X_3,nppiNormL2,NPP_BORDER_REPLICATE,ctx):nppiGradientVectorSobelBorder_8u16s_C3C1R_Ctx(a,pitch,{W,H},{x,y},gx,w*2,gy,w*2,mag,w*2,angle,w*4,{w,h},NPP_MASK_SIZE_3_X_3,nppiNormL2,NPP_BORDER_REPLICATE,ctx);
#endif
  check(gs,"native-gradient");check(cudaStreamSynchronize(stream),"gradient-sync");std::vector<unsigned char> bytes(count*4);
  for(auto entry:std::vector<std::pair<std::string,std::pair<void*,size_t>>>{{"x",{gx,count*2}},{"y",{gy,count*2}},{"magnitude",{mag,count*2}},{"angle",{angle,count*4}}}){check(cudaMemcpy(bytes.data(),entry.second.first,entry.second.second,cudaMemcpyDeviceToHost),"gradient-copy");emit(out+"/native-"+entry.first+".bin",bytes.data(),entry.second.second);}
  check(cudaFree(gx),"free-gx");check(cudaFree(gy),"free-gy");check(cudaFree(mag),"free-mag");check(cudaFree(angle),"free-angle");
 }
 check(cudaFree(scratch),"free-scratch");check(cudaFree(a),"free-input");check(cudaFree(b),"free-output");check(cudaStreamDestroy(stream),"destroy-stream");return 0;
 }catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
