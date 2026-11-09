# cuSOLVER/Xsyevd::cusolver_Xsyevd_example.cu

**PASSED / L4**

使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/Xsyevd/cusolver_Xsyevd_example.cu](../../../../cuSOLVER/Xsyevd/cusolver_Xsyevd_example.cu) |
| 实际库 / 后端 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/Xsyevd/cusolver_Xsyevd_example.cu](../../../../rocm/ported/cuSOLVER/Xsyevd/cusolver_Xsyevd_example.cu) |
| required cases | 3/3 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `473985d99e0f7010ee0fc1ffc0e7f768468e3d190362b8eac40b03408528a409` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`eigenvalues-cpu`, `eigen-residual`, `orthogonality`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsolver；实现 hash：`dea8b9f4f6a8ff7c4db103c7e4617475b6258c7ed7b248430c26664ce77445f3`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/solver-original-validation.json](../../../reports/solver-original-validation.json)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xsyevd_cusolver_Xsyevd_example.cu)
- [migration/reports/additional-comparison.json](../../../reports/additional-comparison.json)
