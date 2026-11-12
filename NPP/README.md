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
## ROCm 支持情况

9 个独立源入口；PASSED 7，PARTIAL 1，FAILED 1，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：RPP HIP, rocPRIM。候选不等于已使用；基础探针成功也不等于整库迁移成功。

精确Euclidean距离/Voronoi位移/整数截断通过，原始两图浮点/整数结果与native NPP逐像素一致。Canny原始图仍有1995/921600像素差异，NCC原始注释图/CLI/计时框架未移植，保留PARTIAL；RPP检查未提供这些对应API，改用HIP。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp](batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp) · [详情](../migration/sample-reports/NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp.md) | Project HIP equal-value 8-connected union/find + hierarchical GPU prefix-scan compression / project HIP CCL | L4 / PASSED | 原始五输入/单图与异构batch、NPP+默认及CUDA11U1压缩分支完整；27组全像素/padding、44运行合同及3项默认/外设备/销毁stream、1..5 batch共15个完整流程/165文件、39CLI、31正反例/BFS、trace/冷检出/三复审通过。包括零值所有区域，编号按最小像素确定；当前NPP/NPP+原生分区错误单列，不复制厂商错误。 | PASSED / OBSERVED | [记录](../migration/reports/evidence/rewrite/I2/CCL-trace-independent-CPU/20261111T142927.675646Z-I2-CPU-reference-2f1a8506ff)；[记录](../migration/reports/evidence/rewrite/I2/CCL-trace/20261111T142810.540767Z-I2-rocm-trace-5998506c21) |
| [distanceTransform/distanceTransform.cpp](distanceTransform/distanceTransform.cpp) · [详情](../migration/sample-reports/NPP/distanceTransform/distanceTransform.cpp.md) | HIP exact separable Euclidean distance/Voronoi/integer truncation kernels / HIP exact separable Euclidean distance/Voronoi/integer truncation kernels | L4 / PASSED | 使用HIP exact separable Euclidean distance/Voronoi/integer truncation kernels；6个预登记case通过独立CPU与同输入兼容CUDA数学基线。仅登记profile/规模/执行方式通过，不外推其它dtype、规模、网格或性能；内部数据重分配/CPU布局编排与项目GPU算法已公开。 | PASSED / PASSED | [记录](../migration/reports/evidence/20261110T053436.400711Z/batches12_15-rocm/NPP_distanceTransform_distanceTransform.cpp)；[记录](../migration/reports/evidence/20261110T053230.152526Z/batches12_15-cuda/NPP_distanceTransform_distanceTransform.cpp) |
| [findContour/findContour.cpp](findContour/findContour.cpp) · [详情](../migration/sample-reports/NPP/findContour/findContour.cpp.md) | Project HIP equal-value 8-connected CCL + directed cell-edge loops + GPU ordering and geometry rasterization / project HIP contour geometry | L4 / PASSED | 两个完整C++入口；22组全像素/逐edge闭环顺序/bbox/count/范围重建，15个实际流程/55RAW/逐点诊断，32CLI、61参数、26畸形设备数据、11状态/stream、58验收器反例及trace/冷检出/三复审通过。保持原例输出与范围/bypass行为；使用公开项目有向单元边表示，非NPP packed ABI。原生错误分区和早期ABI1缺边失败保留单列。 | PASSED / OBSERVED | [记录](../migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152006.301472Z-I2-rocm-original-ff7bc31597)；[记录](../migration/reports/evidence/rewrite/I2/NPP_findContour__findContour.cpp/20261111T152008.273045Z-I2-rocm-original-6fc17f2e31) |
| [houghLines/houghLines.cpp](houghLines/houghLines.cpp) · [详情](../migration/sample-reports/NPP/houghLines/houghLines.cpp.md) | Project HIP C1 Canny plus GPU Hough votes and peak extraction / project HIP image Hough | L4 / PASSED | 完整C++原例、19输入/有效参数/错误CLI及逐字节PPM和完整诊断线表、19运行合同与外设备空流拒绝、真实GPU Sobel/NMS/threshold/votes/peaks、45子记录干净检出与三范围独立复审通过。项目CPU逐线/逐峰/全PPM精确；当前NPP原生默认PPM差10627 RGB像素，五条真值各被双方两条线覆盖。 | PASSED / OBSERVED | [记录](../migration/reports/evidence/rewrite/I3/Hough-valid-options-independent-CPU/20261112T044514.912362Z-I3-CPU-reference-4e20cef9a7)；[记录](../migration/reports/evidence/rewrite/I3/NPP__houghLines_houghLines.cpp/20261111T181159.322261Z-I3-cuda-original-6e3b3023be) |
| [nppCanny/npp_canny_simple.cpp](nppCanny/npp_canny_simple.cpp) · [详情](../migration/sample-reports/NPP/nppCanny/npp_canny_simple.cpp.md) | HIP C3 Sobel/NMS/GPU union-find hysteresis + OpenCV file IO/CPU comparisons / project HIP classical C3 Canny | L4 / PASSED | 完整C++/Python原例三PNG、1预热/10测量及两类OpenCV比较；22组mask/padding对独立CPU精确，55项运行合同、真实C++ ROI/错误/并发实例、10 CLI/无设备、39正反例、trace、冷检出和三复审通过。采用经典8连接强种子滞后：原图比NPP少4328个弱边缘像素（IoU0.6323），全部强种子保留，实测项目边缘均包含在native边缘中；不宣称NPP mask逐点兼容。 | PASSED / PASSED | [记录](../migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132721.980476Z-I1-rocm-CLI-8b9044dd47)；[记录](../migration/reports/evidence/rewrite/I1/image-private-OpenCV-C__/20261111T123829.979807Z-I1-host-setup-196d7f2db2) |
| [nppCanny/npp_canny_simple.py](nppCanny/npp_canny_simple.py) · [详情](../migration/sample-reports/NPP/nppCanny/npp_canny_simple.py.md) | HIP C3 Sobel/NMS/GPU union-find hysteresis + OpenCV file IO/CPU comparisons + ROCm Torch / project HIP classical C3 Canny | L4 / PASSED | 完整C++/Python原例三PNG、1预热/10测量及两类OpenCV比较；22组mask/padding对独立CPU精确，55项运行合同、真实C++ ROI/错误/并发实例、10 CLI/无设备、39正反例、trace、冷检出和三复审通过。采用经典8连接强种子滞后：原图比NPP少4328个弱边缘像素（IoU0.6323），全部强种子保留，实测项目边缘均包含在native边缘中；不宣称NPP mask逐点兼容。 | BLOCKED / PASSED | [记录](../migration/reports/evidence/rewrite/I1/NPP_nppCanny__npp_canny_simple.py/20261111T132721.980476Z-I1-rocm-CLI-8b9044dd47)；[记录](../migration/reports/evidence/rewrite/I1/image-private-OpenCV-C__/20261111T123829.979807Z-I1-host-setup-196d7f2db2) |
| [opencvBenchmark/opencvBenchmark.cpp](opencvBenchmark/opencvBenchmark.cpp) · [详情](../migration/sample-reports/NPP/opencvBenchmark/opencvBenchmark.cpp.md) | Project HIP Gaussian/Canny/resize/RGB gray plus pinned OpenCV 4.12 CPU benchmark / project HIP image benchmark | L3 / PARTIAL | 原始四算子C++流程、6组真实GPU CLI与独立CPU全量输出、5090原生同输入同版OpenCV对照、18运行合同、真实GPU trace及9项证据反例通过；动态加载的GPU/OpenCV库字节已核。Gaussian/Canny项目算法变体记录，原生NPP不输出像素。待最后源码固定提交冷检出、独立复审与组合资格，当前不计整例通过或新增功能族。 | PASSED / OBSERVED | [记录](../migration/reports/image-benchmark-trace.json)；[记录](../migration/reports/image-benchmark-negative.json) |
| [templateMatching/templateMatching.cpp](templateMatching/templateMatching.cpp) · [详情](../migration/sample-reports/NPP/templateMatching/templateMatching.cpp.md) | HIP NCC/full original CLI/RAW input/PGM annotation/HIP-event timing / project HIP kernels | L4 / PASSED | 完整原始合同、登记变体、独立CPU/同字节CUDA、负向/边界与独立复审通过。实际路线：HIP NCC/full original CLI/RAW input/PGM annotation/HIP-event timing。性能不作跨设备比较。 | PASSED / PASSED | [记录](../migration/reports/evidence/rewrite/R3/NPP_templateMatching__templateMatching.cpp/20261110T092525.448735Z-R3-composite-qualification-ad7d1f1dc9)；[记录](../migration/reports/rewrite-R3-qualification.json) |
| [watershedSegmentation/watershedSegmentation.cpp](watershedSegmentation/watershedSegmentation.cpp) · [详情](../migration/sample-reports/NPP/watershedSegmentation/watershedSegmentation.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/NPP/watershedSegmentation/watershedSegmentation.h:41:10: fatal error: 'npp.h' file not found；failed to execute:/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay/lib/llvm/bin/clang++  --offload-arch=gfx1201 --driver-mode=g++ --hip-link  -std=c++17 -O2 -D__HIP_PLATFORM_AMD__ --rocm-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/build/rocm-sdk-overlay --hip-path=/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_mig | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/NPP_watershedSegmentation_watershedSegmentation.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/NPP_watershedSegmentation_watershedSegmentation.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
