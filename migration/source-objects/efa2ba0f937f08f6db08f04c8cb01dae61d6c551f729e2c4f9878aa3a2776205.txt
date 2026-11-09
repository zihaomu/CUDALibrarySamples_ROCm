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
#include <vector>
#include <hipfft/hipfftXt.h>

#include "cufft_utils.h"

using cpudata_t = std::vector<std::complex<float>>;
using gpus_t = std::vector<int>;
using dim_t = std::array<size_t, 3>;

void fill_array(cpudata_t &array) {
    std::mt19937 gen(3); // certified random number
    std::uniform_real_distribution<float> dis(0.0f, 1.0f);

    for (size_t i = 0; i < array.size(); ++i) {
        float real = dis(gen);
        float imag = dis(gen);
        array[i] = {real, imag};
    };
};

/** Single GPU version of cuFFT plan for reference. */
void single(dim_t fft, cpudata_t &h_data_in, cpudata_t &h_data_out) {

    hipfftHandle plan{};

    CUFFT_CALL(hipfftCreate(&plan));

    size_t workspace_size;
    CUFFT_CALL(hipfftMakePlan3d(plan, fft[0], fft[1], fft[2], HIPFFT_C2C, &workspace_size));

    void *d_data;
    size_t datasize = h_data_in.size() * sizeof(std::complex<float>);

    CUDA_RT_CALL(hipMalloc(&d_data, datasize));
    CUDA_RT_CALL(hipMemcpy(d_data, h_data_in.data(), datasize, hipMemcpyHostToDevice));

    CUFFT_CALL(hipfftXtExec(plan, d_data, d_data, HIPFFT_FORWARD));

    CUDA_RT_CALL(hipMemcpy(h_data_out.data(), d_data, datasize, hipMemcpyDeviceToHost));
    CUDA_RT_CALL(hipFree(d_data));

    CUFFT_CALL(hipfftDestroy(plan));
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
    hipfftHandle plan{};
    CUFFT_CALL(hipfftCreate(&plan));

#if 1 // Explicit HIP stream association, qualified independently of CUDA version
    // Create CUDA Stream
    hipStream_t stream{};
    CUDA_RT_CALL(hipStreamCreate(&stream));
    CUFFT_CALL(hipfftSetStream(plan, stream));
#endif

    // Define which GPUS are to be used
    CUFFT_CALL(hipfftXtSetGPUs(plan, gpus.size(), gpus.data()));

    // Create the plan
    // With multiple gpus, worksize will contain multiple sizes
    size_t workspace_sizes[gpus.size()];
    CUFFT_CALL(hipfftMakePlan3d(plan, fft[0], fft[1], fft[2], HIPFFT_C2C, workspace_sizes));

    hipLibXtDesc *indesc;

    // Copy input data to GPUs
    CUFFT_CALL(hipfftXtMalloc(plan, &indesc, subformat));
    CUFFT_CALL(hipfftXtMemcpy(plan, reinterpret_cast<void *>(indesc),
                             reinterpret_cast<void *>(h_data_in.data()),
                             HIPFFT_COPY_HOST_TO_DEVICE));

    // Execute the plan
    CUFFT_CALL(hipfftXtExecDescriptor(plan, indesc, indesc, HIPFFT_FORWARD));

    // Copy output data to CPU
    CUFFT_CALL(hipfftXtMemcpy(plan, reinterpret_cast<void *>(h_data_out.data()),
                             reinterpret_cast<void *>(indesc), HIPFFT_COPY_DEVICE_TO_HOST));

    CUFFT_CALL(hipfftXtFree(indesc));
    CUFFT_CALL(hipfftDestroy(plan));

#if 1 // Explicit HIP stream association, qualified independently of CUDA version
    CUDA_RT_CALL(hipStreamDestroy(stream));
#endif
};

/** Runs single and multi-GPU version of cuFFT plan then compares results.
 * Maximum FFT size limited by single GPU memory.
 * */
int main(int argc, char *argv[]) {

    dim_t fft = {256, 256, 256};
    // can be {0, 0} to run on single-GPU system or if GPUs are not of same architecture
    gpus_t gpus = {0, 1};

    size_t element_count = fft[0] * fft[1] * fft[2];

    cpudata_t data_in(element_count);
    fill_array(data_in);

    cpudata_t data_out_reference(element_count, {-1.0f, -1.0f});
    cpudata_t data_out_test(element_count, {-0.5f, -0.5f});

    hipfftXtSubFormat_t decomposition = HIPFFT_XT_FORMAT_INPLACE_SHUFFLED;

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