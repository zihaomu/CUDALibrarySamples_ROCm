# nvCOMP/benchmarks::benchmark_crc32.cpp

**PARTIAL / L3**

R9候选实现已完成构建并进入独立CPU/native CUDA及原始合同验收；尚未签发复合资格，不计整例通过。历史原生API自动移植失败保留。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvCOMP/benchmarks/benchmark_crc32.cpp](../../../../nvCOMP/benchmarks/benchmark_crc32.cpp) |
| 实际库 / 后端 | Project HIP segmented IEEE CRC32 + GPU GF2 combine + original benchmark harness + hipRAND / Project HIP runtime adapter |
| 候选路线 | hipCOMP |
| 代码 | [rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp](../../../../rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp) |
| required cases | 1/5 |
| CUDA baseline / comparison | BLOCKED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `e343816ec5a4af1af1b907da5534aa010f2c579658883559b913465463a69f7e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`rewrite-R9/current-build`, `rewrite-R9/frozen-inputs-and-original-contract`, `rewrite-R9/CPU-and-native-CUDA`, `rewrite-R9/negative-and-runtime`, `rewrite-R9/independent-review-and-qualification`。

实现方式：`API_PORT`。

恢复/扩展条件：完成当前源码完整原始合同、实际语言/CLI、独立CPU/native CUDA、故障及边界检查和固定提交独立复审后再签发资格。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp:321:3: error: unknown type name 'nvcompCRC32KernelConf_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp:327:5: error: use of undeclared identifier 'nvcompCRC32'

尝试库：—；实现 hash：`a7d9f686fabe127764435e609da33cb658a5435d54d9201ed622bd59dc9c0bc3`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvCOMP_benchmarks_benchmark_crc32.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_benchmarks_benchmark_crc32.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvCOMP_benchmarks_benchmark_crc32.cpp)
- [migration/reports/rewrite-R9.md](../../../reports/rewrite-R9.md)
