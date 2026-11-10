# NPP+/floodFill::floodFillVariousRegionTypesNPPPlus.cpp

**PARTIAL / L4**

使用HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。五种GPU连接/gradient/range/boundary路径及区域统计已验收；原生NPP+ SDK缺失，原例完整paint值/metadata结构和边界策略未逐项等价。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp](../../../../NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp) |
| 实际库 / 后端 | HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata / HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp](../../../../rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp) |
| required cases | 6/7 |
| CUDA baseline / comparison | FAILED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `b607b3cc985c64e4504fa62a9e08f0fd296821737726f87d90d74653c683eb5c` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches12_15/original`, `batches12_15/irregular`, `batches12_15/changed-values`, `batches12_15/boundary`, `batches12_15/repeat`, `batches12_15/singular-or-empty`, `batches12_15/native-NPPPlus-five-mode-metadata-and-paint-contract`。

实现方式：`API_PORT_WITH_EXECUTION_ADAPTER`。

恢复/扩展条件：未完成合同：native-NPPPlus-five-mode-metadata-and-paint-contract；补实现/真实后端并重验。

CUDA 对照限制：CUDA 原始 SDK、绑定或输入前置条件未满足，见该例 CUDA 基线证据。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp:42:10: fatal error: 'nppPlus/nppPlus.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_samp

尝试库：—；实现 hash：`fe19a590d9e1099b485cd5682c436a0b2071117ffebe99962e7623587bc80f8e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。

```bash
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b15
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b15 --qualify
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T051547.561861Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/batches12_15-validation.json](../../../reports/batches12_15-validation.json)
- [migration/reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T051436.908488Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T051620.655991Z/batches12_15-native-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
- [migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp](../../../reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)
