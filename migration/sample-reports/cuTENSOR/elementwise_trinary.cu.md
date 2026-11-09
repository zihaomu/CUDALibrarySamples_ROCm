# cuTENSOR::elementwise_trinary.cu

**PARTIAL / L3**

原始教学输入构建运行通过；独立正确性验证待完成

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuTENSOR/elementwise_trinary.cu](../../../cuTENSOR/elementwise_trinary.cu) |
| 实际库 / 后端 | hiptensor / hipTensor |
| 候选路线 | hipTensor, rocBLAS + HIP permutations |
| 代码 | [rocm/ported/cuTENSOR/elementwise_trinary.cu](../../../rocm/ported/cuTENSOR/elementwise_trinary.cu) |
| required cases | 1/3 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `10417308554360d90de298e5a7af1c77596234763b37fe8d20b0fb95948473f8` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`build-and-original-profile-execution`, `original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

原始教学输入构建运行通过；独立正确性验证待完成

尝试库：hiptensor；实现 hash：`2342a6b3a57a3631352c8a853e41457901ff7d5c1e71227823b106434fe8a06b`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_trinary.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuTENSOR_elementwise_trinary.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_trinary.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuTENSOR_elementwise_trinary.cu)
- [migration/reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_trinary.cu](../../reports/evidence/20261109T091118.060291Z/original-rocm/cuTENSOR_elementwise_trinary.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_trinary.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuTENSOR_elementwise_trinary.cu)
