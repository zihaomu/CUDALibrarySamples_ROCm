# cuSPARSE/gpsvInterleavedBatch::gpsvInterleavedBatch_example.c

**PASSED / L4**

使用 hipSPARSE + hipBLAS / rocSPARSE/rocBLAS 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/gpsvInterleavedBatch/gpsvInterleavedBatch_example.c](../../../../cuSPARSE/gpsvInterleavedBatch/gpsvInterleavedBatch_example.c) |
| 实际库 / 后端 | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/gpsvInterleavedBatch/gpsvInterleavedBatch_example.c](../../../../rocm/ported/cuSPARSE/gpsvInterleavedBatch/gpsvInterleavedBatch_example.c) |
| required cases | 3/3 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `514b103314ee3c081d270dfce0edb65032cfea8bdfe196dc81b26b7ca4579f92` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batch3/original`, `batch3/changed-rhs`, `batch3/diagonal-dominant`。

实现方式：`API_PORT`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsparse；实现 hash：`4db965db79af56922f7ab80931e9b931e388b5f98d0ce371bd4985bfaaecff73`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch3_run.py sparse
python3 tools/migration/batch3_validate.py sparse --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c)
- [migration/reports/evidence/20261109T135624.134389Z/batch3-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c](../../../reports/evidence/20261109T135624.134389Z/batch3-rocm/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c)
- [migration/reports/batch3-validation.json](../../../reports/batch3-validation.json)
- [migration/reports/evidence/20261109T135443.759704Z/batch3-cuda/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c](../../../reports/evidence/20261109T135443.759704Z/batch3-cuda/cuSPARSE_gpsvInterleavedBatch_gpsvInterleavedBatch_example.c)
