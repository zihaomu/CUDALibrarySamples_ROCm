# cuSPARSE/spmm_csr_op::spmm_csr_op_example.c

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c:101:18: error: use of undeclared identifier 'nvrtcGetLTOIRSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c:103:18: error: use of undeclared identifier 'nvrtcGetLTOIR'

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/spmm_csr_op/spmm_csr_op_example.c](../../../../cuSPARSE/spmm_csr_op/spmm_csr_op_example.c) |
| 实际库 / 后端 | — / — |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c](../../../../rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c) |
| required cases | 0/2 |
| CUDA baseline / comparison | FAILED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `a9c8f4e05ee4e157a7b6822ccf2c26757bcb7bd9abd2b3b3087008f2750399f0` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c:101:18: error: use of undeclared identifier 'nvrtcGetLTOIRSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c:103:18: error: use of undeclared identifier 'nvrtcGetLTOIR'

尝试库：hipsparse；实现 hash：`2eb25e438886cb3186b3c3e078933da0b4416d2dbef14f7d4c7f1c5be74ca18c`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_op_spmm_csr_op_example.c)
