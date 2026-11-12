# nvJPEG/Image-Resize::imageResize.cpp

**PARTIAL / L4**

七组原登记流程与同输入 CUDA 数学对照重新通过；12 原始 JPEG 中 10 张 rocJPEG 硬件解码、2 张 progressive 使用 CPU 熵装配 + AMD GPU IDCT/色度/RGB，独立 CPU maxAbs≤3、PSNR≥60.76 dB，真实 GPU kernel trace 已验。当前仍缺：I4/fixed-commit-cold-replay-and-independent-review、I5/GPU-JPEG-reencoding-and-metadata。

| 字段 | 当前记录 |
| --- | --- |
| 原始入口 | [nvJPEG/Image-Resize/imageResize.cpp](../../../../nvJPEG/Image-Resize/imageResize.cpp) |
| 实际库 / 后端 | rocJPEG hardware baseline + project HIP progressive IDCT/chroma/RGB; libjpeg-turbo CPU entropy assembly + current CPU JPEG encode / rocJPEG + project HIP image decoder + libjpeg-turbo entropy |
| 候选路线 | rocJPEG (decode only), RPP |
| 代码 | [rocm/ported/nvJPEG/Image-Resize/imageResize.cpp](../../../../rocm/ported/nvJPEG/Image-Resize/imageResize.cpp) |
| required cases | 8/10 |
| CUDA baseline / comparison | PASSED / PASSED |
| 性能 | NOT_RUN |
| 原始源码 SHA256 | `2fe18e4c075972ba4612b3fcf71d37baffb47c14ebe952f79b527846603b6ca1` |

编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。

必需用例：`batches9_11/original-corpus`, `batches9_11/formats-scale`, `batches9_11/roi-boundary`, `batches9_11/batch-multi-instance`, `batches9_11/invalid-cli`, `batches9_11/postprocess`, `batches9_11/python-integration`, `I4/progressive-GPU-pixel-synthesis`, `I4/fixed-commit-cold-replay-and-independent-review`, `I5/GPU-JPEG-reencoding-and-metadata`。

实现方式：`HYBRID_CPU_GPU`。

恢复/扩展条件：完成 I4/fixed-commit-cold-replay-and-independent-review、I5/GPU-JPEG-reencoding-and-metadata 后重做固定提交资格；progressive灰度/采样变体及错误流仍需增补输入合同。

CUDA 对照限制：既有七组同输入 CUDA 数学对照通过；progressive 采用项目 HIP 与 CPU 熵装配，不声称 nvJPEG 私有 backend/流水线 ABI 一致。

## 原始 API 自动移植稿最近一次尝试

该记录与上表选定的手写/替代实现分别保留。

build 失败：/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm/rocm/ported/nvJPEG/Image-Resize/imageResize.h:38:10: fatal error: 'nvjpeg.h' file not found

尝试库：—；实现 hash：`a74f4096693159f025164cc5e362e66b88de564ed0319177bb9d71f21be29447`。

## 复现与证据

从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。

在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：

```bash
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python3 tools/moat/image_progressive_build.py
HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python3 tools/migration/batches9_11_run.py b10
build/image-cpu-venv/bin/python tools/migration/batches9_11_validate.py b10
python3 tools/moat/qualify_image_progressive_subset.py
```

- [migration/reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_Image-Resize_imageResize.cpp](../../../reports/evidence/20261109T083217.050455Z/original-rocm/nvJPEG_Image-Resize_imageResize.cpp)
- [migration/reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_Image-Resize_imageResize.cpp](../../../reports/evidence/20261109T084256.329631Z/original-rocm/nvJPEG_Image-Resize_imageResize.cpp)
- [migration/reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_Image-Resize_imageResize.cpp](../../../reports/evidence/20261109T084857.451692Z/original-cuda/nvJPEG_Image-Resize_imageResize.cpp)
- [migration/reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_Image-Resize_imageResize.cpp](../../../reports/evidence/20261110T043132.627099Z/batches9_11-rocm/nvJPEG_Image-Resize_imageResize.cpp)
- [migration/reports/batches9_11-validation.json](../../../reports/batches9_11-validation.json)
- [migration/reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_Image-Resize_imageResize.cpp](../../../reports/evidence/20261110T043816.470698Z/batches9_11-cuda/nvJPEG_Image-Resize_imageResize.cpp)
- [migration/reports/evidence/rewrite/I4/nvJPEG_Image-Resize_imageResize.cpp/20261112T085148.827007Z-I4-composite-subset-qualification-16a304defd](../../../reports/evidence/rewrite/I4/nvJPEG_Image-Resize_imageResize.cpp/20261112T085148.827007Z-I4-composite-subset-qualification-16a304defd)
- [migration/reports/evidence/rewrite/I4/six-JPEG-entry-current-full-harness-logs-and-product-hashes/20261112T085059.002402Z-I4-host-evidence-archive-2ec54e2d04/harness/nvJPEG__Image-Resize__imageResize.cpp](../../../reports/evidence/rewrite/I4/six-JPEG-entry-current-full-harness-logs-and-product-hashes/20261112T085059.002402Z-I4-host-evidence-archive-2ec54e2d04/harness/nvJPEG__Image-Resize__imageResize.cpp)
- [migration/reports/image-progressive.md](../../../reports/image-progressive.md)
- [migration/reports/image-progressive-harness-archive.json](../../../reports/image-progressive-harness-archive.json)
- [migration/reports/image-progressive-original-corpus.json](../../../reports/image-progressive-original-corpus.json)
- [migration/reports/image-progressive-runs.json](../../../reports/image-progressive-runs.json)
- [migration/reports/image-progressive-trace.json](../../../reports/image-progressive-trace.json)
