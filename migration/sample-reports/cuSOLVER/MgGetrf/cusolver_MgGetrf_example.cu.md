# cuSOLVER/MgGetrf::cusolver_MgGetrf_example.cu

**PASSED / L4**

使用HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu](../../../../cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu) |
| 实际库 / 后端 | HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads / HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu](../../../../rocm/ported/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu) |
| required cases | 6/6 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `26d83fe9476aadfefcf8e26705577f769f12e18b8c87b831ef07051e3dff9040` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：扩展其它dtype、规模、线程块/进程网格、多节点或性能需新增登记case并重验。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu:56:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu:79:5: error: unknown type name 'cudaLibMgMatrixDesc_t'

尝试库：hipsolver；实现 hash：`fc5900121db6a9b5c909b4782d2ad8b042258935c53e7000077ca4787828f698`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b13
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b13 --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261110T051040.812262Z/batches12_15-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261110T051040.812262Z/batches12_15-rocm/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/batches12_15-validation.json](../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
- [migration/reports/evidence/20261110T051849.336070Z/batches12_15-native-cuda/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu](../../../reports/evidence/20261110T051849.336070Z/batches12_15-native-cuda/cuSOLVER_MgGetrf_cusolver_MgGetrf_example.cu)
