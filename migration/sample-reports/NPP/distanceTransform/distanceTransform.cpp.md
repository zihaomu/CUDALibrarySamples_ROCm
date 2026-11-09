# NPP/distanceTransform::distanceTransform.cpp

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/distanceTransform/distanceTransform.cpp:26:10: fatal error: 'nppdefs.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/distanceTransform/distanceTransform.cpp](../../../../NPP/distanceTransform/distanceTransform.cpp) |
| 实际库 / 后端 | — / — |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/distanceTransform/distanceTransform.cpp](../../../../rocm/ported/NPP/distanceTransform/distanceTransform.cpp) |
| required cases | 0/2 |
| CUDA baseline / comparison | FAILED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `7e5d292f6ee99ef7afc02d9af3659d5d5538ab28915dbde015e4042acdef36d1` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/distanceTransform/distanceTransform.cpp:26:10: fatal error: 'nppdefs.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra

尝试库：—；实现 hash：`dbebe97321b4c498e2c9f25a51274cffb8c9ef1aec62d0463b2fefdc596da161`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_distanceTransform_distanceTransform.cpp)
