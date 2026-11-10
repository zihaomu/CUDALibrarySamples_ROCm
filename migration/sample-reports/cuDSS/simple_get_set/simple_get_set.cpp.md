# cuDSS/simple_get_set::simple_get_set.cpp

**PARTIAL / L4**

使用 CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter；8 个预登记case通过独立CPU与同输入CUDA。稀疏求解、实际Hungarian matching/缩放、分步/融合GPU数值策略、IR、排列/LU/LDL对角/惯性查询已验证；完整cuDSS超级面板策略、16项host/peak内存估计和原矩阵顺序DIAG查询尚未逐项等价。项目核心内存用量与因子顺序对角明确标注，不填造vendor查询。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuDSS/simple_get_set/simple_get_set.cpp](../../../../cuDSS/simple_get_set/simple_get_set.cpp) |
| 实际库 / 后端 | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter / rocSOLVER/HIP runtime |
| 候选路线 | rocSOLVER CSRRF, rocSPARSE/HIP, ISO_C_BINDING |
| 代码 | [rocm/ported/cuDSS/simple_get_set/simple_get_set.cpp](../../../../rocm/ported/cuDSS/simple_get_set/simple_get_set.cpp) |
| required cases | 8/9 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `e621d1f3e3d3a5aa76bd4749d0e48bcbbf6e504113e4a2909ae8ed2718282a64` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original`, `batches9_11/changed-values`, `batches9_11/varied-pattern`, `batches9_11/reorder-natural`, `batches9_11/pivot-required`, `batches9_11/singular-info`, `batches9_11/indefinite`, `batches9_11/configuration`, `batches9_11/full-cuDSS-config-query-semantics`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：缺失范围：full-cuDSS-config-query-semantics；需要真实后端/完整harness并重做验收。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuDSS/simple_get_set/simple_get_set.cpp:26:10: fatal error: 'cudss.h' file not found

尝试库：—；实现 hash：`d459928d87c293493ac6bb1b3e9ce89a639f64408031a11a86d229ebc693cfd1`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches9_11_run.py b11
OPENBLAS_NUM_THREADS=1 python3 tools/migration/batches9_11_validate.py b11 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_get_set_simple_get_set.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/cuDSS_simple_get_set_simple_get_set.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_get_set_simple_get_set.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/cuDSS_simple_get_set_simple_get_set.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_get_set_simple_get_set.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/cuDSS_simple_get_set_simple_get_set.cpp)
- [migration/reports/evidence/20261110T043650.167709Z/batches9_11-rocm/cuDSS_simple_get_set_simple_get_set.cpp](../../../reports/evidence/20261110T043650.167709Z/batches9_11-rocm/cuDSS_simple_get_set_simple_get_set.cpp)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/cuDSS_simple_get_set_simple_get_set.cpp](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/cuDSS_simple_get_set_simple_get_set.cpp)
