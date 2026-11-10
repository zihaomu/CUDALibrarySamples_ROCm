# cuBLASMp::gemm.cu

**PARTIAL / L4**

使用MPI + RCCL distribution + hipBLAS FP32 local GEMM；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。本轮GEMM保持FP32/尺寸与A/C分布；原例B的IB=3子矩阵描述符及完整transpose/CLI控制未逐项等价，保留部分支持。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLASMp/gemm.cu](../../../cuBLASMp/gemm.cu) |
| 实际库 / 后端 | MPI + RCCL distribution + hipBLAS FP32 local GEMM / MPI + RCCL distribution + hipBLAS FP32 local GEMM |
| 候选路线 | rocBLAS, RCCL, MPI |
| 代码 | [rocm/ported/cuBLASMp/gemm.cu](../../../rocm/ported/cuBLASMp/gemm.cu) |
| required cases | 6/7 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `d44714cf598486dc665036d5e9a5e78ad2194489f3b8ec233f1e743020ebe1a0` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`, `batches12_15/original-B-submatrix-offset-and-full-transpose-controls`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：未完成合同：original-B-submatrix-offset-and-full-transpose-controls；补实现/真实后端并重验。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/gemm.cu:19:10: fatal error: 'cublasmp.h' file not found

尝试库：—；实现 hash：`339cb87a559ed99350ddc34e2d9556679b3d445f6822ba8d0dea311baf79838d`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b12
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b12 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuBLASMp_gemm.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuBLASMp_gemm.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_gemm.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_gemm.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_gemm.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_gemm.cu)
- [migration/reports/evidence/20261110T050427.265443Z/batches12_15-rocm/cuBLASMp_gemm.cu](../../reports/evidence/20261110T050427.265443Z/batches12_15-rocm/cuBLASMp_gemm.cu)
- [migration/reports/batches12_15-validation.json](../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_gemm.cu](../../reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_gemm.cu)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_gemm.cu](../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_gemm.cu)
