# cuPQC Library - API Examples

All examples are shipped within [cuPQC Software Development Kit](https://developer.nvidia.com/cupqc-downloads).

## Description

This folder demonstrates how to use the libraries stored in the cuPQC SDK: cuPQC and cuHash.

* [cuPQC download page](https://developer.nvidia.com/cupqc-downloads)
* [cuPQC API documentation](https://docs.nvidia.com/cuda/cupqc/index.html)

## Requirements

* [cuPQC SDK](https://developer.nvidia.com/cupqc-downloads)
* [See cuPQC SDK requirements](https://docs.nvidia.com/cuda/cupqc/requirements.html)
* Linux system with installed NVIDIA drivers
* NVIDIA GPU of Volta (SM70) or newer architecture

## Build
Download and expand the cuPQC SDK then use the MakeFile located in this directory. Make sure that you set the `CUPQC_DIR` to the location of your expanded cuPQC SDK folder.

```
export CUPQC_DIR=<your_path_to_cupqc>
make
// Run
./example_ml_kem
./example_ml_dsa
./example_sha2
./example_sha3
./example_poseidon2
./example_merkle
```

## Examples
There is a ML-KEM and a ML-DSA example in this directory, these demonstrate the usage for the cuPQC library, and requires `libcupqc.a`. 
There are also SHA2, SHA3, Poseidon2 and Merkle Tree examples that demonstrate the usage of the cuHash library, these require `libcuhash.a`. 
For the detailed descriptions of the cuPQC API please visit [cuPQC SDK Docs](https://docs.nvidia.com/cuda/cupqc/index.html) section of the cuPQC documentation.

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

6 个独立源入口；PASSED 2，PARTIAL 0，FAILED 4，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：custom HIP SHA2/SHA3, unresolved post-quantum device APIs。候选不等于已使用；基础探针成功也不等于整库迁移成功。

SHA2/SHA3 使用自有 HIP 设备实现且独立摘要完全一致；ML-KEM/ML-DSA/Merkle/Poseidon2 仍需设备算法与 API 改写。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [example_merkle.cu](example_merkle.cu) · [详情](../migration/sample-reports/cuPQC/example_merkle.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuPQC/example_merkle.cu:24:10: fatal error: 'cuhash.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuPQC_example_merkle.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_merkle.cu) |
| [example_ml_dsa.cu](example_ml_dsa.cu) · [详情](../migration/sample-reports/cuPQC/example_ml_dsa.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuPQC/example_ml_dsa.cu:20:10: fatal error: 'cupqc.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuPQC_example_ml_dsa.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_ml_dsa.cu) |
| [example_ml_kem.cu](example_ml_kem.cu) · [详情](../migration/sample-reports/cuPQC/example_ml_kem.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuPQC/example_ml_kem.cu:20:10: fatal error: 'cupqc.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuPQC_example_ml_kem.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_ml_kem.cu) |
| [example_poseidon2.cu](example_poseidon2.cu) · [详情](../migration/sample-reports/cuPQC/example_poseidon2.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuPQC/example_poseidon2.cu:24:10: fatal error: 'cuhash.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamp | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuPQC_example_poseidon2.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_poseidon2.cu) |
| [example_sha2.cu](example_sha2.cu) · [详情](../migration/sample-reports/cuPQC/example_sha2.cu.md) | HIP runtime + custom device SHA implementation / HIP/gfx1201 | L4 / PASSED | SHA2 one thread; SHA3 cooperative 32-lane wave, one GPU kernel; original input plus padding/rate boundaries；14 个输入与独立 hashlib 精确一致 | BLOCKED / PASSED | [记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_sha2.cu)；[记录](../migration/reports/additional-comparison.json) |
| [example_sha3.cu](example_sha3.cu) · [详情](../migration/sample-reports/cuPQC/example_sha3.cu.md) | HIP runtime + custom device SHA implementation / HIP/gfx1201 | L4 / PASSED | SHA2 one thread; SHA3 cooperative 32-lane wave, one GPU kernel; original input plus padding/rate boundaries；14 个输入与独立 hashlib 精确一致 | BLOCKED / PASSED | [记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuPQC_example_sha3.cu)；[记录](../migration/reports/additional-comparison.json) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
