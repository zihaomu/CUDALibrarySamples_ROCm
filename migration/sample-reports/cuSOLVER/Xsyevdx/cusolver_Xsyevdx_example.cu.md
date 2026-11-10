# cuSOLVER/Xsyevdx::cusolver_Xsyevdx_example.cu

**PASSED / L4**

使用 rocSOLVER dsyevx + checked dimension bridge，原始FP64 profile及4 cases通过CPU/CUDA数值、返回数量与info检查。公开typed接口限制INT_MAX，调用前显式检查，不宣称全尺寸ILP64支持。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu](../../../../cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu) |
| 实际库 / 后端 | rocSOLVER dsyevx + checked dimension bridge / rocSOLVER |
| 候选路线 | hipSOLVER, rocSOLVER |
| 代码 | [rocm/ported/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu](../../../../rocm/ported/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu) |
| required cases | 4/4 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `d444722c1961c89c4de3514893cdd94a141d1c1c4137eb869a08ed4666d01ecc` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches4_8/original`, `batches4_8/value-range`, `batches4_8/all-range`, `batches4_8/empty-range`。

实现方式：`HYBRID_HIP`。

恢复/扩展条件：已登记profile通过；扩展其它精度/规模/矩阵性质或API配置时，新增预登记输入并重新做CPU/CUDA及运行语义验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu:87:20: error: use of undeclared identifier 'cusolverDnXsyevdx_bufferSize'; did you mean 'hipsolverDnXgeev_bufferSize'?；/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu:88:34: error: cannot initialize a parameter of type 'hipsolverEigMode_t' with an lvalue of type 'hipsolverEigRange_t'

尝试库：hipsolver；实现 hash：`f8793660c018e999828a6aa8f6e1af61fe227ed69fd716310c47c46fefe95918`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches4_8_run.py b6
python3 tools/migration/batches4_8_validate.py b6 --qualify
```

- [migration/reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T080822.795958Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T081329.986729Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T081449.022777Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T081655.531829Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T081929.210831Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T084753.304309Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T085841.111146Z/original-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261109T100720.422147Z/original-cuda/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261110T030803.673603Z/batches4_8-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261110T030803.673603Z/batches4_8-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/batches4_8-validation.json](../../../reports/batches4_8-validation.json)
- [migration/reports/evidence/20261110T030639.601947Z/batches4_8-cuda/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261110T030639.601947Z/batches4_8-cuda/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261110T031028.261181Z/batches4_8-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261110T031028.261181Z/batches4_8-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261110T030831.738178Z/batches4_8-cuda/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261110T030831.738178Z/batches4_8-cuda/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
- [migration/reports/evidence/20261110T032348.941328Z/batches4_8-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu](../../../reports/evidence/20261110T032348.941328Z/batches4_8-rocm/cuSOLVER_Xsyevdx_cusolver_Xsyevdx_example.cu)
