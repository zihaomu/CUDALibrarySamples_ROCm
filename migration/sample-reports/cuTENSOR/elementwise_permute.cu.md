# cuTENSOR::elementwise_permute.cu

**PASSED / L4**

使用 hipTensor / hipTensor 保留原始 profile 与数学 API；3 个预登记输入 case 均通过独立 CPU 数值/结构/残差检查。同输入 CUDA 与 CPU 三方对照通过。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuTENSOR/elementwise_permute.cu](../../../cuTENSOR/elementwise_permute.cu) |
| 实际库 / 后端 | hipTensor / hipTensor |
| 候选路线 | hipTensor, rocBLAS + HIP permutations |
| 代码 | [rocm/ported/cuTENSOR/elementwise_permute.cu](../../../rocm/ported/cuTENSOR/elementwise_permute.cu) |
| required cases | 3/3 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `6a268af4f99d92047df63788719d5468f68bba98d5965fd6d726df16d14ab87a` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batch2/original`, `batch2/small-nonzero`, `batch2/small-zero`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hiptensor；实现 hash：`6a5930319fb22f970516633ec0c917792e00cefdde97c945e8250eb8cba46f4c`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batch2_run.py tensor
python3 tools/migration/batch2_validate.py tensor --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_permute.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_permute.cu)
- [migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_permute.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_permute.cu)
- [migration/reports/evidence/20261109T120640.677903Z/batch2-rocm/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T120640.677903Z/batch2-rocm/cuTENSOR_elementwise_permute.cu)
- [migration/reports/batch2-validation.json](../../reports/batch2-validation.json)
- [migration/reports/evidence/20261109T120648.693848Z/batch2-cuda/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T120648.693848Z/batch2-cuda/cuTENSOR_elementwise_permute.cu)
