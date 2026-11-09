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
    hipfftHandle plan;
    hipStream_t stream = NULL;

    int fft_size = 8;
    int batch_size = 2;
    int element_count = batch_size * fft_size;

    using scalar_type = float;
    using data_type = std::complex<scalar_type>;

    std::vector<data_type> data(element_count, 0);

    for (int i = 0; i < element_count; i++) {
        data[i] = data_type(i, -i);
    }

    std::printf("Input array:\n");
    for (auto &i : data) {
        std::printf("%f + %fj\n", i.real(), i.imag());
    }
    std::printf("=====\n");

    hipfftComplex *d_data = nullptr;

    CUFFT_CALL(hipfftPlan1d(&plan, fft_size, HIPFFT_C2C, batch_size));
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

    // Normalize the data
    scaling_kernel<<<1, 128, 0, stream>>>(d_data, element_count, 1.f/fft_size);

    // The original data should be recovered after Forward FFT, normalization and inverse FFT
    CUFFT_CALL(hipfftExecC2C(plan, d_data, d_data, HIPFFT_BACKWARD));

    CUDA_RT_CALL(hipMemcpyAsync(data.data(), d_data, sizeof(data_type) * data.size(),
                                 hipMemcpyDeviceToHost, stream));

    CUDA_RT_CALL(hipStreamSynchronize(stream));

    std::printf("Output array after Forward FFT, Normalization, and Inverse FFT :\n");
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