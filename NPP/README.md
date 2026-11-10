# NVIDIA Performance Primitives (NPP) Library API Examples

## Overview

This repository showcases example applications that utilize the NVIDIA Performance Primitives (NPP) library for high-performance image processing on NVIDIA GPUs.

## Image Processing View

NPP covers the stages of a typical GPU image processing pipeline. The samples are organized below by stage.

```
 decode        pre-process          analyze / detect                 post-process / measure
 (nvJPEG) --> color convert, --> edges, lines, template     --> labeling, contours, distance
              resize, filter       matching, segmentation        transform, statistics
```

| Stage | What it does | NPP functions used in the samples | Sample |
|-------|--------------|-----------------------------------|--------|
| Color conversion and geometry | RGB to gray, resize | `nppiRGBToGray`, `nppiResize` | [opencvBenchmark](opencvBenchmark/) |
| Filtering | Gaussian smoothing | `nppiFilterGaussBorder` | [opencvBenchmark](opencvBenchmark/) |
| Edge detection | Gradient-based edges, color and gray | `nppiFilterCannyBorder` | [nppCanny](nppCanny/), [houghLines](houghLines/) |
| Feature detection | Straight lines | `nppiFilterHoughLine` | [houghLines](houghLines/) |
| Template matching | Locate a pattern, robust to gain and offset | `nppiCrossCorrValid_NormLevel`, `nppiMaxIndx` | [templateMatching](templateMatching/) |
| Segmentation | Region labeling, watershed | `nppiLabelMarkersUF`, `nppiCompressMarkerLabelsUF`, `nppiSegmentWatershed` | [batchedLabelMarkersAndCompression](batchedLabelMarkersAndCompression/), [watershedSegmentation](watershedSegmentation/) |
| Shape analysis | Contours, Euclidean distance transform | `nppiCompressedMarkerLabelsUFInfo`, `nppiDistanceTransformPBA` | [findContour](findContour/), [distanceTransform](distanceTransform/) |
| Pipeline efficiency | Scratch buffer handling across frames, CPU comparison | `nppiWorkspaceCreate`, `_Ctx` calls | [opencvBenchmark](opencvBenchmark/) |

## Examples Included

- [3-Channel Canny Edge Detection](nppCanny/)
  High-performance color edge detection using NPP's unified 3-channel Canny algorithm. 

- [Batched Label Markers and Compression](batchedLabelMarkersAndCompression/)
  Demonstrates how to perform connected region labeling and compress marker labels across a batch of images.

- [Watershed Segmentation](watershedSegmentation/)
  Applies the watershed segmentation algorithm for image segmentation using NPP utilities.

- [Euclidean Distance Transform](distanceTransform/)
  Computes the Euclidean distance transform for binary images.

- [Find Contour](findContour/)
  Extracts contours from labeled image regions using NPP primitives.

- [Template Matching](templateMatching/)
  Locates a template in a large image with normalized cross-correlation and finds the best match on the GPU.

- [Hough Lines](houghLines/)
  Detects straight lines with Canny edge detection followed by the Hough line transform.

- [OpenCV Benchmark](opencvBenchmark/)
  Times Gaussian blur, Canny, resize and RGB to gray on NPP versus single- and multi-threaded OpenCV, kernel-only and end-to-end.

## Latest Developments in NPP (CUDA Toolkit 13.4, NPP 13.2.0.58)

### NPP Workspace

`NppStreamContext` now carries an optional `hWorkspace` handle (the former `nReserved0` field). Attach one with
`nppiWorkspaceCreate()` (declared in `nppworkspace.h`) and pass a `NULL` scratch buffer to the functions that support it:
NPP then reuses a single high-water-mark device buffer instead of the per-call
`GetBufferSize` + `cudaMalloc` + `cudaFree` sequence.

```cpp
NppStreamContext ctx = {};          // hWorkspace must be 0 unless a workspace was created
// ... fill in stream / device fields ...
nppiWorkspaceCreate(&ctx);
nppiLabelMarkersUF_8u32u_C1R_Ctx(src, srcStep, dst, dstStep, roi, nppiNormInf, NULL, ctx);
nppiWorkspaceDestroy(&ctx);
```

Samples using it: [nppCanny](nppCanny/), [findContour](findContour/), [watershedSegmentation](watershedSegmentation/),
[batchedLabelMarkersAndCompression](batchedLabelMarkersAndCompression/). With CUDA 13.4 the
`NULL` scratch buffer is accepted by `nppiLabelMarkersUF_*`, `nppiSegmentWatershed_*` and `nppiFilterCannyBorder_*`;
`nppiCompressMarkerLabelsUF_*` and `nppiDistanceTransformPBA_*` return `NPP_NULL_POINTER_ERROR` for a `NULL` buffer in that release
(later NPP builds accept it). [findContour](findContour/), [batchedLabelMarkersAndCompression](batchedLabelMarkersAndCompression/) and
[distanceTransform](distanceTransform/) therefore try the workspace first and allocate the scratch buffer only if NPP reports that error,
so they work with both.
Applications that do not use a workspace must zero-initialize `NppStreamContext` (as `distanceTransform` now does).
The samples check for `nppworkspace.h` with `__has_include`
and fall back to allocating the scratch buffers themselves, so they also build with CUDA toolkits that predate it.

### Earlier: NPP 13.0.3.9 (CUDA Toolkit 13.0 Update 3)

#### Deprecations

- **Non-CTX APIs** are deprecating and will be removed in **CUDA Toolkit 13.0**.  
- The `nppGetStreamContext()` API will be deprecated starting with CUDA Toolkit 13.0. Developers should migrate to **application-managed stream contexts** as described in the [NPP Documentation – General Conventions](https://docs.nvidia.com/cuda/npp/introduction.html#general-conventions).

#### Resolved Issues

- `nppiTranspose` now supports larger dimensions.  
- Fixed a distance calculation bug in `nppiDistanceTransformPBA_8u16u_C1R_Ctx`.  
- Improved performance of `nppiResizeSqrPixel` and `nppiCrossCorrelation`.  
- `nppiYUVToRGB_8u_C3R` now supports block-linear formatted input.  
- Fixed output pitch issue in `nppiFilterGaussAdvanced`.

## Platform Support

- **Operating Systems**: Linux, Windows  
- **CPU Architectures**: x86_64  
- **Required Toolkit**: [CUDA 13.4 or newer](https://developer.nvidia.com/cuda-downloads)

## CUDA API Reference

- [NPP Library Documentation](https://docs.nvidia.com/cuda/npp/index.html)

## Application-Managed Context and Stream Handling in NPP

The `NppStreamContext` structure was introduced in NPP version 10.1, corresponding to CUDA Toolkit 10.1 (released in early 2019). 
This marked the beginning of support for application-managed stream contexts, allowing developers to explicitly manage CUDA streams for more flexible and concurrent GPU workloads. 

Use of the NppStreamContext structure is strongly recommended in place of the deprecated nppGetStreamContext() API, which is scheduled for removal in CUDA Toolkit 13.0 to support application-managed stream and context control.


### Example: Using Application-Managed Context

```cpp
NppStreamContext nppCtx = {};
nppCtx.hStream = myCudaStream; // Application-managed stream

// Set other fields as needed based on cudaDeviceProp

// Use in API call
nppiFilterGauss_8u_C1R_Ctx(..., nppCtx); 
```

For the most up-to-date details, refer to the official [NPP Documentation – Application-managed Context](https://docs.nvidia.com/cuda/npp/index.html#application-managed-context).

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

9 个独立源入口；PASSED 2，PARTIAL 1，FAILED 6，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：RPP HIP, rocPRIM。候选不等于已使用；基础探针成功也不等于整库迁移成功。

精确Euclidean距离/Voronoi位移/整数截断通过，原始两图浮点/整数结果与native NPP逐像素一致。Canny原始图仍有1995/921600像素差异，NCC原始注释图/CLI/计时框架未移植，保留PARTIAL；RPP检查未提供这些对应API，改用HIP。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp](batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp) · [详情](../migration/sample-reports/NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/batchedLabelMarkersAndCompression/dirent.h:28:10: fatal error: 'windows.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_mi | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompression.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_batchedLabelMarkersAndCompression_batchedLabelMarkersAndCompression.cpp) |
| [distanceTransform/distanceTransform.cpp](distanceTransform/distanceTransform.cpp) · [详情](../migration/sample-reports/NPP/distanceTransform/distanceTransform.cpp.md) | HIP exact separable Euclidean distance/Voronoi/integer truncation kernels / HIP exact separable Euclidean distance/Voronoi/integer truncation kernels | L4 / PASSED | 使用HIP exact separable Euclidean distance/Voronoi/integer truncation kernels；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_distanceTransform_distanceTransform.cpp)；[记录](../migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_distanceTransform_distanceTransform.cpp) |
| [findContour/findContour.cpp](findContour/findContour.cpp) · [详情](../migration/sample-reports/NPP/findContour/findContour.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/findContour/findContour.cpp:26:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamp | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_findContour_findContour.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_findContour_findContour.cpp) |
| [houghLines/houghLines.cpp](houghLines/houghLines.cpp) · [详情](../migration/sample-reports/NPP/houghLines/houghLines.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/houghLines/houghLines.cpp:33:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySample | PASSED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_houghLines_houghLines.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_houghLines_houghLines.cpp) |
| [nppCanny/npp_canny_simple.cpp](nppCanny/npp_canny_simple.cpp) · [详情](../migration/sample-reports/NPP/nppCanny/npp_canny_simple.cpp.md) | HIP three-channel Sobel/NMS/connected hysteresis kernels / HIP three-channel Sobel/NMS/connected hysteresis kernels | L4 / PARTIAL | 使用HIP three-channel Sobel/NMS/connected hysteresis kernels；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。GPU三通道最大梯度/Sobel/NMS/滞后连接已全像素验收；原生NPP C3梯度与NMS tie策略及原例OpenCV文件CLI未完成逐像素等价。 | FAILED / PASSED | [记录](../migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_nppCanny_npp_canny_simple.cpp)；[记录](../migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_nppCanny_npp_canny_simple.cpp) |
| [nppCanny/npp_canny_simple.py](nppCanny/npp_canny_simple.py) · [详情](../migration/sample-reports/NPP/nppCanny/npp_canny_simple.py.md) | 未验证使用库 | L0 / FAILED | Python 原始入口依赖 cv2, torch, ctypes, ctypes, sys, time；锁定 AMD 环境中的 import 资格检查未通过，尚无保留该例 API/算法的 AMD Python 改写。安装 CPU 包不能充作 GPU 迁移。 日志：File "/opt/python/cpython-3.13.13-linux-x86_64-gnu/lib/python3.13/importlib/__init__.py", line 88, in import_module     return _bootstrap._gcd_import(name[level:], package, level)            ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   File "<frozen importlib._bootstrap>", line 1395, in _gcd_import   File "<frozen importlib._bootstrap>", line 1360, in _find_and_load   File "<frozen importlib._bootstrap>", line 1324, in _find_and_load_unlocked ModuleNotFoundError: No module named 'cv2'  | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084354.110802Z/languages/NPP_nppCanny_npp_canny_simple.py)；[记录](../migration/reports/evidence/20261109T092217.782813Z/cuda-language-prerequisites/NPP_nppCanny_npp_canny_simple.py) |
| [opencvBenchmark/opencvBenchmark.cpp](opencvBenchmark/opencvBenchmark.cpp) · [详情](../migration/sample-reports/NPP/opencvBenchmark/opencvBenchmark.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp:34:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALib | BLOCKED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_opencvBenchmark_opencvBenchmark.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_opencvBenchmark_opencvBenchmark.cpp) |
| [templateMatching/templateMatching.cpp](templateMatching/templateMatching.cpp) · [详情](../migration/sample-reports/NPP/templateMatching/templateMatching.cpp.md) | HIP NCC/full original CLI/RAW input/PGM annotation/HIP-event timing / project HIP kernels | L4 / PASSED | 完整原始合同、登记变体、独立CPU/同字节CUDA、负向/边界与独立复审通过。实际路线：HIP NCC/full original CLI/RAW input/PGM annotation/HIP-event timing。性能不作跨设备比较。 | PASSED / PASSED | [记录](../migration/reports/evidence/rewrite/R3/NPP_templateMatching__templateMatching.cpp/20261110T092525.448735Z-R3-composite-qualification-ad7d1f1dc9)；[记录](../migration/reports/rewrite-R3-qualification.json) |
| [watershedSegmentation/watershedSegmentation.cpp](watershedSegmentation/watershedSegmentation.cpp) · [详情](../migration/sample-reports/NPP/watershedSegmentation/watershedSegmentation.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/watershedSegmentation/watershedSegmentation.h:41:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_mig | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_watershedSegmentation_watershedSegmentation.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_watershedSegmentation_watershedSegmentation.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
