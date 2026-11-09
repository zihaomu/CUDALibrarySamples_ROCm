# cuSOLVER/csrqr::cusolver_csrqr_example1.cu

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/csrqr/cusolver_csrqr_example1.cu:32:5: error: unknown type name 'csrqrInfo_t'

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/csrqr/cusolver_csrqr_example1.cu](../../../../cuSOLVER/csrqr/cusolver_csrqr_example1.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/csrqr/cusolver_csrqr_example1.cu](../../../../rocm/ported/cuSOLVER/csrqr/cusolver_csrqr_example1.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | FAILED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `d1f7627c09622d3b43e96300e98a6ce6ddfc4ca6f753baabd9876b3d967d67b9` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/csrqr/cusolver_csrqr_example1.cu:32:5: error: unknown type name 'csrqrInfo_t'

尝试库：hipsolver；实现 hash：`e58be0fb6d460886d8eb124d2cd2b1a5d26a6d534b8c0bc685dada73f43a750d`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_csrqr_cusolver_csrqr_example1.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_csrqr_cusolver_csrqr_example1.cu)
