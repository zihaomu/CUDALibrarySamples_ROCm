#include "binary_observe.hpp"
/*
 * SPDX-FileCopyrightText: Copyright (c) 2020 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


#include "hip/hip_runtime.h"
#include <array>
#include <complex>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
#include <hipfft/hipfftXt.h>

#include "cufft_utils.h"

using cpudata_t = std::vector<std::complex<float>>;
using gpus_t = std::vector<int>;
using dim_t = std::array<size_t, 3>;

void scaleComplex(hipLibXtDesc *desc, const float scale, const size_t N, const int nGPUs) {
    int device;
    int threads{1024};

    int dimGrid = (N / nGPUs + threads - 1) / threads;
    int dimBlock = threads;

    for (int i = 0; i < nGPUs; i++) {
        device = desc->descriptor->GPUs[i];
        CUDA_RT_CALL(hipSetDevice(device));

        scaling_kernel<<<dimGrid, dimBlock>>>((hipfftComplex *)desc->descriptor->data[i],
                                           desc->descriptor->size[i] / sizeof(hipfftComplex), scale);
        if (N / nGPUs != desc->descriptor->size[i] / sizeof(hipfftComplex)) {
            throw std::runtime_error("ERROR: Wrong data size");
        }
    }

    // Wait for device to finish all operation
    for (int i = 0; i < nGPUs; i++) {
        device = desc->descriptor->GPUs[i];
        CUDA_RT_CALL(hipSetDevice(device));
        CUDA_RT_CALL(hipDeviceSynchronize());
    }
}

void fill_array(cpudata_t &array) {
    std::mt19937 gen(3); // certified random number
    std::uniform_real_distribution<float> dis(0.0f, 1.0f);

    for (size_t i = 0; i < array.size(); ++i) {
        float real = dis(gen);
        float imag = dis(gen);
        array[i] = {real, imag};
    }
}

/** Single GPU version of cuFFT plan for reference. */
void single(dim_t fft, cpudata_t &h_data_in, cpudata_t &h_data_out) {

    // Initiate cufft plans, one for r2c and one for c2r
    hipfftHandle plan_r2c{};
    hipfftHandle plan_c2r{};
    CUFFT_CALL(hipfftCreate(&plan_r2c));
    CUFFT_CALL(hipfftCreate(&plan_c2r));

    // Create the plans
    size_t workspace_size;
    CUFFT_CALL(hipfftMakePlan3d(plan_r2c, fft[0], fft[1], fft[2], HIPFFT_R2C, &workspace_size));
    CUFFT_CALL(hipfftMakePlan3d(plan_c2r, fft[0], fft[1], fft[2], HIPFFT_C2R, &workspace_size));

    void *d_data;
    size_t datasize = h_data_in.size() * sizeof(std::complex<float>);

    // Copy input data to GPUs
    CUDA_RT_CALL(hipMalloc(&d_data, datasize));
    CUDA_RT_CALL(hipMemcpy(d_data, h_data_in.data(), datasize, hipMemcpyHostToDevice));

    // Execute the plan_r2c
    CUFFT_CALL(hipfftXtExec(plan_r2c, d_data, d_data, HIPFFT_FORWARD));

    // Scale complex results
    float scale{2.f};
    int threads{1024};

    int dimGrid = (h_data_in.size() + threads - 1) / threads;
    int dimBlock = threads;
    scaling_kernel<<<dimGrid, dimBlock>>>(reinterpret_cast<hipfftComplex *>(d_data),
                                       h_data_in.size(), scale);

    // Execute the plan_c2r
    CUFFT_CALL(hipfftXtExec(plan_c2r, d_data, d_data, HIPFFT_BACKWARD));

    // Copy output data to CPU
    CUDA_RT_CALL(hipMemcpy(h_data_out.data(), d_data, datasize, hipMemcpyDeviceToHost));
    CUDA_RT_CALL(hipFree(d_data));

    CUFFT_CALL(hipfftDestroy(plan_r2c));
    CUFFT_CALL(hipfftDestroy(plan_c2r));
};

/** Since cuFFT 10.4.0 cufftSetStream can be used to associate a stream with
 * multi-GPU plan. cufftXtExecDescriptor synchronizes efficiently to the stream
 * before and after execution. Please refer to
 * https://docs.nvidia.com/cuda/cufft/index.html#function-cufftsetstream for
 * more information.
 * cuFFT by default executes multi-GPU plans in synchronous manner.
 * */
void spmg(dim_t fft, gpus_t gpus, cpudata_t &h_data_in, cpudata_t &h_data_out,
          hipfftXtSubFormat_t subformat) {

    // Initiate cufft plan
    hipfftHandle plan_r2c{};
    hipfftHandle plan_c2r{};
    CUFFT_CALL(hipfftCreate(&plan_r2c));
    CUFFT_CALL(hipfftCreate(&plan_c2r));

#if 1 // Explicit HIP stream association, qualified independently of CUDA version
    // Create CUDA Stream
    hipStream_t stream{};
    CUDA_RT_CALL(hipStreamCreate(&stream));
    CUFFT_CALL(hipfftSetStream(plan_r2c, stream));
    CUFFT_CALL(hipfftSetStream(plan_c2r, stream));
#endif

    // Define which GPUS are to be used
    CUFFT_CALL(hipfftXtSetGPUs(plan_r2c, gpus.size(), gpus.data()));
    CUFFT_CALL(hipfftXtSetGPUs(plan_c2r, gpus.size(), gpus.data()));

    // Create the plans
    // With multiple gpus, worksize will contain multiple sizes
    size_t workspace_sizes[gpus.size()];
    CUFFT_CALL(hipfftMakePlan3d(plan_r2c, fft[0], fft[1], fft[2], HIPFFT_R2C, workspace_sizes));
    CUFFT_CALL(hipfftMakePlan3d(plan_c2r, fft[0], fft[1], fft[2], HIPFFT_C2R, workspace_sizes));

    hipLibXtDesc *indesc;

    // Copy input data to GPUs
    CUFFT_CALL(hipfftXtMalloc(plan_r2c, &indesc, subformat));
    CUFFT_CALL(hipfftXtMemcpy(plan_r2c, (void *)indesc, (void *)h_data_in.data(),
                             HIPFFT_COPY_HOST_TO_DEVICE));

    // Execute the plan_r2c
    CUFFT_CALL(hipfftXtExecDescriptor(plan_r2c, indesc, indesc, HIPFFT_FORWARD));

    // Scale complex results
    float scale{2.f};
    scaleComplex(indesc, scale, h_data_out.size(), gpus.size());

    // Execute the plan_c2r
    CUFFT_CALL(hipfftXtExecDescriptor(plan_c2r, indesc, indesc, HIPFFT_BACKWARD));

    // Copy output data to CPU
    CUFFT_CALL(hipfftXtMemcpy(plan_c2r, (void *)h_data_out.data(), (void *)indesc,
                             HIPFFT_COPY_DEVICE_TO_HOST));

    CUFFT_CALL(hipfftXtFree(indesc));
    CUFFT_CALL(hipfftDestroy(plan_r2c));
    CUFFT_CALL(hipfftDestroy(plan_c2r));

#if 1 // Explicit HIP stream association, qualified independently of CUDA version
    CUDA_RT_CALL(hipStreamDestroy(stream));
#endif
};

/** Runs single and multi-GPU version of cuFFT plan then compares results.
 * Maximum FFT size limited by single GPU memory. */
int main(int argc, char *argv[]) {

    dim_t fft = {256, 256, 256};
    // can be {0, 0} to run on single-GPU system or if GPUs are not of same architecture
    gpus_t gpus = {0, 1};

    size_t element_count = fft[0] * fft[1] * ((fft[2] / 2) + 1);

    cpudata_t data_in(element_count);
    fill_array(data_in);

    cpudata_t data_out_reference(element_count, {-1.0f, -1.0f});
    cpudata_t data_out_test(element_count, {-0.5f, -0.5f});

    hipfftXtSubFormat_t decomposition = HIPFFT_XT_FORMAT_INPLACE;

    spmg(fft, gpus, data_in, data_out_test, decomposition);
    single(fft, data_in, data_out_reference);

    // The cuFFT library doesn't guarantee that single-GPU and multi-GPU cuFFT
    // plans will perform mathematical operations in same order. Small
    // numerical differences are possible.

    // verify results
    double error{};
    double ref{};
    for (size_t i = 0; i < element_count; ++i) {
        error += std::norm(data_out_test[i] - data_out_reference[i]);
        ref += std::norm(data_out_reference[i]);
    };

    double l2_error = (ref == 0.0) ? std::sqrt(error) : std::sqrt(error) / std::sqrt(ref);
    if (l2_error < 0.001) {
        std::cout << "PASSED with L2 error = " << l2_error << std::endl;
    } else {
        std::cout << "FAILED with L2 error = " << l2_error << std::endl;
    };

    // MIGRATION_BINARY_FFT: lossless observations, mathematical calls unchanged.
    migration_binary::emit("input.bin",data_in.data(),data_in.size()*sizeof(cpudata_t::value_type));
    migration_binary::emit("output.bin",data_out_test.data(),data_out_test.size()*sizeof(cpudata_t::value_type));
    return EXIT_SUCCESS;
};