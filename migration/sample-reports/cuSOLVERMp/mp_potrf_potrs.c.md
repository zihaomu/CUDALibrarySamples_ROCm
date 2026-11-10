# cuSOLVERMp::mp_potrf_potrs.c

**PARTIAL / L4**

使用MPI + RCCL + HIP distributed column Cholesky/solve；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。保留MPI双rank/Cholesky+solve和真实分布数值；原例二维网格/子矩阵offset及随机对角占优生成profile尚未等价，当前为已登记Laplacian列分布。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVERMp/mp_potrf_potrs.c](../../../cuSOLVERMp/mp_potrf_potrs.c) |
| 实际库 / 后端 | MPI + RCCL + HIP distributed column Cholesky/solve / MPI + RCCL + HIP distributed column Cholesky/solve |
| 候选路线 | rocSOLVER, rocBLAS, MPI, RCCL |
| 代码 | [rocm/ported/cuSOLVERMp/mp_potrf_potrs.c](../../../rocm/ported/cuSOLVERMp/mp_potrf_potrs.c) |
| required cases | 6/7 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `34d54b821fc3ba83c906f323815c33beebc688ef4c32384d65d8df6de2006e48` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`, `batches12_15/original-Mp-2D-grid-offsets-and-random-SPD-profile`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：未完成合同：original-Mp-2D-grid-offsets-and-random-SPD-profile；补实现/真实后端并重验。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVERMp/mp_potrf_potrs.c:25:10: fatal error: 'mpi.h' file not found

尝试库：—；实现 hash：`bb2ed7a37796f38b8cdd6d1d0ded3e39daa55605a4fdd55a8ac3ed1e5de43da7`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b13
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b13 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/cuSOLVERMp_mp_potrf_potrs.c](../../reports/evidence/20261109T083217.050455Z/original-rocm/cuSOLVERMp_mp_potrf_potrs.c)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_potrf_potrs.c](../../reports/evidence/20261109T084256.329631Z/original-rocm/cuSOLVERMp_mp_potrf_potrs.c)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_potrf_potrs.c](../../reports/evidence/20261109T084857.451692Z/original-cuda/cuSOLVERMp_mp_potrf_potrs.c)
- [migration/reports/evidence/20261110T051040.812262Z/batches12_15-rocm/cuSOLVERMp_mp_potrf_potrs.c](../../reports/evidence/20261110T051040.812262Z/batches12_15-rocm/cuSOLVERMp_mp_potrf_potrs.c)
- [migration/reports/batches12_15-validation.json](../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuSOLVERMp_mp_potrf_potrs.c](../../reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuSOLVERMp_mp_potrf_potrs.c)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuSOLVERMp_mp_potrf_potrs.c](../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/cuSOLVERMp_mp_potrf_potrs.c)
