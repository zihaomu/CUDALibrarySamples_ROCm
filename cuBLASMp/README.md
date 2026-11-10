# cuBLASMp Library API examples

## Description

This folder demonstrates cuBLASMp library API usage. Each sample is a self-contained program that initializes MPI, creates a process grid, and runs a distributed linear algebra operation with performance timing.

### Samples

**Tensor Parallelism Matmul** (communication-overlapped variants):

| Sample | Description |
|--------|-------------|
| [tp_matmul](tp_matmul.cu) | Tensor parallelism example covering AllGather + GEMM and GEMM + ReduceScatter |
| [matmul_ag](matmul_ag.cu) | AllGather + GEMM with configurable data types and scaling |
| [matmul_rs](matmul_rs.cu) | GEMM + ReduceScatter with configurable data types and scaling |
| [matmul_ar](matmul_ar.cu) | GEMM + AllReduce with configurable data types and scaling |

**PBLAS-style operations** (2D block-cyclic distribution):

| Sample | Description |
|--------|-------------|
| [gemm](gemm.cu) | General matrix-matrix multiply (GEMM) |
| [trsm](trsm.cu) | Triangular solve (TRSM) |
| [trmm](trmm.cu) | Triangular matrix-matrix multiply (TRMM) |
| [syrk](syrk.cu) | Symmetric rank-k update (SYRK) |
| [syr2k](syr2k.cu) | Symmetric rank-2k update (SYR2K) |
| [syrkx](syrkx.cu) | Extended symmetric rank-k update (SYRKX) |
| [symm](symm.cu) | Symmetric matrix-matrix multiply (SYMM) |
| [geadd](geadd.cu) | General matrix addition |
| [tradd](tradd.cu) | Triangular matrix addition |
| [gemr2d](gemr2d.cu) | General matrix redistribution between block-cyclic layouts |

### Supported OSes

* Linux

### Supported CPU Architectures

* x86_64
* arm64-sbsa

### Supported Compute Capabilities

* CUDA 12.x
    * [Compute Capability 7.0 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 7.5 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 8.0 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 9.0 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 10.0 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 12.0 ](https://developer.nvidia.com/cuda-gpus)

* CUDA 13.x
    * [Compute Capability 7.5 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 8.0 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 9.0 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 10.0 ](https://developer.nvidia.com/cuda-gpus)
    * [Compute Capability 12.0 ](https://developer.nvidia.com/cuda-gpus)

### Documentation

[cuBLASMp documentation](https://docs.nvidia.com/cuda/cublasmp)

## Usage

### Prerequisites

cuBLASMp is distributed through [NVIDIA Developer Zone](https://developer.nvidia.com/cublasmp-downloads), PyPI ([CUDA 12](https://pypi.org/project/nvidia-cublasmp-cu12/), [CUDA 13](https://pypi.org/project/nvidia-cublasmp-cu13/)), [Conda](https://anaconda.org/nvidia/libcublasmp), [conda-forge](https://anaconda.org/conda-forge/cublasmp) and [HPC SDK](https://developer.nvidia.com/hpc-sdk). cuBLASMp requires CUDA Toolkit and NCCL to be installed on the system. The samples require a C++17 compatible compiler and MPI (HPC-X recommended).

### Build Steps

```bash
git clone https://github.com/NVIDIA/CUDALibrarySamples.git
cd CUDALibrarySamples/cuBLASMp
mkdir build && cd build

export HPCXROOT=<path/to/hpcx>
export CUBLASMP_HOME=<path/to/cublasmp>
export NCCL_HOME=<path/to/nccl>
source ${HPCXROOT}/hpcx-mt-init-ompi.sh
hpcx_load

cmake .. -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CUDA_ARCHITECTURES="75;80;90;100;120" \
    -DCUBLASMP_INCLUDE_DIRECTORIES=${CUBLASMP_HOME}/include \
    -DCUBLASMP_LIBRARIES=${CUBLASMP_HOME}/lib/libcublasmp.so \
    -DNCCL_INCLUDE_DIRECTORIES=${NCCL_HOME}/include \
    -DNCCL_LIBRARIES=${NCCL_HOME}/lib/libnccl.so
make -j
```

### Running

By default, the number of MPI processes must equal the process grid size (`p * q`). With `-gpus-per-process N`,
the sample launches up to `N` local GPU worker threads per MPI process, so the process grid can be supplied by fewer
MPI processes. All samples accept `-help` for a full list of options.

**Tensor Parallelism Matmul** (1D grid, processes along one dimension):

```bash
# AllGather + GEMM with FP16
mpirun -n 2 ./matmul_ag -p 1 -q 2 -typeA fp16 -typeB fp16 -typeD fp16 -transA t -transB n

# GEMM + ReduceScatter with FP16
mpirun -n 2 ./matmul_rs -p 1 -q 2 -typeA fp16 -typeB fp16 -typeD fp16 -transA t -transB n

# GEMM + AllReduce with FP16
mpirun -n 2 ./matmul_ar -p 1 -q 2 -typeA fp16 -typeB fp16 -typeD fp16 -transA t -transB n

# End-to-end tensor parallelism
mpirun -n 2 ./tp_matmul -p 1 -q 2
```

**PBLAS-style operations** (2D grid with `-p` rows and `-q` columns):

```bash
mpirun -n 2 ./gemm -p 2 -q 1
mpirun -n 2 ./trsm -p 2 -q 1
mpirun -n 2 ./trmm -p 2 -q 1
mpirun -n 2 ./syrk -p 2 -q 1
mpirun -n 2 ./syr2k -p 2 -q 1
mpirun -n 2 ./syrkx -p 2 -q 1
mpirun -n 2 ./symm -p 2 -q 1
mpirun -n 2 ./geadd -p 2 -q 1
mpirun -n 2 ./tradd -p 2 -q 1
mpirun -n 2 ./gemr2d -p 2 -q 1
```

**Single-process multi-GPU samples** (one MPI process launches multiple local GPU worker threads):

```bash
# Two local GPU ranks in one MPI process
mpirun -n 1 ./gemm -gpus-per-process 2 -p 1 -q 2

# Tensor-parallel samples use the same local-rank model
mpirun -n 1 ./matmul_ag -gpus-per-process 2 -p 1 -q 2 \
    -typeA fp16 -typeB fp16 -typeD fp16 -transA t -transB n

# Redistribution and addition samples also support SPMG
mpirun -n 1 ./gemr2d -gpus-per-process 2 -p 1 -q 2
mpirun -n 1 ./geadd -gpus-per-process 2 -p 1 -q 2

# Use a subset of the available SPMG ranks: two participating ranks out of up to four local GPU workers
mpirun -n 1 ./gemm -gpus-per-process 4 -p 1 -q 2
```

### Common Options

Individual operations may use only a subset of these options, and not every datatype or scaling-mode combination is valid for every sample.

| Option | Description |
|--------|-------------|
| `-m`, `-n`, `-k` | Matrix dimensions |
| `-mbA`, `-nbA`, `-mbB`, `-nbB`, `-mbC`, `-nbC` | Block sizes for the distributed matrices |
| `-ia`, `-ja`, `-ib`, `-jb`, `-ic`, `-jc` | 1-based starting indices of the operated submatrices |
| `-p`, `-q` | Process grid dimensions (p rows, q columns) |
| `-gpus-per-process` | Number of local GPU worker threads per MPI process for SPMG mode |
| `-typeA`, `-typeB`, `-typeC`, `-typeD` | Data types (`fp16`, `bf16`, `fp32`, `fp64`, `fp8_e4m3`, `fp8_e5m2`, `fp4_e2m1`, `cfp32`, `cfp64`) |
| `-transA`, `-transB` | Transpose operations (`n`, `t`, `c`) |
| `-scaleA`, `-scaleB`, `-scaleD`, `-scaleDOut` | Scaling modes (`scalar_fp32`, `vec16_ue4m3`, `vec32_ue8m0`, `outer_vec_fp32`, `vec128_fp32`, `blk128x128_fp32`) |
| `-gridLayout` | Process grid layout (`c` column-major, `r` row-major) |
| `-emulationStrategy` | FP emulation strategy (`default`, `performant`, `eager`) |
| `-checkResult` | Enable result verification (`true` or `false`; default: `true`) |
| `-no-check` | Disable result verification |
| `-cycles` | Number of iterations for timing |
| `-warmup` | Number of warmup iterations |
| `-verbose` | Print detailed output |
| `-help` | Print all available options |

### Matmul Scaling Modes

The `matmul_ag`, `matmul_rs`, and `matmul_ar` samples support both Hopper FP8 scaling modes
(`vec128_fp32`, `blk128x128_fp32`, `outer_vec_fp32`) and Blackwell block scaling modes
(`vec32_ue8m0`, `vec16_ue4m3`). Support for a given datatype and scaling-mode combination depends on the
GPU architecture, CUDA Toolkit, and cuBLASLt support available at runtime.

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

14 个独立源入口；PASSED 2，PARTIAL 4，FAILED 8，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：rocBLAS, RCCL, MPI。候选不等于已使用；基础探针成功也不等于整库迁移成功。

B12原始FP64 GEADD与block-cyclic重分布/往返通过；MPI双rank使用不同GPU及真实RCCL。GEMM原始B子矩阵offset、FP16 collective舍入/FP8/FP4 scale和完整CLI保持PARTIAL；没有多节点资格。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [geadd.cu](geadd.cu) · [详情](../migration/sample-reports/cuBLASMp/geadd.cu.md) | MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD / MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD | L4 / PASSED | 使用MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_geadd.cu)；[记录](../migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_geadd.cu) |
| [gemm.cu](gemm.cu) · [详情](../migration/sample-reports/cuBLASMp/gemm.cu.md) | MPI + RCCL distribution + hipBLAS FP32 local GEMM / MPI + RCCL distribution + hipBLAS FP32 local GEMM | L4 / PARTIAL | 使用MPI + RCCL distribution + hipBLAS FP32 local GEMM；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。本轮GEMM保持FP32/尺寸与A/C分布；原例B的IB=3子矩阵描述符及完整transpose/CLI控制未逐项等价，保留部分支持。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_gemm.cu)；[记录](../migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_gemm.cu) |
| [gemr2d.cu](gemr2d.cu) · [详情](../migration/sample-reports/cuBLASMp/gemr2d.cu.md) | MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip / MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip | L4 / PASSED | 使用MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_gemr2d.cu)；[记录](../migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_gemr2d.cu) |
| [matmul_ag.cu](matmul_ag.cu) · [详情](../migration/sample-reports/cuBLASMp/matmul_ag.cu.md) | MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization / MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization | L4 / PARTIAL | 使用MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_matmul_ag.cu)；[记录](../migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_matmul_ag.cu) |
| [matmul_ar.cu](matmul_ar.cu) · [详情](../migration/sample-reports/cuBLASMp/matmul_ar.cu.md) | MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization / MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization | L4 / PARTIAL | 使用MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_matmul_ar.cu)；[记录](../migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_matmul_ar.cu) |
| [matmul_rs.cu](matmul_rs.cu) · [详情](../migration/sample-reports/cuBLASMp/matmul_rs.cu.md) | MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization / MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization | L4 / PARTIAL | 使用MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_matmul_rs.cu)；[记录](../migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_matmul_rs.cu) |
| [symm.cu](symm.cu) · [详情](../migration/sample-reports/cuBLASMp/symm.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/symm.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_symm.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_symm.cu) |
| [syr2k.cu](syr2k.cu) · [详情](../migration/sample-reports/cuBLASMp/syr2k.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/syr2k.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_syr2k.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_syr2k.cu) |
| [syrk.cu](syrk.cu) · [详情](../migration/sample-reports/cuBLASMp/syrk.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/syrk.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_syrk.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_syrk.cu) |
| [syrkx.cu](syrkx.cu) · [详情](../migration/sample-reports/cuBLASMp/syrkx.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/syrkx.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_syrkx.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_syrkx.cu) |
| [tp_matmul.cu](tp_matmul.cu) · [详情](../migration/sample-reports/cuBLASMp/tp_matmul.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/tp_matmul.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_tp_matmul.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_tp_matmul.cu) |
| [tradd.cu](tradd.cu) · [详情](../migration/sample-reports/cuBLASMp/tradd.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/tradd.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_tradd.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_tradd.cu) |
| [trmm.cu](trmm.cu) · [详情](../migration/sample-reports/cuBLASMp/trmm.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/trmm.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_trmm.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_trmm.cu) |
| [trsm.cu](trsm.cu) · [详情](../migration/sample-reports/cuBLASMp/trsm.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/trsm.cu:20:10: fatal error: 'cublasmp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_trsm.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_trsm.cu) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
