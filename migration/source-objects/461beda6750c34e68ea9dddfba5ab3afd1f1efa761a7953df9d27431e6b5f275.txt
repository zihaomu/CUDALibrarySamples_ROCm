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
#include <complex>
#include <iostream>
#include <vector>
#include <hipfft/hipfft.h>
#include "cufft_utils.h"

int main(int argc, char *argv[]) {
    hipfftHandle planr2c, planc2r;
    hipStream_t stream = NULL;

    int fft_size = 8;
    int batch_size = 2;
    int element_count = batch_size * fft_size;

    using scalar_type = float;
    using input_type = scalar_type;
    using output_type = std::complex<scalar_type>;

    std::vector<input_type> input(element_count, 0);
    std::vector<output_type> output((fft_size / 2 + 1) * batch_size);

    for (auto i = 0; i < element_count; i++) {
        input[i] = static_cast<input_type>(i);
    }

    std::printf("Input array:\n");
    for (auto &i : input) {
        std::printf("%f\n", i);
    }
    std::printf("=====\n");

    input_type *d_input = nullptr;
    hipfftComplex *d_output = nullptr;

    CUFFT_CALL(hipfftPlan1d(&planr2c, fft_size, HIPFFT_R2C, batch_size));
    CUFFT_CALL(hipfftPlan1d(&planc2r, fft_size, HIPFFT_C2R, batch_size));

    CUDA_RT_CALL(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUFFT_CALL(hipfftSetStream(planr2c, stream));
    CUFFT_CALL(hipfftSetStream(planc2r, stream));

    // Create device arrays
    CUDA_RT_CALL(
        hipMalloc(reinterpret_cast<void **>(&d_input), sizeof(input_type) * input.size()));
    CUDA_RT_CALL(
        hipMalloc(reinterpret_cast<void **>(&d_output), sizeof(output_type) * output.size()));
    CUDA_RT_CALL(hipMemcpyAsync(d_input, input.data(), sizeof(input_type) * input.size(),
                                 hipMemcpyHostToDevice, stream));

    // out-of-place Forward transform
    CUFFT_CALL(hipfftExecR2C(planr2c, d_input, d_output));

    CUDA_RT_CALL(hipMemcpyAsync(output.data(), d_output, sizeof(output_type) * output.size(),
                                 hipMemcpyDeviceToHost, stream));

    CUDA_RT_CALL(hipStreamSynchronize(stream));

    std::printf("Output array after Forward FFT:\n");
    for (auto &i : output) {
        std::printf("%f + %fj\n", i.real(), i.imag());
    }
    std::printf("=====\n");

    // Normalize the data
    scaling_kernel<<<1, 128, 0, stream>>>(d_output, output.size(), 1./fft_size);

    // out-of-place Inverse transform
    CUFFT_CALL(hipfftExecC2R(planc2r, d_output, d_input));

    CUDA_RT_CALL(hipMemcpyAsync(input.data(), d_input, sizeof(input_type) * input.size(),
                                 hipMemcpyDeviceToHost, stream));

    CUDA_RT_CALL(hipStreamSynchronize(stream));
    std::printf("Output array after Forward FFT, Normalization, and Inverse FFT:\n");
    for (auto value : input) std::printf("%f\n", value);
    std::printf("=====\n");

    /* free resources */
    CUDA_RT_CALL(hipFree(d_input));
    CUDA_RT_CALL(hipFree(d_output));

    CUFFT_CALL(hipfftDestroy(planr2c));
    CUFFT_CALL(hipfftDestroy(planc2r));

    CUDA_RT_CALL(hipStreamDestroy(stream));

    // Keep the HIP runtime alive for rocFFT cache cleanup.

    return EXIT_SUCCESS;
}