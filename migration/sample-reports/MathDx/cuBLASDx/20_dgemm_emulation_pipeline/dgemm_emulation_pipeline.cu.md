# MathDx/cuBLASDx/20_dgemm_emulation_pipeline::dgemm_emulation_pipeline.cu

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu:28:10: fatal error: 'cublasdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu](../../../../../MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | rocWMMA, Composable Kernel |
| 代码 | [rocm/ported/MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu](../../../../../rocm/ported/MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `44af86c66313379cf8c4b41dec5563d6d8199f39946d1c6f2a0a9024422c740f` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu:28:10: fatal error: 'cublasdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_

尝试库：—；实现 hash：`9e2a271d1c2f5ef6c1d4c64d7c598b8212eccac6e3d3161b4e97f93a343cdd53`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_20_dgemm_emulation_pipeline_dgemm_emulation_pipeline.cu](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuBLASDx_20_dgemm_emulation_pipeline_dgemm_emulation_pipeline.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_20_dgemm_emulation_pipeline_dgemm_emulation_pipeline.cu](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuBLASDx_20_dgemm_emulation_pipeline_dgemm_emulation_pipeline.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_20_dgemm_emulation_pipeline_dgemm_emulation_pipeline.cu](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuBLASDx_20_dgemm_emulation_pipeline_dgemm_emulation_pipeline.cu)
