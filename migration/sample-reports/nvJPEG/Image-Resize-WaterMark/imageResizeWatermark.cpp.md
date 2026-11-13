# nvJPEG/Image-Resize-WaterMark::imageResizeWatermark.cpp

**PARTIAL / L4**

七组原CLI、当前68产品独立数学/严格全MCU解码及CPU质量通过，生产GPU编码trace及产品seal反向检查通过；progressive解码仍有CPU熵阶段，源progressive输出/DQT/APP/COM继承及完整冷检出未完成，保留PARTIAL。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp](../../../../nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp) |
| 实际库 / 后端 | rocJPEG + project HIP progressive pixels/resize/watermark + full HIP baseline JPEG encoder; CPU progressive decode entropy remains / rocJPEG + project HIP + libjpeg-turbo progressive entropy |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/ported/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp](../../../../rocm/ported/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp) |
| required cases | 9/12 |
| CUDA baseline / comparison | PASSED / BLOCKED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `e4f336ff2598fdcc5d0899d168eaf7785ed4b277fb494cd6f23960d181fe405b` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`IMG-01/resize/original-corpus`, `IMG-01/resize/formats-scale`, `IMG-01/resize/roi-boundary`, `IMG-01/resize/batch-multi-instance`, `IMG-01/resize/invalid-cli`, `IMG-01/resize/postprocess`, `IMG-01/resize/python-integration`, `IMG-01/resize/current-JPEG-mathematics`, `IMG-01/resize/actual-entry-GPU-trace`, `IMG-03/full-GPU-progressive-entropy`, `IMG-05/progressive-output-source-DQT-APP-COM`, `IMG-10/full-entry-cold-native-review`。

实现方式：`ALGORITHM_VARIANT`。

恢复/扩展条件：Progressive decode entropy still CPU; source progressive output, source quantization tables and APP/COM metadata inheritance; full entry cold/native qualification under IMG-03–05.

CUDA 对照限制：既有CUDA数学对照保留历史；当前新JPEG算术按CPU数学变体验收，完整新入口native复核随IMG-05完成。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.h:38:10: fatal error: 'nvjpeg.h' file not found

尝试库：—；实现 hash：`12c6e6a738f590a579b1d7a362e30aeb0565d882896bc490e7decafb77aba007`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 python3 tools/moat/image_encoder_full_gpu_integration.py
build/image-cpu-venv/bin/python tools/moat/image_encoder_full_gpu_products_compare.py
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 python3 tools/moat/image_encoder_full_gpu_frontend_trace.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp)
- [migration/reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp](../../../reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp)
- [migration/reports/evidence/rewrite/I4/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T085147.482242Z-I4-composite-subset-qualification-671d449fb5](../../../reports/evidence/rewrite/I4/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T085147.482242Z-I4-composite-subset-qualification-671d449fb5)
- [migration/reports/evidence/rewrite/I4/six-JPEG-entry-current-full-harness-logs-and-product-hashes/20261112T085059.002402Z-I4-host-evidence-archive-2ec54e2d04/harness/nvJPEG__Image-Resize-WaterMark__imageResizeWatermark.cpp](../../../reports/evidence/rewrite/I4/six-JPEG-entry-current-full-harness-logs-and-product-hashes/20261112T085059.002402Z-I4-host-evidence-archive-2ec54e2d04/harness/nvJPEG__Image-Resize-WaterMark__imageResizeWatermark.cpp)
- [migration/reports/image-progressive.md](../../../reports/image-progressive.md)
- [migration/reports/image-progressive-harness-archive.json](../../../reports/image-progressive-harness-archive.json)
- [migration/reports/image-progressive-original-corpus.json](../../../reports/image-progressive-original-corpus.json)
- [migration/reports/image-progressive-runs.json](../../../reports/image-progressive-runs.json)
- [migration/reports/image-progressive-trace.json](../../../reports/image-progressive-trace.json)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T091036.654996Z-I5-composite-subset-qualification-9b880eedfb](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T091036.654996Z-I5-composite-subset-qualification-9b880eedfb)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T090828.673890Z-I5-rocm-original-entry-integration-faa2e75109](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T090828.673890Z-I5-rocm-original-entry-integration-faa2e75109)
- [migration/reports/image-jpeg-encoder.md](../../../reports/image-jpeg-encoder.md)
- [migration/reports/image-jpeg-encoder-integration.json](../../../reports/image-jpeg-encoder-integration.json)
- [migration/reports/image-jpeg-encoder-runs.json](../../../reports/image-jpeg-encoder-runs.json)
- [migration/reports/image-jpeg-encoder-trace.json](../../../reports/image-jpeg-encoder-trace.json)
- [migration/reports/image-jpeg-encoder-negative.json](../../../reports/image-jpeg-encoder-negative.json)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T092541.290750Z-I5-composite-subset-qualification-962fb0c234](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T092541.290750Z-I5-composite-subset-qualification-962fb0c234)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T092522.572015Z-I5-rocm-original-entry-integration-e2c3697df4](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T092522.572015Z-I5-rocm-original-entry-integration-e2c3697df4)
- [migration/reports/image-jpeg-entropy-prototype.md](../../../reports/image-jpeg-entropy-prototype.md)
- [migration/reports/image-jpeg-encoder-gpu-packing-runs.json](../../../reports/image-jpeg-encoder-gpu-packing-runs.json)
- [migration/reports/image-jpeg-encoder-gpu-packing-trace.json](../../../reports/image-jpeg-encoder-gpu-packing-trace.json)
- [migration/reports/evidence/rewrite/I5/GPU-Huffman-prefix-pack-stuff-build/20261112T093831.801126Z-I5-rocm-build-19a6241159](../../../reports/evidence/rewrite/I5/GPU-Huffman-prefix-pack-stuff-build/20261112T093831.801126Z-I5-rocm-build-19a6241159)
- [migration/reports/evidence/rewrite/I5/GPU-Huffman-pack-stuff-two-real-traces-and-input-change/20261112T093942.919441Z-I5-rocm-trace-329f7dedd1](../../../reports/evidence/rewrite/I5/GPU-Huffman-pack-stuff-two-real-traces-and-input-change/20261112T093942.919441Z-I5-rocm-trace-329f7dedd1)
- [migration/reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093902.336506Z-I5-rocm-prototype-200881a852](../../../reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093902.336506Z-I5-rocm-prototype-200881a852)
- [migration/reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093904.854345Z-I5-rocm-prototype-c88273b9db](../../../reports/evidence/rewrite/I5/GPU-JPEG-Huffman-prefix-pack-stuff-byte-parity/20261112T093904.854345Z-I5-rocm-prototype-c88273b9db)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T095507.951209Z-I5-full-GPU-JPEG-original-entry-subset-qualification-b0a5e51346](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T095507.951209Z-I5-full-GPU-JPEG-original-entry-subset-qualification-b0a5e51346)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T095002.313615Z-I5-rocm-full-GPU-JPEG-original-entry-integration-08af1af745](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T095002.313615Z-I5-rocm-full-GPU-JPEG-original-entry-integration-08af1af745)
- [migration/reports/image-jpeg-encoder-full-gpu-integration.json](../../../reports/image-jpeg-encoder-full-gpu-integration.json)
- [migration/reports/image-jpeg-encoder-full-gpu-frontend-trace.json](../../../reports/image-jpeg-encoder-full-gpu-frontend-trace.json)
- [migration/reports/image-jpeg-encoder-full-gpu-products-comparison.json](../../../reports/image-jpeg-encoder-full-gpu-products-comparison.json)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T101034.778214Z-I5-full-GPU-JPEG-original-entry-subset-qualification-d1c172995a](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261112T101034.778214Z-I5-full-GPU-JPEG-original-entry-subset-qualification-d1c172995a)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T100832.671105Z-I5-rocm-full-GPU-JPEG-original-entry-integration-03ae7858c2](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark_imageResizeWatermark.cpp/20261112T100832.671105Z-I5-rocm-full-GPU-JPEG-original-entry-integration-03ae7858c2)
- [migration/reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261113T062443.019215Z-I5-current-resize-mathematical-subset-0493502d8b](../../../reports/evidence/rewrite/I5/nvJPEG_Image-Resize-WaterMark__imageResizeWatermark.cpp/20261113T062443.019215Z-I5-current-resize-mathematical-subset-0493502d8b)
- [migration/reports/image-encoder-math-variant.md](../../../reports/image-encoder-math-variant.md)
- [migration/reports/image-encoder-performance.md](../../../reports/image-encoder-performance.md)
- [migration/reports/image-completion-IMG-01.md](../../../reports/image-completion-IMG-01.md)
