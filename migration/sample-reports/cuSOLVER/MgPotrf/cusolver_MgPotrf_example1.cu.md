# cuSOLVER/MgPotrf::cusolver_MgPotrf_example1.cu

**PARTIAL / L4**

使用HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。8阶/2RHS与单进程多GPU数值通过；项目按列重分配让两卡计算，未实现原始tile256输入/输出描述符的完整转换契约。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu](../../../../cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu) |
| 实际库 / 后端 | HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads / HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu](../../../../rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu) |
| required cases | 6/7 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `61487e5427c3ae4649052dbada90a53e4005921d45342be5a5f7e32641957571` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`, `batches12_15/original-Mg-input-distribution-descriptor`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：未完成合同：original-Mg-input-distribution-descriptor；补实现/真实后端并重验。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu:67:5: error: unknown type name 'cusolverMgHandle_t'；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu:92:5: error: unknown type name 'cudaLibMgMatrixDesc_t'

尝试库：hipsolver；实现 hash：`4fb56543015d98b3b8025b4b70f6fe639e13dda25aad7750d0023973eb036fd0`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b13
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b13 --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261110T051040.812262Z/batches12_15-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261110T051040.812262Z/batches12_15-rocm/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/batches12_15-validation.json](../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261110T052304.022239Z/batches12_15-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
- [migration/reports/evidence/20261110T051849.336070Z/batches12_15-native-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu](../../../reports/evidence/20261110T051849.336070Z/batches12_15-native-cuda/cuSOLVER_MgPotrf_cusolver_MgPotrf_example1.cu)
