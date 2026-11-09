// SPDX-License-Identifier: Apache-2.0
#include "check.hpp"
#include <hipblas/hipblas.h>
#include <chrono>
using namespace sample;
template<class T>hipblasStatus_t gemm(hipblasHandle_t h,int n,const T*alpha,const T*a,const T*b,const T*beta,T*c);
template<>hipblasStatus_t gemm<float>(hipblasHandle_t h,int n,const float*alpha,const float*a,const float*b,const float*beta,float*c){return hipblasSgemm(h,HIPBLAS_OP_N,HIPBLAS_OP_N,n,n,n,alpha,a,n,b,n,beta,c,n);}
template<>hipblasStatus_t gemm<double>(hipblasHandle_t h,int n,const double*alpha,const double*a,const double*b,const double*beta,double*c){return hipblasDgemm(h,HIPBLAS_OP_N,HIPBLAS_OP_N,n,n,n,alpha,a,n,b,n,beta,c,n);}
template<class T>void measure(int n,const char*dtype){
 hipblasHandle_t h;CHECK(hipblasCreate(&h));Stream stream;CHECK(hipblasSetStream(h,stream.p));
 #if defined(__HIP_PLATFORM_AMD__)
 CHECK(hipblasSetMathMode(h,HIPBLAS_DEFAULT_MATH));
 #else
 CHECK(hipblasSetMathMode(h,CUBLAS_PEDANTIC_MATH));
 #endif
 std::vector<T>a(n*n),b(n*n);for(int j=0;j<n;j++)for(int i=0;i<n;i++){a[i+j*n]=T(((i*13+j*7)%29)/31.0-0.5);b[i+j*n]=T(((i*3+j*11)%23)/27.0-0.5);}
 Device<T> da(a),db(b),dc(size_t(n)*n);T alpha=1,beta=0;
 CHECK(gemm(h,n,&alpha,da.p,db.p,&beta,dc.p));CHECK(hipStreamSynchronize(stream.p));auto c=dc.get();double maxerr=0;
 for(int p=0;p<16;p++){int i=(p*113)%n,j=(p*197+3)%n;long double ref=0;for(int k=0;k<n;k++)ref+=static_cast<long double>(a[i+k*n])*b[k+j*n];double err=std::abs(double(c[i+j*n])-double(ref));double tol=sizeof(T)==4?1e-4:1e-10;if(!std::isfinite(double(c[i+j*n]))||err>tol+tol*std::abs(double(ref)))throw std::runtime_error("benchmark correctness failed");maxerr=std::max(maxerr,err);}
 int warmup=0;auto warmstart=std::chrono::steady_clock::now();do{for(int i=0;i<32;i++){CHECK(gemm(h,n,&alpha,da.p,db.p,&beta,dc.p));++warmup;}CHECK(hipStreamSynchronize(stream.p));}while(std::chrono::duration<double>(std::chrono::steady_clock::now()-warmstart).count()<1.0);
 hipEvent_t begin,end;CHECK(hipEventCreate(&begin));CHECK(hipEventCreate(&end));
 std::vector<double> all,medians;double wall_total=0;
 for(int group=0;group<3;group++){std::vector<double> times;auto start=std::chrono::steady_clock::now();for(int it=0;it<100;it++){
 CHECK(hipEventRecord(begin,stream.p));CHECK(gemm(h,n,&alpha,da.p,db.p,&beta,dc.p));CHECK(hipEventRecord(end,stream.p));CHECK(hipEventSynchronize(end));float ms=0;CHECK(hipEventElapsedTime(&ms,begin,end));times.push_back(ms);all.push_back(ms);}
 wall_total+=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();std::sort(times.begin(),times.end());medians.push_back(times[times.size()/2]);}
 std::sort(all.begin(),all.end());double median=all[all.size()/2],p95=all[size_t(all.size()*0.95)];
 std::cout<<std::setprecision(17)<<"{\"benchmark\":\"gemm\",\"dtype\":\""<<dtype<<"\",\"n\":"<<n<<",\"warmup\":"<<warmup<<",\"minimum_warmup_ms\":1000,\"groups\":3,\"iterations_per_group\":100,\"gpu_median_ms\":"<<median<<",\"gpu_p95_ms\":"<<p95<<",\"wall_mean_ms\":"<<wall_total/300<<",\"tflops\":"<<2.*n*n*n/(median*1.e9)<<",\"max_reference_error\":"<<maxerr<<",\"group_medians_ms\":["<<medians[0]<<','<<medians[1]<<','<<medians[2]<<"]}"<<std::endl;
 CHECK(hipEventDestroy(begin));CHECK(hipEventDestroy(end));CHECK(hipblasDestroy(h));
}
int main(){return run([]{for(int n:{256,1024,2048}){measure<float>(n,"fp32");measure<double>(n,"fp64");}});}
