# nvCOMPDx Examples

## Description

This folder contains examples demonstrating the usage of the nvCOMPDx C++ API.

## Examples

- [LZ4 GPU compression introduction](01_introduction/lz4_gpu_compression_introduction.cu)

  The introductory sample demonstrates warp-level GPU LZ4 compression and decompression via nvCOMPDx. Note that the example presented here is deliberately simple to demonstrate the basic usage of nvCOMPDx and is **not** optimized for performance.

  ```sh
  lz4_gpu_compression_introduction -f <input file> -o <output file>
  ```

- [LZ4 GPU compression and decompression](02_lz4_gpu/lz4_gpu_compression_decompression.cu)

  The sample demonstrates warp-level GPU LZ4 compression and decompression into global memory via nvCOMPDx.

  ```sh
  lz4_gpu_compression_decompression -t {uint8|uint16|uint32} -f <input file(s)>
  ```

- [LZ4 CPU compression](03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu)

  The sample demonstrates CPU LZ4 compression via `lz4::LZ4_compress_HC`, and subsequent warp-level GPU decompression into global memory via nvCOMPDx.

  ```sh
  lz4_cpu_compression_gpu_decompression -f <input file(s)>
  ```

- [LZ4 CPU decompression](03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu)

  The sample demonstrates warp-level GPU LZ4 compression into global memory via nvCOMPDx, and subsequent CPU decompression via `lz4::LZ4_decompress_safe`.

  ```sh
  lz4_gpu_compression_cpu_decompression -f <input file(s)>
  ```

- [ANS GPU compression and decompression](04_ans_gpu/ans_gpu_compression_decompression.cu)

  The sample demonstrates block-level GPU ANS compression and decompression into global memory via nvCOMPDx.

  ```sh
  ans_gpu_compression_decompression -t {uint8|float16} -f <input file(s)>
  ```

- [ANS decompress and reduce](04_ans_gpu/ans_gpu_decompression_reduction.cu)

  The sample demonstrates GPU ANS decompression followed by a reduction operation fused within the same GPU kernel.

  ```sh
  ans_gpu_decompression_and_reduction
  ```

- [LZ4 NVRTC+nvJitLink](05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu)

  The sample demonstrates CPU LZ4 compression via `lz4::LZ4_compress_HC`, and subsequent warp-level GPU decompression into global memory via a runtime-compiled and linked kernel by NVRTC and nvJitLink. The non-runtime-compiled variant can be found [here](03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu).

  ```sh
  lz4_cpu_compression_nvrtc_decompression -f <input file(s)>
  ```

## Building (x86-64, or aarch64)

The samples require the following external libraries to be installed prior to compilation: `lz4`.

### Linux

The external libraries can be installed via a package manager (both on ARM and on x86):

```sh
# Ubuntu:
# LZ4
sudo apt-get install liblz4-dev
sudo apt-get install liblz4-1

# Red Hat:
# LZ4
dnf install lz4-devel
dnf install lz4-libs
```

Alternatively, they can also be compiled from source.

Afterwards, the example compilation via CMake is relatively simple:

```sh
cd <nvCOMPDx example folder>
mkdir build
cd build

cmake .. -DCMAKE_PREFIX_PATH=<MathDx sysroot path> \
         -DCMAKE_BUILD_TYPE=Release

cmake --build .
```

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

7 个独立源入口；PASSED 0，PARTIAL 0，FAILED 7，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipCOMP algorithm reuse (device API unresolved)。候选不等于已使用；基础探针成功也不等于整库迁移成功。

hipCOMP 的 host API 不等于 device-callable nvCOMPDx；原始设备融合/CPU互通/ANS 等需要专门重写。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [01_introduction/lz4_gpu_compression_introduction.cu](01_introduction/lz4_gpu_compression_introduction.cu) · [详情](../../migration/sample-reports/MathDx/nvCOMPDx/01_introduction/lz4_gpu_compression_introduction.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/nvCOMPDx/01_introduction/lz4_gpu_compression_introduction.cu:25:10: fatal error: 'nvcompdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libr | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_nvCOMPDx_01_introduction_lz4_gpu_compression_introduction.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_nvCOMPDx_01_introduction_lz4_gpu_compression_introduction.cu) |
| [02_lz4_gpu/lz4_gpu_compression_decompression.cu](02_lz4_gpu/lz4_gpu_compression_decompression.cu) · [详情](../../migration/sample-reports/MathDx/nvCOMPDx/02_lz4_gpu/lz4_gpu_compression_decompression.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/nvCOMPDx/02_lz4_gpu/lz4_gpu_compression_decompression.cu:19:10: fatal error: 'nvcompdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_nvCOMPDx_02_lz4_gpu_lz4_gpu_compression_decompression.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_nvCOMPDx_02_lz4_gpu_lz4_gpu_compression_decompression.cu) |
| [03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu](03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu) · [详情](../../migration/sample-reports/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu:19:10: fatal error: 'lz4.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_lib | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_nvCOMPDx_03_lz4_gpu_and_cpu_lz4_cpu_compression_gpu_decompression.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_nvCOMPDx_03_lz4_gpu_and_cpu_lz4_cpu_compression_gpu_decompression.cu) |
| [03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu](03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu) · [详情](../../migration/sample-reports/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu:19:10: fatal error: 'lz4.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_lib | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_nvCOMPDx_03_lz4_gpu_and_cpu_lz4_gpu_compression_cpu_decompression.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_nvCOMPDx_03_lz4_gpu_and_cpu_lz4_gpu_compression_cpu_decompression.cu) |
| [04_ans_gpu/ans_gpu_compression_decompression.cu](04_ans_gpu/ans_gpu_compression_decompression.cu) · [详情](../../migration/sample-reports/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_compression_decompression.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_compression_decompression.cu:19:10: fatal error: 'nvcompdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_nvCOMPDx_04_ans_gpu_ans_gpu_compression_decompression.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_nvCOMPDx_04_ans_gpu_ans_gpu_compression_decompression.cu) |
| [04_ans_gpu/ans_gpu_decompression_reduction.cu](04_ans_gpu/ans_gpu_decompression_reduction.cu) · [详情](../../migration/sample-reports/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_decompression_reduction.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_decompression_reduction.cu:23:10: fatal error: 'nvcompdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_s | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_nvCOMPDx_04_ans_gpu_ans_gpu_decompression_reduction.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_nvCOMPDx_04_ans_gpu_ans_gpu_decompression_reduction.cu) |
| [05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu](05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu) · [详情](../../migration/sample-reports/MathDx/nvCOMPDx/05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/nvCOMPDx/05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu:19:10: fatal error: 'lz4.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda | BLOCKED / BLOCKED | [记录](../../migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_nvCOMPDx_05_lz4_cpu_and_nvrtc_lz4_cpu_compression_nvrtc_decompression.cu)；[记录](../../migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_nvCOMPDx_05_lz4_cpu_and_nvrtc_lz4_cpu_compression_nvrtc_decompression.cu) |

生成来源：[migration/samples.yaml](../../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
