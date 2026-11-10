# nvCOMP/examples::low_level_quickstart_example.cpp

**PASSED / L4**

使用 hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter；8 个预登记case通过独立CPU与同输入CUDA。保留原始规模、矩阵类别/CPU-GPU阶段分工；适配范围与实际GPU执行、status/返回长度及配置查询逐例记录。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvCOMP/examples/low_level_quickstart_example.cpp](../../../../nvCOMP/examples/low_level_quickstart_example.cpp) |
| 实际库 / 后端 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs |
| 候选路线 | hipCOMP |
| 代码 | [rocm/ported/nvCOMP/examples/low_level_quickstart_example.cpp](../../../../rocm/ported/nvCOMP/examples/low_level_quickstart_example.cpp) |
| required cases | 8/8 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `b7a99efe68d232e33b83aa26ee446f85a4176353ed01cc8e035782fe385ba4ff` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original`, `batches9_11/variable-batch`, `batches9_11/boundary-lengths`, `batches9_11/random`, `batches9_11/repeat`, `batches9_11/corrupt-stream`, `batches9_11/truncated-stream`, `batches9_11/cross-library-interop`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：扩展其它精度/规模/参数需要新增预登记case并重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/low_level_quickstart_example.cpp:51:19: error: use of undeclared identifier 'nvcompLZ4CompressionMaxAllowedChunkSize'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/examples/low_level_quickstart_example.cpp:106:5: error: use of undeclared identifier 'nvcompBatchedLZ4CompressDefaultOpts'

尝试库：—；实现 hash：`3b64f6b33a7fd6c714d36888eeb30fa61ea7de9f2430288ad57badf93886d51e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b9
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b9 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/native-probes.json](../../../reports/native-probes.json)
- [migration/reports/evidence/20261109T084040.925641Z/native-probes/hipcomp_lz4](../../../reports/evidence/20261109T084040.925641Z/native-probes/hipcomp_lz4)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/evidence/20261110T040459.173461Z/batches9_11-rocm/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261110T040459.173461Z/batches9_11-rocm/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T040252.903898Z/batches9_11-cuda/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261110T040252.903898Z/batches9_11-cuda/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/evidence/20261110T043427.533946Z/batches9_11-rocm/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261110T043427.533946Z/batches9_11-rocm/nvCOMP_examples_low_level_quickstart_example.cpp)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvCOMP_examples_low_level_quickstart_example.cpp](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvCOMP_examples_low_level_quickstart_example.cpp)
