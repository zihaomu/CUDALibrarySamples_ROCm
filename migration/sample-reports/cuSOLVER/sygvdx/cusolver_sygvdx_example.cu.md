# cuSOLVER/sygvdx::cusolver_sygvdx_example.cu

**PASSED / L4**

使用 hipSOLVER / rocSOLVER/rocBLAS 保留原始 profile 与数学 API；4 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/sygvdx/cusolver_sygvdx_example.cu](../../../../cuSOLVER/sygvdx/cusolver_sygvdx_example.cu) |
| 实际库 / 后端 | hipSOLVER / rocSOLVER/rocBLAS |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/sygvdx/cusolver_sygvdx_example.cu](../../../../rocm/ported/cuSOLVER/sygvdx/cusolver_sygvdx_example.cu) |
| required cases | 4/4 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `fb64f3df569a58ae20f1f7f0c67598aa5c27fef236d26a8083c41d503b81f63e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batch3/original`, `batch3/value-range`, `batch3/all-range`, `batch3/empty-range`。

实现方式：`API_PORT`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsolver；实现 hash：`29132ea0d7db8169f01cac8482eea2bc8afb48f7504fa28caf262e2df70090c9`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch3_run.py solver
python3 tools/migration/batch3_validate.py solver --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/evidence/20261109T140152.327246Z/batch3-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T140152.327246Z/batch3-rocm/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
- [migration/reports/batch3-validation.json](../../../reports/batch3-validation.json)
- [migration/reports/evidence/20261109T135901.256203Z/batch3-cuda/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu](../../../reports/evidence/20261109T135901.256203Z/batch3-cuda/cuSOLVER_sygvdx_cusolver_sygvdx_example.cu)
