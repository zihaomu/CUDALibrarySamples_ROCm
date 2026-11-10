#include <hip/hip_runtime.h>
#include <hipblas/hipblas.h>
#include <cstdio>
int main(){hipblasHandle_t h;if(hipblasCreate(&h))return 2;int8_t*a,*b;int*c;
 if(hipMalloc(&a,16)||hipMalloc(&b,16)||hipMalloc(&c,64))return 3;
 int8_t data[16];for(int i=0;i<16;++i)data[i]=i;
 if(hipMemcpy(a,data,16,hipMemcpyHostToDevice)||hipMemcpy(b,data,16,hipMemcpyHostToDevice))return 4;
 int one=1,zero=0;auto status=hipblasGemmEx(h,HIPBLAS_OP_N,HIPBLAS_OP_N,4,4,4,&one,a,HIP_R_8I,4,b,HIP_R_8I,4,&zero,c,HIP_R_32I,4,HIPBLAS_COMPUTE_32I,HIPBLAS_GEMM_DEFAULT);
 std::printf("{\"api\":\"hipblasGemmEx\",\"m\":4,\"n\":4,\"k\":4,\"status\":%d}\n",int(status));
 if(status==0){int out[16];if(hipDeviceSynchronize()||hipMemcpy(out,c,64,hipMemcpyDeviceToHost))return 5;for(int i=0;i<16;++i)std::printf("%d%c",out[i],i==15?'\n':' ');}
 (void)hipFree(a);(void)hipFree(b);(void)hipFree(c);(void)hipblasDestroy(h);return 0;}
