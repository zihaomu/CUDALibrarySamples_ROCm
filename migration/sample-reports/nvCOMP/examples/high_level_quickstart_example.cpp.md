# nvCOMP/examples::high_level_quickstart_example.cpp

**FAILED / L1**

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/high_level_quickstart_example.cpp:58:19: error: use of undeclared identifier 'nvcompLZ4CompressionMaxAllowedChunkSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/high_level_quickstart_example.cpp:62:3: error: use of undeclared identifier 'nvcompBatchedLZ4CompressOpts_t'; did you mean 'hipcompBatchedLZ4CompressAsync'?

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvCOMP/examples/high_level_quickstart_example.cpp](../../../../nvCOMP/examples/high_level_quickstart_example.cpp) |
| 实际库 / 后端 | — / — |
| 候选路线 | hipCOMP |
| 代码 | [rocm/ported/nvCOMP/examples/high_level_quickstart_example.cpp](../../../../rocm/ported/nvCOMP/examples/high_level_quickstart_example.cpp) |
| required cases | 0/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `fcc9d1b3999d8970d2a1f1d3d61ae2a977d26c60be6665acac01967f2391bb52` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-functional-contract`, `independent-numerical-or-semantic-reference`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/high_level_quickstart_example.cpp:58:19: error: use of undeclared identifier 'nvcompLZ4CompressionMaxAllowedChunkSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/high_level_quickstart_example.cpp:62:3: error: use of undeclared identifier 'nvcompBatchedLZ4CompressOpts_t'; did you mean 'hipcompBatchedLZ4CompressAsync'?

尝试库：—；实现 hash：`c5d8ee2fc306e9f04ff313f642e0698975a51ed882a5a708953781ed2b08669a`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_examples_high_level_quickstart_example.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_examples_high_level_quickstart_example.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_examples_high_level_quickstart_example.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_examples_high_level_quickstart_example.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_examples_high_level_quickstart_example.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_examples_high_level_quickstart_example.cpp)
