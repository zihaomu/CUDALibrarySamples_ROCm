# cuBLASLt/LtHSHgemmStridedBatchSimple::main.cpp

**PASSED / L4**

使用 hipBLASLt 保留原始 4×4 profile、alpha/beta 与 FP16 input/output + FP32 compute（HSH）或 FP32（SGEMM）及 batch 存储方式；完整输出通过独立 NumPy GEMM 与显式 half 舍入检查。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLASLt/LtHSHgemmStridedBatchSimple/main.cpp](../../../../cuBLASLt/LtHSHgemmStridedBatchSimple/main.cpp) |
| 实际库 / 后端 | hipBLASLt / hipBLASLt |
| 候选路线 | hipBLASLt |
| 代码 | [rocm/ported/cuBLASLt/LtHSHgemmStridedBatchSimple/main.cpp](../../../../rocm/ported/cuBLASLt/LtHSHgemmStridedBatchSimple/main.cpp) |
| required cases | 1/1 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `413210efaecbc3571804be39521b56d32806c637a52de8b1683758475616c6ab` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-fixed-input-cpu-gemm`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipblaslt；实现 hash：`35f018047bc76aaaaa76d41ae98e99aa6dcf9589e6df0af99c7c61ec20968789`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T085205.912828Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T085546.110648Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T090201.483404Z/original-rocm/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/blaslt-original-validation.json](../../../reports/blaslt-original-validation.json)
- [migration/reports/evidence/20261109T100608.316377Z/original-cuda/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp](../../../reports/evidence/20261109T100608.316377Z/original-cuda/cuBLASLt_LtHSHgemmStridedBatchSimple_main.cpp)
- [migration/reports/additional-comparison.json](../../../reports/additional-comparison.json)
