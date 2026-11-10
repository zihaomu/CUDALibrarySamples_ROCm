# cuBLASMp::gemr2d.cu

**PASSED / L4**

使用MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuBLASMp/gemr2d.cu](../../../cuBLASMp/gemr2d.cu) |
| 实际库 / 后端 | MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip / MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip |
| 候选路线 | rocBLAS, RCCL, MPI |
| 代码 | [rocm/ported/cuBLASMp/gemr2d.cu](../../../rocm/ported/cuBLASMp/gemr2d.cu) |
| required cases | 6/6 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `65d864ae78fdcad8441048b34d5727534d2fdae2e5a69909be26fe3b66c8f5c6` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：扩展其它dtype、规模、线程块/进程网格、多节点或性能需新增登记case并重验。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuBLASMp/gemr2d.cu:19:10: fatal error: 'cublasmp.h' file not found

尝试库：—；实现 hash：`04ab7a0d3388e7c5c34309641fe33e758024395cfc8ac9e188f8ee392f40e344`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b12
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b12 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuBLASMp_gemr2d.cu](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuBLASMp_gemr2d.cu)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_gemr2d.cu](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuBLASMp_gemr2d.cu)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_gemr2d.cu](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuBLASMp_gemr2d.cu)
- [migration/reports/evidence/20261110T050427.265443Z/batches12_15-rocm/cuBLASMp_gemr2d.cu](../../reports/evidence/20261110T050427.265443Z/batches12_15-rocm/cuBLASMp_gemr2d.cu)
- [migration/reports/batches12_15-validation.json](../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_gemr2d.cu](../../reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuBLASMp_gemr2d.cu)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_gemr2d.cu](../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuBLASMp_gemr2d.cu)
