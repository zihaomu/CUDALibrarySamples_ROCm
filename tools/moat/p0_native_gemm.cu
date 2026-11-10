#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cstdio>
#define C(x) do{int rc=(int)(x);if(rc){std::fprintf(stderr,"%s %d\n",#x,rc);return 1;}}while(0)
int main(){double a[4]={1,3,2,4},b[4]={5,7,6,8},out[4],*aa,*bb,*cc;C(cudaMalloc(&aa,32));C(cudaMalloc(&bb,32));C(cudaMalloc(&cc,32));C(cudaMemcpy(aa,a,32,cudaMemcpyHostToDevice));C(cudaMemcpy(bb,b,32,cudaMemcpyHostToDevice));cublasHandle_t h;C(cublasCreate(&h));double one=1,zero=0;C(cublasDgemm(h,CUBLAS_OP_N,CUBLAS_OP_N,2,2,2,&one,aa,2,bb,2,&zero,cc,2));C(cudaDeviceSynchronize());C(cudaMemcpy(out,cc,32,cudaMemcpyDeviceToHost));std::printf("{\"case\":\"original_profile\",\"values\":[%.17g,%.17g,%.17g,%.17g]}\n",out[0],out[1],out[2],out[3]);C(cublasDestroy(h));C(cudaFree(aa));C(cudaFree(bb));C(cudaFree(cc));return 0;}
