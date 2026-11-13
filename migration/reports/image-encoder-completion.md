# 多实例 JPEG 编码入口：当前功能与验收范围

实现已完成冷构建、数值验证和独立复审，正在进行 Git 资格发布。当前主表状态以 samples.yaml 为准。

| 功能 | 实现与验证 |
| --- | --- |
| 原输入和参数 | 递归 BMP、自然排序、截断与重复、Q1–100 夹取、n/r/s/j 语义、help 和错误返回；15 主 CLI 与 16 运行合同 |
| GPU 编码 | 整数 RGB/采样、FDCT 与量化、标准/优化 Huffman、checked prefix、打包/stuff；240 个独立 CPU 与原始 CUDA 质量/数学用例 |
| 多实例生命周期 | 每 state 两 slot，pinned/device 资源、stream/event、预分配与复用、5 项 slot 故障；生产 trace 和变化输入重放 |
| 大图和容量 | 64 位索引、prefix 溢出及分配前检查；8 组大图 24 产品，含 65535 长轴；不声称最大方图可分配 |
| 性能与内存 | 两平台各 6 场景，2 预热+7 独立进程；目标 PID RSS 和 12 组 GPU/pinned 分配峰值分别记录 |
| 冷构建 | 固定提交新建应用/probe/observer，59 个子实验；240 数学产品和 8 大图组字节复现 |

AMD 路线上 CPU 负责 BMP 读取、文件、marker 和优化 DHT 表设计，像素变换与熵编码由 GPU 完成。AUTO/GPU 选择 AMD GPU，强制 NVIDIA hardware 返回明确能力错误。自动线程搜索是已有合同声明的有界实测变体。

[数学变体及旧失败](image-encoder-math-variant.md)说明精确颜色、DC 舍入、逐系数数学界限和独立严格熵解码。旧局部质量比值失败没有删除。CPU/native 全图质量门槛保持，旧局部指标作为诊断；不声称通过 JPEG 正式符合性认证。

[性能与内存](image-encoder-performance.md)明确墙钟、内部计时、allocation 峰值和目标 PID RSS 的范围。[冷构建记录](image-encoder-completion-cold.json)保存固定源码、全部命令、子实验与输出身份；旧极窄图 CPU 解码差异及修订证明分别引用。

两个 resize 入口仅更新当前 baseline 数学子集：68 产品及 GPU 编码 trace 通过。progressive 解码的 CPU 熵阶段、源 progressive 输出、源 DQT 与 APP/COM 继承仍在 IMG-03–05 完成。

冷构建源码提交：`86ff181ab18f920ba93bfd6c124f7202d68083fa`。平台限定 Linux/gfx1201/ROCm10.1。
