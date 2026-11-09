/*
 * SPDX-FileCopyrightText: Copyright (c) 1993-2022 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

#include <algorithm>          // std::fill
#include <cstdio>             // printf
#include <cstdlib>            // EXIT_FAILURE
#include <hip/hip_runtime.h>             // cuMemCreate
#include <hip/hip_runtime_api.h> // cudaMalloc, cudaMemcpy, etc.
#include <hipsparse.h>         // hipsparseAxpby
#include <numeric>            // std::iota

#define CHECK_DRV(func)                                                        \
{                                                                              \
    hipError_t status = (func);                                                  \
    if (status != hipSuccess) {                                              \
        const char* error_str;                                                 \
        hipDrvGetErrorString(status, &error_str);                                  \
        std::printf("cuMem API failed at line %d with error: %s (%d)\n",       \
                    __LINE__, error_str, status);                              \
        std::exit(EXIT_FAILURE);                                               \
    }                                                                          \
}

#define CHECK_CUDA(func)                                                       \
{                                                                              \
    hipError_t status = (func);                                               \
    if (status != hipSuccess) {                                               \
        std::printf("CUDA API failed at line %d with error: %s (%d)\n",        \
                    __LINE__, hipGetErrorString(status), status);             \
        std::exit(EXIT_FAILURE);                                               \
    }                                                                          \
}

#define CHECK_CUSPARSE(func)                                                   \
{                                                                              \
    hipsparseStatus_t status = (func);                                          \
    if (status != HIPSPARSE_STATUS_SUCCESS) {                                   \
        std::printf("CUSPARSE API failed at line %d with error: %s (%d)\n",    \
                    __LINE__, hipsparseGetErrorString(status), status);         \
        std::exit(EXIT_FAILURE);                                               \
    }                                                                          \
}

size_t round_up(size_t value, size_t div) {
    return ((value + div - 1) / div) * div;
}

//------------------------------------------------------------------------------

template<typename T>
class drvMemory {
public:
    explicit drvMemory(int64_t num_items, const T* h_values) {
        // DRIVER CONTEXT
        auto     size_bytes = num_items * sizeof(T);
        hipDevice_t dev        = 0;
        // (1) Set allocation properties, enable compression
        hipMemAllocationProp prop = {};
        prop.allocFlags.compressionType = CU_MEM_ALLOCATION_COMP_GENERIC;
        prop.type                       = hipMemAllocationTypePinned;
        prop.location.type              = hipMemLocationTypeDevice;
        prop.location.id                = static_cast<int>(dev);
        prop.win32HandleMetaData        = 0;

        // (2) Retrieve allocation granularity
        size_t granularity = 0;
        CHECK_DRV( hipMemGetAllocationGranularity(&granularity, &prop,
                                            hipMemAllocationGranularityMinimum) )
        _padded_size = round_up(size_bytes, granularity);

        // (3) Reverse Address range
        hipDeviceptr_t d_ptr_raw = 0ULL;
        CHECK_DRV( hipMemAddressReserve(&d_ptr_raw, _padded_size, 0, 0, 0) )

        // (4) Create the Allocation Handle
        CHECK_DRV( hipMemCreate(&_allocation_handle, _padded_size, &prop, 0) )

        // (5) Memory mappping
        CHECK_DRV( hipMemMap(d_ptr_raw, _padded_size, 0, _allocation_handle, 0) )

        // (6) Verify that the allocation properties are supported
        CHECK_DRV( hipMemGetAllocationPropertiesFromHandle(&prop,
                                                          _allocation_handle) )

        // (7) Set Access Permissions
        hipMemAccessDesc accessDesc = {};
        accessDesc.location        = prop.location;
        accessDesc.flags           = hipMemAccessFlagsProtReadWrite;
        CHECK_DRV( hipMemSetAccess(d_ptr_raw, _padded_size, &accessDesc, 1) )

        // (7) Convert the raw pointer
        _d_ptr = reinterpret_cast<T*>(d_ptr_raw);
        CHECK_CUDA( hipMemcpy(_d_ptr, h_values, num_items * sizeof(T),
                               hipMemcpyHostToDevice) )
    }

    T* ptr() const { return static_cast<T*>(_d_ptr); }

    ~drvMemory() {
        auto ptr = reinterpret_cast<hipDeviceptr_t>(_d_ptr);
        CHECK_DRV( hipMemUnmap(ptr, _padded_size)       )
        CHECK_DRV( hipMemAddressFree(ptr, _padded_size) )
        CHECK_DRV( hipMemRelease(_allocation_handle)    )
    }

private:
    hipMemGenericAllocationHandle_t _allocation_handle {};
    size_t                       _padded_size       { 0 };
    void*                        _d_ptr             { nullptr };
};

//------------------------------------------------------------------------------

template<typename T>
class cudaMemory {
public:
    explicit cudaMemory(int64_t num_items, const T* h_values) {
        CHECK_CUDA( hipMalloc(reinterpret_cast<void**>(&_d_ptr),
                               num_items * sizeof(T)) )
        CHECK_CUDA( hipMemcpy(_d_ptr, h_values, num_items * sizeof(T),
                               hipMemcpyHostToDevice) )
    }

    T* ptr() const { return _d_ptr; }

    ~cudaMemory() { CHECK_CUDA( hipFree(_d_ptr) ) }

private:
    T* _d_ptr { nullptr };
};

//------------------------------------------------------------------------------

float benchmark(int64_t nnz,
                int64_t size,
                void*   dX_indices,
                void*   dX_values,
                void*   dY) {
    float alpha = 1.0f;
    float beta  = 1.0f;
    // CUSPARSE APIs
    hipsparseHandle_t     handle = NULL;
    hipsparseSpVecDescr_t vecX;
    hipsparseDnVecDescr_t vecY;
    CHECK_CUSPARSE( hipsparseCreate(&handle) )
    // Create sparse vector X
    CHECK_CUSPARSE( hipsparseCreateSpVec(&vecX, size, nnz, dX_indices, dX_values,
                                        HIPSPARSE_INDEX_32I,
                                        HIPSPARSE_INDEX_BASE_ZERO, HIP_R_32F) )
    // Create dense vector y
    CHECK_CUSPARSE( hipsparseCreateDnVec(&vecY, size, dY, HIP_R_32F) )

    // Warmup run
    CHECK_CUSPARSE( hipsparseAxpby(handle, &alpha, vecX, &beta, vecY) )
    CHECK_CUDA( hipDeviceSynchronize() )
    // Timer setup
    float       elapsed_ms = 0;
    hipEvent_t start_event{}, stop_event{};
    CHECK_CUDA( hipEventCreate(&start_event) )
    CHECK_CUDA( hipEventCreate(&stop_event) )
    CHECK_CUDA( hipEventRecord(start_event, nullptr) )

    // Computation
    for (int i = 0; i < 10; i++)
        hipsparseAxpby(handle, &alpha, vecX, &beta, vecY);

    CHECK_CUDA( hipEventRecord(stop_event, nullptr) )
    CHECK_CUDA( hipEventSynchronize(stop_event) )
    CHECK_CUDA( hipEventElapsedTime(&elapsed_ms, start_event, stop_event) )
    CHECK_CUDA( hipEventDestroy(start_event) )
    CHECK_CUDA( hipEventDestroy(stop_event) )

    // Destroy matrix/vector descriptors
    CHECK_CUSPARSE( hipsparseDestroySpVec(vecX) )
    CHECK_CUSPARSE( hipsparseDestroyDnVec(vecY) )
    CHECK_CUSPARSE( hipsparseDestroy(handle) )
    return elapsed_ms;
}

//------------------------------------------------------------------------------
 constexpr int EXIT_UNSUPPORTED = 2;

int main() {
    hipFree(nullptr);
    // Without a previous CUDA runtime call (e.g. cudaMalloc) we need to
    // explicitly initialize the context:
    //
    // CUcontext ctx;
    // CHECK_DRV( cuInit(0) )
    // CHECK_DRV( cuDevicePrimaryCtxRetain(&ctx, 0) )
    // CHECK_DRV( cuCtxSetCurrent(ctx) )
    // CHECK_DRV( cuCtxGetDevice(&dev) )

    // Check if Memory Compression and Virtual Address Management is supported
    hipDevice_t dev                 = 0;
    int      supportsCompression = 0;
    int      supportsVMM         = 0;
    CHECK_DRV( hipDeviceGetAttribute(
                    &supportsCompression,
                    CU_DEVICE_ATTRIBUTE_GENERIC_COMPRESSION_SUPPORTED, dev) )
    if (supportsCompression == 0) {
        std::printf("\nL2 compression is not supported on the "
                    "current device\n\n");
        return EXIT_UNSUPPORTED;
    }
    CHECK_DRV( hipDeviceGetAttribute(
                    &supportsVMM,
                    CU_DEVICE_ATTRIBUTE_VIRTUAL_ADDRESS_MANAGEMENT_SUPPORTED,
                    dev) )
    if (supportsVMM == 0) {
        std::printf("\nVirtual Memory Management is not supported on the "
                    "current device\n\n");
        return EXIT_UNSUPPORTED;
    }
    //--------------------------------------------------------------------------
    // Host problem definition
    int64_t size       = 134217728; // 2^27
    int64_t nnz        = 134217728; // 2^27
    auto    hX_indices = new int[nnz];
    auto    hX_values  = new float[nnz];
    auto    hY         = new float[size];

    std::iota(hX_indices, hX_indices + nnz, 0);
    std::fill(hX_values,  hX_values + nnz,  1.0f);
    std::fill(hY,         hY + size,        1.0f);
    //--------------------------------------------------------------------------
    // Device memory management
    float cuda_elapsed_ms = 0.0f;
    float drv_elapsed_ms  = 0.0f;
    {
        cudaMemory<int>   dX_indices_cuda{nnz, hX_indices};
        cudaMemory<float> dX_values_cuda{nnz,  hX_values};
        cudaMemory<float> dY_cuda{size, hY};
        cuda_elapsed_ms = benchmark(nnz, size, dX_indices_cuda.ptr(),
                                    dX_values_cuda.ptr(), dY_cuda.ptr());
    }
    {
        drvMemory<int>   dX_indices_drv{nnz, hX_indices};
        drvMemory<float> dX_values_drv{nnz,  hX_values};
        drvMemory<float> dY_drv{size, hY};
        drv_elapsed_ms = benchmark(nnz, size, dX_indices_drv.ptr(),
                                   dX_values_drv.ptr(), dY_drv.ptr());
    }
    delete[] hX_indices;
    delete[] hX_values;
    delete[] hY;
    auto speedup = ((cuda_elapsed_ms - drv_elapsed_ms) / cuda_elapsed_ms)
                    * 100.0f;
    std::printf("\nStandard call:    %.1f ms"
                "\nL2 Compression:   %.1f ms"
                "\nPerf improvement: %.1f%%\n\n",
                cuda_elapsed_ms, drv_elapsed_ms, speedup);
    return EXIT_SUCCESS;
}