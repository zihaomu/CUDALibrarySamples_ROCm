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
## ROCm 支持情况

7 个独立源入口；PASSED 0，PARTIAL 7，FAILED 0，BLOCKED 0，UNSUPPORTED 0，NOT_STARTED 0，IN_PROGRESS 0。

候选库：rocJPEG (decode only), RPP。候选不等于已使用；基础探针成功也不等于整库迁移成功。

B10 六个入口的baseline硬件解码、9布局/缩放/RGB ROI/native batch/多实例、HIP Lanczos/水印与真实CLI/Python测试已验收。原始12张图中2张progressive明确CPU libjpeg fallback，锁定rocJPEG HYBRID返回-12；GPU progressive、部分原例调度/decoupled/backend控制未等价，6项仍PARTIAL；JPEG编码为CPU。

| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |
| --- | --- | --- | --- | --- | --- |
| [Image-Resize-WaterMark/imageResizeWatermark.cpp](Image-Resize-WaterMark/imageResizeWatermark.cpp) · [详情](../migration/sample-reports/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp.md) | rocJPEG baseline hardware + project HIP progressive decode + project HIP full baseline JPEG encode (GPU color/FDCT/MCU/Huffman/pack/stuff; CPU marker orchestration) / rocJPEG + project HIP JPEG decoder/encoder + libjpeg-turbo progressive entropy only | L4 / PARTIAL | 七组原登记 CLI/独立 CPU 与同输入 CUDA 数学流程均通过；35 件重编码 JPEG 由 AMD GPU 完成色彩/FDCT/MCU/Huffman/scan/pack/stuff，CPU 仅组装标准 baseline marker，禁 CPU 熵编码。两个入口68产品共8,191,374个 RGB 字节与旧独立数值路径完全一致，采样/量化表一致；实际 C++ 入口各12个 GPU JPEG 内核及重放 SHA 已验。源 progressive 输出模式、表及 APP/COM metadata 继承和 GPU prefix 性能尚缺，故 PARTIAL。 | PASSED / PASSED | [记录](../migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T101034.778214Z-I5-full-GPU-JPEG-original-entry-subset-qualification-d1c172995a)；[记录](../migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T100832.671105Z-I5-rocm-full-GPU-JPEG-original-entry-integration-03ae7858c2) |
| [Image-Resize/imageResize.cpp](Image-Resize/imageResize.cpp) · [详情](../migration/sample-reports/nvJPEG/Image-Resize/imageResize.cpp.md) | rocJPEG baseline hardware + project HIP progressive decode + project HIP full baseline JPEG encode (GPU color/FDCT/MCU/Huffman/pack/stuff; CPU marker orchestration) / rocJPEG + project HIP JPEG decoder/encoder + libjpeg-turbo progressive entropy only | L4 / PARTIAL | 七组原登记 CLI/独立 CPU 与同输入 CUDA 数学流程均通过；33 件重编码 JPEG 由 AMD GPU 完成色彩/FDCT/MCU/Huffman/scan/pack/stuff，CPU 仅组装标准 baseline marker，禁 CPU 熵编码。两个入口68产品共8,191,374个 RGB 字节与旧独立数值路径完全一致，采样/量化表一致；实际 C++ 入口各12个 GPU JPEG 内核及重放 SHA 已验。源 progressive 输出模式、表及 APP/COM metadata 继承和 GPU prefix 性能尚缺，故 PARTIAL。 | PASSED / PASSED | [记录](../migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize__imageResize.cpp/20261112T101033.399316Z-I5-full-GPU-JPEG-original-entry-subset-qualification-bc3df8784b)；[记录](../migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize_imageResize.cpp/20261112T100821.274252Z-I5-rocm-full-GPU-JPEG-original-entry-integration-69e4628c9b) |
| [nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp.md) | rocJPEG hardware baseline + project HIP progressive IDCT/chroma/RGB; libjpeg-turbo CPU entropy assembly / rocJPEG + project HIP image decoder + libjpeg-turbo entropy | L4 / PARTIAL | 七组原登记流程与同输入 CUDA 数学对照重新通过；12 原始 JPEG 中 10 张 rocJPEG 硬件解码、2 张 progressive 使用 CPU 熵装配 + AMD GPU IDCT/色度/RGB，独立 CPU maxAbs≤3、PSNR≥60.76 dB，真实 GPU kernel trace 已验。当前仍缺：I4/fixed-commit-cold-replay-and-independent-review、I4/original-backend-enums-and-decoupled-pipeline。 | PASSED / PASSED | [记录](../migration/reports/image-progressive-runs.json)；[记录](../migration/reports/image-progressive-trace.json) |
| [nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp](nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp.md) | rocJPEG hardware baseline + project HIP progressive IDCT/chroma/RGB; libjpeg-turbo CPU entropy assembly / rocJPEG + project HIP image decoder + libjpeg-turbo entropy | L4 / PARTIAL | 七组原登记流程与同输入 CUDA 数学对照重新通过；12 原始 JPEG 中 10 张 rocJPEG 硬件解码、2 张 progressive 使用 CPU 熵装配 + AMD GPU IDCT/色度/RGB，独立 CPU maxAbs≤3、PSNR≥60.76 dB，真实 GPU kernel trace 已验。当前仍缺：I4/fixed-commit-cold-replay-and-independent-review、I4/original-automatic-multiple-instance-scheduling。 | PASSED / PASSED | [记录](../migration/reports/image-progressive-runs.json)；[记录](../migration/reports/image-progressive-trace.json) |
| [nvJPEG-Decoder/tests/test_decoder.py](nvJPEG-Decoder/tests/test_decoder.py) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md) | rocJPEG hardware baseline + project HIP progressive IDCT/chroma/RGB; libjpeg-turbo CPU entropy assembly / rocJPEG + project HIP image decoder + libjpeg-turbo entropy | L4 / PARTIAL | 七组原登记流程与同输入 CUDA 数学对照重新通过；12 原始 JPEG 中 10 张 rocJPEG 硬件解码、2 张 progressive 使用 CPU 熵装配 + AMD GPU IDCT/色度/RGB，独立 CPU maxAbs≤3、PSNR≥60.76 dB，真实 GPU kernel trace 已验。当前仍缺：I4/fixed-commit-cold-replay-and-independent-review。 | PASSED / PASSED | [记录](../migration/reports/image-progressive-runs.json)；[记录](../migration/reports/image-progressive-trace.json) |
| [nvJPEG-Decoder/nvjpegDecoder.cpp](nvJPEG-Decoder/nvjpegDecoder.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp.md) | rocJPEG hardware baseline + project HIP progressive IDCT/chroma/RGB; libjpeg-turbo CPU entropy assembly / rocJPEG + project HIP image decoder + libjpeg-turbo entropy | L4 / PARTIAL | 七组原登记流程与同输入 CUDA 数学对照重新通过；12 原始 JPEG 中 10 张 rocJPEG 硬件解码、2 张 progressive 使用 CPU 熵装配 + AMD GPU IDCT/色度/RGB，独立 CPU maxAbs≤3、PSNR≥60.76 dB，真实 GPU kernel trace 已验。当前仍缺：I4/fixed-commit-cold-replay-and-independent-review。 | PASSED / PASSED | [记录](../migration/reports/image-progressive-runs.json)；[记录](../migration/reports/image-progressive-trace.json) |
| [nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp) · [详情](../migration/sample-reports/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp.md) | Project HIP multi-stream baseline JPEG color/downsample/FDCT/quant/Huffman/pack/stuff; libjpeg-turbo standard markers and optimized -f fallback / project HIP full baseline JPEG encoder + libjpeg-turbo optimized Huffman fallback | L4 / PARTIAL | 原始 C++ 七组 CLI 通过：3张 BMP 自然排序、7次重复、2线程/4状态、Q75/90、420/444、优化 Huffman、硬件不可用/错误输入拒绝；16件JPEG产品独立跨解码与旧路径逐 RGB 字节、采样和量化表一致。非优化 baseline 用 GPU 完成色彩/FDCT/MCU/Huffman/pack/stuff，真实 GPU trace 有7图/84内核、2个独立HIP stream，改输入重放通过。-f 优化 Huffman 仍调用 CPU libjpeg；pinned buffer/事件重叠/自动标定与 GPU prefix 性能尚未完整验收，因此 PARTIAL。 | FAILED / BLOCKED | [记录](../migration/reports/evidence/rewrite/I5/original-JPEG-encoder-concurrent-HIP-streams-and-changed-input/20261112T100631.107895Z-I5-rocm-trace-c6f9a5a6c2)；[记录](../migration/reports/image-jpeg-encoder-instances-full-comparison.json) |

生成来源：[migration/samples.yaml](../migration/samples.yaml)；执行 `python3 tools/migration/render.py` 更新。
<!-- ROCM-MIGRATION:END -->
