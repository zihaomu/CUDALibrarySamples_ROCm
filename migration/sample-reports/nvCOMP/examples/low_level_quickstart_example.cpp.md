# nvCOMP/examples::low_level_quickstart_example.cpp

**PARTIAL / L3**

LZ4 GPU 压缩/解压在 128/32768/65536 字节、单 chunk 输入逐字节往返通过；原始现代 nvCOMP status/options、batch 和其它 codec 契约未完成，保留 PARTIAL。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvCOMP/examples/low_level_quickstart_example.cpp](../../../../nvCOMP/examples/low_level_quickstart_example.cpp) |
| 实际库 / 后端 | hipCOMP / hipCOMP |
| 候选路线 | hipCOMP |
| 代码 | [rocm/probes/hipcomp_lz4.cpp](../../../../rocm/probes/hipcomp_lz4.cpp) |
| required cases | 1/2 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `b7a99efe68d232e33b83aa26ee446f85a4176353ed01cc8e035782fe385ba4ff` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`gpu-subset-probe`, `original-full-functional-contract`。

实现方式：`API_PORT`。

恢复/扩展条件：实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/low_level_quickstart_example.cpp:51:19: error: use of undeclared identifier 'nvcompLZ4CompressionMaxAllowedChunkSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/low_level_quickstart_example.cpp:106:5: error: use of undeclared identifier 'nvcompBatchedLZ4CompressDefaultOpts'

尝试库：—；实现 hash：`3b64f6b33a7fd6c714d36888eeb30fa61ea7de9f2430288ad57badf93886d51e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python tools/migration/probes.py hipcomp_lz4
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/native-probes.json](../../../reports/native-probes.json)
- [migration/reports/evidence/20261109T084040.925641Z/native-probes/hipcomp_lz4](../../../reports/evidence/20261109T084040.925641Z/native-probes/hipcomp_lz4)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_examples_low_level_quickstart_example.cpp)
