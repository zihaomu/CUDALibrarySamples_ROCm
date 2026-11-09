// SPDX-License-Identifier: Apache-2.0
#include "check.hpp"
#include <rpp/rpp.h>
#include <rpp/rppt_tensor_geometric_augmentations.h>
using namespace sample;
int main(){return run([]{
 Stream stream;rppHandle_t handle=nullptr;CHECK(rppCreate(&handle,1,0,stream.p,RppBackend::RPP_HIP_BACKEND));
 for(unsigned channels:{1u,3u}){
  const unsigned width=32,height=24;std::vector<unsigned char> x(width*height*channels);for(size_t i=0;i<x.size();++i)x[i]=(i*7)%251;
  Device<unsigned char> in(x),out(x.size());RpptDesc src(1,channels,height,width,RpptDataType::U8,RpptLayout::NHWC),dst=src;
  RpptROI* roi=nullptr;RpptImagePatch* size=nullptr;CHECK(hipMallocManaged(&roi,sizeof(*roi)));CHECK(hipMallocManaged(&size,sizeof(*size)));roi->xywhROI={{0,0},int(width),int(height)};*size={width,height};
  CHECK(rppt_resize(in.p,&src,out.p,&dst,size,RpptInterpolationType::NEAREST_NEIGHBOR,roi,RpptRoiType::XYWH,handle,RppBackend::RPP_HIP_BACKEND));CHECK(hipStreamSynchronize(stream.p));report("resize-identity-c"+std::to_string(channels),out.get(),x,0,0);
  CHECK(hipFree(size));CHECK(hipFree(roi));
 }CHECK(rppDestroy(handle));
});}
