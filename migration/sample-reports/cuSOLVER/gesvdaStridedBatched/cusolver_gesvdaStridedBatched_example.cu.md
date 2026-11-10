# cuSOLVER/gesvdaStridedBatched::cusolver_gesvdaStridedBatched_example.cu

**PARTIAL / L3**

已完成GPU重写与独立数值复核；候选尚需独立审查及完整资格，未升级整例。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu](../../../../cuSOLVER/gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu) |
| 实际库 / 后端 | hipSOLVER/rocSOLVER native full GPU SVD + HIP rank projection and FP64 residual / rocSOLVER + project HIP |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu](../../../../rocm/ported/cuSOLVER/gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu) |
| required cases | 7/8 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `c3afaca538159c5f139b72fbcf97ca28237373a813c901c74d2da2814f9d1916` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/R3/svd/original`, `rewrite/R3/svd/changed-values`, `rewrite/R3/svd/irregular`, `rewrite/R3/svd/layout`, `rewrite/R3/svd/repeat`, `rewrite/R3/svd/rank-deficient`, `rewrite/R3/svd/rank-truncated`, `rewrite/R3/svd/independent-review-and-qualification`。

实现方式：`LIBRARY_REWRITE`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsolver；实现 hash：`0b19a1a4db2e4e618ee17f64047b4e6fcb61dc1fd531458c6b5ad414f5453b62`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesvdaStridedBatched_cusolver_gesvdaStridedBatched_example.cu)
- [migration/reports/rewrite-extension-rocm.json](../../../reports/rewrite-extension-rocm.json)
- [migration/reports/rewrite-extension-rocm-validation.json](../../../reports/rewrite-extension-rocm-validation.json)
