# nvCOMP/benchmarks::benchmark_lz4_chunked.cu

**PARTIAL / L4**

使用 hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter；8 个预登记case通过独立CPU与同输入CUDA。默认uint8 LZ4/Snappy batch核心及互操作已验证；原始NVBENCH注册/控制参数与完整benchmark CLI未移植，不将codec driver当成完整benchmark。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvCOMP/benchmarks/benchmark_lz4_chunked.cu](../../../../nvCOMP/benchmarks/benchmark_lz4_chunked.cu) |
| 实际库 / 后端 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs |
| 候选路线 | hipCOMP |
| 代码 | [rocm/ported/nvCOMP/benchmarks/benchmark_lz4_chunked.cu](../../../../rocm/ported/nvCOMP/benchmarks/benchmark_lz4_chunked.cu) |
| required cases | 8/9 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `f3a33a146c336c726c36f0e78628bb3c86c8de67f6ee47e714f1c0606302c5b0` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original`, `batches9_11/variable-batch`, `batches9_11/boundary-lengths`, `batches9_11/random`, `batches9_11/repeat`, `batches9_11/corrupt-stream`, `batches9_11/truncated-stream`, `batches9_11/cross-library-interop`, `batches9_11/original-nvbench-CLI-and-measurement-harness`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：缺失范围：original-nvbench-CLI-and-measurement-harness；需要真实后端/完整harness并重做验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/benchmarks/benchmark_lossy_common.h:29:10: fatal error: 'hipcomp/native/bitcomp.h' file not found

尝试库：—；实现 hash：`7c252df45869fa4ca7ddfec77a72a8ce538452ca386b3f9d6a6643f55726916b`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b9
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b9 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_benchmarks_benchmark_lz4_chunked.cu](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_benchmarks_benchmark_lz4_chunked.cu)
- [migration/reports/evidence/20261110T040459.173461Z/batches9_11-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu](../../../reports/evidence/20261110T040459.173461Z/batches9_11-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T040252.903898Z/batches9_11-cuda/nvCOMP_benchmarks_benchmark_lz4_chunked.cu](../../../reports/evidence/20261110T040252.903898Z/batches9_11-cuda/nvCOMP_benchmarks_benchmark_lz4_chunked.cu)
- [migration/reports/evidence/20261110T043427.533946Z/batches9_11-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu](../../../reports/evidence/20261110T043427.533946Z/batches9_11-rocm/nvCOMP_benchmarks_benchmark_lz4_chunked.cu)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvCOMP_benchmarks_benchmark_lz4_chunked.cu](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvCOMP_benchmarks_benchmark_lz4_chunked.cu)
