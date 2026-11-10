# cuDSS/simple_batch::simple_batch.cpp

**PASSED / L4**

使用 CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter；8 个预登记case通过独立CPU与同输入CUDA。保留原始规模、矩阵类别/CPU-GPU阶段分工；适配范围与实际GPU执行、status/返回长度及配置查询逐例记录。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/simple_batch/simple_batch.cpp](../../../../cuDSS/simple_batch/simple_batch.cpp) |
| 实际库 / 后端 | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter / rocSOLVER/HIP runtime |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/simple_batch/simple_batch.cpp](../../../../rocm/ported/cuDSS/simple_batch/simple_batch.cpp) |
| required cases | 8/8 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `35bce10e48fb98d910d3f9bafa653786b39faeaa22f8a14844b75aa9525cb856` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original`, `batches9_11/changed-values`, `batches9_11/varied-pattern`, `batches9_11/reorder-natural`, `batches9_11/pivot-required`, `batches9_11/singular-info`, `batches9_11/indefinite`, `batches9_11/configuration`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：扩展其它精度/规模/参数需要新增预登记case并重新验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/simple_batch/simple_batch.cpp:25:10: fatal error: 'cudss.h' file not found

尝试库：—；实现 hash：`2179ffc241a18684a7f620e3cd8f9449a6649f817611df0156f6fb0447aa1715`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b11
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b11 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_batch_simple_batch.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_batch_simple_batch.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_batch_simple_batch.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_batch_simple_batch.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_batch_simple_batch.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_batch_simple_batch.cpp)
- [migration/reports/evidence/20261110T043650.167709Z/batches9_11-rocm/cuDSS_simple_batch_simple_batch.cpp](../../../reports/evidence/20261110T043650.167709Z/batches9_11-rocm/cuDSS_simple_batch_simple_batch.cpp)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/cuDSS_simple_batch_simple_batch.cpp](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/cuDSS_simple_batch_simple_batch.cpp)
