# cuSPARSE/graph_capture::graph_capture_example.c

**PASSED / L4**

使用 hipSPARSE + HIP Graph / rocSPARSE + HIP runtime 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。初始化确定性输入并改用device pointer mode；实际GPU图节点及三次输入变化replay均已检查。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/graph_capture/graph_capture_example.c](../../../../cuSPARSE/graph_capture/graph_capture_example.c) |
| 实际库 / 后端 | hipSPARSE + HIP Graph / rocSPARSE + HIP runtime |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/graph_capture/graph_capture_example.c](../../../../rocm/ported/cuSPARSE/graph_capture/graph_capture_example.c) |
| required cases | 3/3 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `23cea5e0266b517c4176c69f5c706c00b2b3cf1cfb953b4aa64d19d6f5618fe0` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batch3/original`, `batch3/sparse-small`, `batch3/cancellation`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsparse；实现 hash：`fb76c4297d87a4242163c90c4c31374a220bcd3971f9d38d5e8f1dcb3bca8bb3`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch3_run.py graph
python3 tools/migration/batch3_validate.py graph --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_graph_capture_graph_capture_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_graph_capture_graph_capture_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_graph_capture_graph_capture_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_graph_capture_graph_capture_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_graph_capture_graph_capture_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_graph_capture_graph_capture_example.c)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_graph_capture_graph_capture_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_graph_capture_graph_capture_example.c)
- [migration/reports/evidence/20261109T140254.599681Z/batch3-rocm/cuSPARSE_graph_capture_graph_capture_example.c](../../../reports/evidence/20261109T140254.599681Z/batch3-rocm/cuSPARSE_graph_capture_graph_capture_example.c)
- [migration/reports/batch3-validation.json](../../../reports/batch3-validation.json)
- [migration/reports/evidence/20261109T140047.312334Z/batch3-cuda/cuSPARSE_graph_capture_graph_capture_example.c](../../../reports/evidence/20261109T140047.312334Z/batch3-cuda/cuSPARSE_graph_capture_graph_capture_example.c)
