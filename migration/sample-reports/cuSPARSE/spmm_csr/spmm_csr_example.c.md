# cuSPARSE/spmm_csr::spmm_csr_example.c

**PASSED / L4**

使用 hipSPARSE（rocSPARSE）成功实现原始 profile 和 9 个数值用例，并通过 CUDA 对照

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/spmm_csr/spmm_csr_example.c](../../../../cuSPARSE/spmm_csr/spmm_csr_example.c) |
| 实际库 / 后端 | hipSPARSE / rocSPARSE |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/cuSPARSE/spmm_csr/sample.cpp](../../../../rocm/cuSPARSE/spmm_csr/sample.cpp) |
| required cases | 9/9 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `79b81e804018634f72945092b276ff4ecd46fce8dec9a47d4e1c37e5d087ded3` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`base0_beta0.000000`, `base0_beta0.500000`, `base1_beta0.000000`, `base1_beta0.500000`, `original_profile`, `empty_base0_beta0.000000`, `empty_base0_beta0.500000`, `empty_base1_beta0.000000`, `empty_base1_beta0.500000`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsparse；实现 hash：`5790b4e3c5f824985aadd085307840ed5b9a879188e707a6f44ac36a5608c8cf`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter cuSPARSE/spmm_csr
```

- [migration/reports/evidence/20261109T074106.668062Z/rocm/cuSPARSE_spmm_csr](../../../reports/evidence/20261109T074106.668062Z/rocm/cuSPARSE_spmm_csr)
- [migration/reports/evidence/20261109T074136.696317Z/rocm/cuSPARSE_spmm_csr](../../../reports/evidence/20261109T074136.696317Z/rocm/cuSPARSE_spmm_csr)
- [migration/reports/evidence/20261109T074302.621128Z/rocm/cuSPARSE_spmm_csr](../../../reports/evidence/20261109T074302.621128Z/rocm/cuSPARSE_spmm_csr)
- [migration/reports/evidence/20261109T074409.357725Z/rocm/cuSPARSE_spmm_csr](../../../reports/evidence/20261109T074409.357725Z/rocm/cuSPARSE_spmm_csr)
- [migration/reports/evidence/20261109T075141.556119Z/rocm/cuSPARSE_spmm_csr](../../../reports/evidence/20261109T075141.556119Z/rocm/cuSPARSE_spmm_csr)
- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spmm_csr_spmm_csr_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spmm_csr_spmm_csr_example.c)
- [migration/reports/evidence/20261109T081304.129128Z/rocm/cuSPARSE_spmm_csr](../../../reports/evidence/20261109T081304.129128Z/rocm/cuSPARSE_spmm_csr)
- [migration/reports/evidence/20261109T081927.659318Z/rocm/cuSPARSE_spmm_csr](../../../reports/evidence/20261109T081927.659318Z/rocm/cuSPARSE_spmm_csr)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spmm_csr_spmm_csr_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spmm_csr_spmm_csr_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmm_csr_spmm_csr_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spmm_csr_spmm_csr_example.c)
- [migration/reports/sparse-original-validation.json](../../../reports/sparse-original-validation.json)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_spmm_csr_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spmm_csr_spmm_csr_example.c)
