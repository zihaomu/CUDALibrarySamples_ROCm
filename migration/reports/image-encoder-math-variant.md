# JPEG encoder：明确的颜色与量化数学变体

状态：**新80项数学验收通过，已接入工作区；受影响生产资格正在刷新，未提升原始样例资格**。合同见[首版](../rewrite/image-encoder-math-variant-profile.json)与[结构加强版 v2](../rewrite/image-encoder-math-variant-v2-profile.json)。两版保留相同输入、颜色权重和数值预算；v2 增加完整 MCU、严格结束标记和零恢复警告检查。

原合同中的每 32×32 区域源图 MSE 比值不能单独定义两个有损编码器的算法等价。[封存的交叉实验](image-encoder-reference-crosscheck.json)表明，独立 CPU 与 CUDA 编码器互相比较也会失败：开发矩阵两个方向为 2/0，新保留矩阵为 4/2。原生产实现 78/80、仅修正 DC 的候选新保留集 74/80，均保持原来的失败结论。

实际 GPU 平面进一步证明，十进制颜色公式的浮点求值会在半整数附近改变舍入；此外，先平均颜色值再舍入与先逐像素舍入再降采样，本来就可能得到不同整数。这些差异在 Q1 的粗量化边界处会放大为局部像素差异。它们需要明确的数学定义和逐阶段验证，不能仅凭全图相似度忽略。

## 新变体的定义

- RGB→YCbCr 使用整数分子及公共分母 1,000,000，权重分别为 `(299000,587000,114000)`、`(-168736,-331264,500000)`、`(500000,-418688,-81312)`。色度增加 128。
- 4:2:0 对 2×2 RGB 求和后做一次颜色转换及 nearest-even 舍入，再裁剪到 0–255；奇数宽高复制最后一行/列。4:4:4 逐像素处理。这个定义不宣称与厂商内部预处理相同。
- 分量扩展到完整 8×8 块时复制边缘。DC 精确使用中心化像素和的 1/8，并用整数参考核查半整数远离零。AC 使用标准正交 DCT 的浮点近似。
- 对每一个有效 AC 系数，要求 `abs(量化整数 × q − 独立 DCT) ≤ q/2 + 0.01`。0.01 是未量化 DCT 单位的绝对预算，不再乘 q；这是有界近似，不声称 AC 在所有精确半整数处都采用唯一舍入结果。
- MCU 中超出有效分量块范围的填充块，其 64 个量化系数全部为零；独立解码须恢复 DC 预测后验证，不能只读取可见图像块。

## 必须同时通过的验证

1. 独立整数模型检查全部 GPU 颜色像素；独立 float64 DCT 只读取该模型的平面，不复用 GPU 余弦表。另用 80 位 Decimal 独立计算 9 个极值、常量、脉冲及高频块的 576 个频率，检查参考自身误差。
2. 独立 Python Huffman 解码器读取完整 baseline 码流，检查每个 MCU 的分量、位置、DC/AC、填充块、byte stuffing、最终填充位和 EOI；完整文件不允许额外尾部或截断恢复。独立 libjpeg 系数读取还要求恢复警告为零。
3. JPEG 的每个有效系数必须与实际 GPU 变换输出精确一致，并满足上述独立数学约束。几何、采样、DQT、SOF0/8bit/三分量和全部文件身份继续精确检查。
4. 保留原 CPU/native 全图逐通道 MSE（1dB 因子加 4）和全局 SSIM（最多下降 0.02）门槛；标准/优化 Huffman 像素必须相同，质量参数必须生效。
5. 原逐 tile 误差和最差位置继续完整记录，作为厂商间算法差异诊断，不能据此宣传局部质量相同。新 80 项保留矩阵及两个历史 80 项矩阵都须执行，历史失败不覆盖。

新输入包含独立尺寸、随机 seed 97531、色块排列和自然图 img5；合同在新候选质量结果之前冻结。新80项三方验收全部通过：29,143,040个有效系数、456,900个MCU块（含1,540个填充块）逐项检查；两项旧tile比值诊断未通过，仍保留。95项数学/严格解析检查、56项Huffman/质量控制通过；实际libjpeg完整文件通过，缺EOI和截断entropy拒绝。84项补充证据绑定检查已通过MOAT独立复核；两个历史80项矩阵也全部通过；正式整合入口进一步重跑240项，全部完整JPEG与独立验收候选逐字节一致。

这份合同只定义项目采用的功能等价变体。[T.81](https://www.w3.org/Graphics/JPEG/itu-t81.pdf)给出 DCT/量化和码流框架；正式符合性测试另见[ISO/IEC 10918-2](https://www.iso.org/standard/20689.html)。本项目这些实验不构成 T.83/Part 2 认证。

原入口仍需满足异步调度、错误处理、全部 CLI、性能/峰值内存、共享核心回归及冷构建要求，才能从 PARTIAL 升级。

证据：[80项数学结果](image-encoder-math-cpu.json)、[补充构建/探针/CPU绑定](image-encoder-math-binding.json)、[控制实验](image-encoder-math-controls.json)、[模式比较](image-encoder-math-groups.json)、[真实libjpeg截断拒绝](image-encoder-strict-decoder-negatives.json)、[工作区整合](image-encoder-math-integration.json)。

当前源码结果：[新矩阵80](image-encoder-math-production-fresh.json)、[历史开发80](image-encoder-math-production-development.json)、[历史保留80](image-encoder-math-production-heldout.json)。
