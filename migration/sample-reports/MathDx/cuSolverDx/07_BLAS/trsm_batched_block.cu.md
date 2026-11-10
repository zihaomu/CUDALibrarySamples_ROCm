# MathDx/cuSolverDx/07_BLAS::trsm_batched_block.cu

**PASSED / L4**

原始数据/精度/布局与登记扩展用例通过 AMD、独立 CPU、相同输入 CUDA 验收；真实执行语义、反向检查及独立复审完成。实际路线：HIP caller-kernel cooperative real FP64 right/lower triangular solve。性能未验收。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu](../../../../../MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu) |
| 实际库 / 后端 | HIP caller-kernel cooperative real FP64 right/lower triangular solve / project HIP device algorithm |
| 候选路线 | unresolved device solver |
| 代码 | [rocm/ported/MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu](../../../../../rocm/ported/MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu) |
| required cases | 9/9 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `b754f28b4bd5e0b36706ed8de75c4e5c847dcdfd653138dde3b33bf8622d3859` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original`, `rewrite/changed-values`, `rewrite/irregular`, `rewrite/layout`, `rewrite/repeat`, `rewrite/boundary`, `rewrite/independent-negative-checks`, `rewrite/native-device-original`, `rewrite/invalid-descriptors`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu:19:10: fatal error: 'cusolverdx.hpp' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_worksp

尝试库：—；实现 hash：`3bc2904c6754c619ab85d1f832a9463479d8a5df6399cb5d52429f41d42dc938`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuSolverDx_07_BLAS_trsm_batched_block.cu](../../../../reports/evidence/20261109T083217.050455Z/original-rocm/MathDx_cuSolverDx_07_BLAS_trsm_batched_block.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuSolverDx_07_BLAS_trsm_batched_block.cu](../../../../reports/evidence/20261109T084256.329631Z/original-rocm/MathDx_cuSolverDx_07_BLAS_trsm_batched_block.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuSolverDx_07_BLAS_trsm_batched_block.cu](../../../../reports/evidence/20261109T084857.451692Z/original-cuda/MathDx_cuSolverDx_07_BLAS_trsm_batched_block.cu)
- [migration/reports/evidence/rewrite/R2/MathDx_cuSolverDx_07_BLAS__trsm_batched_block.cu/20261110T083838.501295Z-R2-composite-qualification-f6d677810e](../../../../reports/evidence/rewrite/R2/MathDx_cuSolverDx_07_BLAS__trsm_batched_block.cu/20261110T083838.501295Z-R2-composite-qualification-f6d677810e)
- [migration/reports/rewrite-first-qualification.json](../../../../reports/rewrite-first-qualification.json)
- [migration/reports/rewrite-first-negative.json](../../../../reports/rewrite-first-negative.json)
- [migration/reports/rewrite-evidence-errata.json](../../../../reports/rewrite-evidence-errata.json)
