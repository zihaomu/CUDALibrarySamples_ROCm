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
#include <vector>
#include <hipfft/hipfft.h>
#include "cufft_utils.h"

using dim_t = std::array<int, 2>;

int main(int argc, char *argv[]) {
    hipfftHandle planc2r, planr2c;
    hipStream_t stream = NULL;

    int nx = 2;
    int ny = 4;
    dim_t fft_size = {nx, ny};
    int batch_size = 2;

    using scalar_type = float;
    using input_type = std::complex<scalar_type>;
    using output_type = scalar_type;

    std::vector<input_type> input_complex(batch_size * nx * (ny/2 + 1));
    std::vector<output_type> output_real(batch_size * nx * ny, 0);

    for (int i = 0; i < input_complex.size(); i++) {
        input_complex[i] = input_type(i, 0);
    }

    std::printf("Input array:\n");
    for (auto &i : input_complex) {
        std::printf("%f + %fj\n", i.real(), i.imag());
    }
    std::printf("=====\n");

    hipfftComplex *d_data = nullptr;

    // inembed/onembed being nullptr indicates contiguous data for each batch, then the stride and dist settings are ignored
    CUFFT_CALL(hipfftPlanMany(&planc2r, fft_size.size(), fft_size.data(),
                             nullptr, 1, 0, // *inembed, istride, idist
                             nullptr, 1, 0, // *onembed, ostride, odist
                             HIPFFT_C2R, batch_size));
    CUFFT_CALL(hipfftPlanMany(&planr2c, fft_size.size(), fft_size.data(),
                             nullptr, 1, 0, // *inembed, istride, idist
                             nullptr, 1, 0, // *onembed, ostride, odist
                             HIPFFT_R2C, batch_size));

    CUDA_RT_CALL(hipStreamCreateWithFlags(&stream, hipStreamNonBlocking));
    CUFFT_CALL(hipfftSetStream(planc2r, stream));
    CUFFT_CALL(hipfftSetStream(planr2c, stream));

    // Create device arrays
    // For in-place r2c/c2r transforms, make sure the device array is always allocated to the size of complex array
    CUDA_RT_CALL(
        hipMalloc(reinterpret_cast<void **>(&d_data), sizeof(input_type) * input_complex.size()));

    CUDA_RT_CALL(hipMemcpyAsync(d_data, (input_complex.data()), sizeof(input_type) * input_complex.size(),
                                 hipMemcpyHostToDevice, stream));

    migration_binary::emit("input.bin",input_complex.data(),input_complex.size()*sizeof(input_type));
    // C2R
    CUFFT_CALL(hipfftExecC2R(planc2r, d_data, reinterpret_cast<scalar_type*>(d_data)));

    std::vector<float> raw_display(input_complex.size()*2);
    CUDA_RT_CALL(hipMemcpyAsync(raw_display.data(), reinterpret_cast<scalar_type*>(d_data), sizeof(float) * raw_display.size(),
                                 hipMemcpyDeviceToHost, stream));

    CUDA_RT_CALL(hipStreamSynchronize(stream));

    for(int b=0;b<batch_size;++b)for(int x=0;x<nx;++x)for(int y=0;y<ny;++y)output_real[b*nx*ny+x*ny+y]=raw_display[(b*nx+x)*2*(ny/2+1)+y];
    std::printf("Output array after C2R:\n");
    for (auto i = 0; i < output_real.size(); i++) {
        std::printf("%f\n", output_real[i]);
    }
    std::printf("=====\n");

    // Normalize the data
    scaling_kernel<<<1, 128, 0, stream>>>(d_data, input_complex.size(), 1.f/(nx * ny));

    CUDA_RT_CALL(hipGetLastError());
    CUDA_RT_CALL(hipStreamSynchronize(stream));
    // MIGRATION_2D_OBSERVE: preserve the full in-place allocation for CPU layout verification.
    std::vector<float> raw_observation(input_complex.size()*2);
    CUDA_RT_CALL(hipMemcpy(raw_observation.data(),d_data,raw_observation.size()*sizeof(float),hipMemcpyDeviceToHost));
    migration_binary::emit("intermediate.bin",raw_observation.data(),raw_observation.size()*sizeof(float));
    // R2C
    CUFFT_CALL(hipfftExecR2C(planr2c, reinterpret_cast<scalar_type*>(d_data), d_data));

    CUDA_RT_CALL(hipMemcpyAsync(input_complex.data(), d_data, sizeof(input_type) * input_complex.size(),
                                 hipMemcpyDeviceToHost, stream));

    CUDA_RT_CALL(hipStreamSynchronize(stream));
    std::printf("Output array after C2R, Normalization, and R2C:\n");
    for (auto i = 0; i < input_complex.size(); i++) {
        std::printf("%f + %fj\n", input_complex[i].real(), input_complex[i].imag());
    }
    std::printf("=====\n");


    migration_binary::emit("output.bin",input_complex.data(),input_complex.size()*sizeof(input_type));
    /* free resources */
    CUDA_RT_CALL(hipFree(d_data));

    CUFFT_CALL(hipfftDestroy(planc2r));
    CUFFT_CALL(hipfftDestroy(planr2c));

    CUDA_RT_CALL(hipStreamDestroy(stream));

    // Keep the HIP runtime alive for rocFFT cache cleanup.

    return EXIT_SUCCESS;
}