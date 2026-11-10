# cuTENSOR::elementwise_permute_padding.cu

**PASSED / L4**

使用 HIP GPU permutation/padding；保留原始规模和FP32精度，3 cases全输出独立FP64 CPU及同输入CUDA通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuTENSOR/elementwise_permute_padding.cu](../../../cuTENSOR/elementwise_permute_padding.cu) |
| 实际库 / 后端 | HIP GPU permutation/padding / HIP runtime |
| 候选路线 | hipTensor, rocBLAS + HIP permutations |
| 代码 | [rocm/ported/cuTENSOR/elementwise_permute_padding.cu](../../../rocm/ported/cuTENSOR/elementwise_permute_padding.cu) |
| required cases | 3/3 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `baacb8555230f7371983ac578221d6cffea32ca4963881aee778053f45f90f50` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches4_8/original`, `batches4_8/small-asymmetric`, `batches4_8/small-strided`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

run 失败：

尝试库：hiptensor；实现 hash：`c7fcad92d46499e155c3df1f9cf92d90b567be9ed6dcca711eb6d87769a574db`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches4_8_run.py b5
python3 tools/migration/batches4_8_validate.py b5 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/evidence/20261110T025416.579830Z/batches4_8-rocm/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261110T025416.579830Z/batches4_8-rocm/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/batches4_8-validation.json](../../reports/batches4_8-validation.json)
- [migration/reports/evidence/20261110T025136.624496Z/batches4_8-cuda/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261110T025136.624496Z/batches4_8-cuda/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/evidence/20261110T030255.868642Z/batches4_8-rocm/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261110T030255.868642Z/batches4_8-rocm/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/evidence/20261110T031151.160107Z/batches4_8-rocm/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261110T031151.160107Z/batches4_8-rocm/cuTENSOR_elementwise_permute_padding.cu)
- [migration/reports/evidence/20261110T030424.000639Z/batches4_8-cuda/cuTENSOR_elementwise_permute_padding.cu](../../reports/evidence/20261110T030424.000639Z/batches4_8-cuda/cuTENSOR_elementwise_permute_padding.cu)
