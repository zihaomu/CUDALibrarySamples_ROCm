// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <hip/hip_runtime.h>
#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#define CHECK(call) do { auto status_=(call); if (int(status_)!=0) throw std::runtime_error(std::string(#call)+" status="+std::to_string(int(status_))+" line="+std::to_string(__LINE__)); } while(0)
namespace sample {
template<class T> struct Device {
 T* p=nullptr; size_t n;
 explicit Device(size_t count):n(count){if(n)CHECK(hipMalloc(reinterpret_cast<void**>(&p),n*sizeof(T)));}
 explicit Device(const std::vector<T>& v):Device(v.size()){CHECK(hipMemcpy(p,v.data(),n*sizeof(T),hipMemcpyHostToDevice));}
 ~Device(){if(p)(void)hipFree(p);}
 Device(const Device&)=delete;Device& operator=(const Device&)=delete;
 std::vector<T> get() const {std::vector<T> v(n);CHECK(hipMemcpy(v.data(),p,n*sizeof(T),hipMemcpyDeviceToHost));return v;}
};
struct Stream {hipStream_t p;Stream(){CHECK(hipStreamCreateWithFlags(&p,hipStreamNonBlocking));}~Stream(){(void)hipStreamDestroy(p);}};
template<class T> std::vector<T> input(size_t n,size_t offset=0){
 const char* path=std::getenv("MIGRATION_FIXTURE");if(!path)throw std::runtime_error("set MIGRATION_FIXTURE to m1-input.f64");
 std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("cannot open fixture");f.seekg(offset*sizeof(double));
 std::vector<double> raw(n);f.read(reinterpret_cast<char*>(raw.data()),n*sizeof(double));if(!f)throw std::runtime_error("short fixture");return std::vector<T>(raw.begin(),raw.end());
}
template<class T> void report(const std::string& id,const std::vector<T>& got,const std::vector<T>& ref,double atol=1e-10,double rtol=1e-10){
 if(got.size()!=ref.size())throw std::runtime_error("size mismatch");double maxerr=0;
 for(size_t i=0;i<got.size();++i){double x=double(got[i]),y=double(ref[i]);if(!std::isfinite(x)||!std::isfinite(y)||std::abs(x-y)>atol+rtol*std::abs(y))throw std::runtime_error(id+" mismatch at "+std::to_string(i)+" actual="+std::to_string(x)+" ref="+std::to_string(y));maxerr=std::max(maxerr,std::abs(x-y));}
 std::cout<<std::setprecision(17)<<"{\"case\":\""<<id<<"\",\"passed\":true,\"max_abs_error\":"<<maxerr<<",\"values\":[";
 for(size_t i=0;i<got.size();++i){if(i)std::cout<<',';std::cout<<double(got[i]);}std::cout<<"]}"<<std::endl;
}
template<class F> int run(F fn){try{fn();CHECK(hipDeviceSynchronize());return 0;}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}
}
