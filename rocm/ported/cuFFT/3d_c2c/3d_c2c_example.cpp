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


#include <array>
#include <complex>
#include <iostream>
#include <random>
#include <vector>
#include <hip/hip_runtime.h>
#include <hipfft/hipfft.h>

#include "cufft_utils.h"

using dim_t = std::array<int, 3>;

int main(int argc, char *argv[]) {
    hipfftHandle plan;
    hipStream_t stream = NULL;

    int n = 2;
    dim_t fft = {n, n, n};
    int batch_size = 2;
    int fft_size = fft[0] * fft[1] * fft[2];

    using scalar_type = float;
    using data_type = std::complex<scalar_type>;

    std::vector<data_type> data(fft_size * batch_size);

    for (int i = 0; i < data.size(); i++) {
        data[i] = data_type(i, -i);
    }

    std::printf("Input array:\n");
    for (auto &i : data) {
        std::printf("%f + %fj\n", i.real(), i.imag());
    }
    std::printf("=====\n");

    hipfftComplex *d_data = nullptr;

    // inembed/onembed being nullptr indicates contiguous data for each batch, then the stride and dist settings are ignored
    CUFFT_CALL(hipfftPlanMany(&plan, fft.size(), fft.data(),
                             nullptr, 1, 0, // *inembed, istride, idist
                             nullptr, 1, 0, // *onembed, ostride, odist
                             HIPFFT_C2C, batch_size));

    CUDA_RT_CALL(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUFFT_CALL(hipfftSetStream(plan, stream));

    // Create device data arrays
    CUDA_RT_CALL(hipMalloc(reinterpret_cast<void **>(&d_data), sizeof(data_type) * data.size()));
    CUDA_RT_CALL(hipMemcpyAsync(d_data, data.data(), sizeof(data_type) * data.size(),
                                 hipMemcpyHostToDevice, stream));

    /*
     * Note:
     *  Identical pointers to data and output arrays implies in-place transformation
     */
    CUFFT_CALL(hipfftExecC2C(plan, d_data, d_data, HIPFFT_FORWARD));
    CUDA_RT_CALL(hipMemcpyAsync(data.data(), d_data, sizeof(data_type) * data.size(),
                                 hipMemcpyDeviceToHost, stream));
    CUDA_RT_CALL(hipStreamSynchronize(stream));

    std::printf("Output array after Forward transform:\n");
    for (auto &i : data) {
        std::printf("%f + %fj\n", i.real(), i.imag());
    }
    std::printf("=====\n");

    // Normalize the data and inverse FFT
    scaling_kernel<<<1, 128, 0, stream>>>(d_data, data.size(), 1.f/fft_size);
    CUFFT_CALL(hipfftExecC2C(plan, d_data, d_data, HIPFFT_BACKWARD));
    CUDA_RT_CALL(hipMemcpyAsync(data.data(), d_data, sizeof(data_type) * data.size(),
                                 hipMemcpyDeviceToHost, stream));

    CUDA_RT_CALL(hipStreamSynchronize(stream));

    std::printf("Output array after Forward, Normalization and Inverse transform:\n");
    for (auto &i : data) {
        std::printf("%f + %fj\n", i.real(), i.imag());
    }
    std::printf("=====\n");



    /* free resources */
    CUDA_RT_CALL(hipFree(d_data))

    CUFFT_CALL(hipfftDestroy(plan));

    CUDA_RT_CALL(hipStreamDestroy(stream));

    // Keep the HIP runtime alive for rocFFT cache cleanup.

    return EXIT_SUCCESS;
}