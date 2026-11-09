// SPDX-License-Identifier: Apache-2.0
// ORIGINAL_PROFILE_IMPLEMENTED
// ROCm implementation of cuRAND/Host/philox/normal; calls remain explicit for comparison.
#include "check.hpp"
#include <hiprand/hiprand.h>
using namespace sample;
int main(){return run([]{
Stream stream;int n=65536;
 {std::vector<double> bounds;for(bool host:{false,true}){std::vector<float> first;for(int repeat=0;repeat<2;repeat++){hiprandGenerator_t gen;CHECK(host?hiprandCreateGeneratorHost(&gen,HIPRAND_RNG_PSEUDO_PHILOX4_32_10):hiprandCreateGenerator(&gen,HIPRAND_RNG_PSEUDO_PHILOX4_32_10));CHECK(hiprandSetStream(gen,stream.p));CHECK(hiprandSetGeneratorOffset(gen,0));CHECK(hiprandSetGeneratorOrdering(gen,HIPRAND_ORDERING_PSEUDO_BEST));CHECK(hiprandSetPseudoRandomGeneratorSeed(gen,1234));Device<float>d(12);std::vector<float>x(12);float*dest=host?x.data():d.p;CHECK(hiprandGenerateNormal(gen,dest,12,0.f,1.f));CHECK(hipStreamSynchronize(stream.p));if(!host)x=d.get();CHECK(hiprandDestroyGenerator(gen));for(float v:x)if(!std::isfinite(v) )throw std::runtime_error("original RNG range");if(repeat==0)first=x;else if(first!=x)throw std::runtime_error("original RNG reproducibility");}bounds.push_back(1.);}report("original_profile",bounds,std::vector<double>{1,1},0,0);}
 for(bool host:{false,true})for(unsigned long long offset:{0ULL,16ULL}){
 std::vector<float> first;
 for(int repeat=0;repeat<2;repeat++){
 hiprandGenerator_t gen;CHECK(host?hiprandCreateGeneratorHost(&gen,HIPRAND_RNG_PSEUDO_PHILOX4_32_10):hiprandCreateGenerator(&gen,HIPRAND_RNG_PSEUDO_PHILOX4_32_10));
 CHECK(hiprandSetStream(gen,stream.p));CHECK(hiprandSetGeneratorOffset(gen,offset));CHECK(hiprandSetGeneratorOrdering(gen,HIPRAND_ORDERING_PSEUDO_BEST));CHECK(hiprandSetPseudoRandomGeneratorSeed(gen,1234ULL));
 Device<float> device(n);std::vector<float> out(n);float* dest=host?out.data():device.p;
 CHECK(hiprandGenerateNormal(gen,dest,n,0.f,1.f));
 CHECK(hipStreamSynchronize(stream.p));if(!host)out=device.get();CHECK(hiprandDestroyGenerator(gen));
 double mean=0,second=0;for(float x:out){if(!std::isfinite(x) )throw std::runtime_error("RNG invalid value");mean+=x;second+=double(x)*x;}mean/=n;second=second/n-mean*mean;
 if(std::abs(mean-0.)>0.02||std::abs(second-1.)>0.04)throw std::runtime_error("RNG statistics failed");
 if(repeat==0)first=out;else if(out!=first)throw std::runtime_error("RNG seed+offset reproducibility failed");
 if(repeat==1)report("host"+std::to_string(host)+"_offset"+std::to_string(offset),std::vector<double>{mean,second},std::vector<double>{0.,1.},0.04,0);
 }
 }
});}
