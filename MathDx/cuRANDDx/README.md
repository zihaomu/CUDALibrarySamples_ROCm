# cuRANDDx Library - API Examples

All examples are shipped within [cuRANDDx package](https://developer.nvidia.com/curanddx-downloads).

## Description

This folder demonstrates cuRANDDx APIs usage.

* [cuRANDDx API documentation](https://docs.nvidia.com/cuda/curanddx/index.html)

## Requirements

* [See cuRANDDx requirements](https://docs.nvidia.com/cuda/curanddx/get_started/requirement.html)
* CMake 3.23 or newer
* Linux system with installed NVIDIA drivers
* NVIDIA GPU of Turing (SM75) or newer architecture

## Build

* You may specify `CURANDDX_CUDA_ARCHITECTURES` to limit CUDA architectures used for compilation (see [CMake:CUDA_ARCHITECTURES](https://cmake.org/cmake/help/latest/prop_tgt/CUDA_ARCHITECTURES.html#prop_tgt:CUDA_ARCHITECTURES))
* `mathdx_ROOT` - path to mathDx package (XX.Y - version of the package)

```
mkdir build && cd build
cmake -DCURANDDX_CUDA_ARCHITECTURES=80-real -Dmathdx_ROOT=<path_of_mathdx>/mathdx/XX.Y ..
make
# Run
ctest
```

## Examples

For the detailed descriptions of the examples please visit [Examples](https://docs.nvidia.com/cuda/curanddx/index.html) section of the cuRANDDx documentation.

| Group                 | Example                             | Description                                                                                          |
| --------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Introduction Examples | philox_thread_api                   | Introduction example explaining the basics of cuRANDDx using the Philox generator                    |
| Thread API Examples   | pcg_thread_api                      | Use the PCG generator to create 32-bit random numbers matching NVPL RAND with strict ordering        |
|                       | philox_random_bits_thread_api       | Use the Philox generator to generate a sequence of random bits                                       |
|                       | xorwow_init_and_generate_thread_api | Set up generator states first, then generate random numbers in later kernels                         |
|                       | mrg_two_distributions_thread_api    | Generate two sequences of different distributions in a single kernel using skip functions (MRG32k3a) |
|                       | sobol_thread_api                    | Generate quasirandom numbers using the 64-bit scrambled Sobol generator                              |
| NVRTC Examples        | nvrtc_pcg_thread_api                | Use cuRANDDx with NVRTC runtime compilation                                                          |

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

7 个独立源入口；PASSED 0，PARTIAL 1，FAILED 6，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：rocRAND device API。候选不等于已使用；基础探针成功也不等于整库迁移成功。

rocRAND设备Philox4x32-10原生引擎与独立整数oracle逐word通过；显式53bit Box-Muller数学通过。原生normal头/overlay接口差异及NVIDIA LEGACY逐位host/device序列未等价，PARTIAL。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [01_introduction/philox_thread_api.cu](01_introduction/philox_thread_api.cu) · [详情](../../migration/sample-reports/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu.md) | rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal / rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal | L4 / PARTIAL | 使用rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。使用真实rocRAND Philox设备引擎，CPU整数oracle逐word验证counter/subsequence；分布使用显式53-bit Box-Muller。ROCm normal头与当前overlay不兼容，且不声称原例NVIDIA LEGACY host/device逐位相等。 | FAILED / PASSED | [记录](../../migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu)；[记录](../../migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/MathDx_cuRANDDx_01_introduction_philox_thread_api.cu) |
| [02_thread_api/mrg_two_distributions_thread_api.cu](02_thread_api/mrg_two_distributions_thread_api.cu) · [详情](../../migration/sample-reports/MathDx/cuRANDDx/02_thread_api/mrg_two_distributions_thread_api.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/02_thread_api/mrg_two_distributions_thread_api.cu:28:10: fatal error: 'curanddx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_librar | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_02_thread_api_mrg_two_distributions_thread_api.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_02_thread_api_mrg_two_distributions_thread_api.cu) |
| [02_thread_api/pcg_thread_api.cu](02_thread_api/pcg_thread_api.cu) · [详情](../../migration/sample-reports/MathDx/cuRANDDx/02_thread_api/pcg_thread_api.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/02_thread_api/pcg_thread_api.cu:22:10: fatal error: 'curanddx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspac | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_02_thread_api_pcg_thread_api.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_02_thread_api_pcg_thread_api.cu) |
| [02_thread_api/philox_random_bits_thread_api.cu](02_thread_api/philox_random_bits_thread_api.cu) · [详情](../../migration/sample-reports/MathDx/cuRANDDx/02_thread_api/philox_random_bits_thread_api.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/02_thread_api/philox_random_bits_thread_api.cu:22:10: fatal error: 'curanddx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_ | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_02_thread_api_philox_random_bits_thread_api.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_02_thread_api_philox_random_bits_thread_api.cu) |
| [02_thread_api/sobol_thread_api.cu](02_thread_api/sobol_thread_api.cu) · [详情](../../migration/sample-reports/MathDx/cuRANDDx/02_thread_api/sobol_thread_api.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/02_thread_api/sobol_thread_api.cu:23:10: fatal error: 'curanddx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_worksp | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_02_thread_api_sobol_thread_api.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_02_thread_api_sobol_thread_api.cu) |
| [02_thread_api/xorwow_init_and_generate_thread_api.cu](02_thread_api/xorwow_init_and_generate_thread_api.cu) · [详情](../../migration/sample-reports/MathDx/cuRANDDx/02_thread_api/xorwow_init_and_generate_thread_api.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/02_thread_api/xorwow_init_and_generate_thread_api.cu:22:10: fatal error: 'curanddx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_lib | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_02_thread_api_xorwow_init_and_generate_thread_api.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_02_thread_api_xorwow_init_and_generate_thread_api.cu) |
| [03_nvrtc/nvrtc_pcg_thread_api.cpp](03_nvrtc/nvrtc_pcg_thread_api.cpp) · [详情](../../migration/sample-reports/MathDx/cuRANDDx/03_nvrtc/nvrtc_pcg_thread_api.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/03_nvrtc/nvrtc_helper.hpp:66:53: error: use of undeclared identifier 'CURANDDX_INCLUDE_DIRS'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuRANDDx/03_nvrtc/nvrtc_pcg_thread_api.cpp:76:27: error: expected '}' | FAILED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuRANDDx_03_nvrtc_nvrtc_pcg_thread_api.cpp)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuRANDDx_03_nvrtc_nvrtc_pcg_thread_api.cpp) |

生成来源：[migration/samples.yaml](../../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
