# I5：优化 Huffman 的 GPU 熵编码独立原型

状态：**组件 PASSED；原始多实例编码入口仍 PARTIAL**。该原型先于原始入口接入，复用已验 baseline HIP 色彩/FDCT/量化/MCU/Huffman/pack/stuff。新增 HIP `histogram` 内核统计量化 MCU 的 DC/AC 符号频率；CPU 根据小型频率表生成最长 16 bit 的合法 JPEG DHT；实际熵编码与位流打包、byte stuffing 在 GPU 执行，`cpu_entropy=false`。不把 CPU DHT 设计称为 GPU 表设计。

四组在实现前冻结的 RGB/quality/采样输入全部通过独立 libjpeg/Pillow 跨解码。输出尺寸、420/444 采样、量化表与旧 GPU FDCT baseline 一致，**全部解码 RGB 字节精确相同**；三个非平凡图的 DHT 均不同于标准表。另有 1 组截断 RGB 被拒绝且无产品。四件文件大小为 821→478、685→355、1676→1136、629→283 字节，合计 3811→2252 字节；这是四组固定输入的文件大小观察，不是吞吐或通用压缩比结论。

rocprofv3 对 33×29/420 用例记录到 3 个色彩内核、3 个 FDCT 内核及各 1 个 MCU gather、符号直方图、Huffman 编码、bit prefix、pack、stuff prefix 和 scatter 内核，均运行于物理 GPU1 `0000:23:00.0`；追踪与非追踪 JPEG SHA 相同。[先冻结合同](../rewrite/image-jpeg-opt-huffman-profile.json) · [构建](image-jpeg-opt-huffman-build.json) · [逐组结果](image-jpeg-opt-huffman-runs.json) · [trace](image-jpeg-opt-huffman-trace.json)。

DHT 表生成另以单符号、256 均匀符号、25 个 2 的幂长尾、120 稀疏符号和最大偏斜五类分布检查符号库存、16 bit 限长、无全 1 码和前缀不冲突，5/5 通过；长尾分布实际触发 16 bit 限长。[边界日志](image-jpeg-opt-huffman-edges.json)。首次把 Fibonacci 序列当作超长树的自检失败已保留：加入 JPEG 伪符号后该序列的未受限最长码仅 13 bit，未覆盖目标边界；改用 2 的幂序列后通过。

该独立原型随后已[接入原始 `nvJPEG-Encoder-MultipleInstances` 的 `-f` 路径](image-jpeg-encoder.md)：七组 CLI、16 产品跨解码及 baseline 84/优化 39 个 GPU kernel 多 stream trace 通过；复合资格仍为 PARTIAL。pinned buffer、事件重叠、自动线程标定、并行前缀性能及原生 CUDA 入口基线仍未完成。
