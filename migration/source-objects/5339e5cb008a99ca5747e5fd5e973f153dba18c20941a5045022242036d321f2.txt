// SPDX-License-Identifier: Apache-2.0
#ifndef ROCM_IMAGE_HOUGH_H
#define ROCM_IMAGE_HOUGH_H
#include <hip/hip_runtime.h>
#include <cstdint>
struct RocmHoughPeak { int rho_index; int theta_degrees; int votes; };
// Candidate storage is device memory with at least 180*accumulator_height cells.
// Count is device memory; caller owns all spans through stream completion.
extern "C" hipError_t rocm_image_hough_peaks(const uint8_t* edges,int width,int height,
    int threshold,RocmHoughPeak* peaks,int candidate_capacity,int* count,hipStream_t stream);
extern "C" int rocm_image_hough_accumulator_height(int width,int height);
#endif
