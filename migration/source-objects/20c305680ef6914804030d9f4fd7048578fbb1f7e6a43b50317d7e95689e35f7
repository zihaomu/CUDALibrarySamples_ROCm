// SPDX-License-Identifier: Apache-2.0
#include "ccl_sample.hpp"
#ifndef CUDA11U1
#define IMAGE_CCL_BATCH_COMPRESSION false
#else
#define IMAGE_CCL_BATCH_COMPRESSION true
#endif
int main(int argc,char**argv){return rocm_image_ccl_sample::application(argc,argv,IMAGE_CCL_BATCH_COMPRESSION);}
