# cuTENSORMp

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

3 个独立源入口；PASSED 0，PARTIAL 0，FAILED 3，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipTensor, MPI, RCCL。候选不等于已使用；基础探针成功也不等于整库迁移成功。

原始 MPI tensor 描述与分布式算法尚未改写；RCCL 基础可行性不等同原始 Mp profile。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [cutensorMp_contraction.cu](cutensorMp_contraction.cu) · [详情](../migration/sample-reports/cuTENSORMp/cutensorMp_contraction.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSORMp/cutensorMp_contraction.cu:18:10: fatal error: 'cutensorMp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSORMp_cutensorMp_contraction.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSORMp_cutensorMp_contraction.cu) |
| [cutensorMp_redistribute.cu](cutensorMp_redistribute.cu) · [详情](../migration/sample-reports/cuTENSORMp/cutensorMp_redistribute.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSORMp/cutensorMp_redistribute.cu:27:10: fatal error: 'cutensorMp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSORMp_cutensorMp_redistribute.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSORMp_cutensorMp_redistribute.cu) |
| [cutensorMp_unfold_fold.cu](cutensorMp_unfold_fold.cu) · [详情](../migration/sample-reports/cuTENSORMp/cutensorMp_unfold_fold.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSORMp/cutensorMp_unfold_fold.cu:54:10: fatal error: 'cutensorMp.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSORMp_cutensorMp_unfold_fold.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSORMp_cutensorMp_unfold_fold.cu) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
