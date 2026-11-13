// SPDX-License-Identifier: Apache-2.0
#include "watershed.h"
#include "watershed_v2.hpp"

extern "C" hipError_t rocm_image_watershed8(const uint8_t* input,uint8_t* segments,
    uint32_t* labels,uint32_t* compact,uint8_t* boundaries,uint8_t* contrast,
    int width,int height,hipStream_t stream){
  const size_t row=static_cast<size_t>(width);
  image_watershed_v2::Outputs outputs;
  outputs.segments={segments,row};outputs.labels={labels,row*4};
  outputs.compact={compact,row*4};outputs.boundaries={boundaries,row};
  outputs.contrast={contrast,row};
  return image_watershed_v2::run(input,row,outputs,width,height,stream);
}
