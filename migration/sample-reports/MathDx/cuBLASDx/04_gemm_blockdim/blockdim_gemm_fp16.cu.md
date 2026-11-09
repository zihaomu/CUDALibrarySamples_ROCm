# MathDx/cuBLASDx/04_gemm_blockdim::blockdim_gemm_fp16.cu

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu:23:10: fatal error: 'cublasdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_w

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu](../../../../../MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | rocWMMA, Composable Kernel |
| 代码 | [rocm/ported/MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu](../../../../../rocm/ported/MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `24b20c3fb79afa6e65bcefc4dc0ea18f5122c4d8b81327f884d414557aa689c0` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu:23:10: fatal error: 'cublasdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_w

尝试库：—；实现 hash：`e84192e79b46d1a4e8eac488ba84ec078c97705da4436fd5908f15b8ae697f3b`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_04_gemm_blockdim_blockdim_gemm_fp16.cu](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_04_gemm_blockdim_blockdim_gemm_fp16.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_04_gemm_blockdim_blockdim_gemm_fp16.cu](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_04_gemm_blockdim_blockdim_gemm_fp16.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_04_gemm_blockdim_blockdim_gemm_fp16.cu](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_04_gemm_blockdim_blockdim_gemm_fp16.cu)
