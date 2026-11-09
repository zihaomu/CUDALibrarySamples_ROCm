# cuSOLVER/gesvdj::cusolver_gesvdj_example.cu

**PASSED / L4**

使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/gesvdj/cusolver_gesvdj_example.cu](../../../../cuSOLVER/gesvdj/cusolver_gesvdj_example.cu) |
| 实际库 / 后端 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/gesvdj/cusolver_gesvdj_example.cu](../../../../rocm/ported/cuSOLVER/gesvdj/cusolver_gesvdj_example.cu) |
| required cases | 4/4 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `0a497fd41f0c5e7314e56f688dc6a7b6da907e15bcad50ab546c702c88342f2a` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`singular-values-cpu`, `reconstruction`, `U-orthogonality`, `V-orthogonality`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsolver；实现 hash：`8f5febb5a3127e656f448f7d77cc0c58959674b1c6889f472033d354e89e08cc`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)
- [migration/reports/solver-original-validation.json](../../../reports/solver-original-validation.json)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_gesvdj_cusolver_gesvdj_example.cu)
- [migration/reports/additional-comparison.json](../../../reports/additional-comparison.json)
