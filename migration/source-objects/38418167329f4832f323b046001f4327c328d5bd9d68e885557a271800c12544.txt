/*
 * SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
#include <iostream>
#include <iomanip>
#include <vector>
#include <limits>

#include <hip/hip_runtime_api.h>
#include <cufftdx.hpp>
#include <hipfft/hipfft.h>

#include "../common/block_io.hpp"
#include "../common/block_io_strided.hpp"
#include "../common/common.hpp"
#include "../common/random.hpp"

// #define CUFFTDX_EXAMPLE_DETAIL_DEBUG_FFT_2D
inline constexpr unsigned int cufftdx_example_warm_up_runs = 5;
inline constexpr unsigned int cufftdx_example_performance_runs = 20;

template<class FFT, class InputType, class OutputType>
__launch_bounds__(FFT::max_threads_per_block) __global__
    void fft_2d_kernel_y(const InputType* input, OutputType* output, typename FFT::workspace_type workspace) {
    CUFFTDX_SKIP_IF_NOT_APPLICABLE_SM(FFT);

    using complex_type = typename FFT::value_type;

    // Local array for thread
    complex_type thread_data[FFT::storage_size];

    // ID of FFT in CUDA block, in range [0; FFT::ffts_per_block)
    const unsigned int local_fft_id = threadIdx.y;
    // Load data from global memory to registers
    example::io<FFT>::load(input, thread_data, local_fft_id);

    // Execute FFT
    extern __shared__ __align__(alignof(float4)) complex_type shared_mem[];
    FFT().execute(thread_data, shared_mem, workspace);

    // Save results
    example::io<FFT>::store(thread_data, output, local_fft_id);
}

template<class FFTF,
         class FFTI,
         unsigned int Stride,
         unsigned int SizeY,
         bool         UseSharedMemoryStridedIO,
         class ComplexType = typename FFTF::value_type>
__launch_bounds__(FFTF::max_threads_per_block) __global__
    void fft_2d_kernel_x(const ComplexType*            input,
                         ComplexType*                  output,
                         typename FFTF::workspace_type workspacef,
                         typename FFTI::workspace_type workspacei) {
    CUFFTDX_SKIP_IF_NOT_APPLICABLE_SM(FFTF);

    using complex_type = typename FFTF::value_type;

    extern __shared__ __align__(alignof(float4)) complex_type shared_mem[];

    // Local array for thread
    complex_type thread_data[FFTF::storage_size];

    // ID of FFT in CUDA block, in range [0; FFT::ffts_per_block)
    const unsigned int local_fft_id = threadIdx.y;
    // Load data from global memory to registers
    if constexpr (UseSharedMemoryStridedIO) {
        example::io_strided<FFTF>::load_strided<Stride, SizeY>(input, thread_data, shared_mem, local_fft_id);
    } else {
        example::io_strided<FFTF>::load_strided<Stride, SizeY>(input, thread_data, local_fft_id);
    }

    // Execute FFT (part of the 2D R2C FFT)
    FFTF().execute(thread_data, shared_mem, workspacef);

    // Note: You can do any point-wise operation in here.

    // Execute FFT (part of the 2D C2R FFT)
    FFTI().execute(thread_data, shared_mem, workspacei);

    // Save results
    if constexpr (UseSharedMemoryStridedIO) {
        example::io_strided<FFTI>::store_strided<Stride, SizeY>(thread_data, shared_mem, output, local_fft_id);
    } else {
        example::io_strided<FFTI>::store_strided<Stride, SizeY>(thread_data, output, local_fft_id);
    }
}

template<class RealType, class ComplexType>
example::fft_results<RealType> cufft_fft_2d_r2c_c2r(unsigned int fft_size_x,
                                             unsigned int fft_size_y,
                                             RealType*           real_values,
                                             ComplexType*           complex_values,
                                             hipStream_t stream) {
    using complex_type = hipfftComplex;
    static_assert(sizeof(ComplexType) == sizeof(complex_type), "");
    static_assert(std::alignment_of_v<ComplexType> == std::alignment_of_v<complex_type>, "");
    using real_type = hipfftReal;
    static_assert(sizeof(ComplexType) % sizeof(real_type) == 0, "");
    static_assert(std::alignment_of_v<ComplexType> % std::alignment_of_v<real_type> == 0, "");
    static_assert(sizeof(RealType) == sizeof(real_type), "");
    static_assert(std::alignment_of_v<RealType> == std::alignment_of_v<real_type>, "");

    real_type*    cufft_input_r2c  = reinterpret_cast<real_type*>(real_values);
    complex_type* cufft_output_r2c = reinterpret_cast<complex_type*>(complex_values);
    complex_type* cufft_input_c2r  = cufft_output_r2c;
    real_type*    cufft_output_c2r = reinterpret_cast<real_type*>(real_values);

    // Create cuFFT plan
    hipfftHandle plan_r2c;
    hipfftHandle plan_c2r;
    CUFFT_CHECK_AND_EXIT(hipfftPlan2d(&plan_r2c, fft_size_x, fft_size_y, HIPFFT_R2C));
    CUFFT_CHECK_AND_EXIT(hipfftPlan2d(&plan_c2r, fft_size_x, fft_size_y, HIPFFT_C2R));
    CUFFT_CHECK_AND_EXIT(hipfftSetStream(plan_r2c, stream));
    CUFFT_CHECK_AND_EXIT(hipfftSetStream(plan_c2r, stream));

    // Execute cuFFT
    auto cufft_execution = [&](hipStream_t /* stream */) {
        // Out-of-place R2C
        CUFFT_CHECK_AND_EXIT(hipfftExecR2C(plan_r2c, cufft_input_r2c, cufft_output_r2c));
        // Out-of-place C2R
        CUFFT_CHECK_AND_EXIT(hipfftExecC2R(plan_c2r, cufft_input_c2r, cufft_output_c2r));
    };

    // Correctness run
    cufft_execution(stream);
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());
    // Copy results to host
    const size_t           flat_fft_size       = fft_size_x * fft_size_y;
    const size_t           flat_fft_size_bytes = flat_fft_size * sizeof(real_type);
    std::vector<real_type> output_host(flat_fft_size, std::numeric_limits<real_type>::quiet_NaN());
    CUDA_CHECK_AND_EXIT(hipMemcpy(output_host.data(), cufft_output_c2r, flat_fft_size_bytes, hipMemcpyDeviceToHost));
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

    // Performance measurements
    auto time = example::measure_execution_ms(
        cufft_execution,
        cufftdx_example_warm_up_runs,
        cufftdx_example_performance_runs,
        stream);

    // Clean-up
    CUFFT_CHECK_AND_EXIT(hipfftDestroy(plan_r2c));
    CUFFT_CHECK_AND_EXIT(hipfftDestroy(plan_c2r));

    // Return results
    return example::fft_results<RealType> {output_host, (time / cufftdx_example_performance_runs)};
}

template<class FFTR2CX, class FFTR2CY, class FFTC2RX, class FFTC2RY, bool UseSharedMemoryStridedIO, class RealType, class ComplexType>
example::fft_results<RealType> cufftdx_fft_2d_r2c_c2r(RealType* real_values, ComplexType* complex_values, hipStream_t stream) {
    using FFTX         = FFTR2CX;
    using FFTY         = FFTR2CY;
    using complex_type = typename FFTX::value_type;
    using real_type    = typename complex_type::value_type;

    static constexpr unsigned int fft_size_y = cufftdx::size_of<FFTY>::value;
    static constexpr unsigned int fft_size_x = cufftdx::size_of<FFTX>::value;

    // Checks that FFTX and FFTY are correctly defined
    static_assert(std::is_same_v<cufftdx::precision_of_t<FFTX>, cufftdx::precision_of_t<FFTY>>,
                  "FFTY and FFTX must have the same precision");
    static_assert(std::is_same_v<typename FFTX::value_type, typename FFTY::value_type>,
                  "FFTY and FFTX must operator on the same type");
    static_assert(sizeof(ComplexType) == sizeof(complex_type), "");
    static_assert(std::alignment_of_v<ComplexType> == std::alignment_of_v<complex_type>, "");
    static_assert(sizeof(RealType) == sizeof(real_type), "");
    static_assert(std::alignment_of_v<RealType> == std::alignment_of_v<real_type>, "");
    // Checks below are not caused by any limitation in cuFFTDx, but rather in the example IO functions.
    static_assert((fft_size_x % FFTY::ffts_per_block == 0),
                  "FFTsPerBlock for FFTX must divide Y dimension as IO doesn't check if a batch is in range");

    real_type*    cufftdx_real_values    = reinterpret_cast<real_type*>(real_values);
    complex_type* cufftdx_complex_values = reinterpret_cast<complex_type*>(complex_values);

    // Set shared memory requirements
    auto error_code = hipFuncSetAttribute(reinterpret_cast<const void*>(fft_2d_kernel_y<FFTR2CY, real_type, complex_type>),
                                           hipFuncAttributeMaxDynamicSharedMemorySize,
                                           FFTR2CY::shared_memory_size);
    CUDA_CHECK_AND_EXIT(error_code);
    error_code = hipFuncSetAttribute(reinterpret_cast<const void*>(fft_2d_kernel_y<FFTC2RY, complex_type, real_type>),
                                      hipFuncAttributeMaxDynamicSharedMemorySize,
                                      FFTC2RY::shared_memory_size);
    CUDA_CHECK_AND_EXIT(error_code);
    unsigned int fft_x_shared_memory_smem_io =
        std::max<unsigned>({FFTR2CX::shared_memory_size,
                            FFTC2RX::shared_memory_size,
                            FFTX::ffts_per_block * fft_size_x * sizeof(complex_type)});
    unsigned int fft_x_shared_memory =
        UseSharedMemoryStridedIO ? fft_x_shared_memory_smem_io : FFTX::shared_memory_size;
    error_code = hipFuncSetAttribute(reinterpret_cast<const void*>(fft_2d_kernel_x<FFTR2CX,
                                                      FFTC2RX,
                                                      FFTY::output_length,
                                                      FFTY::output_length,
                                                      UseSharedMemoryStridedIO,
                                                      complex_type>),
                                      hipFuncAttributeMaxDynamicSharedMemorySize,
                                      fft_x_shared_memory);
    CUDA_CHECK_AND_EXIT(error_code);

    // Create workspaces for FFTs
    auto workspace_y_r2c = cufftdx::make_workspace<FFTR2CY>(error_code, stream);
    CUDA_CHECK_AND_EXIT(error_code);
    auto workspace_x_r2c = cufftdx::make_workspace<FFTR2CX>(error_code, stream);
    CUDA_CHECK_AND_EXIT(error_code);
    auto workspace_y_c2r = cufftdx::make_workspace<FFTC2RY>(error_code, stream);
    CUDA_CHECK_AND_EXIT(error_code);
    auto workspace_x_c2r = cufftdx::make_workspace<FFTC2RX>(error_code, stream);
    CUDA_CHECK_AND_EXIT(error_code);

    // Synchronize device before execution
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

    // Out-of-place R2C kernel (R2C Y dimension)
    const auto grid_fft_size_y_r2c = ((fft_size_x + FFTR2CY::ffts_per_block - 1) / FFTR2CY::ffts_per_block);
    const auto grid_fft_size_x     = ((FFTY::output_length + FFTX::ffts_per_block - 1) / FFTX::ffts_per_block);
    const auto grid_fft_size_y_c2r = ((fft_size_x + FFTC2RY::ffts_per_block - 1) / FFTC2RY::ffts_per_block);
    auto       fft_2d_execution    = [&](hipStream_t stream) {
        fft_2d_kernel_y<FFTY, real_type, complex_type>
            <<<grid_fft_size_y_r2c, FFTY::block_dim, FFTY::shared_memory_size, stream>>>(
                cufftdx_real_values, cufftdx_complex_values, workspace_y_r2c);
        CUDA_CHECK_AND_EXIT(hipGetLastError());

        // In-place C2CF (R2C X dimension) and C2CI (C2R X dimension) kernel
        fft_2d_kernel_x<FFTR2CX,
                        FFTC2RX,
                        FFTY::output_length,
                        FFTY::output_length,
                        UseSharedMemoryStridedIO,
                        complex_type><<<grid_fft_size_x, FFTX::block_dim, fft_x_shared_memory, stream>>>(
            cufftdx_complex_values, cufftdx_complex_values, workspace_x_r2c, workspace_x_c2r);
        CUDA_CHECK_AND_EXIT(hipGetLastError());

        // Out-of-place C2R kernel (C2R Y dimension)
        fft_2d_kernel_y<FFTC2RY, complex_type, real_type>
            <<<grid_fft_size_y_c2r, FFTC2RY::block_dim, FFTC2RY::shared_memory_size, stream>>>(
                cufftdx_complex_values, cufftdx_real_values, workspace_y_c2r);
        CUDA_CHECK_AND_EXIT(hipGetLastError());
    };

    // Correctness run
    fft_2d_execution(stream);
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());
    // Copy results to host
    static constexpr size_t flat_fft_size       = fft_size_x * fft_size_y;
    static constexpr size_t flat_fft_size_bytes = flat_fft_size * sizeof(real_type);
    std::vector<real_type>  output_host(flat_fft_size, std::numeric_limits<real_type>::quiet_NaN());
    CUDA_CHECK_AND_EXIT(hipMemcpy(output_host.data(), cufftdx_real_values, flat_fft_size_bytes, hipMemcpyDeviceToHost));
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

    // Performance measurements
    auto time = example::measure_execution_ms(
        [&](hipStream_t stream) {
            fft_2d_execution(stream);
        },
        cufftdx_example_warm_up_runs,
        cufftdx_example_performance_runs,
        stream);

    // Return results
    return example::fft_results<RealType> {output_host, (time / cufftdx_example_performance_runs)};
}

// Example showing how cuFFTDx can be used to perform a 2D FFT R2C-C2R convolution in 3 kernels. In the 2nd kernel any scalar
// operation can be performed on the FFT data.
//
// Notes:
// * This examples shows how to use cuFFTDx to run multi-dimensional FFT. Final performance will vary depending on the
// FFT definitions (precision, size, type, ept, fpb) and other user customizations.
// * Best possible performance requires adapting parameters in the sample to particular set of parameters and code customizations.
// * Only FP32 was tested for this example, other types might require adjustments.
// * cuFFTDx with enabled shared memory IO usually be the faster cuFFTDx option for larger (>512) sizes.
// * The shared memory IO cuFFTDx has high shared memory requirements and will not work for all possible sizes in X dimension.
template<unsigned int Arch>
int fft_2d() {
    using precision_type                     = float;
    using complex_type                       = cufftdx::complex<precision_type>;
    using real_type                          = complex_type::value_type;

    // FFT
    static constexpr unsigned int fft_size_y = 1024;
    static constexpr unsigned int fft_size_x = 1024;
    // Kernel Settings
    static constexpr unsigned int ept_y = 16;
    static constexpr unsigned int fpb_y = 1;
    static constexpr unsigned int ept_x = 16;
    static constexpr unsigned int fpb_x = 8;

    // Other recommended configurations to test:
    // 1:
    // static constexpr unsigned int fft_size_y = 16384;
    // static constexpr unsigned int fft_size_x = 4096;
    // static constexpr unsigned int ept_y = 16;
    // static constexpr unsigned int fpb_y = 1;
    // static constexpr unsigned int ept_x = 16;
    // static constexpr unsigned int fpb_x = 2;
    // 2:
    // static constexpr unsigned int fft_size_y = 2048;
    // static constexpr unsigned int fft_size_x = 2048;
    // static constexpr unsigned int ept_y = 16;
    // static constexpr unsigned int fpb_y = 1;
    // static constexpr unsigned int ept_x = 8;
    // static constexpr unsigned int fpb_x = 4;
    // 3:
    // static constexpr unsigned int fft_size_y = 128;
    // static constexpr unsigned int fft_size_x = 128;
    // static constexpr unsigned int ept_y = 16;
    // static constexpr unsigned int fpb_y = 1;
    // static constexpr unsigned int ept_x = 16;
    // static constexpr unsigned int fpb_x = 8;

    using namespace cufftdx;
    using fft_base  = decltype(Block() + Precision<precision_type>() + SM<Arch>());
    using fft_y_r2c = decltype(fft_base() + Type<fft_type::r2c>() + Size<fft_size_y>() + ElementsPerThread<ept_y>() +
                               FFTsPerBlock<fpb_y>());
    using fft_x_r2c =
        decltype(fft_base() + Type<fft_type::c2c>() + Size<fft_size_x>() + Direction<fft_direction::forward>() +
                 ElementsPerThread<ept_x>() + FFTsPerBlock<fpb_x>());
    using fft_y_c2r = cufftdx::replace_t<fft_y_r2c, Type<fft_type::c2r>>;
    using fft_x_c2r = cufftdx::replace_t<fft_x_r2c, Direction<fft_direction::inverse>>;

    // Host data
    static constexpr size_t flat_fft_size_real          = fft_size_x * fft_size_y;
    static constexpr size_t flat_fft_size_complex       = fft_size_x * fft_y_r2c::output_length;
    static constexpr size_t flat_fft_size_real_bytes    = flat_fft_size_real * sizeof(precision_type);
    static constexpr size_t flat_fft_size_complex_bytes = flat_fft_size_complex * sizeof(complex_type);
#ifdef CUFFTDX_EXAMPLE_DETAIL_DEBUG_FFT_2D
    std::vector<precision_type> input_host(flat_fft_size_real);
    for (size_t i = 0; i < flat_fft_size_real; i++) {
        float sign    = (i % 3 == 0) ? -1.0f : 1.0f;
        input_host[i] = sign * static_cast<float>(i) / flat_fft_size_real;
    }
#else
    auto input_host = example::get_random_real_data<precision_type>(flat_fft_size_real, -1, 1);
#endif

    // Device data
    real_type* real_values;
    complex_type* complex_values;
    CUDA_CHECK_AND_EXIT(hipMalloc(&real_values, flat_fft_size_real_bytes));
    CUDA_CHECK_AND_EXIT(hipMalloc(&complex_values, flat_fft_size_complex_bytes));

    // Copy host to device
    CUDA_CHECK_AND_EXIT(hipMemset(complex_values, 0b11111111, flat_fft_size_complex_bytes));
    CUDA_CHECK_AND_EXIT(hipMemcpy(real_values, input_host.data(), flat_fft_size_real_bytes, hipMemcpyHostToDevice));
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

    hipStream_t stream;
    CUDA_CHECK_AND_EXIT(hipStreamCreate(&stream));

    // cuFFTDx fused 2D R2C->C2R
    // * the 2nd R2C (dim X) kernel and the 1st (dim X) C2R kernel are fused into one
    // * the final results are stored in real_values
    auto cufftdx_results =
        cufftdx_fft_2d_r2c_c2r<fft_x_r2c, fft_y_r2c, fft_x_c2r, fft_y_c2r, false>(real_values, complex_values, stream);
    CUDA_CHECK_AND_EXIT(hipMemcpy(real_values, input_host.data(), flat_fft_size_real_bytes, hipMemcpyHostToDevice));
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

    // cuFFTDx fused 2D R2C->C2R
    // * the 2nd R2C (dim X) kernel and the 1st (dim X) C2R kernel are fused into one
    // * the final results are stored in real_values
    // * Uses shared memory to speed-up IO in the strided kernel
    auto cufftdx_smemio_results =
        cufftdx_fft_2d_r2c_c2r<fft_x_r2c, fft_y_r2c, fft_x_c2r, fft_y_c2r, true>(real_values, complex_values, stream);
    CUDA_CHECK_AND_EXIT(hipMemcpy(real_values, input_host.data(), flat_fft_size_real_bytes, hipMemcpyHostToDevice));
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

    // cuFFT 2D R2C->C2R
    // * the final results are stored in real_values
    auto cufft_results = cufft_fft_2d_r2c_c2r(fft_size_x, fft_size_y, real_values, complex_values, stream);
    CUDA_CHECK_AND_EXIT(hipMemcpy(real_values, input_host.data(), flat_fft_size_real_bytes, hipMemcpyHostToDevice));
    CUDA_CHECK_AND_EXIT(hipDeviceSynchronize());

    // Destroy created CUDA stream
    CUDA_CHECK_AND_EXIT(hipStreamDestroy(stream));

    // Free CUDA buffers
    CUDA_CHECK_AND_EXIT(hipFree(real_values));
    CUDA_CHECK_AND_EXIT(hipFree(complex_values));

    std::cout << "FFT: (" << fft_size_x << ", " << fft_size_y << ")\n";

#ifdef CUFFTDX_EXAMPLE_DETAIL_DEBUG_FFT_2D
    std::cout << "cuFFT, cuFFTDx\n";
    for (size_t i = 0; i < 8; i++) {
        std::cout << i << ": ";
        std::cout << "(" << cufft_output_host[i] << ")";
        std::cout << ", ";
        std::cout << "(" << cufftdx_output_host[i] << ")";
        std::cout << "\n";
    }
#endif

    bool success = true;
    // Check if cuFFTDx results are correct
    {
        auto fft_error =
            example::fft_signal_error::calculate_for_real_values(cufftdx_results.output, cufft_results.output);
        std::cout << "cuFFTDx\n";
        std::cout << "L2 error: " << fft_error.l2_relative_error << "\n";
        std::cout << "Peak error (index: " << fft_error.peak_error_index << "): " << fft_error.peak_error << "\n";
        std::cout << "Peak relative error (index: " << fft_error.peak_error_index << "): " << fft_error.peak_error_relative << "\n";
        if (success) {
            success = (fft_error.l2_relative_error < 0.001);
        }
    }
    // Check cuFFTDx with shared memory io
    {
        auto fft_error =
            example::fft_signal_error::calculate_for_real_values(cufftdx_smemio_results.output, cufft_results.output);
        std::cout << "cuFFTDx (shared memory IO)\n";
        std::cout << "L2 error: " << fft_error.l2_relative_error << "\n";
        std::cout << "Peak error (index: " << fft_error.peak_error_index << "): " << fft_error.peak_error << "\n";
        std::cout << "Peak relative error (index: " << fft_error.peak_error_index << "): " << fft_error.peak_error_relative << "\n";
        if (success) {
            success = (fft_error.l2_relative_error < 0.001);
        }
    }

    // Print performance results
    if (success) {
        std::cout << "\nPerformance results:\n";
        std::cout << std::setw(28) << "cuFFTDx: " << cufftdx_results.avg_time_in_ms << " [ms]\n";
        std::cout << std::setw(28) << "cuFFTDx (shared memory IO): " << cufftdx_smemio_results.avg_time_in_ms
                  << " [ms]\n";
        std::cout << std::setw(28) << "cuFFT: " << cufft_results.avg_time_in_ms << " [ms]\n";
    }

    if (success) {
        std::cout << "Success\n";
        return 0;
    } else {
        std::cout << "Failure\n";
        return 1;
    }
}

template<unsigned int Arch>
struct fft_2d_functor {
    int operator()() { return fft_2d<Arch>(); }
};

int main(int, char**) {
    return example::sm_runner<fft_2d_functor>();
}
