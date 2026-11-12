# I5：JPEG 熵编码 GPU 原型

状态：**独立原型通过，GPU 熵内核已接入两个 resize 入口**。GPU 逐 block 生成 baseline JPEG 的 DC 差分、zigzag/AC RLE 与 Huffman 码字；后续版本还在 GPU 上完成 bit offset 前缀扫描、按位打包、末字节填 1、`0xFF` byte stuffing 的前缀扫描及 scatter。此独立原型的 CPU 仅提取已有 JPEG 的系数与表作参考；生产路径通过 HIP FDCT/MCU gather 直接向这些 GPU 内核提供系数，CPU 只组装标准 marker/头部。

| 冻结码流 | 原码流熵数据 | GPU Huffman + GPU pack/stuff | 比较 | 实际 GPU kernel |
| --- | ---: | ---: | --- | ---: |
| odd-420, Q75, 33×29 | 194 B | 194 B | 逐字节一致 | 5 |
| odd-444, Q90, 13×11 | 60 B | 60 B | 逐字节一致 | 5 |

两条数据的 `encode_blocks`、`prefix_bits`、`pack_bytes`、`prefix_stuff`、`scatter_stuff` 均通过 rocprofv3 验证，实际 PCI 为物理 GPU1 `0000:23:00.0`，两次 profile 输出 SHA 与未 profile 完全一致。420 码流含 3 处真实 `0xFF 0x00` stuffing，已覆盖该分支。修改 420 RGB 的 8×8 像素区域后，重新编码得到不同熵数据；新 GPU 熵数据仍与其对应合法 JPEG 逐字节一致。

**限制**：当前前缀扫描是单线程 GPU 正确性原型，不能据此声明高吞吐；该独立原型只覆盖三分量 baseline、无 restart 的两条输入。生产接入覆盖四组原型与两个 resize 入口，详情见[编码入口报告](image-jpeg-encoder.md)。优化 Huffman、restart、progressive 输出、APP/COM metadata 与多实例编码/错误传播仍待完整验收。原始样例的整例支持数不因本原型变化。

证据：[预冻结 Huffman 合同](../rewrite/image-jpeg-encoder-entropy-profile.json)、[GPU 码字/CPU 拼接逐字节验收](image-jpeg-encoder-entropy-runs.json)、[GPU 码字实际 trace](image-jpeg-encoder-entropy-trace.json)、[预冻结 GPU packing 合同](../rewrite/image-jpeg-encoder-gpu-packing-profile.json)、[GPU 全熵链逐字节验收](image-jpeg-encoder-gpu-packing-runs.json)、[五内核 trace 与改输入重放](image-jpeg-encoder-gpu-packing-trace.json)。每次构建、输出、完整命令、标准输出/错误和物理设备快照在对应 `migration/reports/evidence/rewrite/I5/` 下；首次结果失败或重试均保留。
