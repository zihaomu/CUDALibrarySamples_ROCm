# libmathdx Library - API Examples

All examples are shipped within [libmathdx package](https://developer.nvidia.com/cublasdx-downloads).

## Description

This folder demonstrates libmathdx APIs usage. libmathdx is a runtime library for MathDx enabling JIT compilation of MathDx operations.
libmathdx exposes a simple C-API interface for ease of adoption in non-C++ projects, and is the backend powering NVIDIA Python projects such as [Warp](https://developer.nvidia.com/warp-python) and [nvmath-python](https://developer.nvidia.com/nvmath-python).

* [libmathdx download page](https://developer.nvidia.com/cublasdx-downloads)
* [libmathdx API documentation](https://docs.nvidia.com/cuda/libmathdx/index.html)

## Requirements

* CMake 3.31 or newer
* Linux or Windows system with installed NVIDIA drivers
* NVIDIA GPU of Turing (SM75) or newer architecture
* CUDA Toolkit 13.X

## Build

* The examples use `find_package(libmathdx CONFIG REQUIRED)`, which consumes the `libmathdx-config.cmake` shipped under `lib/cmake/libmathdx/` in the libmathdx package. Point CMake at the package with `-DCMAKE_PREFIX_PATH=<libmathdx_path>` or `-Dlibmathdx_ROOT=<libmathdx_path>`.

Linux build:
```bash
mkdir build && cd build
cmake .. # or cmake -Dlibmathdx_ROOT=<libmathdx_path> ..
make
# Run
LD_LIBRARY_PATH=<cuda_root_directory>/lib64 ctest --parallel 8
```

Windows build:
```bat
mkdir build && cd build
cmake .. # or cmake -Dlibmathdx_ROOT=<libmathdx_path> ..
cmake --build . --config Release
REM Run
set PATH=%PATH%;<libmathdx_dll_path>;<cuda_library_path>
ctest -C Release --parallel 8
```

Python wheels:
libmathdx is also shipped as downloadable wheels on [PyPI](https://pypi.org/project/nvidia-libmathdx-cu13/):
```bash
pip install nvidia-libmathdx-cu13
```

Optional environment variables:
* `LIBMATHDX_EXAMPLE_VERBOSE` - print generated kernel source to stdout
* `LIBMATHDX_EXAMPLE_DUMP_FILENAME=<path>` - write JITed intermediates to a file

See the [libmathdx documentation](https://docs.nvidia.com/cuda/libmathdx/index.html) for more details.

## Examples

For the detailed descriptions of the examples please visit the Examples section of the [libmathdx documentation](https://docs.nvidia.com/cuda/libmathdx/index.html).

| Group               | Example                                  | Description                                                                     |
|---------------------|------------------------------------------|---------------------------------------------------------------------------------|
| cuFFTDx Examples    | cufftdx                                  | cuFFTDx API introduction example, performs a C2C FFT                            |
|                     | cufftdx_heuristics                       | Performs a C2C FFT with queryable tuning knobs                                  |
| cuBLASDx Examples   | cublasdx                                 | cuBLASDx API introduction example, performs a GEMM                              |
|                     | cublasdx_tensor                          | Performs a GEMM with the Opaque Tensor API                                      |
|                     | cublasdx_pipeline                        | Performs a GEMM using the pipelining APIs                                       |
|                     | cublasdx_pipelining_callback             | Performs a GEMM using pipelining/TMA instructions with a user callback function |
| cuSolverDx Examples | cusolverdx_trsm                          | cuSolverDx API introduction example, performs a triangular matrix solve         |
|                     | cusolverdx_potrf                         | Performs Cholesky factorization                                                 |
|                     | cusolverdx_potrs                         | Performs a linear solve using Cholesky factors                                  |
| cuRANDDx Examples   | curanddx                                 | cuRANDDx API introduction example, generates random numbers                     |
| nvCOMPDx Examples   | nvcompdx                                 | nvCOMPDx API introduction example, builds an LZ4 compress device function       |
|                     | nvcompdx_batch                           | End-to-end LZ4 compress/decompress round-trip across a batch of chunks          |

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

12 个独立源入口；PASSED 0，PARTIAL 0，FAILED 12，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：HIPRTC + device algorithms。候选不等于已使用；基础探针成功也不等于整库迁移成功。

HIPRTC 已在 FFT JIT 路线验证，但不自带原始 libmathdx 的各设备算法生成器/描述 DSL，尚未等价改写。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [cublasdx.cpp](cublasdx.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cublasdx.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cublasdx.cpp:18:10: fatal error: 'libcublasdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibra | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cublasdx.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cublasdx.cpp) |
| [cublasdx_pipeline.cpp](cublasdx_pipeline.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cublasdx_pipeline.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cublasdx_pipeline.cpp:19:10: fatal error: 'libcublasdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/ | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cublasdx_pipeline.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cublasdx_pipeline.cpp) |
| [cublasdx_pipelining_callback.cpp](cublasdx_pipelining_callback.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cublasdx_pipelining_callback.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cublasdx_pipelining_callback.cpp:19:10: fatal error: 'libcublasdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_works | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cublasdx_pipelining_callback.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cublasdx_pipelining_callback.cpp) |
| [cublasdx_tensor.cpp](cublasdx_tensor.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cublasdx_tensor.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cublasdx_tensor.cpp:18:10: fatal error: 'libcommondx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CU | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cublasdx_tensor.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cublasdx_tensor.cpp) |
| [cufftdx.cpp](cufftdx.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cufftdx.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cufftdx.cpp:19:10: fatal error: 'libcufftdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrary | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cufftdx.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cufftdx.cpp) |
| [cufftdx_heuristics.cpp](cufftdx_heuristics.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cufftdx_heuristics.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cufftdx_heuristics.cpp:18:10: fatal error: 'libcufftdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/ | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cufftdx_heuristics.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cufftdx_heuristics.cpp) |
| [curanddx.cpp](curanddx.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/curanddx.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/curanddx.cpp:19:10: fatal error: 'libcuranddx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibra | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_curanddx.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_curanddx.cpp) |
| [cusolverdx_potrf.cpp](cusolverdx_potrf.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cusolverdx_potrf.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cusolverdx_potrf.cpp:18:10: fatal error: 'libcusolverdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cusolverdx_potrf.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cusolverdx_potrf.cpp) |
| [cusolverdx_potrs.cpp](cusolverdx_potrs.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cusolverdx_potrs.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cusolverdx_potrs.cpp:18:10: fatal error: 'libcusolverdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cusolverdx_potrs.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cusolverdx_potrs.cpp) |
| [cusolverdx_trsm.cpp](cusolverdx_trsm.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/cusolverdx_trsm.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/cusolverdx_trsm.cpp:18:10: fatal error: 'libcusolverdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/ | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_cusolverdx_trsm.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_cusolverdx_trsm.cpp) |
| [nvcompdx.cpp](nvcompdx.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/nvcompdx.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/nvcompdx.cpp:18:10: fatal error: 'libnvcompdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibra | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_nvcompdx.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_nvcompdx.cpp) |
| [nvcompdx_batch.cpp](nvcompdx_batch.cpp) · [详情](../../migration/sample-reports/MathDx/libmathdx/nvcompdx_batch.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/libmathdx/nvcompdx_batch.cpp:19:10: fatal error: 'libnvcompdx.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUD | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_libmathdx_nvcompdx_batch.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_libmathdx_nvcompdx_batch.cpp) |

生成来源：[migration/samples.yaml](../../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
