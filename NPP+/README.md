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

6 个独立源入口；PASSED 1，PARTIAL 1，FAILED 4，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：RPP HIP, rocPRIM。候选不等于已使用；基础探针成功也不等于整库迁移成功。

HIP等值/gradient/range/boundary五种连接区域试点及GPU面积/bbox/边界统计通过；缺原生NPP+ SDK，完整paint/metadata/边界语义未等价，PARTIAL；其它入口未实现。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp](batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/batchedLabelMarkersAndCompression/dirent.h:28:10: fatal error: 'windows.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_m | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompressionNPPPlus.cpp) |
| [cannyEdgeDetectorPython/cannyEdgeDetector.py](cannyEdgeDetectorPython/cannyEdgeDetector.py) · [详情](../migration/sample-reports/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py.md) | Project HIP Canny + ROCm Torch (C1 Sobel3/L2/local threshold) / project HIP image C ABI | L4 / PASSED | 完整C1原例8分辨率、5 warmup/1000测量及PNG/CSV通过；31组最终mask与独立CPU逐像素一致，native NPP+全部内部像素一致，仅两研究用例合计3外圈点不同。两stream/并发/类型转换/非法span与trace、验收器反向和独立复审通过。 | BLOCKED / PASSED | [记录](../migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.898910Z-I1-CPU-original-fecc4d7fdd)；[记录](../migration/reports/evidence/rewrite/I1/NPP__cannyEdgeDetectorPython__cannyEdgeDetector.py/20261111T120835.899416Z-I1-CPU-reference-919c2d65a9) |
| [distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp](distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp:42:10: fatal error: 'nppPlus/nppPlus.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cud | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_distanceTransform_unsignedAndSignedDistanceTransformNPPPlus.cpp) |
| [findContour/findContourNPPPlus.cpp](findContour/findContourNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/findContour/findContourNPPPlus.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/findContour/findContourNPPPlus.cpp:42:10: fatal error: 'nppPlus/nppPlus.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_m | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_findContour_findContourNPPPlus.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_findContour_findContourNPPPlus.cpp) |
| [floodFill/floodFillVariousRegionTypesNPPPlus.cpp](floodFill/floodFillVariousRegionTypesNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp.md) | HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata / HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata | L4 / PARTIAL | 使用HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。五种GPU连接/gradient/range/boundary路径及区域统计已验收；原生NPP+ SDK缺失，原例完整paint值/metadata结构和边界策略未逐项等价。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp)；[记录](../migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP+_floodFill_floodFillVariousRegionTypesNPPPlus.cpp) |
| [watershedSegmentation/watershedSegmentationNPPPlus.cpp](watershedSegmentation/watershedSegmentationNPPPlus.cpp) · [详情](../migration/sample-reports/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.h:41:10: fatal error: 'nppPlus/nppPlus.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_ | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP+_watershedSegmentation_watershedSegmentationNPPPlus.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
