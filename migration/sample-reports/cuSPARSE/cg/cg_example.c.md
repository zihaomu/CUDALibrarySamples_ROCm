# cuSPARSE/cg::cg_example.c

**PASSED / L4**

使用 hipSPARSE + hipBLAS / rocSPARSE/rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/cg/cg_example.c](../../../../cuSPARSE/cg/cg_example.c) |
| 实际库 / 后端 | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/cg/cg_example.c](../../../../rocm/ported/cuSPARSE/cg/cg_example.c) |
| required cases | 3/3 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `1eb109366144aa5f7d9d213f7bcfed340c738ea835d767d4ec57034cc233c967` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batch3/original`, `batch3/small-varied`, `batch3/nonzero-initial`。

实现方式：`API_PORT`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsparse；实现 hash：`070054702cb29cd4ac35ee0c7276c41143a8f646e0a6223a7f162edc5736cee0`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch3_run.py sparse
python3 tools/migration/batch3_validate.py sparse --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_cg_cg_example.c)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_cg_cg_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_cg_cg_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_cg_cg_example.c)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_cg_cg_example.c)
- [migration/reports/evidence/20261109T135624.134389Z/batch3-rocm/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T135624.134389Z/batch3-rocm/cuSPARSE_cg_cg_example.c)
- [migration/reports/batch3-validation.json](../../../reports/batch3-validation.json)
- [migration/reports/evidence/20261109T135443.759704Z/batch3-cuda/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T135443.759704Z/batch3-cuda/cuSPARSE_cg_cg_example.c)
- [migration/reports/evidence/20261109T140002.910290Z/batch3-rocm/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T140002.910290Z/batch3-rocm/cuSPARSE_cg_cg_example.c)
- [migration/reports/evidence/20261109T135811.364204Z/batch3-cuda/cuSPARSE_cg_cg_example.c](../../../reports/evidence/20261109T135811.364204Z/batch3-cuda/cuSPARSE_cg_cg_example.c)
