# cuTENSOR::elementwise_permute.cu

**PARTIAL / L3**

原始教学输入构建运行通过；独立正确性验证待完成

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuTENSOR/elementwise_permute.cu](../../../cuTENSOR/elementwise_permute.cu) |
| 实际库 / 后端 | hiptensor / hipTensor |
| 候选路线 | hipTensor, rocBLAS + HIP permutations |
| 代码 | [rocm/ported/cuTENSOR/elementwise_permute.cu](../../../rocm/ported/cuTENSOR/elementwise_permute.cu) |
| required cases | 1/3 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `6a268af4f99d92047df63788719d5468f68bba98d5965fd6d726df16d14ab87a` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`build-and-original-profile-execution`, `original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hiptensor；实现 hash：`6a5930319fb22f970516633ec0c917792e00cefdde97c945e8250eb8cba46f4c`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_permute.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_permute.cu)
- [migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_permute.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_permute.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_permute.cu)
