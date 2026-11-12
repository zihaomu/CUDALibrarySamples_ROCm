# I5：HIP JPEG 前向编码与入口接入

状态：**GPU 前向变换子集通过，三个关联入口均 PARTIAL**。四组预冻结 RGB 输入的 420/444、奇数尺寸、MCU 边界和 1×1 在物理 GPU1 上完成色彩转换、色度降采样、8×8 FDCT 与量化。libjpeg-turbo 负责 CPU 熵编码和 JPEG 头/码流组装；这不是完整 GPU JPEG 编码器。

| 固定用例 | 采样/质量 | 独立解码尺寸 | 对源 RGB PSNR | 与 CPU encoder 解码像素最大差 | 结果 |
| --- | --- | --- | ---: | ---: | --- |
| odd-420 | 420 / Q75 | 33×29 | 33.02 dB | 13 | PASSED |
| odd-444 | 444 / Q90 | 13×11 | 47.58 dB | 2 | PASSED |
| mcu-boundary | 420 / Q75 | 64×40 | 17.20 dB | 22 | PASSED |
| tiny-444 | 444 / Q75 | 1×1 | ∞ | 0 | PASSED |

量化表与 CPU libjpeg-turbo 参考完全一致；第三组棋盘格的 17.20 dB 通过在运行前固定的 12 dB 门槛。PSNR 是相对于无损 RGB 源的有损压缩重建质量，不能解读为跨编码器误差。rocprofv3 记录 3 个 `rgb_to_plane` 与 3 个 `forward_dct_quantize` 内核，均落在物理 GPU1 `0000:23:00.0`，profile 前后 JPEG SHA 相同。截断 RGB、零宽度、非法 quality 与非法采样四组均返回错误且没有输出文件。

两个原始 resize 入口已切换到隔离的 `jpeg_decoder_v3.hpp`，在完整七组 B10 CLI 流程下各 7/7 命令及独立 CPU 数值验收通过。`Image-Resize` 的 33 个、`Image-Resize-WaterMark` 的 35 个重编码产品标记 `gpu_software_encode=1` 和 `cpu_entropy_encode=1`。输出是可解码 baseline JPEG。原始输出的 progressive encoding、APP/COM metadata、量化表继承尚未按全合同验证；CPU entropy/Huffman、GPU bitstream packing 尚未实现，因此两个入口保持 PARTIAL。

原始 `nvJPEG-Encoder-MultipleInstances` C++ 入口已由项目 HIP 适配：3 张 BMP 自然排序，`-n 7 -j 2 -s 4` 重复与多状态，Q75/90、420/444、`-f` 优化 Huffman、显式硬件不可用及无效目录/quality 拒绝，七组预登记 CLI 全部通过。16 件实际 JPEG 产品由独立 Pillow/libjpeg 解码，尺寸、采样与量化表匹配；`-f` 确实改变 DHT 表。实际 rocprof trace 有 7 图共 42 个前向内核，落在物理 GPU1 上至少两个 HIP stream；修改一张 BMP 后，只有对应编码文件变化。原始 pinned host/device workspace、事件重叠、自动线程标定和纯 GPU Huffman 尚未完成；历史原生 CUDA baseline 仍未成功构建，不能声称三方原始入口验收。因此该入口由旧构建失败更新为 **PARTIAL**，不计入整例支持数。

证据：[预冻结合同](../rewrite/image-jpeg-encoder-gpu-profile.json)、[GPU 原型构建](image-jpeg-encoder-build.json)、[四组解码比较](image-jpeg-encoder-runs.json)、[真实 GPU trace](image-jpeg-encoder-trace.json)、[非法输入](image-jpeg-encoder-negative.json)、[两个 resize 原始入口七组流程](image-jpeg-encoder-integration.json)、[多实例冻结合同](../rewrite/image-jpeg-encoder-instances-profile.json)、[多实例七组 CLI 与独立跨解码](image-jpeg-encoder-instances-runs.json)、[多实例真实 GPU trace 与改输入重放](image-jpeg-encoder-instances-trace.json)、[逐步实验记录](image-libraries-progress.md)。每个子项的命令、stdout/stderr、设备快照和源码哈希位于对应 `migration/reports/evidence/rewrite/I5/` 目录；首次宿主环境拒绝和 HIP 编译失败也保留。两个 resize 入口沿用已封存 B10 同输入 CUDA 数学对照；独立编码器目前只有 CPU/GPU 交叉验收。

下一步：GPU DC predictor、zigzag/RLE、Huffman、位长扫描与 byte stuffing；复制编码模式、表及 APP/COM 元数据；对原始 encoder 多实例入口重写 state/slot/stream/事件调度并验收；全部阶段通过后再申请整例资格。
