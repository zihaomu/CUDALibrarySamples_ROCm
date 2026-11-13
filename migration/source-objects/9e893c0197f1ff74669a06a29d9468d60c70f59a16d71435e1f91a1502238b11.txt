// SPDX-License-Identifier: Apache-2.0
// Thresholds frozen by migration/rewrite/image-prefix-dispatch-selection.json.
#pragma once
#include "jpeg_serial_prefix.hpp"

namespace image_jpeg_adaptive_prefix {
constexpr unsigned bit_serial_threshold=128;
constexpr unsigned stuff_serial_threshold=64;
template<bool Stuff>constexpr bool use_serial(unsigned count) {
    return count<=(Stuff?stuff_serial_threshold:bit_serial_threshold);
}
template<class T,bool Stuff>
inline hipError_t launch(const T* input,unsigned* offsets,unsigned* sums,unsigned* bases,
    image_jpeg_checked_prefix::Result* result,unsigned count,hipStream_t stream=nullptr) {
    // Keep pointer/count validation identical for both paths.
    if(!input||!offsets||!sums||!bases||!result||!count)return hipErrorInvalidValue;
    if(use_serial<Stuff>(count))return image_jpeg_serial_prefix::launch<T,Stuff>(input,offsets,result,count,stream);
    return image_jpeg_checked_prefix::launch<T,Stuff>(input,offsets,sums,bases,result,count,stream);
}
} // namespace image_jpeg_adaptive_prefix
