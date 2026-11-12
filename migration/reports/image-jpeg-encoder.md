# I5：HIP JPEG 前向编码与入口接入

状态：**GPU 前向变换子集通过，整例仍 PARTIAL / FAILED**。四组预冻结 RGB 输入的 420/444、奇数尺寸、MCU 边界和 1×1 在物理 GPU1 上完成色彩转换、色度降采样、8×8 FDCT 与量化。libjpeg-turbo 负责 CPU 熵编码和 JPEG 头/码流组装；这不是完整 GPU JPEG 编码器。

| 固定用例 | 采样/质量 | 独立解码尺寸 | 对源 RGB PSNR | 与 CPU encoder 解码像素最大差 | 结果 |
| --- | --- | --- | ---: | ---: | --- |
| odd-420 | 420 / Q75 | 33×29 | 33.02 dB | 13 | PASSED |
| odd-444 | 444 / Q90 | 13×11 | 47.58 dB | 2 | PASSED |
| mcu-boundary | 420 / Q75 | 64×40 | 17.20 dB | 22 | PASSED |
| tiny-444 | 444 / Q75 | 1×1 | ∞ | 0 | PASSED |

量化表与 CPU libjpeg-turbo 参考完全一致；第三组棋盘格的 17.20 dB 通过在运行前固定的 12 dB 门槛。PSNR 是相对于无损 RGB 源的有损压缩重建质量，不能解读为跨编码器误差。rocprofv3 记录 3 个 `rgb_to_plane` 与 3 个 `forward_dct_quantize` 内核，均落在物理 GPU1 `0000:23:00.0`，profile 前后 JPEG SHA 相同。截断 RGB、零宽度、非法 quality 与非法采样四组均返回错误且没有输出文件。

两个原始 resize 入口已切换到隔离的 `jpeg_decoder_v3.hpp`，在完整七组 B10 CLI 流程下各 7/7 命令及独立 CPU 数值验收通过。`Image-Resize` 的 33 个、`Image-Resize-WaterMark` 的 35 个重编码产品标记 `gpu_software_encode=1` 和 `cpu_entropy_encode=1`。输出是可解码 baseline JPEG。原始输出的 progressive encoding、APP/COM metadata、量化表继承尚未按全合同验证；CPU entropy/Huffman、GPU bitstream packing 和真正的多实例编码调度尚未实现。因此两个入口只能保持 PARTIAL，独立编码器原例仍 FAILED。

证据：[预冻结合同](../rewrite/image-jpeg-encoder-gpu-profile.json)、[GPU 原型构建](image-jpeg-encoder-build.json)、[四组解码比较](image-jpeg-encoder-runs.json)、[真实 GPU trace](image-jpeg-encoder-trace.json)、[非法输入](image-jpeg-encoder-negative.json)、[两个原始入口七组流程](image-jpeg-encoder-integration.json)、[逐步实验记录](image-libraries-progress.md)。每个子项的命令、stdout/stderr、设备快照和源码哈希位于对应 `migration/reports/evidence/rewrite/I5/` 目录；首次宿主环境拒绝和 HIP 编译失败也保留。独立 CUDA 同输入数学对照沿用已封存 B10 记录，当前 I5 不是新的原生 nvJPEG 编码器对照结论。

下一步：GPU DC predictor、zigzag/RLE、Huffman、位长扫描与 byte stuffing；复制编码模式、表及 APP/COM 元数据；对原始 encoder 多实例入口重写 state/slot/stream/事件调度并验收；全部阶段通过后再申请整例资格。
