# MathDx/cuBLASDx/01_gemm_introduction::introduction_example.cu

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu:24:10: fatal error: 'cublasdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sa

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu](../../../../../MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | rocWMMA, Composable Kernel |
| 代码 | [rocm/ported/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu](../../../../../rocm/ported/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `2b4a07e4a4980fd1e3f22688af5438cdd9a33f5ec1ac251f9291987775563dd2` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu:24:10: fatal error: 'cublasdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sa

尝试库：—；实现 hash：`bce9150b18c0121cbc3ddd2797d03e373c168a131be9c21fb94eb7abb50c43a3`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_01_gemm_introduction_introduction_example.cu)
