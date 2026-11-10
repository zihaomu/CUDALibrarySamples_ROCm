// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "observe.hpp"
#include "binary_observe.hpp"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <string>
#include <stdexcept>
#include <vector>
#ifdef __HIP_PLATFORM_AMD__
#include <hip/hip_runtime.h>
#include <hipblas.h>
#include <hipsparse.h>
#include <hipsolver.h>
#define MB_RT(x) hip##x
#define MB_BLAS(x) hipblas##x
#define MB_SPARSE(x) hipsparse##x
#define MB_SOLVER(x) hipsolverDn##x
#define MB_CONST(x) HIPBLAS_##x
#else
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cusparse.h>
#include <cusolverDn.h>
#define MB_RT(x) cuda##x
#define MB_BLAS(x) cublas##x
#define MB_SPARSE(x) cusparse##x
#define MB_SOLVER(x) cusolverDn##x
#define MB_CONST(x) CUBLAS_##x
#endif
#define MB_CHECK(call) do{auto status=(call);if(int(status)!=0)throw std::runtime_error(std::string(#call)+" status="+std::to_string(int(status)));}while(0)
namespace migration_batch {
inline std::string selected_case(){const char* s=std::getenv("MIGRATION_CASE");return s?s:"original";}
template<class T>struct Buffer{
 T* p=nullptr;size_t n;
 explicit Buffer(size_t count):n(count){MB_CHECK(MB_RT(Malloc)(reinterpret_cast<void**>(&p),std::max(size_t(1),n*sizeof(T))));}
 explicit Buffer(const std::vector<T>&v):Buffer(v.size()){put(v);}
 Buffer(const Buffer&)=delete;Buffer& operator=(const Buffer&)=delete;
 ~Buffer(){if(p)MB_RT(Free)(p);}
 void put(const std::vector<T>&v){if(v.size()>n)throw std::runtime_error("buffer overflow");MB_CHECK(MB_RT(Memcpy)(p,v.data(),v.size()*sizeof(T),MB_RT(MemcpyHostToDevice)));}
 std::vector<T> get()const{std::vector<T>v(n);MB_CHECK(MB_RT(Memcpy)(v.data(),p,n*sizeof(T),MB_RT(MemcpyDeviceToHost)));return v;}
};
template<class T>void emit(const char* name,const std::vector<T>& v){migration_observer::emit(name,v.data(),v.size());}
template<class T>void scalar(const char* name,T v){migration_observer::emit(name,&v,1);}
struct Blas{MB_BLAS(Handle_t) h;Blas(){MB_CHECK(MB_BLAS(Create)(&h));}~Blas(){MB_BLAS(Destroy)(h);}};
}
