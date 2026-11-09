# cuSOLVERMp Library API examples

## Description

Here we provide examples of cuSOLVERMp library API usage

### Key Concepts

Distributed decompositions and linear system solutions

### Examples

[Dense matrix LU factorization and linear system solve](mp_getrf_getrs.c)

[Dense matrix Cholesky factorization and linear system solve](mp_potrf_potrs.c)

[Dense matrix Cholesky factorization and linear system solve (FP32)](mp_potrf_potrs_fp32.c)

[Dense matrix Cholesky factorization and linear system solve (FP32 emulation)](mp_potrf_potrs_fp32emulation.c)

[Dense matrix Symmetric Eigensolver](mp_syevd.c)

[Dense matrix Symmetric Generalized Eigensolver](mp_sygvd.c)

[Dense matrix symmetric-definite transformation](mp_sygst.c)

[Dense matrix SYTRD + STEDC + ORMTR workflow](mp_sytrd_stedc_ormtr.c)

[Dense matrix QR factorization](mp_geqrf.c)

[Dense matrix QR factorization with explicit Q formation](mp_geqrf_orgqr.c)

[Dense matrix QR reflector application](mp_ormqr.c)

[Dense matrix QR factorization and linear system solve](mp_gels.c)

[Dense matrix initialization (LASET)](mp_laset.c)

[Dense matrix polar decomposition](mp_polar.c)

[Dense matrix Singular Value Decomposition (polar-based)](mp_gesvd.c)

[Newton-Schulz Iterations](mp_newton_schulz.cpp)

Examples are bootstrapped by MPI and use it to set up distributed data. Those examples are intended just to show how API is used and not for performance benchmarking. For same reasons process grid defaults to `2x1` in the examples, however you can change it using `-p` and `-q` command line parameters.

Based on your distributed setup you can choose how your GPU devices are mapped to processes - change following line in the example to suit your needs:
`const int localDeviceId = getLocalRank();`

In these samples each process will use CUDA device ID equal to the local MPI rank ID of the process.

### Supported OSes

* Linux

### Supported CPU Architecture

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

[cuSOLVERMp documentation](https://docs.nvidia.com/cuda/cusolvermp/index.html)

## Usage

### Prerequisites

cuSOLVERMp is distributed through [NVIDIA Developer Zone](https://developer.nvidia.com/cusolvermp), PyPI ([CUDA 12](https://pypi.org/project/nvidia-cusolvermp-cu12), [CUDA 13](https://pypi.org/project/nvidia-cusolvermp-cu13)), [Conda](https://anaconda.org/nvidia/cusolvermp) and [HPC SDK](https://developer.nvidia.com/hpc-sdk). cuSOLVERMp requires CUDA Toolkit, NCCL, and cuBLASMp to be installed on the system. The samples require a C++17 compatible compiler.

### Building

```
git clone https://github.com/NVIDIA/CUDALibrarySamples.git
cd CUDALibrarySamples/cuSOLVERMp
mkdir build
cd build
export HPCXROOT=<path/to/hpcx>
export CUSOLVERMP_HOME=<path/to/cusolvermp>
export NCCL_HOME=<path/to/nccl>
export CUBLASMP_HOME=<path/to/cublasmp>
source ${HPCXROOT}/hpcx-mt-init-ompi.sh
hpcx_load
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES="75;80;90;100;120" -DCUSOLVERMP_INCLUDE_DIRECTORIES=${CUSOLVERMP_HOME}/include -DCUSOLVERMP_LINK_DIRECTORIES=${CUSOLVERMP_HOME}/lib/ -DNCCL_INCLUDE_DIR=${NCCL_HOME}/include -DNCCL_LIBRARIES=${NCCL_HOME}/lib/libnccl.so -DCUBLASMP_LINK_DIRECTORIES=${CUBLASMP_HOME}/lib -DCUBLASMP_LIBRARIES=${CUBLASMP_HOME}/lib/libcublasmp.so
make -j
```

### Running

Run examples with mpi command and number of processes according to process grid values, i.e.

`mpirun -n 2 ./mp_getrf_getrs`

`mpirun -n 4 ./mp_getrf_getrs -p 2 -q 2`

`mpirun -n 2 ./mp_potrf_potrs`

`mpirun -n 4 ./mp_potrf_potrs_fp32 -p 2 -q 2 -n 8192 -nbA 1024 -mbA 1024 -nbB 1024 -mbB 1024 -ia 1 -ja 1 -ib 1 -jb 1`

`mpirun -n 4 ./mp_potrf_potrs_fp32emulation -p 2 -q 2 -n 8192 -nbA 1024 -mbA 1024 -nbB 1024 -mbB 1024 -ia 1 -ja 1 -ib 1 -jb 1`

`mpirun -n 2 ./mp_syevd`

`mpirun -n 4 ./mp_syevd -grid_layout C -p 2 -q 2`

`mpirun -n 4 ./mp_syevd -grid_layout R -p 2 -q 2`

`mpirun -n 2 ./mp_sygvd`

`mpirun -n 2 ./mp_sygst`

`mpirun -n 4 ./mp_sygst -p 2 -q 2 -n 128 -mbA 32 -nbA 32 -mbB 32 -nbB 32`

`mpirun -n 2 ./mp_sytrd_stedc_ormtr`

`mpirun -n 4 ./mp_sytrd_stedc_ormtr -p 2 -q 2 -n 64 -mbA 16 -nbA 16 -mbQ 16 -nbQ 16`

`mpirun -n 2 ./mp_geqrf`

`mpirun -n 2 ./mp_geqrf_orgqr`

`mpirun -n 4 ./mp_geqrf_orgqr -p 2 -q 2 -m 100 -n 50 -mbA 32 -nbA 32`

`mpirun -n 2 ./mp_ormqr`

`mpirun -n 4 ./mp_ormqr -p 2 -q 2 -m 128 -n 64 -nrhs 64 -mbA 32 -nbA 32 -mbB 32 -nbB 32`

`mpirun -n 2 ./mp_gels`

`mpirun -n 2 ./mp_laset`

`mpirun -n 4 ./mp_laset -p 2 -q 2 -n 20 -mbA 4 -nbA 4`

`mpirun -n 2 ./mp_polar`

`mpirun -n 2 ./mp_gesvd`

`mpirun -n 4 ./mp_gesvd -p 2 -q 2 -m 256 -n 128 -mbA 32 -nbA 32`

`mpirun -n 2 ./mp_newton_schulz -p 2 -q 1 -m 16384 -n 2048`

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

16 个独立源入口；PASSED 0，PARTIAL 0，FAILED 16，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：rocSOLVER, rocBLAS, MPI, RCCL。候选不等于已使用；基础探针成功也不等于整库迁移成功。

分布式 LU/Cholesky/特征值等需要 MPI/通信及算法层改写；不能以单卡 hipSOLVER 作为成功。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [mp_gels.c](mp_gels.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_gels.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_gels.c:26:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_gels.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_gels.c) |
| [mp_geqrf.c](mp_geqrf.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_geqrf.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_geqrf.c:25:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_geqrf.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_geqrf.c) |
| [mp_geqrf_orgqr.c](mp_geqrf_orgqr.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_geqrf_orgqr.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_geqrf_orgqr.c:45:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_geqrf_orgqr.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_geqrf_orgqr.c) |
| [mp_gesvd.c](mp_gesvd.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_gesvd.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_gesvd.c:49:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_gesvd.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_gesvd.c) |
| [mp_getrf_getrs.c](mp_getrf_getrs.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_getrf_getrs.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_getrf_getrs.c:24:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_getrf_getrs.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_getrf_getrs.c) |
| [mp_laset.c](mp_laset.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_laset.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_laset.c:40:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_laset.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_laset.c) |
| [mp_newton_schulz.cpp](mp_newton_schulz.cpp) · [详情](../migration/sample-reports/cuSOLVERMp/mp_newton_schulz.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_newton_schulz.cpp:25:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_newton_schulz.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_newton_schulz.cpp) |
| [mp_ormqr.c](mp_ormqr.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_ormqr.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_ormqr.c:39:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_ormqr.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_ormqr.c) |
| [mp_polar.c](mp_polar.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_polar.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_polar.c:47:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_polar.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_polar.c) |
| [mp_potrf_potrs.c](mp_potrf_potrs.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_potrf_potrs.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_potrf_potrs.c:25:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_potrf_potrs.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_potrf_potrs.c) |
| [mp_potrf_potrs_fp32.c](mp_potrf_potrs_fp32.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_potrf_potrs_fp32.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_potrf_potrs_fp32.c:25:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_potrf_potrs_fp32.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_potrf_potrs_fp32.c) |
| [mp_potrf_potrs_fp32emulation.c](mp_potrf_potrs_fp32emulation.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_potrf_potrs_fp32emulation.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_potrf_potrs_fp32emulation.c:25:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_potrf_potrs_fp32emulation.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_potrf_potrs_fp32emulation.c) |
| [mp_syevd.c](mp_syevd.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_syevd.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_syevd.c:25:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_syevd.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_syevd.c) |
| [mp_sygst.c](mp_sygst.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_sygst.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_sygst.c:35:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_sygst.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_sygst.c) |
| [mp_sygvd.c](mp_sygvd.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_sygvd.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_sygvd.c:25:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_sygvd.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_sygvd.c) |
| [mp_sytrd_stedc_ormtr.c](mp_sytrd_stedc_ormtr.c) · [详情](../migration/sample-reports/cuSOLVERMp/mp_sytrd_stedc_ormtr.c.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_sytrd_stedc_ormtr.c:39:10: fatal error: 'mpi.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_sytrd_stedc_ormtr.c)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_sytrd_stedc_ormtr.c) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
