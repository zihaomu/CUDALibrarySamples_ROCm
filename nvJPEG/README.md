# nvJPEG Library API examples

## Description

This folder demonstrates nvJPEG library API usage.

## Key Concepts

Image Encoding and Decoding from NVJPEG Library

## Examples

[JPEG Image Decoder](nvJPEG-Decoder/)

[JPEG Image Decoder MultipleInstances](nvJPEG-Decoder-MultipleInstances/)

[JPEG Image Decoder Backend and ROI](nvJPEG-Decoder-Backend-ROI/)

[Image Resize](Image-Resize/)

[Image Resize Watermarking](Image-Resize-WaterMark/)

## Supported SM Architectures

[SM 3.5 ](https://developer.nvidia.com/cuda-gpus)  [SM 3.7 ](https://developer.nvidia.com/cuda-gpus)  [SM 5.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 5.2 ](https://developer.nvidia.com/cuda-gpus)  [SM 6.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 6.1 ](https://developer.nvidia.com/cuda-gpus)  [SM 7.0 ](https://developer.nvidia.com/cuda-gpus)  [SM 7.2 ](https://developer.nvidia.com/cuda-gpus)  [SM 7.5 ](https://developer.nvidia.com/cuda-gpus)

## Supported OSes

Linux Windows

## Supported CPU Architecture

x86_64

## CUDA APIs involved
[NVJPEG](https://docs.nvidia.com/cuda/nvjpeg/index.html)


# Prerequisites
- A Linux system with recent NVIDIA drivers.
- Install the [CUDA 11.0 toolkit and above](https://developer.nvidia.com/cuda-downloads).

<!-- ROCM-MIGRATION:START -->
## ROCm 迁移实时状态

7 个独立源入口；PASSED 0，PARTIAL 6，FAILED 1，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：rocJPEG (decode only), RPP。候选不等于已使用；基础探针成功也不等于整库迁移成功。

B10 六个入口的baseline硬件解码、9布局/缩放/RGB ROI/native batch/多实例、HIP Lanczos/水印与真实CLI/Python测试已验收。原始12张图中2张progressive明确CPU libjpeg fallback，锁定rocJPEG HYBRID返回-12；GPU progressive、部分原例调度/decoupled/backend控制未等价，6项仍PARTIAL；JPEG编码为CPU。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [Image-Resize-WaterMark/imageResizeWatermark.cpp](Image-Resize-WaterMark/imageResizeWatermark.cpp) · [详情](../migration/sample-reports/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo | L4 / PARTIAL | 使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。 | PASSED / PASSED | [记录](../migration/reports/batches9_11-validation.json)；[记录](../migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp) |
| [Image-Resize/imageResize.cpp](Image-Resize/imageResize.cpp) · [详情](../migration/sample-reports/nvJPEG/Image-Resize/imageResize.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo | L4 / PARTIAL | 使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。 | PASSED / PASSED | [记录](../migration/reports/batches9_11-validation.json)；[记录](../migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_Image-Resize_imageResize.cpp) |
| [nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo | L4 / PARTIAL | 使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。 | PASSED / PASSED | [记录](../migration/reports/batches9_11-validation.json)；[记录](../migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder-Backend-ROI_nvJPEGROIDecode.cpp) |
| [nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp](nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo | L4 / PARTIAL | 使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。 | PASSED / PASSED | [记录](../migration/reports/batches9_11-validation.json)；[记录](../migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder-MultipleInstances_nvJPEGDecMultipleInstances.cpp) |
| [nvJPEG-Decoder/tests/test_decoder.py](nvJPEG-Decoder/tests/test_decoder.py) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo | L4 / PARTIAL | 使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。 | PASSED / PASSED | [记录](../migration/reports/batches9_11-validation.json)；[记录](../migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder_tests_test_decoder.py) |
| [nvJPEG-Decoder/nvjpegDecoder.cpp](nvJPEG-Decoder/nvjpegDecoder.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo | L4 / PARTIAL | 使用 rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode；7 个预登记case通过独立CPU与同输入CUDA。锁定rocJPEG的HYBRID创建返回-12；原始12图中2张progressive由明确标注的libjpeg CPU fallback解码。GPU格式/ROI/缩放/Lanczos/水印和真实CLI已验证，CPU编码不声称AMDGPU JPEG encoder支持。 | PASSED / PASSED | [记录](../migration/reports/batches9_11-validation.json)；[记录](../migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_nvJPEG-Decoder_nvjpegDecoder.cpp) |
| [nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp.md) | 未验证使用库 | L1 / FAILED | build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp:34:10: fatal error: 'nvjpeg.h' file not found | FAILED / BLOCKED | [记录](../migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp)；[记录](../migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_nvJPEG-Encoder-MultipleInstances_nvJPEGEncMultipleInstances.cpp) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
