// SPDX-License-Identifier: Apache-2.0
#include "check.hpp"
#include <rccl/rccl.h>
#include <hipblas/hipblas.h>
using namespace sample;
int main(){return run([]{
 int count=0;CHECK(hipGetDeviceCount(&count));if(count!=2)throw std::runtime_error("requires exactly two qualified devices");int devices[2]={0,1};ncclComm_t comm[2];CHECK(ncclCommInitAll(comm,2,devices));hipStream_t streams[2];hipblasHandle_t handles[2];float *a[2],*b[2],*c[2],*g[2];
 std::vector<float>B={1,2,3,4,5,6};
 for(int rank=0;rank<2;++rank){CHECK(hipSetDevice(rank));CHECK(hipStreamCreate(&streams[rank]));CHECK(hipblasCreate(&handles[rank]));CHECK(hipblasSetStream(handles[rank],streams[rank]));CHECK(hipMalloc(&a[rank],6*sizeof(float)));CHECK(hipMalloc(&b[rank],6*sizeof(float)));CHECK(hipMalloc(&c[rank],4*sizeof(float)));CHECK(hipMalloc(&g[rank],8*sizeof(float)));std::vector<float>A(6);for(int k=0;k<3;++k)for(int i=0;i<2;++i)A[i+2*k]=1+rank*2+i+4*k;CHECK(hipMemcpy(a[rank],A.data(),24,hipMemcpyHostToDevice));CHECK(hipMemcpy(b[rank],B.data(),24,hipMemcpyHostToDevice));float alpha=1,beta=0;CHECK(hipblasSgemm(handles[rank],HIPBLAS_OP_N,HIPBLAS_OP_N,2,2,3,&alpha,a[rank],2,b[rank],3,&beta,c[rank],2));}
 CHECK(ncclGroupStart());for(int rank=0;rank<2;++rank){CHECK(hipSetDevice(rank));CHECK(ncclAllGather(c[rank],g[rank],4,ncclFloat,comm[rank],streams[rank]));}CHECK(ncclGroupEnd());
 std::vector<float> expected(8);for(int r=0;r<2;++r)for(int j=0;j<2;++j)for(int i=0;i<2;++i){float z=0;for(int k=0;k<3;++k)z+=(1+r*2+i+4*k)*B[k+3*j];expected[r*4+i+2*j]=z;}
 for(int rank=0;rank<2;++rank){CHECK(hipSetDevice(rank));CHECK(hipStreamSynchronize(streams[rank]));std::vector<float>actual(8);CHECK(hipMemcpy(actual.data(),g[rank],32,hipMemcpyDeviceToHost));report("distributed-row-gemm-rank"+std::to_string(rank),actual,expected,0,0);CHECK(ncclCommDestroy(comm[rank]));CHECK(hipblasDestroy(handles[rank]));CHECK(hipFree(a[rank]));CHECK(hipFree(b[rank]));CHECK(hipFree(c[rank]));CHECK(hipFree(g[rank]));CHECK(hipStreamDestroy(streams[rank]));}
});}
