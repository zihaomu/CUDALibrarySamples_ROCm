# Nvidia Performance Primitives (NPP+) Library API Examples

## Overview

This repository demonstrates the usage of the **Nvidia Performance Primitives (NPP+)** library for high-performance image processing tasks. NPP+ provides a wide range of performance-optimized functions for image, video, and signal processing, making it ideal for use cases that require efficient computation on large datasets using Nvidia GPUs.

The examples provided in this repository highlight key NPP+ functions for various image processing tasks, enabling developers to understand how to integrate NPP+ into their own projects.

## Key Concepts

The examples cover the following core concepts using NPP+:

- **Flood Fill Algorithms**: Efficiently filling connected image regions starting from a seed point.
- **Contour Detection**: Detecting the boundaries of objects within an image.
- **Euclidean Distance Transform**: Calculating the Euclidean distance from image elements to the nearest object.
- **Watershed-based Image Segmentation**: Dividing an image into regions based on intensity gradients.
- **Labeling and Compression of Image Regions**: Labeling connected regions and compressing them for optimized processing.

Each example demonstrates the practical application of these high-performance primitives.

## Getting Started with NPP+

To begin using NPP+, download the latest version of the library and install it on your Nvidia GPU-equipped machine.

- [Download NPP+](https://developer.nvidia.com/nppplus-downloads)

### Prerequisites

To run these examples, ensure the following dependencies are installed:

- A Linux or Windows system with an Nvidia GPU.
- The latest [NVIDIA drivers](https://www.nvidia.com/Download/index.aspx).
- [CUDA 12.0 Toolkit](https://developer.nvidia.com/cuda-downloads).
- [CMake](https://cmake.org/) for building the samples.
- [NPP+](https://developer.nvidia.com/nppplus-downloads).

## Examples

Explore the following examples to see how NPP+ APIs are applied in various image processing tasks:

- [**Flood Fill Sample**](floodFill/): Demonstrates the flood fill algorithm using NPP+ to fill connected image regions.
- [**Find Contour Sample**](findContour/): Shows how to find image contours efficiently using NPP+.
- [**Image Euclidean Distance Transform**](distanceTransform/): Applies the Euclidean distance transform to images.
- [**Watershed Segmentation**](watershedSegmentation/): Performs image segmentation using the watershed algorithm.
- [**Batched Label Markers and Compression**](batchedLabelMarkersAndCompression/): Explains how to label connected regions and apply compression to labeled image regions.

Each of these examples provides code snippets, performance benchmarks, and insights into how NPP+ can be leveraged for GPU-accelerated image processing.

## System Requirements

### Supported SM Architectures

The examples in this repository are optimized for the following Nvidia GPU architectures:

- [SM 7.0](https://developer.nvidia.com/cuda-gpus)
- [SM 7.2](https://developer.nvidia.com/cuda-gpus)
- [SM 7.5](https://developer.nvidia.com/cuda-gpus)
- [SM 8.0](https://developer.nvidia.com/cuda-gpus)

### Supported Operating Systems

- Linux
- Windows

### Supported CPU Architecture

- x86_64

## NPP+ CUDA APIs Involved

This repository primarily demonstrates the use of the [NPP+](https://docs.nvidia.com/cuda/nppplus/introduction.html) library.

<!-- ROCM-MIGRATION:START -->
## ROCm 支持情况

6 个独立源入口；PASSED 5，PARTIAL 1，FAILED 0，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：RPP HIP, rocPRIM。候选不等于已使用；基础探针成功也不等于整库迁移成功。

HIP等值/gradient/range/boundary五种连接区域试点及GPU面积/bbox/边界统计通过；缺原生NPP+ SDK，完整paint/metadata/边界语义未等价，PARTIAL；其它入口未实现。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp](batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp.md) | Project HIP equal-value 8-connected union/find + hierarchical GPU prefix-scan compression / project HIP CCL | L4 / PASSED | 原始五输入/单图与异构batch、NPP+默认及CUDA11U1压缩分支完整；27组全像素/padding、44运行合同及3项默认/外设备/销毁stream、1..5 batch共15个完整流程/165文件、39CLI、31正反例/BFS、trace/冷检出/三复审通过。包括零值所有区域，编号按最小像素确定；当前NPP/NPP+原生分区错误单列，不复制厂商错误。 | PASSED / OBSERVED | [记录](../migration/reports/evidence/rewrite/I2/CCL-trace-independent-CPU/20261111T142927.675646Z-I2-CPU-reference-2f1a8506ff)；[记录](../migration/reports/evidence/rewrite/I2/CCL-trace/20261111T142810.540767Z-I2-rocm-trace-5998506c21) |
| [cannyEdgeDetectorPython/cannyEdgeDetector.py](cannyEdgeDetectorPython/cannyEdgeDetector.py) · [详情](../migration/sample-reports/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py.md) | Project HIP Canny + ROCm Torch (C1 Sobel3/L2/local threshold) / project HIP image C ABI | L4 / PASSED | 完整C1原例8分辨率、5 warmup/1000测量及PNG/CSV通过；31组最终mask与独立CPU逐像素一致，native NPP+全部内部像素一致，仅两研究用例合计3外圈点不同。两stream/并发/类型转换/非法span与trace、验收器反向和独立复审通过。 | BLOCKED / PASSED | [记录](../migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.898910Z-I1-CPU-original-fecc4d7fdd)；[记录](../migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.899416Z-I1-CPU-reference-919c2d65a9) |
| [distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp](distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp.md) | Project HIP exact unsigned EDT + compact threshold-crossing signed site set + GPU FP64 search, deterministic Voronoi and visualization / project HIP distance transform | L4 / PASSED | 完整五图/12RAW C++入口，30全量输入，4流程48RAW，69参数、27状态/极值、19CLI、100CPU模型、57验收器检查及trace/12子记录冷检出/三复审通过。Signed使用预固定的线性阈值交点site距离与独立CPU定义；和NPP+闭源算法/锚点规则的差异完整单列，不承诺逐位vendor一致。 | PASSED / OBSERVED | [记录](../migration/reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164307.057198Z-I2-rocm-original-8dfed26bf6)；[记录](../migration/reports/evidence/rewrite/I2/NPP__distanceTransform__unsignedAndSignedDistanceTransformNPPPlus.cpp/20261111T164309.204860Z-I2-rocm-original-4df824750e) |
| [findContour/findContourNPPPlus.cpp](findContour/findContourNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/findContour/findContourNPPPlus.cpp.md) | Project HIP equal-value 8-connected CCL + directed cell-edge loops + GPU ordering and geometry rasterization / project HIP contour geometry | L4 / PASSED | 两个完整C++入口；22组全像素/逐edge闭环顺序/bbox/count/范围重建，15个实际流程/55RAW/逐点诊断，32CLI、61参数、26畸形设备数据、11状态/stream、58验收器反例及trace/冷检出/三复审通过。保持原例输出与范围/bypass行为；使用公开项目有向单元边表示，非NPP packed ABI。原生错误分区和早期ABI1缺边失败保留单列。 | PASSED / OBSERVED | [记录](../migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152006.301472Z-I2-rocm-original-ff7bc31597)；[记录](../migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152008.273045Z-I2-rocm-original-6fc17f2e31) |
| [floodFill/floodFillVariousRegionTypesNPPPlus.cpp](floodFill/floodFillVariousRegionTypesNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp.md) | Project HIP fixed-seed RGB flood fill and shared GPU connectivity / project HIP image flood fill | L4 / PASSED | 完整五模式/两原图/五RGB产品C++入口；29全量输入、4流程20RGB、72运行合同、18CLI、60基础验收器与16资格门反例、真实GPU trace、36子记录冷检出及独立复审通过。项目固定seed八连通/内边界与原生NPP+的分区和元数据差异单列；项目GPU对独立CPU逐字节精确。 | PASSED / OBSERVED | [记录](../migration/reports/evidence/rewrite/I3/FloodFill-full-RGB-GPU-backend-build/20261111T181533.727560Z-I3-rocm-build-895672330e)；[记录](../migration/reports/evidence/rewrite/I3/FloodFill-legacy-last-row-padding-actual-counterexample/20261111T184511.535189Z-I3-rocm-contract-probe-d3ff42ca14) |
| [watershedSegmentation/watershedSegmentationNPPPlus.cpp](watershedSegmentation/watershedSegmentationNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp.md) | Project HIP eight-neighbor gradient descent and root-label compression / project HIP image watershed | L3 / PARTIAL | 完整原始入口及 3 张图/12 件产品已在 AMD GPU 执行，独立 NumPy 模型逐字节一致，缺图拒绝通过；原生 NPP 最低分割像素一致率 0.7171，平台区归属和边界语义未达到原例等价，当前只能算部分实现。 | PASSED / OBSERVED_ALGORITHM_VARIANT | [记录](../migration/reports/evidence/rewrite/I3/NPP__watershedSegmentation__watershedSegmentationNPPPlus.cpp/20261112T080409.072052Z-I3-rocm-real-kernel-trace-e7c32312de)；[记录](../migration/reports/image-watershed.md) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
