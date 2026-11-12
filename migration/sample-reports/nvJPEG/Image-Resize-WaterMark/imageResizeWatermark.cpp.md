# nvJPEG/Image-Resize-WaterMark::imageResizeWatermark.cpp

**PARTIAL / L4**

七组原登记 CLI/数值流程及同输入 CUDA 数学对照通过；35 件重编码 JPEG 使用 AMD GPU 色彩转换、色度降采样、FDCT 与量化，CPU libjpeg-turbo 完成熵编码/头部；四组预登记输入独立跨解码及物理 GPU trace 通过。完整 GPU Huffman、原编码模式/表/元数据复制和冷检出尚缺，故只算 PARTIAL。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp](../../../../nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp) |
| 实际库 / 后端 | rocJPEG baseline hardware + project HIP progressive IDCT/chroma/RGB + project HIP JPEG color/downsample/FDCT/quant; libjpeg-turbo CPU progressive entropy and JPEG encode entropy/headers / rocJPEG + project HIP image decoder/forward encoder + libjpeg-turbo entropy |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/ported/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp](../../../../rocm/ported/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp) |
| required cases | 9/12 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `e4f336ff2598fdcc5d0899d168eaf7785ed4b277fb494cd6f23960d181fe405b` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original-corpus`, `batches9_11/formats-scale`, `batches9_11/roi-boundary`, `batches9_11/batch-multi-instance`, `batches9_11/invalid-cli`, `batches9_11/postprocess`, `batches9_11/python-integration`, `I4/progressive-GPU-pixel-synthesis`, `I5/GPU-JPEG-forward-transform-and-cross-decode`, `I5/GPU-Huffman-entropy-and-bitstream-packing`, `I5/original-encoding-mode-tables-and-APP-COM-metadata`, `I4-I5/fixed-commit-cold-replay-and-independent-review`。

实现方式：`HYBRID_CPU_GPU`。

恢复/扩展条件：完成 GPU 熵编码/Huffman、原编码模式/表/APP-COM 继承和冷检出后重做全入口资格；跨编码器不要求合法码流字节完全一致。

CUDA 对照限制：既有七组同输入 CUDA 数学对照通过；I5 GPU FDCT 对独立 CPU JPEG 解码和固定门槛验收，不声称与 NVIDIA 私有编码 backend 字节一致。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.h:38:10: fatal error: 'nvjpeg.h' file not found

尝试库：—；实现 hash：`12c6e6a738f590a579b1d7a362e30aeb0565d882896bc490e7decafb77aba007`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh env ROCR_VISIBLE_DEVICES=3 HIP_VISIBLE_DEVICES=0 python3 tools/moat/image_encoder_integration.py
python3 tools/moat/qualify_image_encoder_subset.py
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
