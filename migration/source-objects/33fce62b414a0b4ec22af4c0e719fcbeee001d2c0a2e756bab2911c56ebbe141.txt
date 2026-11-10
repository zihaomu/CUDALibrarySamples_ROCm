#include <cuda_runtime.h>
#include <cublasLt.h>
#include <cstdio>
#include <vector>
#define CHECK(x) do { int s=(int)(x); if(s){std::fprintf(stderr,"%s: %d\n",#x,s);return 1;} } while(0)
int main(){
  cublasLtHandle_t h; CHECK(cublasLtCreate(&h));
  cublasLtMatrixTransformDesc_t t; CHECK(cublasLtMatrixTransformDescCreate(&t,CUDA_R_32F));
  cublasLtMatrixLayout_t a,b; CHECK(cublasLtMatrixLayoutCreate(&a,CUDA_R_8I,8,32,8));
  CHECK(cublasLtMatrixLayoutCreate(&b,CUDA_R_8I,8,32,256));
  cublasLtOrder_t order=CUBLASLT_ORDER_COL4_4R2_8C;
  CHECK(cublasLtMatrixLayoutSetAttribute(b,CUBLASLT_MATRIX_LAYOUT_ORDER,&order,sizeof(order)));
  std::vector<signed char> in(256),out(256);for(int i=0;i<256;++i)in[i]=(signed char)i;
  signed char *ai,*bi;CHECK(cudaMalloc(&ai,256));CHECK(cudaMalloc(&bi,256));
  CHECK(cudaMemcpy(ai,in.data(),256,cudaMemcpyHostToDevice));float one=1,zero=0;
  CHECK(cublasLtMatrixTransform(h,t,&one,ai,a,&zero,nullptr,nullptr,bi,b,0));
  CHECK(cudaDeviceSynchronize());CHECK(cudaMemcpy(out.data(),bi,256,cudaMemcpyDeviceToHost));
  std::vector<int> map(256);for(int j=0;j<256;++j)map[(unsigned char)out[j]]=j;
  std::printf("{\"native_api\":\"cublasLtMatrixTransform\",\"map\":[");
  for(int j=0;j<256;++j)std::printf("%s%d",j?",":"",map[j]);std::puts("]}");
  CHECK(cudaFree(ai));CHECK(cudaFree(bi));CHECK(cublasLtMatrixLayoutDestroy(a));CHECK(cublasLtMatrixLayoutDestroy(b));
  CHECK(cublasLtMatrixTransformDescDestroy(t));CHECK(cublasLtDestroy(h));return 0;
}
