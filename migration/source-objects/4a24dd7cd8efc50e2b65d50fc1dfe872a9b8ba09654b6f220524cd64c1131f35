// SPDX-License-Identifier: Apache-2.0
#pragma once
#include <hip/hip_runtime.h>
#include <cstdint>
namespace rocm_image {
inline bool spans_overlap(const void*a,uint64_t an,const void*b,uint64_t bn){
 uintptr_t aa=reinterpret_cast<uintptr_t>(a),bb=reinterpret_cast<uintptr_t>(b);
 return an>UINTPTR_MAX-aa||bn>UINTPTR_MAX-bb||(aa<bb+bn&&bb<aa+an);
}
inline hipError_t device_span(const void*pointer,uint64_t bytes,int current){
 hipPointerAttribute_t attr{};hipError_t status=hipPointerGetAttributes(&attr,pointer);
 if(status!=hipSuccess||attr.type!=hipMemoryTypeDevice)return hipErrorInvalidValue;
 if(attr.device!=current)return hipErrorInvalidDevice;
 hipDeviceptr_t base{};size_t size=0;status=hipMemGetAddressRange(&base,&size,reinterpret_cast<hipDeviceptr_t>(const_cast<void*>(pointer)));
 if(status!=hipSuccess)return status;
 uintptr_t start=reinterpret_cast<uintptr_t>(pointer),origin=reinterpret_cast<uintptr_t>(base);
 return start<origin||start-origin>size||bytes>size-(start-origin)?hipErrorInvalidValue:hipSuccess;
}
}
