# cuBLASLt/LtIgemmTensor::main.cpp

**PASSED / L4**

原始数据/精度/布局与登记扩展用例通过 AMD、独立 CPU、相同输入 CUDA 验收；真实执行语义、反向检查及独立复审完成。实际路线：HIP COL32/COL4 packing/unpacking + native hipBLAS GemmEx INT8/INT32。性能未验收。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLASLt/LtIgemmTensor/main.cpp](../../../../cuBLASLt/LtIgemmTensor/main.cpp) |
| 实际库 / 后端 | HIP COL32/COL4 packing/unpacking + native hipBLAS GemmEx INT8/INT32 / rocBLAS |
| 候选路线 | hipBLASLt |
| 代码 | [rocm/ported/cuBLASLt/LtIgemmTensor/main.cpp](../../../../rocm/ported/cuBLASLt/LtIgemmTensor/main.cpp) |
| required cases | 7/7 |
| CUDA baseline / comparison | BLOCKED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `5149fa890384de3a2eab09938c1676b78442d6617ad30381761d25af55e844df` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite/original`, `rewrite/changed-values`, `rewrite/irregular`, `rewrite/layout`, `rewrite/repeat`, `rewrite/boundary`, `rewrite/independent-negative-checks`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtIgemmTensor/sample_cublasLt_LtIgemmTensor.cu:58:36: error: use of undeclared identifier 'CUBLASLT_ORDER_COL32'; did you mean 'HIPBLASLT_ORDER_COL'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASLt/LtIgemmTensor/sample_cublasLt_LtIgemmTensor.cu:59:42: error: use of undeclared identifier 'CUBLASLT_ORDER_COL4_4R2_8C'

尝试库：hipblaslt；实现 hash：`b2f5f2e0499719043ec71d80124d9c635cc960ea46c9f1dcce1e386e3b2655d8`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtIgemmTensor_main.cpp](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuBLASLt_LtIgemmTensor_main.cpp)
- [migration/reports/evidence/rewrite/R1/cuBLASLt_LtIgemmTensor__main.cpp/20261110T083836.070469Z-R1-composite-qualification-2a63fbaaca](../../../reports/evidence/rewrite/R1/cuBLASLt_LtIgemmTensor__main.cpp/20261110T083836.070469Z-R1-composite-qualification-2a63fbaaca)
- [migration/reports/rewrite-first-qualification.json](../../../reports/rewrite-first-qualification.json)
- [migration/reports/rewrite-first-negative.json](../../../reports/rewrite-first-negative.json)
- [migration/reports/rewrite-evidence-errata.json](../../../reports/rewrite-evidence-errata.json)
