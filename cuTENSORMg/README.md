# cuTENSORMg

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

2 个独立源入口；PASSED 0，PARTIAL 0，FAILED 2，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：hipTensor, RCCL, MPI。候选不等于已使用；基础探针成功也不等于整库迁移成功。

单进程跨卡 tensor 分区/布局/通信 API 尚未实现；单卡 hipTensor 不等同 Mg。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [blog_post.cu](blog_post.cu) · [详情](../migration/sample-reports/cuTENSORMg/blog_post.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSORMg/blog_post.cu:18:10: fatal error: 'hiptensor.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSORMg_blog_post.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSORMg_blog_post.cu) |
| [contraction_multi_gpu.cu](contraction_multi_gpu.cu) · [详情](../migration/sample-reports/cuTENSORMg/contraction_multi_gpu.cu.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuTENSORMg/contraction_multi_gpu.cu:18:10: fatal error: 'hiptensor.h' file not found | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSORMg_contraction_multi_gpu.cu)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSORMg_contraction_multi_gpu.cu) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
