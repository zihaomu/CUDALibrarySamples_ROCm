# NPP+/watershedSegmentation::watershedSegmentationNPPPlus.cpp

**PARTIAL / L3**

完整原始入口及 3 张图/12 件产品已在 AMD GPU 执行，独立 NumPy 模型逐字节一致，缺图拒绝通过；原生 NPP 最低分割像素一致率 0.7171，平台区归属和边界语义未达到原例等价，当前只能算部分实现。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp](../../../../NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp) |
| 实际库 / 后端 | Project HIP eight-neighbor gradient descent and root-label compression / project HIP image watershed |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp](../../../../rocm/ported/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp) |
| required cases | 4/6 |
| CUDA baseline / comparison | PASSED / OBSERVED_ALGORITHM_VARIANT |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `da1f96daa9b45c9bc4e4bbf81545586f47adf1c9f1a2b389d163490837b8a8f5` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`original-products-and-names`, `independent-project-CPU-all-output-bytes`, `missing-input-rejection`, `real-HIP-kernel-trace`, `NPP-native-algorithm-parity`, `fixed-commit-cold-and-independent-review`。

实现方式：`ALGORITHM_VARIANT`。

恢复/扩展条件：重写分桶浸没、平台区、压紧标签和边界模式；预登记原生分区/边界/像素阈值后重新独立验收及冷检出。

CUDA 对照限制：原始5090完整输入/产品与HIP逐像素对照见 image-watershed-native-comparison.json；标签ID与分割边界均有显著差异。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.h:41:10: fatal error: 'nppPlus/nppPlus.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_

尝试库：—；实现 hash：`f71623d375288b05799a830e98e8f87f9c64e6ebda29b7752f29872301ed6f8b`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_watershed_contracts.py
python3 tools/moat/image_watershed_build.py
python3 tools/moat/image_watershed_run.py
python3 tools/moat/image_watershed_reference.py
python3 tools/moat/image_watershed_native_compare.py
python3 tools/moat/image_watershed_negative.py
python3 tools/moat/image_watershed_trace.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp)
- [migration/reports/evidence/rewrite/I3/two-original-watershed-entrypoints-HIP-build/20261112T075703.512339Z-I3-rocm-build-306c18b8a2](../../../reports/evidence/rewrite/I3/two-original-watershed-entrypoints-HIP-build/20261112T075703.512339Z-I3-rocm-build-306c18b8a2)
- [migration/reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T075927.527937Z-I3-rocm-original-full-images-4cd77331fc](../../../reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T075927.527937Z-I3-rocm-original-full-images-4cd77331fc)
- [migration/reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T080052.117443Z-I3-independent-CPU-reference-a5790b1f7d](../../../reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T080052.117443Z-I3-independent-CPU-reference-a5790b1f7d)
- [migration/reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T080329.992777Z-I3-rocm-missing-input-4522aa3497](../../../reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T080329.992777Z-I3-rocm-missing-input-4522aa3497)
- [migration/reports/evidence/rewrite/I3/both-watershed-full-native-product-comparison/20261112T080218.005011Z-I3-CPU-native-comparison-6dd3738b3d](../../../reports/evidence/rewrite/I3/both-watershed-full-native-product-comparison/20261112T080218.005011Z-I3-CPU-native-comparison-6dd3738b3d)
- [migration/reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T080409.072052Z-I3-rocm-real-kernel-trace-e7c32312de](../../../reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T080409.072052Z-I3-rocm-real-kernel-trace-e7c32312de)
- [migration/reports/image-watershed.md](../../../reports/image-watershed.md)
