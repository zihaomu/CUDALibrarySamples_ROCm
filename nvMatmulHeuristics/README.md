# nvMatmulHeuristics

This directory contains samples demonstrating the usage of nvMatmulHeuristics.

More informations on nvMatmulHeuristics can be found here:

- https://docs.nvidia.com/cuda/nvidia-matmul-heuristics 
- https://developer.nvidia.com/nvidia-matmul-heuristics-downloads

## C++ Samples

### How to build

To build any of the C++ sample (replace `${SAMPLE}` by the appropriate sample name)

```bash
g++ -std=c++17 ${SAMPLE}.cpp -o ${SAMPLE} -lnvMatmulHeuristics -I${NVMMH_HOME}/include -L${NVMMH_HOME}/lib
```

where `NVMMH_HOME` points to the root of the nvMatmulHeuristics installation.

All C++ samples can be run as-is without any arguments.

### 1 - GEMM Heuristics

Located in `1_gemm_heuristics.cpp`.
Shows how to use nvMatmulHeuristics to get the top-8 GEMM kernel configurations. 
Note that `runtime` refers to the estimated GEMM kernel runtime, not the heuristics runtime.

Sample output:

```bash
nvMatmulHeuristics version 0.1.0

[1] CTA: 128 128 64, Warp: 64 64 64, Instr: 16 8 16, Stages: 5, SplitK: 108, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.264863 ms
[2] CTA: 128 128 32, Warp: 64 64 32, Instr: 16 8 16, Stages: 8, SplitK: 108, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.264863 ms
[3] CTA: 128 128 32, Warp: 32 32 32, Instr: 16 8 16, Stages: 8, SplitK: 108, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.264863 ms
[4] CTA: 128 64 64, Warp: 32 64 64, Instr: 16 8 16, Stages: 6, SplitK: 54, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.246302 ms
[5] CTA: 128 64 32, Warp: 64 32 32, Instr: 16 8 16, Stages: 8, SplitK: 54, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.246302 ms
[6] CTA: 64 64 64, Warp: 32 32 64, Instr: 16 8 16, Stages: 8, SplitK: 27, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.239468 ms
[7] CTA: 256 128 64, Warp: 64 64 64, Instr: 16 8 16, Stages: 3, SplitK: 108, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.407087 ms
[8] CTA: 256 128 32, Warp: 64 64 32, Instr: 16 8 16, Stages: 6, SplitK: 108, Raster: 0, SwizzleFactor: 1, estimated GEMM runtime: 0.407087 ms
```

### 2 - Discovery

Located in `2_discovery.cpp`.
Shows how to use the discovery process in nvMatmulHeuristics. 
Kernel benchmarking is not present in this sample and is replaced by a placeholder querying the nvMatmulHeuristics timing model instead.

Sample output:

```bash
nvMatmulHeuristics version 0.1.0

[1] Problem: M: 2272, N: 16, K: 16, layout: NVMMH_MATMUL_LAYOUT_TN_ROW_MAJOR, Config: CTA: 16 16 16, Warp: 16 16 16, Instr: 16 8 16, Stages: 1, SplitK: 1, Raster: 0, SwizzleFactor: 1
[2] Problem: M: 18080, N: 18080, K: 16, layout: NVMMH_MATMUL_LAYOUT_TN_ROW_MAJOR, Config: CTA: 128 128 16, Warp: 64 64 16, Instr: 16 8 16, Stages: 1, SplitK: 1, Raster: 0, SwizzleFactor: 1
[3] Problem: M: 18080, N: 18064, K: 16, layout: NVMMH_MATMUL_LAYOUT_TN_ROW_MAJOR, Config: CTA: 128 128 16, Warp: 64 64 16, Instr: 16 8 16, Stages: 1, SplitK: 1, Raster: 0, SwizzleFactor: 1
[4] Problem: M: 18080, N: 16, K: 18080, layout: NVMMH_MATMUL_LAYOUT_TN_ROW_MAJOR, Config: CTA: 128 16 128, Warp: 32 16 128, Instr: 16 8 16, Stages: 2, SplitK: 1, Raster: 0, SwizzleFactor: 1
...
```

### 3 - Energy Discovery

Located in `3_energy_discovery.cpp`. 
Demonstrates how to use nvMatmulHeuristics for energy-aware kernel discovery and selection.

Sample output:

```bash
nvMatmulHeuristics version 0.1.0

Estimated Energy Before: 0
[1] Problem: M: 512, N: 6912, K: 64, layout: NVMMH_MATMUL_LAYOUT_TN_ROW_MAJOR, Config: CTA: 256 128 64, Warp: 64 64 32, Instr: 16 8 16, Stages: 5, SplitK: 1, Raster: 1, SwizzleFactor: 1
...
[43] Problem: M: 32768, N: 32768, K: 32768, layout: NVMMH_MATMUL_LAYOUT_TN_ROW_MAJOR, Config: CTA: 128 256 64, Warp: 64 64 32, Instr: 16 8 16, Stages: 5, SplitK: 1, Raster: 0, SwizzleFactor: 1
Estimated Energy After: 6.45915
```

### 4 - Kernel Runtime Estimation

Located in `4_runtime_estimation.cpp`
Shows how to use nvMatmulHeuristics to estimate the runtime of a GEMM kernel configuration. This sample demonstrates:

- Creating a matmul problem
- Getting a kernel configuration using heuristics
- Estimating the runtime for the configuration
- Displaying detailed kernel configuration information

Sample output:

```bash
Problem: M=1024, N=2048, K=4096, Layout=NN
Kernel Configuration:
  CTA: 128x128x32
  Warp: 64x64x32
  Instr: 16x8x16
  SplitK: 1
  Load Stages: 8
  Grid Swizzle: 1
  CTA Order: 0
  Cluster Config: 1x1
Estimated Runtime: 0.000046 seconds
```

## Python Samples

### How to install

Install nvMatmulHeuristics through

```bash
pip install nvidia-matmul-heuristics
```

### 5 - GEMM configurations

Demonstrates how to use nvMatmulHeuristics to get GEMM configurations for a given problem size and hardware. 
This sample shows the basic usage of the public API.

Usage:

```bash
python3 5_get_configs.py -M 1024 -N 1024 -K 1024 --gpu A100_SXM_80GB
```

Sample output

```
Getting 8 configurations for:
Problem size: M=1024, N=1024, K=1024
Batch size: 1
GPU: A100_SXM_80GB
Layout: NN_ROW
Backend: CUTLASS3
Precision: HSH

Successfully loaded internal discovery set.
Found 8 configurations:

Configuration 1:
  Kernel: layout(NN_ROW) stages(6) cta(128 80 64) warp(32 40 64) instr(16 8 16) splitK(1) swizz(1) ctaOrder(0) cluster(1 1)
  Estimated runtime: 0.020084 ms
...
Configuration 8:
  Kernel: layout(NN_ROW) stages(2) cta(64 256 128) warp(64 64 128) instr(16 8 16) splitK(1) swizz(1) ctaOrder(0) cluster(1 1)
  Estimated runtime: 0.025779 ms
```

### 6 - GEMM configurations with extended interface

Demonstrates the usage of the extended interface (`NvMatmulHeuristicsInterfaceEx`) which provides additional features like automatic discovery set loading and per-call precision specification. 
This example shows how to track implicitly loaded discovery sets and use the simplified GPU-based initialization. 
`HSH` below indicates FP16 input, FP16 output and FP32 accumulation.

Usage:

```bash
python3 6_get_configs_ex.py -M 1024 -N 1024 -K 1024 --layout NN_ROW_MAJOR --gpu H100_SXM --precision HSH
```

Key features demonstrated:

- Automatic hardware descriptor management
- Implicit discovery set loading with tracking
- Per-call precision specification
- Simplified GPU-based initialization

Sample output:

```bash
Getting 8 configurations for:
Problem size: M=1024, N=1024, K=1024
Batch size: 1
GPU: H100_SXM
Layout: NN_ROW
Backend: CUTLASS3
Precision: HSH
Auto-load discovery sets: True


Getting configurations with precision (HSH)...

Implicitly loaded discovery sets:
  - Target: CUTLASS3, Precision: HSH, Layout: NN_ROW

Found 8 configurations with HSH precision:

Configuration 1:
  Kernel: layout(NN_ROW) stages(4) cta(128 64 128) warp(64 32 128) instr(64 8 16) splitK(1) swizz(1) ctaOrder(0) cluster(1 2)
  Estimated runtime: 0.017216 ms
...
Configuration 8:
  Kernel: layout(NN_ROW) stages(8) cta(64 128 64) warp(64 32 32) instr(64 8 16) splitK(1) swizz(1) ctaOrder(0) cluster(2 1)
  Estimated runtime: 0.017216 ms
```

### 7 - SMEM carveout

Demonstrates how to use the SMEM carveout feature to reserve a portion of shared memory for other purposes. This example compares kernel configurations with and without SMEM carveout to show how it
affects the kernel parameters.

Usage:

```bash
python3 7_smem_carveout.py -M 2560 -N 2560 -K 2560 --layout NN_ROW_MAJOR --gpu H100_SXM --smem-carveout 60000
```

Example output:

```
Comparing configurations with and without SMEM carveout:
Problem size: M=2560, N=2560, K=2560
GPU: H100_SXM
Layout: NN_ROW
Backend: CUTLASS3
Precision: HSH
SMEM Carveout: 60000 bytes


Configuration without SMEM carveout:
  CTA Tile: 256x128x64
  Warp Tile: 64x64x32
  Instruction Tile: 64x8x16
  Split K: 1
  Stages: 4
  CTA swizzling: 1
  CTA Order: 0
  Cluster Config: 1x2
  Estimated Runtime: 0.095070 ms

Configuration with SMEM carveout:
  CTA Tile: 256x128x64
  Warp Tile: 64x64x32
  Instruction Tile: 64x8x16
  Split K: 1
  Stages: 3
  CTA swizzling: 1
  CTA Order: 0
  Cluster Config: 1x2
  Estimated Runtime: 0.095070 ms
```

In this example, we can see how the SMEM carveout affects the kernel configuration: the number of stages decrease from 4 to 2 to compensate.
The estimated runtime remains the same.

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

7 个独立源入口；PASSED 0，PARTIAL 0，FAILED 7，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipBLASLt heuristics (subset)。候选不等于已使用；基础探针成功也不等于整库迁移成功。

hipBLASLt heuristic 已在 M1 验证；原始配置格式/模型与搜索接口未完整迁移，Origami 仅为待验收候选。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [1_gemm_heuristics.cpp](1_gemm_heuristics.cpp) · [详情](../migration/sample-reports/nvMatmulHeuristics/1_gemm_heuristics.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvMatmulHeuristics/1_gemm_heuristics.cpp:22:10: fatal error: 'nvMatmulHeuristics/nvMatmulHeuristics.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvMatmulHeuristics_1_gemm_heuristics.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvMatmulHeuristics_1_gemm_heuristics.cpp) |
| [2_discovery.cpp](2_discovery.cpp) · [详情](../migration/sample-reports/nvMatmulHeuristics/2_discovery.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvMatmulHeuristics/2_discovery.cpp:19:10: fatal error: 'nvMatmulHeuristics/nvMatmulHeuristics.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvMatmulHeuristics_2_discovery.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvMatmulHeuristics_2_discovery.cpp) |
| [3_energy_discovery.cpp](3_energy_discovery.cpp) · [详情](../migration/sample-reports/nvMatmulHeuristics/3_energy_discovery.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvMatmulHeuristics/3_energy_discovery.cpp:20:10: fatal error: 'nvMatmulHeuristics/nvMatmulHeuristics.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvMatmulHeuristics_3_energy_discovery.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvMatmulHeuristics_3_energy_discovery.cpp) |
| [4_runtime_estimation.cpp](4_runtime_estimation.cpp) · [详情](../migration/sample-reports/nvMatmulHeuristics/4_runtime_estimation.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvMatmulHeuristics/4_runtime_estimation.cpp:19:10: fatal error: 'nvMatmulHeuristics/nvMatmulHeuristics.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvMatmulHeuristics_4_runtime_estimation.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvMatmulHeuristics_4_runtime_estimation.cpp) |
| [5_get_configs.py](5_get_configs.py) · [详情](../migration/sample-reports/nvMatmulHeuristics/5_get_configs.py.md) | 未验证使用库 | L0 / FAILED | Python 原始入口依赖 argparse, sys, nvMatmulHeuristics；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。 日志：on/cpython-3.13.13-linux-x86_64-gnu/lib/python3.13/importlib/__init__.py", line 88, in import_module     return _bootstrap._gcd_import(name[level:], package, level)            ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "<frozen importlib._bootstrap>", line 1395, in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1324, in _find_and_load_unlocked ModuleNotFoundError: No module named 'nvMatmulHeuristics'  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084354.110802Z/languages/nvMatmulHeuristics_5_get_configs.py)；[记录](../migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/nvMatmulHeuristics_5_get_configs.py) |
| [6_get_configs_ex.py](6_get_configs_ex.py) · [详情](../migration/sample-reports/nvMatmulHeuristics/6_get_configs_ex.py.md) | 未验证使用库 | L0 / FAILED | Python 原始入口依赖 argparse, sys, nvMatmulHeuristics；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。 日志：on/cpython-3.13.13-linux-x86_64-gnu/lib/python3.13/importlib/__init__.py", line 88, in import_module     return _bootstrap._gcd_import(name[level:], package, level)            ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "<frozen importlib._bootstrap>", line 1395, in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1324, in _find_and_load_unlocked ModuleNotFoundError: No module named 'nvMatmulHeuristics'  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084354.110802Z/languages/nvMatmulHeuristics_6_get_configs_ex.py)；[记录](../migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/nvMatmulHeuristics_6_get_configs_ex.py) |
| [7_smem_carveout.py](7_smem_carveout.py) · [详情](../migration/sample-reports/nvMatmulHeuristics/7_smem_carveout.py.md) | 未验证使用库 | L0 / FAILED | Python 原始入口依赖 argparse, ctypes, sys, nvMatmulHeuristics；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。 日志：on/cpython-3.13.13-linux-x86_64-gnu/lib/python3.13/importlib/__init__.py", line 88, in import_module     return _bootstrap._gcd_import(name[level:], package, level)            ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "<frozen importlib._bootstrap>", line 1395, in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1324, in _find_and_load_unlocked ModuleNotFoundError: No module named 'nvMatmulHeuristics'  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084354.110802Z/languages/nvMatmulHeuristics_7_smem_carveout.py)；[记录](../migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/nvMatmulHeuristics_7_smem_carveout.py) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
