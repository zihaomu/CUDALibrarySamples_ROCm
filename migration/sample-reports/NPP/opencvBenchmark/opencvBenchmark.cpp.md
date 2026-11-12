# NPP/opencvBenchmark::opencvBenchmark.cpp

**PARTIAL / L3**

原始四算子C++流程、6组真实GPU CLI与独立CPU全量输出、5090原生同输入同版OpenCV对照、18运行合同、真实GPU trace及9项证据反例通过；动态加载的GPU/OpenCV库字节已核。Gaussian/Canny项目算法变体记录，原生NPP不输出像素。待最后源码固定提交冷检出、独立复审与组合资格，当前不计整例通过或新增功能族。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [NPP/opencvBenchmark/opencvBenchmark.cpp](../../../../NPP/opencvBenchmark/opencvBenchmark.cpp) |
| 实际库 / 后端 | Project HIP Gaussian/Canny/resize/RGB gray plus pinned OpenCV 4.12 CPU benchmark / project HIP image benchmark |
| 候选路线 | RPP HIP, rocPRIM |
| 代码 | [rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp](../../../../rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp) |
| required cases | 8/11 |
| CUDA baseline / comparison | PASSED / OBSERVED |
| 性能 | OBSERVED_NOT_QUALIFIED |
| 原始源码 SHA256 | `0332d73b327bbf76726b6eb13e38bbf68110baff7f923f328dbaabbca54fb30e` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`image-benchmark/frozen-six-CLI`, `image-benchmark/matched-OpenCV4.12-and-four-HIP-build`, `image-benchmark/six-real-GPU-CLI`, `image-benchmark/all-four-independent-CPU`, `image-benchmark/original-CUDA-observed-semantics`, `image-benchmark/eighteen-device-contracts`, `image-benchmark/real-four-operation-trace`, `image-benchmark/nine-reader-counterexamples`, `image-benchmark/fixed-commit-cold-replay`, `image-benchmark/independent-review`, `image-benchmark/composite-qualification-and-Git-anchor`。

实现方式：`DOCUMENTED_IMAGE_ALGORITHM_VARIANTS`。

恢复/扩展条件：重建和原例/CPU/运行/trace任一改变须重新资格；NPP逐像素等价需原生输出采集。

CUDA 对照限制：同4096×2048/20×5、同OpenCV4.12、同输入；NPP原例只输出统计与计时，不输出像素，故不声称NPP逐像素相等；性能未资格。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp:34:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALib

尝试库：—；实现 hash：`b13ac23af0be4505194eacf6a2e4d3d4511cdfdc5726de2f4a2663fc8222c45e`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
python3 tools/moat/image_benchmark_contracts.py
python3 tools/moat/image_benchmark_deps.py
python3 tools/moat/image_benchmark_build.py
python3 tools/moat/image_benchmark_run.py
build/image-cpu-venv/bin/python tools/moat/image_benchmark_reference.py
python3 tools/moat/image_benchmark_runtime.py
python3 tools/moat/image_benchmark_trace.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_opencvBenchmark_opencvBenchmark.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/NPP_opencvBenchmark_opencvBenchmark.cpp)
- [migration/reports/image-benchmark.md](../../../reports/image-benchmark.md)
- [migration/reports/image-benchmark-contracts.json](../../../reports/image-benchmark-contracts.json)
- [migration/reports/image-I3-rocm-OpenCV.json](../../../reports/image-I3-rocm-OpenCV.json)
- [migration/reports/image-benchmark-build.json](../../../reports/image-benchmark-build.json)
- [migration/reports/image-benchmark-runs.json](../../../reports/image-benchmark-runs.json)
- [migration/reports/image-benchmark-validation.json](../../../reports/image-benchmark-validation.json)
- [migration/reports/image-benchmark-native-comparison.json](../../../reports/image-benchmark-native-comparison.json)
- [migration/reports/image-benchmark-runtime.json](../../../reports/image-benchmark-runtime.json)
- [migration/reports/image-benchmark-trace.json](../../../reports/image-benchmark-trace.json)
- [migration/reports/image-benchmark-negative.json](../../../reports/image-benchmark-negative.json)
