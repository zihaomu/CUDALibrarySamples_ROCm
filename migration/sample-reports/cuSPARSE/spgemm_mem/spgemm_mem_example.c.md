# cuSPARSE/spgemm_mem::spgemm_mem_example.c

**PASSED / L4**

使用 HIP GPU budgeted CSR SpGEMM adapter，保留原始稀疏布局/精度和数学公式；结构、全量数值、自定义行为/内存预算通过CPU/CUDA。原生CUDA SpGEMM ALG3/SpMMOp通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSPARSE/spgemm_mem/spgemm_mem_example.c](../../../../cuSPARSE/spgemm_mem/spgemm_mem_example.c) |
| 实际库 / 后端 | HIP GPU budgeted CSR SpGEMM adapter / HIP runtime |
| 候选路线 | hipSPARSE, rocSPARSE |
| 代码 | [rocm/ported/cuSPARSE/spgemm_mem/spgemm_mem_example.c](../../../../rocm/ported/cuSPARSE/spgemm_mem/spgemm_mem_example.c) |
| required cases | 4/4 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `2f013a7879a207f451f92e0046597ac30b57e49b72e0ff3e1835081e7bcbcb30` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches4_8/original`, `batches4_8/small-budget`, `batches4_8/changed-values`, `batches4_8/empty-row`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spgemm_mem/spgemm_mem_example.c:151:20: error: use of undeclared identifier 'cusparseSpGEMM_getNumProducts'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSPARSE/spgemm_mem/spgemm_mem_example.c:155:9: error: use of undeclared identifier 'cusparseSpGEMM_estimateMemory'

尝试库：hipsparse；实现 hash：`5fda3eb6408eb16c48d3f84020fc78e8b7ec095793f2781f4b1f8a00ef14463a`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches4_8_run.py b8
python3 tools/migration/batches4_8_validate.py b8 --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261109T081122.138627Z/original-cuda/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/evidence/20261110T032004.925898Z/batches4_8-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261110T032004.925898Z/batches4_8-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/batches4_8-validation.json](../../../reports/batches4_8-validation.json)
- [migration/reports/evidence/20261110T031641.554572Z/batches4_8-cuda/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261110T031641.554572Z/batches4_8-cuda/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/evidence/20261110T032153.928454Z/batches4_8-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261110T032153.928454Z/batches4_8-rocm/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/evidence/20261110T031918.495272Z/batches4_8-cuda/cuSPARSE_spgemm_mem_spgemm_mem_example.c](../../../reports/evidence/20261110T031918.495272Z/batches4_8-cuda/cuSPARSE_spgemm_mem_spgemm_mem_example.c)
- [migration/reports/b8-native-cuda-api-failure.json](../../../reports/b8-native-cuda-api-failure.json)
