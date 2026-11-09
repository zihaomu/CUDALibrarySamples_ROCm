# cuSPARSE/spgemm_reuse::spgemm_reuse_example.c

**PASSED / L4**

使用 hipSPARSE / rocSPARSE 保留原始 profile 与数学 API；2 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/spgemm_reuse/spgemm_reuse_example.c](../../../../cuSPARSE/spgemm_reuse/spgemm_reuse_example.c) |
| 实际库 / 后端 | hipSPARSE / rocSPARSE |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/spgemm_reuse/spgemm_reuse_example.c](../../../../rocm/ported/cuSPARSE/spgemm_reuse/spgemm_reuse_example.c) |
| required cases | 2/2 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `cdab2fc7c4b6ae183223a5c5f4c7f7d9291c749df5c155884169d26675f8a3f9` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batch2/original`, `batch2/changed-values`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hipsparse；实现 hash：`7ea3d5514aff9f895d409e599aae17fde1f7ba7c85faf7a9877b96a6aa8f9f24`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按第二批报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch2_run.py sparse
python3 tools/migration/batch2_validate.py sparse --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c)
- [migration/reports/evidence/20261109T115319.593333Z/batch2-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c](../../../reports/evidence/20261109T115319.593333Z/batch2-rocm/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c)
- [migration/reports/batch2-validation.json](../../../reports/batch2-validation.json)
- [migration/reports/evidence/20261109T115141.126114Z/batch2-cuda/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c](../../../reports/evidence/20261109T115141.126114Z/batch2-cuda/cuSPARSE_spgemm_reuse_spgemm_reuse_example.c)
