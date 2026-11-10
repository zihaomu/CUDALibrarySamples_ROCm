# cuSPARSE/spsv_sell::spsv_sell_example.c

**PASSED / L4**

使用 hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime 保留原始dtype/布局与数学运算；4 个预登记输入case通过独立CPU与同输入CUDA，GPU适配和数值路径均已检查。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/spsv_sell/spsv_sell_example.c](../../../../cuSPARSE/spsv_sell/spsv_sell_example.c) |
| 实际库 / 后端 | hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/spsv_sell/spsv_sell_example.c](../../../../rocm/ported/cuSPARSE/spsv_sell/spsv_sell_example.c) |
| required cases | 4/4 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `fa3d1179dcd4b59c39ffd29da69daec10a43e426ddf1871eb1b25126fec24ef0` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches4_8/original`, `batches4_8/changed-values`, `batches4_8/unit-diagonal`, `batches4_8/upper`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败：CUSPARSE API failed at line 128 with error: function is not implemented (10)

尝试库：hipsparse；实现 hash：`0da5732d542fadee17bc8105a51ec24dd5a371081d8ef213f80dd08c0e307e3f`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches4_8_run.py b4
python3 tools/migration/batches4_8_validate.py b4 --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spsv_sell_spsv_sell_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spsv_sell_spsv_sell_example.c)
- [migration/reports/evidence/20261110T024004.667635Z/batches4_8-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c](../../../reports/evidence/20261110T024004.667635Z/batches4_8-rocm/cuSPARSE_spsv_sell_spsv_sell_example.c)
- [migration/reports/batches4_8-validation.json](../../../reports/batches4_8-validation.json)
- [migration/reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuSPARSE_spsv_sell_spsv_sell_example.c](../../../reports/evidence/20261110T023758.405542Z/batches4_8-cuda/cuSPARSE_spsv_sell_spsv_sell_example.c)
