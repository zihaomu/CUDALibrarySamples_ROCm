# I6：JPEG2000 可逆变换组件与原图参考

状态：**I6 IN_PROGRESS；nvJPEG2000 仍为 0/4 整例通过、0/4 部分支持**。本记录验收独立 MQ 算术解码、可逆 5/3 逆小波和逆 RCT 的 HIP 组件，没有把 CPU OpenJPEG 解码当作 AMD GPU 解码。

## 固定版本 MQ 算术解码纵向组件

独立 CPU oracle 固定为 OpenJPEG v2.5.4 commit `6c4a29b00211eb0430fa0e5e890f1ce5c80f409f`。静态参考库构建成功，首次宿主环境缺少 `cmake` 的构建失败和第一次内部头缺少类型定义的探针构建失败均保留在不可变日志中；后者改为按 OpenJPEG 原项目 include 顺序构建。依据固定 `mqc.c` 生成 94 项状态表，并随代码保留 BSD-2-Clause 许可。[参考锁](../rewrite/image-j2k-openjpeg-reference-lock.json) · [构建记录](image-j2k-openjpeg-build.json) · [状态表派生](image-j2k-mq-table.json)。

在 GPU 实现前冻结四组 OpenJPEG 自编码、自解码的 MQ 码流、19 个 context 的调度序列及期望 bit SHA。HIP 算术解码在 97、256、511、1023 个 symbol 上全部逐 bit 精确，共 1,887 bit；改变码流字节后输出变化，单字节截断和非法 context 均拒绝且不产出结果，合计 7/7 项通过。1023-bit 用例的 rocprofv3 显示一个实际 `decode_one` kernel，在物理 GPU1 `0000:23:00.0` 执行，追踪输出仍与 CPU oracle 精确一致。[冻结合同](../rewrite/image-j2k-mq-profile.json) · [逐项结果](image-j2k-mq-runs.json) · [GPU trace](image-j2k-mq-trace.json)。

该 kernel 目前每条码流只用一个 GPU 线程，尚无吞吐结论；输入是独立生成的 MQ symbol/context 序列，**不是**从原始 JP2/J2K packet 中分出的 EBCOT 码块。尚缺 bitplane 上下文生成、significance/refinement/cleanup pass、raw bypass、码块终止/重启、packet/tile 解析及把 MQ 输出连接到逆小波。它不升级任何原始样例资格，也不构成完整 JPEG2000 解码。

## 真实 JP2/J2K 容器与主头

项目 CPU 解析组件从原始三张 JP2 读取 box/codestream 边界、SOC/SIZ/COD、尺寸、分量、tile、层数、progression 与可逆/不可逆变换标志。2k 两张均为 1920×1080，4k 为 3840×2160，均有 3 个 8-bit unsigned 分量、单 tile、一层质量层、五级分解；无损图标志为 5/3，有损图标志为 9/7。尺寸/分量使用独立 OpenJPEG 解码结果核对；其余字段是有界的主头观测，尚非完整码流验收。

三张原始 JP2、从原图提取的 raw J2K、签名损坏、box 长度损坏、主头截断、零分量和 SIZ 宽度变化重放共 9 组通过预冻结合同。解析器拒绝四组损坏输入，变更宽度后报告值从 1920 变为 1919。解析器尚未遍历 packet/tier1，也不在 GPU 上执行；这项结果不升级任何原始入口。[冻结合同](../rewrite/image-j2k-container-profile.json) · [逐组日志与结果](image-j2k-container-runs.json)。

## 已完成的 GPU 组件实验

先从仓库原始 `TestImage640x480.bmp` 冻结 1×1、13×11、16×16、17×19、33×29 五组 RGB 裁剪。独立 CPU 实现正向 RCT 与一层 5/3 变换，将三个 int32 分量的系数及预期 RGB 分别按 SHA256 封存。HIP 组件按垂直逆变换、水平逆变换、逆 RCT 三阶段运行；五组 RGB 全字节精确还原。截断系数、零宽度输入被拒绝；修改一个系数后输出变化。17×19 的 rocprofv3 追踪显示三个真实 kernel 均在物理 GPU1 `0000:23:00.0`，追踪与非追踪结果 SHA 一致。

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 五组固定尺寸和负例、变化重放 | 8/8 通过 | [逐例结果](image-j2k-i53-runs.json) |
| GPU kernel、PCI 和重放 | 3/3 kernel，物理 GPU1 | [trace](image-j2k-i53-trace.json) |
| 输入/系数/预期值先冻结 | 5/5 SHA 对 | [合同](../rewrite/image-j2k-i53-rct-profile.json) |

本组件使用一层、原点为偶数相位的 5/3 表示，局部输入尺寸上限 64。它尚未接收真实 JP2/J2K 的 packet/codeblock 数据，也未处理 MQ/EBCOT、HTJ2K、9/7、tile/ROI、NLT3、编码或多 stream pipeline。下一步必须让真实码流的 GPU tier1 输出进入该变换链，并对多分辨率/奇数原点与原始四个 C++ 入口重新验收；当前五组实验不能升级任何原始入口。

## 独立 CPU 与原始 CUDA 对照

三张仓库原始 JP2 与已运行的 NVIDIA 原始例 BMP 输出在解码前先按 SHA 冻结。Pillow 链接的 OpenJPEG 在独立 CPU 进程完成跨解码；这只给后续 GPU 实现提供参考。无损图的 6,220,800 个 RGB 字节与 CUDA 输出完全一致；有损图差异均为 1 级舍入。

| 原图 | 尺寸 | 与 CUDA 输出不同的 RGB 字节 | 最大绝对差 | PSNR |
| --- | ---: | ---: | ---: | ---: |
| 2k_lossless.jp2 | 1920×1080 | 0 | 0 | ∞ |
| 2k_lossy.jp2 | 1920×1080 | 151 | 1 | 94.28 dB |
| 4k_lossy.jp2 | 3840×2160 | 664 | 1 | 93.87 dB |

原图、CUDA 产品、实际加载的 OpenJPEG 动态库和逐图误差见[冻结合同](../rewrite/image-j2k-part1-crossdecode-profile.json)、[跨解码结果](image-j2k-part1-crossdecode.json)及各自证据目录。原始 NVIDIA 基线另见 [I0 原例记录](image-I0-native-JPEG2000-originals.json)。可逆 5/3 的算法依据为 [ITU-T T.800](https://www.itu.int/rec/T-REC-T.800-202407-I/en) 和 [OpenJPEG 参考实现](https://github.com/uclouvain/openjpeg/blob/master/src/lib/openjp2/dwt.c)；这里只验证本项目冻结的变换子集。

## 后续门槛

I6 还需真实 JP2/J2K 容器与 packet/codeblock 解析、GPU MQ tier1、5/3 与 9/7 多级/tile 还原、RGB/YUV/位深/符号分支、局部 ROI 的实际 tile 调度和原始 decoder/pipeline/tile 三入口。I7 需要对应 encoder 与 HT/NLT3；I8 才能组合验收四个原始入口。每一项必须在前置合同中固定输入、数据类型、CPU/CUDA 比较和拒绝路径。

后续 MQ/codeblock 研究的独立 CPU 参考固定为 [OpenJPEG v2.5.4 源码锁](../rewrite/image-j2k-openjpeg-reference-lock.json)，commit `6c4a29b00211eb0430fa0e5e890f1ce5c80f409f`，BSD-2-Clause 许可及 `mqc.c`、`t1.c`、DWT 源文件 SHA 均已记录。该私有参考源码不作为已移植的 GPU 后端。
