# NPP/distanceTransform::distanceTransform.cpp

**PASSED / L4**

使用HIP exact separable Euclidean distance/Voronoi/integer truncation kernels；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/distanceTransform/distanceTransform.cpp](../../../../NPP/distanceTransform/distanceTransform.cpp) |
| 实际库 / 后端 | HIP exact separable Euclidean distance/Voronoi/integer truncation kernels / HIP exact separable Euclidean distance/Voronoi/integer truncation kernels |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/distanceTransform/distanceTransform.cpp](../../../../rocm/ported/NPP/distanceTransform/distanceTransform.cpp) |
| required cases | 6/6 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `7e5d292f6ee99ef7afc02d9af3659d5d5538ab28915dbde015e4042acdef36d1` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：扩展其它dtype、规模、线程块/进程网格、多节点或性能需新增登记case并重验。

CUDA 对照限制：当前 AMD 路线尚未通过正确性验收。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/distanceTransform/distanceTransform.cpp:26:10: fatal error: 'nppdefs.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra

尝试库：—；实现 hash：`dbebe97321b4c498e2c9f25a51274cffb8c9ef1aec62d0463b2fefdc596da161`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b15
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b15 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/batches12_15-validation.json](../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_distanceTransform_distanceTransform.cpp)
- [migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_distanceTransform_distanceTransform.cpp](../../../reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_distanceTransform_distanceTransform.cpp)
