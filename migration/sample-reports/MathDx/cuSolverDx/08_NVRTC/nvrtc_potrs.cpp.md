# MathDx/cuSolverDx/08_NVRTC::nvrtc_potrs.cpp

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp:27:10: fatal error: 'nvJitLink.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migr

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp](../../../../../MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp) |
| 实际库 / 后端 | — / — |
| 候选路线 | unresolved device solver |
| 代码 | [rocm/ported/MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp](../../../../../rocm/ported/MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp) |
| required cases | 0/2 |
| CUDA baseline / comparison | FAILED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `a09bcdb175fe26302e46f25fb813c6086ad9ff4d8468caa78380a89830b31e1c` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp:27:10: fatal error: 'nvJitLink.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migr

尝试库：—；实现 hash：`7e8ad594c52786cec763f6e5c3230aa0593e6e891ccb49f9f27f539398060f2e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuSolverDx_08_NVRTC_nvrtc_potrs.cpp](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuSolverDx_08_NVRTC_nvrtc_potrs.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuSolverDx_08_NVRTC_nvrtc_potrs.cpp](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuSolverDx_08_NVRTC_nvrtc_potrs.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuSolverDx_08_NVRTC_nvrtc_potrs.cpp](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuSolverDx_08_NVRTC_nvrtc_potrs.cpp)
