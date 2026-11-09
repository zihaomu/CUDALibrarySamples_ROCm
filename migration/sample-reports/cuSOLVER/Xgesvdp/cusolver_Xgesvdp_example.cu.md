# cuSOLVER/Xgesvdp::cusolver_Xgesvdp_example.cu

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu:104:20: error: use of undeclared identifier 'cusolverDnXgesvdp_bufferSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu:125:20: error: use of undeclared identifier 'cusolverDnXgesvdp'

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu](../../../../cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu) |
| 实际库 / 后端 | — / — |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu](../../../../rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu) |
| required cases | 0/2 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `0d04ecd1953eb480968a903bedff6e7e7e2780f989e5904f615ef377ffce78e6` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu:104:20: error: use of undeclared identifier 'cusolverDnXgesvdp_bufferSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu:125:20: error: use of undeclared identifier 'cusolverDnXgesvdp'

尝试库：hipsolver；实现 hash：`231339ad2d11da24b44e45035b82fcf0c306a250621203226f6ab0fee23c7c63`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xgesvdp_cusolver_Xgesvdp_example.cu)
