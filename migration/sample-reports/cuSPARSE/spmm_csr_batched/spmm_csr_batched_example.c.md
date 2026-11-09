# cuSPARSE/spmm_csr_batched::spmm_csr_batched_example.c

**PASSED / L4**

使用 hipSPARSE/rocSPARSE 保留原始存储格式与教学输入，逐索引/数值对照原始源码中独立给定的 expected 数组通过。扩展规模与性能未验收。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/spmm_csr_batched/spmm_csr_batched_example.c](../../../../cuSPARSE/spmm_csr_batched/spmm_csr_batched_example.c) |
| 实际库 / 后端 | hipSPARSE / rocSPARSE |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/spmm_csr_batched/spmm_csr_batched_example.c](../../../../rocm/ported/cuSPARSE/spmm_csr_batched/spmm_csr_batched_example.c) |
| required cases | 1/1 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `0fd66a433ec791dfd40c089b2e486c6885c66999d3fb359edb7b32ddb3216a99` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-fixed-input-and-expected-arrays`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：AMD 已通过所列 CPU/数学参考，但同输入跨 GPU 独立对照尚未完成。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsparse；实现 hash：`d88cfb3bd70e96a2c5399af69db578759763c3bb19ad42e2836a43ab3556570e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c)
- [migration/reports/sparse-original-validation.json](../../../reports/sparse-original-validation.json)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_batched_spmm_csr_batched_example.c)
