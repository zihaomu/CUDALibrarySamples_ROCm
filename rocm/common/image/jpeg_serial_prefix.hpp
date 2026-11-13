// SPDX-License-Identifier: Apache-2.0
// Checked single-lane candidate for short JPEG prefix inputs.
#pragma once
#include "jpeg_checked_prefix.hpp"

namespace image_jpeg_serial_prefix {
using image_jpeg_checked_prefix::Result;
template<class T,bool Stuff>
__global__ void serial(const T* input,unsigned* offsets,Result* result,unsigned count) {
    if(blockIdx.x||threadIdx.x)return;
    uint64_t sum=0;unsigned errors=0;
    for(unsigned i=0;i<count;++i) {
        offsets[i]=static_cast<unsigned>(sum+(Stuff?uint64_t(i):0));
        const unsigned value=input[i];
        if constexpr(Stuff)sum+=value==0xff;
        else {
            if(!value||value>4096)errors|=image_jpeg_checked_prefix::invalid_length;
            sum+=value;
        }
    }
    if constexpr(Stuff)sum+=count;
    const uint64_t limit=Stuff?uint64_t(UINT32_MAX):uint64_t(UINT32_MAX)-7;
    if(sum>limit) {errors|=image_jpeg_checked_prefix::offset_overflow;result->total=0;}
    else result->total=static_cast<unsigned>(sum);
    result->errors=errors;
}
template<class T,bool Stuff>
inline hipError_t launch(const T* input,unsigned* offsets,Result* result,unsigned count,hipStream_t stream=nullptr) {
    if(!input||!offsets||!result||!count)return hipErrorInvalidValue;
    serial<T,Stuff><<<1,1,0,stream>>>(input,offsets,result,count);
    return hipGetLastError();
}
} // namespace image_jpeg_serial_prefix
