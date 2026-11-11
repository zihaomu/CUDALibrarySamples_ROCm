# NPP、NPP+、nvJPEG、nvJPEG2000 完整样例支持与重写方案

日期：2026-11-11。状态：**IN_PROGRESS**。已开始按计划实施；原设计与基线保留，当前实验和阶段状态见下方执行记录。

## 1. 目标和“完整支持”的含义

目标是将仓库这四个模块的 **26 个原始入口全部验收通过**，包括原图、完整 CLI、文件输出、批处理/多实例/Python 入口和源码条件分支所要求的功能。已有 2 个通过入口也必须参与共享后端回归。其余 **24 个入口：8 PARTIAL、16 FAILED** 是新增整例验收目标。

验收单位是原始样例及它实际调用的 API/模式，不把原程序缩成几个小图片或数值演示。NPP/NPP+ 整套商业 SDK 的全部 API、所有平台和未出现在本仓库的格式属于额外产品范围，需另列清单；本计划不声称覆盖它们。

| 模块 | 当前通过 | 部分 | 失败 | 本计划目标 |
| --- | ---: | ---: | ---: | ---: |
| NPP | 2/9 | 1 | 6 | 9/9 |
| NPP+ | 0/6 | 1 | 5 | 6/6 |
| nvJPEG | 0/7 | 6 | 1 | 7/7 |
| nvJPEG2000 | 0/4 | 0 | 4 | 4/4 |
| 合计 | 2/26 | 8 | 16 | 26/26 |

全项目基线为 241 PASSED、23 PARTIAL、375 FAILED，639 入口、119 功能族、18 模块。如这 24 个缺口均收口且其它资格不撤销，则目标为 **265 PASSED、15 PARTIAL、359 FAILED**。功能族数由实际算子映射重新去重计算，不按 24 个入口直接相加。

“完整”同时要求以下条件：

1. **功能完整**：原始有效输入、合法参数、dtype、布局、ROI、stride、边界、文件/metadata、错误行为和语言入口全部覆盖。原有公开 CPU 文件处理步骤可保留并记录。
2. **计算路径明确**：图像算法实际在 HIP GPU 或 AMD 媒体引擎执行。JPEG/JPEG2000 最终目标中，熵编解码、变换和像素处理由 GPU/媒体引擎实现；CPU 可承担文件、容器、marker/packet 描述解析和调度，不允许整幅 CPU codec 回退替代最终 GPU 实现。临时 CPU 熵解码原型只作过渡研究记录。
3. **三方对照**：AMD 实际输出、独立 CPU 参考和 5090 原生 NPP/NPP+/nvJPEG/nvJPEG2000 输出分别核对。SDK/硬件模式不能运行时保持具体阻塞，不用同一份 HIP/CUDA 算法互相验证后冒充原生基线。
4. **厂商边界透明**：NVIDIA 私有硬件编号、专有二进制及同名 backend 不直接伪装成 AMD 能力。AUTO 选 AMD 实际后端；强制硬件模式需真实能力，无法提供时明确拒绝并保留该子合同缺口。若原例要求该模式成功，则该入口保持 PARTIAL，不能通过修改条件把它排除。
5. **效果可检查**：像素/label/metadata/bitstream 都有结构化检查；性能是独立结果，不以“能跑”声称达到 NVIDIA 吞吐或速度比。

## 2. 已核实的缺口与选型

仓库中已有 NPP 精确 EDT/Voronoi、完整文件 NCC、Canny/FloodFill 子集，以及 rocJPEG+HIP 图像布局/ROI/缩放/水印。重用时保留原始源码、原始资格和已封存失败，按共享后端依赖重新验证。

| 子系统 | 首选实现 | 必须补齐的内容 | 不作为完成依据的替代 |
| --- | --- | --- | --- |
| 通用图像计算 | 项目 HIP；RPP 仅在具体操作语义实测一致时复用 | Canny、Gaussian、resize、色彩、连通域、轮廓、watershed、Hough、signed EDT | 安装 OpenCV、只运行 CPU API、近似算法输出“看起来一致” |
| JPEG baseline decode | 已锁定 rocJPEG/VCN；功能不覆盖时 HIP decoder | batch、颜色格式、ROI、缩放、异步生命周期及实际能力查询 | 只凭函数/枚举存在认定可解码 |
| JPEG progressive decode | 实测可用的 AMD GPU 后端优先；缺口用 HIP 重写 | 多 scan、DC/AC 首次和 refinement、EOB run、restart、IDCT、上采样 | 现有 libjpeg 整图 fallback |
| JPEG encode | 项目 HIP 编码器；若新增 AMD 原生能力通过实测可替换 | DCT/量化、DC 差分、zigzag/RLE、Huffman、byte stuffing、编码表/metadata、多实例 | CPU libjpeg 编码后拷回 GPU |
| JPEG2000 | 项目 HIP codec；参考 OpenJPEG/OpenJPH 和公开标准 | Part 1 编解码、tile/ROI/流水线、HTJ2K、源中 NLT3/浮点条件分支 | 将 JP2 交给 JPEG parser；仅完成 DWT 或 CPU OpenJPEG 回退 |

rocJPEG 是面向 AMD 媒体引擎的 JPEG 解码库，其源码位于 rocm-systems。[AMD 官方介绍](https://rocm.docs.amd.com/projects/rocJPEG/en/latest/)。开发文档列出的编码过程枚举及 decoder capabilities 只能作为调查入口：要记录实际 `coding_process_mask`、输出格式、驱动与真实文件结果；锁定版本没有查询接口时用 header/symbol gate 和逐模式真实 probe。[能力接口文档](https://rocm.docs.amd.com/projects/rocJPEG/en/develop/reference/rocJPEG-api-reference.html)。

现有 HYBRID 创建 -12、progressive CPU fallback、NPP Canny 像素差异和原生 NPP+ SDK 不可用均是历史观察。P0 将重新锁定它们，不将历史限制当成当前所有版本永久不能实现。

OpenJPEG 可作 JPEG2000 算法参考和 CPU oracle，OpenJPH 提供 HTJ2K 的独立参考；都不是本项目已经验证的 HIP 后端。[OpenJPEG 项目](https://www.openjpeg.org/index.html)、[OpenJPH 项目](https://github.com/aous72/OpenJPH)。HTJ2K、浮点 NLT3 的具体参考能力必须另行编译/试跑确认，不能由“支持 JPEG2000”推定。libjpeg-turbo 用作独立 JPEG CPU 验证，不接入最终 GPU 生产路径。[官方说明](https://libjpeg-turbo.org/)。

## 3. 共享后端和入口组织

采用项目现有 MOAT 包装 skill 及固定上游规则：`migration/moat/lock.json`；固定 commit `7b5082cc516c61b91038295346adbe8a1b5d8315`。本次为已有项目的增量设计，保留 surface 的全部 owed 项，不回退全项目状态，也不重建 639 个任务 ID。

CMake C++/HIP 使用兼容适配层和独立后端；Python 为真实 C ABI 调用者。原始 CUDA 树保持不动，在 `rocm/ported` 保留原入口、CLI 和文件流程。新模块与建议文件如下（均为待实现/待拆分，不能按路径列为已完成）：

```text
rocm/backends/image/
  image_view.hpp             # 宽高、通道、dtype、pitch、ROI、设备、stream
  pointwise.hip              # 色彩、alpha、饱和/舍入
  filter_resize.hip          # Gaussian、Sobel、采样/边界
  canny.hip                  # C1/C3 梯度、NMS、阈值、连通滞后
  components.hip             # CCL、label compact、GPU prefix-scan
  contours.hip               # boundary/direction/offset/geometry
  regions.hip                # flood fill、watershed
  hough.hip
  distance.hip               # unsigned/signed EDT、Voronoi
  ncc_contract.hpp            # 现有完整 NCC 路径，纳入回归
rocm/backends/codec/jpeg/
  parser.cpp                 # 头、表、scan 描述，不做 CPU 整图解码
  decode.hip                 # baseline/progressive GPU 核心
  encode.hip                 # DCT、量化、Huffman、输出打包
  rocjpeg_adapter.cpp         # 媒体引擎能力与 surface/stream 适配
rocm/backends/codec/jpeg2000/
  container.cpp              # JP2/J2K、marker/packet 描述与输入界限
  transform.hip              # 5/3、9/7、MCT、量化、NLT
  tier1.hip                  # EBCOT/MQ
  ht.hip                     # HTJ2K 码块
  tier2.cpp                  # packet/container 组装；不回退 CPU 码块编解码
  pipeline.cpp               # tile、ROI、batch、streams/slots
rocm/adapters/image/          # 共享 C ABI、NPP/NPP+ 调用适配
rocm/python/image/            # 两个 Canny 与 decoder 测试入口
cmake/RewriteImages.cmake
```

现有 `rocm/common/batch15_image.hpp`、`batch10_image.hpp` 等先保留，再逐项迁入已验收的共享核心，不能用新接口破坏旧证据。所有 descriptor 明确 byte pitch、元素类型、ROI 原点、C1/C3、planar/interleaved、alpha、所有权与 stream；图像尺寸/分配乘积采用溢出检查，ROI 外及 padding 用 sentinel 验证。

Python 使用 ROCm PyTorch 与共享 HIP C ABI。`torch.cuda` 在 ROCm 中仍是合法接口名；检查 `torch.version.hip`、实际 PCI 设备、stream 和指针，不能仅按包名判断 GPU。保留 permute 后的 stride、contiguous 复制语义、真实 CLI、输出文件和测试断言。OpenCV/Pillow 可用于文件读写和 CPU 参考，但不替代待支持 GPU 算法。

适配层还必须实现原例使用的 workspace 大小查询/创建/销毁、错误状态、context/state 生命周期和 stream 语义。C ABI 固定结构尺寸、整数宽度、对齐和所有权；设备/版本查询报告真实 AMD/项目能力，不伪造 NVIDIA compute capability 或硬件 engine 数量。

只有 API/像素语义一致的操作才复用 RPP。第三方源码在 P0 固定 commit、许可文本 hash、构建选项和实际链接库 hash；OpenJPEG/OpenJPH 候选分别按其真实许可保留声明。若复用源码移植 HIP，同时保持独立 CPU 程序与原生 NVIDIA 验证，不让生产实现和 oracle 共用同一个结果计算函数。

## 4. 分阶段实施顺序

采用 I0–I9 编号，避免与已有实验批次混淆。下列工期是**工程人周的初步估算**，不是 GPU 运行时长或交付日期。I0 的实际纵向原型与基线结果会修订估算；首要目标仍是完整功能与证据。

| 阶段 | 内容 | 依赖 | 可新增整例资格 | 四模块累计目标 | 初估人周 |
| --- | --- | --- | ---: | ---: | --- |
| I0 | 26 入口合同、SDK/驱动能力、原图清单、CPU/5090 基线、fixture 与阈值冻结 | 无 | 0 | 2/26 | 1–2 |
| I1 | 精确 C1/C3 Canny、两个 Python 调用、共享基础图像操作 | I0 | 3 | 5/26 | 2–4 |
| I2 | CCL/label compact、NPP/NPP+ contour、NPP+ unsigned/signed EDT；既有 EDT/NCC 回归 | I1 基础设施 | 5 | 10/26 | 3–5 |
| I3 | NPP/NPP+ watershed、完整 flood fill、Hough、OpenCV benchmark | I1–I2 | 5 | 15/26 | 3–6 |
| I4 | GPU baseline/progressive JPEG decode、批处理/多实例/ROI、decoder Python 测试 | I0、I1 图像核心 | 4 | 19/26 | 4–8 |
| I5 | GPU JPEG encode、表/metadata 复制、resize/watermark 完整重编码、多实例编码调度 | I4 | 3 | 22/26 | 4–8 |
| I6 | JPEG2000 Part 1 decoder、CPU/native 交叉解码；tile/ROI/流水线纵向原型 | I0 | 0，扩展分支未齐前保留候选 | 22/26 | 5–9 |
| I7 | JPEG2000 encoder、rate/quality、HTJ2K、NLT3 各阶段独立验证 | I6 | 0，整例资格待 I8 | 22/26 | 5–9 |
| I8 | HT/浮点/码块/CLI 全部组合，4 个 JPEG2000 原始入口复合验收 | I6–I7 | 4 | 26/26 | 4–8 |
| I9 | 全 26 回归、既有项目资格检查、冷构建、独立复审、性能专项和交付 | I1–I8 | 0 | 26/26 | 1–2 |

合计约 32–61 工程人周，主要不确定性在 JPEG 熵编码、NPP+ 厂商细节、JPEG2000 MQ/HT/NLT3。单人顺序研发应按数月到一年以上规模准备，不能承诺一次短会话完成。实施时可以交付已完整验收的入口；I6/I7 的组件成功不提前升级含未支持模式的 JPEG2000 原例。JPEG2000 线可在图像基础和证据格式稳定后独立推进，但需要单独安排执行资源。

### 4.1 I0 必须先完成的调查

- 保存 26 入口和相关 headers/CMake 的 source SHA、所有 CLI 开关/默认值、API 调用与条件编译结果、输入/输出文件列表及合法/非法边界。
- NPP+ SDK：取得匹配头/库，在 5090 编译并运行原例，记录 SDK hash/动态库路径和完整原生输出。获取或运行失败则明确保持 `NATIVE_BASELINE_BLOCKED`，继续其它可独立实施项，不签发精确 NPP+ 厂商语义资格。
- rocJPEG：在锁定 ROCm10.1 环境测试 baseline/progressive、采样/分量数、HYBRID/硬件及 ROI/scale；新源码可在项目私有前缀重建，不能把修改系统 SDK 或退回 ROCm7 当作方案。
- 编解码纵向实验至少包含：GPU baseline JPEG 解码、progressive scan/refinement 一个非平凡图、GPU Huffman 编码输出跨解码、GPU JPEG2000 MQ 码块与一个 HT 码块对照。记录不支持分支，避免先堆包装层再发现码流不可实现。
- 固定 nvJPEG2000 SDK 版本及 `NVJPEG2K_HAS_NLT3_{ENCODE,DECODE}`。源码中浮点分支不能通过选旧 SDK 宏关闭后称完整；只有明确不存在于所冻结原始构建面的分支才可写成条件不适用，并保留理由。
- CPU oracle 环境与 GPU 项目环境分开固定；Python3.13/ROCm Torch 的二进制依赖在项目环境构建，原环境与包配对不被静默替换。

## 5. 核心算法合同

### 5.1 NPP / NPP+

**Canny 与图像操作**：分离原始 NPP C3→C1、NPP+ Python C1 与 benchmark C1 合同。逐阶段核对 Sobel/梯度范数、三通道归并、方向量化、NMS 的相等值规则、双阈值、连接和边界。先复现当前原图差异，再补单像素斜线/交叉/平台值，禁止通过放宽整图误差把旧差异隐藏。Gaussian 5×5、linear/Lanczos resize、RGB/BGR、灰度、alpha 的像素中心/系数/舍入分别冻结。

**CCL 与 label compact**：GPU union-find/边界合并 + prefix-scan，支持原图异构 batch 与独立 pitch。这里的 compression 是标签编号压紧，不是 LZ4/JPEG 压缩。检查连通划分、背景、分量数、label 范围、batch 不串扰。只有原 API 明确允许 label ID 任意重命名时才能预先定义 canonicalization；原例文件/metadata 要求编号顺序时逐值匹配。厂商反复运行的允许变化在 I0 留证，不能事后选择有利匹配规则。

**Contour**：NPP 的 contour mask/direction/totals/counts/offset 与 NPP+ 的 geometry lists 是不同合同。核对外边界/孔洞、开放/闭合轮廓、像素链/方向、区域归属、长度、bbox、前缀偏移及实际文件输出。只有非零轮廓像素总数不构成通过。

**Watershed / FloodFill / Hough**：watershed 实现排序/分桶浸没和平台区归属，逐像素验证 boundaries/contrasting boundaries/压紧 labels；CPU OpenCV watershed 不是天然同语义 oracle。FloodFill 五模式保留 seed、gradient 与 range 的比较对象、边界规则、paint、完整 metadata。Hough 保留 rho/theta 网格、票数阈值、线数量、最大线数和排序/tie；只有文档允许无序结果才做预先冻结的集合比较。

**Distance**：NPP 原 unsigned EDT/Voronoi/整数截断继续回归；NPP+ 增加 8u→64f、32f/64f signed 输入、符号和零水平集语义。不能简单对浮点图二值化。Voronoi tie 规则、ROI/padding 和输出类型单列。

**Benchmark**：原四类操作 Gaussian/Canny/resize/RGBToGray、OpenCV 单/多线程、warmup/循环/输出检查与 CSV/计时口径均保留。OpenCV CUDA/NPP 原生路径在 AMD 上不虚构存在，可用项目 HIP 后端并明确平台名；CPU 对照保持独立。功能合同通过与有可发布的性能比率分别判定。

### 5.2 JPEG

GPU decoder 先实现 Huffman 表/MCU、restart、dequant/IDCT，再补 progressive 多 scan 的 spectral selection、successive approximation、DC/AC refinement 和 EOB run。所有 scan 对同一 coefficient buffer 的累积顺序与每个分量尺寸都验收；仅成功解出 baseline 不能升级 progressive。

GPU encoder 实现色度下采样、DCT、量化、DC predictor、AC RLE、Huffman（含优化表）、位流长度 prefix-scan 和 byte stuffing；resize/watermark 原例会复制源 JPEG encoding，若该有效输入要求 progressive 输出，则还必须实现 progressive 多 scan 编码和 refinement，不能静默改成 baseline；支持原例采样/quality、encoding 类型及 resize/watermark 的量化表和 APP/COM metadata 复制流程。多实例保留独立 state、slot、host pinned buffer、device workspace、异步事件、输出命名和故障传播，不能退化成一个串行 CPU codec。

baseline/progressive、grayscale/RGB/YCbCr、所有实际接受的 subsampling、ROI/scale、奇数尺寸和 batch 尾部都建矩阵。有效输入原图完整跑，损坏/截断/缺表/错误 scan 不崩溃且返回规定错误。硬件只能按真实 AMD 能力报告；NVIDIA backend ID 通过适配层解释，不能硬编码“hardware available”。

### 5.3 JPEG2000

完整数据流：容器/marker 描述 → packet/codeblock 分发 → MQ/EBCOT 或 HT 码块解码 → 反量化 → 5/3 或 9/7 IDWT → RCT/ICT/MCT → 输出；编码为对应反向链，并包含合法 packet/JP2 组装。

- **Part 1**：原始 JP2/J2K、lossy/lossless、灰度/多分量、符号/位深、subsampling、边界对称延拓、tile 边缘和量化。
- **源码扩展**：实际 `-ht`、`-cblk`（含128×32）、`-I`、Q-factor/quantization/target-PSNR、resolution/LRCP 设置、YUV precision1–16、PFM 与 FP16/FP32 NLT type3 分别登记。不同 quality enum 不能统一当一个数值 scale。
- **NLT3**：确认浮点到可逆整数表示及反变换的标准语义。FP16 输出与先按原例转换后的 half bits 比较；不能与原始 PFM FP32 直接作零误差比较。±0、有限极值、非有限值按原生/标准有效域测试，非法项明确拒绝。
- **Tile/partial**：验证 decode area、坐标、跨 tile ROI、分量采样、输出偏移和行 pitch；与完整解码裁剪结果交叉核对，同时记录实际只调度所需 tile/codeblock。先解全图再裁剪仅作原型，不能代替该执行合同。
- **Pipelined**：双/多 slot 独立 buffers、码流生命周期、CPU parse / H2D / GPU decode / output 的真实事件依赖，输入改变后重复，尾 batch、失败 slot 和并发实例不串数据。不靠单线程顺序循环冒充流水线。

## 6. 测试矩阵与误差策略

每个入口至少登记原始完整 profile、非规则尺寸、修改输入、pitch/ROI、边界/空输入、重复/并发、损坏输入七类，并展开其实际 CLI、类型和算法分支。七类是最低分类，不是把所有入口都限定为七个 case。完整输入文件、seed、SHA256、阈值和 case ID 在编码前冻结。

| 输出类型 | 默认验收原则 | 额外检查 |
| --- | --- | --- |
| mask、labels、整数像素、metadata、文件尺寸 | 确定性合同逐元素/字段精确 | ROI外和padding保留；label/geometry完整，不只比总量 |
| EDT FP32/FP64 | 预设目标分别≤2/4 ULP，I0按标准及原生行为冻结 | 符号、Voronoi坐标、截断与非有限值分别判断 |
| JPEG decode | 同一冻结输出规则逐像素；IDCT合法差异另列门槛 | 初始候选8-bit maxAbs≤2且PSNR≥48dB，仅在原合同允许且I0确认后采用；逐分量/全像素，不仅平均值 |
| JPEG encode | 标准有效码流、表/metadata/模式一致、独立跨解码 | quality/采样生效，量化表和受影响像素检查；不默认要求两个合法encoder产生相同字节流 |
| JPEG2000 reversible | 原始有效整数逐值精确；可逆浮点按规定转换后bits精确 | 双向跨解码与尺寸/分量/位深/符号/marker |
| JPEG2000 irreversible | 对原指定quality语义、量化及重建误差逐项验收 | 同时看全图max误差、MSE/PSNR和局部残差；PSNR目标容差在I0冻结，不事后为了通过调整 |

边界 corpus 至少包括1×1、奇数宽高、非对齐 stride、tile/codeblock 交界、常量、棋盘、斜线、噪声、大面积平台/孔洞、无前景/全前景、大分量数和不同输入同一 workspace 连续运行。只测一个 seed 或同一小图不够。

GPU 路径验证：HIP 用 rocprofv3 留 kernel/copy/event trace；rocJPEG/VCN 结合 VA-API/backend 记录、实际 surface/设备输出及媒体引擎 trace。媒体解码不是 HIP kernel，不能以 HIP kernel 数量为唯一判据。生产 GPU 模式另测 CPU codec 禁用，CPU oracle 在独立进程执行。

负向检查必须覆盖错像素/丢 scan/错label/错offset/错码块/少处理一个batch、空图或空输出、偷偷 CPU fallback、伪造 hardware capability、错误 ABI/stream、NaN/inf/零计时、缺原图、错源码/二进制/fixture/SDK 与篡改资格。CLI要求预期退出码及诊断；超时、崩溃和加载失败不算预期拒绝。

## 7. 实验记录和资格签发

扩展现有 `tools/moat/experiment.py`、`qualification_common.py`、`audit.py`、`selected_proofs.py`，不另建一套互相矛盾的通过统计。建议新增 `tools/moat/image_{contracts,fixtures,build,run,cpu,native,negative,qualify,publish}.py`，按需要拆分 JPEG/JPEG2000 子驱动。

每个尝试使用单独 experiment ID，至少保存：

```text
manifest.json                  sample/case/backend/parent/comparison/outcome
source.json                    当前源码、完整编译依赖和source CAS
inputs/manifest.json            原始/生成输入SHA、dtype/形状/ROI/CLI
commands.json                   真实命令、cwd、环境、退出码、stdout/stderr
backend.observed.json           ROCm/HIP/driver/VA-API/库SO/PCI/设备信息
outputs/                       像素、labels、metadata、码流、文件清单
validation.json                每个检查、阈值、观测值和失败坐标/分量
trace/                         HIP/媒体引擎及stream事件证据
qualification.json             所有必需case与完整证据引用、review/source commit
sealed.json                    所有归档文件大小与hash
```

纯进程内复合资格没有外部命令时可不生成 commands.json；其引用的真实构建/GPU/CPU/CUDA实验必须核对命令。大二进制留 artifacts/远端时仍保存明确位置/大小/hash与CPU实际读取记录；可重建 fixture 必须有seed/生成器hash和文件hash。

通过流程：合同冻结 → 项目环境构建 → 每个GPU/CPU/native场景 → 故障/ABI/CLI/执行语义 → 固定源码独立复审 → 复合资格封存 → **先提交资格与引用seal到Git** → publisher重新验证完整case、类型/语言/实现/hash、所有引用与当前依赖 → 更新 samples/tasks/library registry → render。记录每次失败、超时和中断；不覆盖旧结果。

首次发布新入口前补齐 `tools/migration/operator_support.py` 中 NPP 的新增算法及 NPP+/nvJPEG/nvJPEG2000 的显式算子映射。按模块和原核心功能去重，Python、batch 和精度变体不增加功能族；每个被声明的操作都要有对应原例与独立验收，不能只改计数绕过缺项。

首页仅展示当前总量和模块支持矩阵；具体支持方式、效果、未支持原因与日志继续在 `migration/reports/support-log-index.md` 及模块子页。I0–I9进展写入 `migration/reports/image-libraries-progress.md`，不重新放回首页。开发历史保留在独立归档。

## 8. 环境、构建和性能

AMD 固定现有 ROCm10.1.0 镜像（SHA见项目锁）、gfx1201、HIP7.16；通过 `/home/zihaomu/zihaomu_workspace/rocm10-launch.sh` 进入项目环境。按PCI/guard选择实际允许的卡，物理GPU3禁止计算，GPU4–7先查预约。不能把HIP ordinal当物理编号。CUDA在 `nvidia-5090x2` 使用实际安装的匹配SDK；独立CPU环境也锁定包/源码。

构建入口扩展现有 `cmake/Rewrite*.cmake`，注册共享图像ABI、C++样例、Python真实调用和codec测试；禁止在测试阶段下载/替换全局SDK。若工程存在目录枚举的 Windows-only `dirent.h` 错误，使用项目标准文件枚举适配，保留原图集合/遍历行为，不因修复编译就登记通过。

性能专项在功能资格之后，报告 GPU/媒体引擎时间、host parse、H2D/D2H、端到端延迟/吞吐、batch/分辨率/码率/quality和峰值内存，保留冷/热和P50/P95。GPU空闲资格不满足时标记未验收，继续完成正确性；不发布速度比，也不把 NVIDIA 原示例中的宣传速度当目标。

## 9. 交付与完成判断

- 四个模块26入口的 frozen contracts 全覆盖；24个缺口逐项新资格，2个原通过入口回归有效。
- 对源码仍存在而本计划承诺覆盖的 CLI/HT/NLT/float/geometry 分支，任何未完成项都保留在该入口 required cases 中；不能因基础路径过关而移出分母。
- NPP/NPP+、JPEG、JPEG2000三个独立CPU/native交叉验收链；CPU整图fallback计数为零，媒体/软件GPU路径如实标明。
- 主表、任务状态、算子去重、实际库/候选库、详细支持记录和复现命令一致；shared后端变化触发全部受影响入口回归。
- 从干净检出重新构建26入口，输入重建与实际输出重新验收；已有31项MOAT资格的当前依赖审计及原项目16项CTest按影响范围回归，866原源/477构建定义/639入口保持。
- 固定内容独立复审、所有seal/schema/当前依赖/失败中断核算通过后，提交并推送用户fork `rocm`，核对远端SHA与README。只记本计划范围完成，不清空其它 owed 组件或未验证平台。

最早可执行的一批为 **I0 + I1**：先恢复 NPP/NPP+ 5090 基线、冻结三种 Canny 合同与原图，再完成3个Canny入口及其共享C ABI/Python调用。JPEG和JPEG2000同时在I0完成可行性纵向探针，避免到后期才发现SDK/码流分支缺口。该段为设计时的首批顺序；实际执行情况以末尾实时记录为准。

## 10. 逐入口实施主表

基线提交：`605a561e7fafc81be52a44354867c84f3078161b`；本表根据原始清单生成。各行 source SHA、相邻 header SHA、API 提示、用例分类和阶段依赖见 `migration/rewrite/image-libraries-plan.json`。相邻 headers 只是静态调查，完整编译依赖由 I0/实际构建记录补齐。

| 模块 / 原始入口 | 当前结论 | 收口阶段 | 主要实现 |
| --- | --- | --- | --- |
| [NPP/nppCanny/npp_canny_simple.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/nppCanny/npp_canny_simple.cpp) | PARTIAL | I1 | Shared exact HIP C1/C3 Canny + C ABI; real C++/ROCm Python caller |
| [NPP/nppCanny/npp_canny_simple.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/nppCanny/npp_canny_simple.py) | FAILED | I1 | Shared exact HIP C1/C3 Canny + C ABI; real C++/ROCm Python caller |
| [NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp) | FAILED | I2 | HIP CCL/union-find + scan/label compact; independent batch descriptors |
| [NPP/findContour/findContour.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/findContour/findContour.cpp) | FAILED | I2 | Shared HIP labels + contour mask/direction/offset; NPP+ geometry adapters |
| [NPP/houghLines/houghLines.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/houghLines/houghLines.cpp) | FAILED | I3 | HIP Canny + Hough accumulator/peak extraction |
| [NPP/opencvBenchmark/opencvBenchmark.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/opencvBenchmark/opencvBenchmark.cpp) | FAILED | I3 | Shared HIP Gaussian/Canny/resize/color + independent CPU OpenCV benchmark |
| [NPP/watershedSegmentation/watershedSegmentation.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/watershedSegmentation/watershedSegmentation.cpp) | FAILED | I3 | HIP bucket/sort flooding + plateau assignment + segmentation outputs |
| [NPP/distanceTransform/distanceTransform.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/distanceTransform/distanceTransform.cpp) | PASSED | I9（回归守护） | HIP exact separable Euclidean distance/Voronoi/integer truncation kernels |
| [NPP/templateMatching/templateMatching.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP/templateMatching/templateMatching.cpp) | PASSED | I9（回归守护） | HIP NCC/full original CLI/RAW input/PGM annotation/HIP-event timing |
| [NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP%2B/cannyEdgeDetectorPython/cannyEdgeDetector.py) | FAILED | I1 | Shared exact HIP C1/C3 Canny + C ABI; real C++/ROCm Python caller |
| [NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP%2B/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp) | FAILED | I2 | HIP CCL/union-find + scan/label compact; independent batch descriptors |
| [NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP%2B/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp) | FAILED | I2 | HIP exact unsigned/signed EDT and Voronoi; 32f/64f semantics |
| [NPP+/findContour/findContourNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP%2B/findContour/findContourNPPPlus.cpp) | FAILED | I2 | Shared HIP labels + contour mask/direction/offset; NPP+ geometry adapters |
| [NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP%2B/floodFill/floodFillVariousRegionTypesNPPPlus.cpp) | PARTIAL | I3 | HIP five flood-fill modes + paint/metadata |
| [NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/NPP%2B/watershedSegmentation/watershedSegmentationNPPPlus.cpp) | FAILED | I3 | HIP bucket/sort flooding + plateau assignment + segmentation outputs |
| [nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp) | PARTIAL | I4 | Probed rocJPEG/VCN + HIP baseline/progressive decoder and real framework |
| [nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp) | PARTIAL | I4 | Probed rocJPEG/VCN + HIP baseline/progressive decoder and real framework |
| [nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp) | PARTIAL | I4 | Probed rocJPEG/VCN + HIP baseline/progressive decoder and real framework |
| [nvJPEG/nvJPEG-Decoder/tests/test_decoder.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py) | PARTIAL | I4 | Probed rocJPEG/VCN + HIP baseline/progressive decoder and real framework |
| [nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp) | PARTIAL | I5 | HIP JPEG encoder + shared GPU resize/alpha; full multi-instance scheduling |
| [nvJPEG/Image-Resize/imageResize.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG/Image-Resize/imageResize.cpp) | PARTIAL | I5 | HIP JPEG encoder + shared GPU resize/alpha; full multi-instance scheduling |
| [nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp) | FAILED | I5 | HIP JPEG encoder + shared GPU resize/alpha; full multi-instance scheduling |
| [nvJPEG2000/nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG2000/nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp) | FAILED | I8 | Project HIP JPEG2000 MQ/HT codec + header/container orchestration |
| [nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp) | FAILED | I8 | Project HIP JPEG2000 MQ/HT codec + header/container orchestration |
| [nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp) | FAILED | I8 | Project HIP JPEG2000 MQ/HT codec + header/container orchestration |
| [nvJPEG2000/nvJPEG2000-Encoder/nvjpeg2k_encode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/nvJPEG2000/nvJPEG2000-Encoder/nvjpeg2k_encode.cpp) | FAILED | I8 | Project HIP JPEG2000 MQ/HT codec + header/container orchestration |

## 11. 计划文件与当前结论

本地设计：`doc/cuda_samples_on_rocm_image_libraries_plan.md`；仓库镜像：`migration/image-libraries-plan.md`；机器队列：`migration/rewrite/image-libraries-plan.json`。现有支持状态继续以 `migration/samples.yaml` 为准。此处与机器队列保留设计基线；实际合同调查、实现和验收状态见文末执行记录及 migration/reports/image-libraries-progress.json。

## 12. 主要风险与处理决策

| 风险 / 尚待确认项 | 处理办法 | 完成判断 |
| --- | --- | --- |
| NPP+原生SDK尚未取得，ABI/厂商细节缺参考 | I0先固定可用SDK并运行真实原例；失败保留独立基线阻塞，其它算法线继续 | 没有原生对照时不声称精确NPP+厂商语义收口 |
| NPP label、轮廓、watershed平台区和Canny tie规则不同 | 微型构造图、native重复运行、逐阶段数据与原图同时检查，规则先冻结 | 原例要求的精确字段/像素全部满足；不事后改变匹配规则 |
| rocJPEG新接口不代表锁定GPU能跑progressive/各分量 | 固定库/驱动/PCI/能力及真实输入；缺口由HIP实现 | 不剩CPU整图fallback，CMYK/YCCK等若属于原例有效域也必须补齐 |
| JPEG2000 HT/NLT3缺独立CPU参考或当前SDK不支持 | 原标准、候选库实际构建、独立小码块/浮点测试和新旧SDK条件分支留证 | HT和NLT3不能从源码中被静默关闭以通过整例 |
| 强制NVIDIA硬件行为无法在AMD上原样提供 | AUTO使用真实AMD能力，强制硬件按实际成功或拒绝；保留原例仍未满足的子合同 | 不伪造硬件数量/编号或把软件GPU报告为专用硬件 |
| GPU熵编码性能低、workspace过大 | 先正确实现、分tile/码块有界处理，再做并行度/流水线与性能专项 | 保留原始规模且全输出正确；性能结论独立发布 |

这些是实施依赖和研发风险，不是已经证明算法不可能实现。若实际执行发现与本计划不同的能力或合同，应更新本文件与逐例队列，保留变化依据和失败记录。


<!-- IMAGE_EXECUTION:START -->

## 实时执行记录

最近更新：2026-11-11T09:18:24.226917+00:00。26入口当前2通过/8部分/16失败；实验运行成功不会直接升级支持数。

| 时间 | 阶段 | 事件 / 结果 | 证据 |
| --- | --- | --- | --- |
| 2026-11-11T08:18:51.858327+00:00 | I0 | 按用户指令开始实施；固定MOAT skill/state-library hash及现有26入口清单已核对，取得linux/gfx1201 porting锁。先做原始源码/CLI/输入合同与真实NVIDIA/AMD能力调查，尚不增加支持数。 |  |
| 2026-11-11T08:19:30.797668+00:00 | I0 | 锁定ROCm环境/允许设备及实际库、Python包、rocJPEG创建能力调查完成；这不是图像功能验收。 | `migration/reports/evidence/rewrite/I0/image-AMD-environment/20261111T081925.957029Z-I0-rocm-probe-2b6e43dfd7` |
| 2026-11-11T08:20:11.681716+00:00 | I0 | 26入口、24原构建定义、186原仓库图像/参考输出资产SHA已封存；CLI/API/条件分支静态提示已记录，语义/default/input分类仍需逐例核实。 | `migration/reports/evidence/rewrite/I0/image-original-contract-inventory/20261111T082010.526784Z-I0-host-inventory-68c870ae2f` |
| 2026-11-11T08:20:13.220675+00:00 | I0 | 5090实际SDK/动态库/设备与OpenCV前置条件调查已归档。 | `migration/reports/evidence/rewrite/I0/image-native-SDK-environment/20261111T082012.024994Z-I0-cuda-host-0a086ba7e9` |
| 2026-11-11T08:22:24.551021+00:00 | I0 | NPP+/nvJPEG2000官方发布索引查询及网络失败均已封存，后续从实际发布清单固定SDK。 | `migration/reports/evidence/rewrite/I0/image-NVIDIA-distribution-index/20261111T082220.553601Z-I0-host-download-0cb8b6039e` |
| 2026-11-11T08:22:26.923916+00:00 | I0 | 锁定ROCm环境/允许设备及实际库、Python包、rocJPEG创建能力调查完成；这不是图像功能验收。 | `migration/reports/evidence/rewrite/I0/image-AMD-environment/20261111T082221.708001Z-I0-rocm-probe-272c93fe54` |
| 2026-11-11T08:22:29.188046+00:00 | I0 | 项目私有CPU参考环境安装/实际加载已记录；独立NumPy/OpenCV/Pillow用于参考，不作为GPU实现。 | `migration/reports/evidence/rewrite/I0/image-private-CPU-reference-environment/20261111T082228.326430Z-I0-host-build-a39cba82dc` |
| 2026-11-11T08:22:53.762784+00:00 | I0 | 已确认rocJPEG实际位于SDK core目录；硬件backend创建成功，HYBRID返回-12。当前库无GetDecoderCaps，不能按新文档枚举宣称模式支持；继续用实际文件decode核验。 | `migration/reports/image-I0-AMD-environment.json` |
| 2026-11-11T08:23:25.532600+00:00 | I0 | 取得官方NPP+0.10/nvJPEG2000 0.12发布清单；后续按清单SHA下载私有SDK，不改系统CUDA。 | `migration/reports/evidence/rewrite/I0/image-native-SDK-manifests/20261111T082321.035090Z-I0-host-download-dc842ed7fa` |
| 2026-11-11T08:24:41.785650+00:00 | I0 | nvjpeg2000 SDK 0.12.0.58 / cuda13 官方下载与SHA核验：VERIFIED_DOWNLOAD；仅项目私有前缀，编译/运行资格另验。 | `migration/reports/evidence/rewrite/I0/image-private-nvjpeg2000-SDK/20261111T082437.431401Z-I0-host-download-8ccdc20260` |
| 2026-11-11T08:24:47.123769+00:00 | I0 | 宿主ensurepip缺失的安装失败已保留；通过无pip的私有venv和指定目标解释器安装独立CPU参考环境，未改系统包。 | `migration/reports/evidence/rewrite/I0/image-private-CPU-reference-environment-retry/20261111T082344.568179Z-I0-host-build-1fd46def0d` |
| 2026-11-11T08:25:39.363068+00:00 | I0 | ROCm Python私有cv2绑定安装与实际导入已记录；使用--no-deps保留原Torch/torchvision/NumPy配对，不把CPU Canny测试视作GPU成功。 | `migration/reports/evidence/rewrite/I0/image-private-GPU-Python-dependency/20261111T082442.941570Z-I0-rocm-build-8532478964` |
| 2026-11-11T08:26:29.987919+00:00 | I0 | nppplus SDK 0.10.0.0 / cuda12 官方下载与SHA核验：VERIFIED_DOWNLOAD；仅项目私有前缀，编译/运行资格另验。 | `migration/reports/evidence/rewrite/I0/image-private-nppplus-SDK/20261111T082442.289932Z-I0-host-download-36f42a812b` |
| 2026-11-11T08:27:53.875357+00:00 | I0 | 7个真实NPP C1/C3 Canny探针已执行：原Teapot、随机、平台tie、阶跃与常量。探针输出只用于冻结像素语义，尚不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T082738.035930Z-I0-cuda-probe-07785e4f70`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T082740.357279Z-I0-cuda-probe-d4aa0767eb`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T082742.587609Z-I0-cuda-probe-869c5f17ff`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T082744.864221Z-I0-cuda-probe-4804c9c2a2`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T082747.148882Z-I0-cuda-probe-463a41c501`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T082749.427361Z-I0-cuda-probe-b5e8dd9c53`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T082751.599010Z-I0-cuda-probe-a424fb0559` |
| 2026-11-11T08:28:54.864695+00:00 | I0 | 独立CPU Canny阶段模型与真实NPP像素作研究对照；包含整数梯度、L2量化、NMS方向/tie与边界候选，不以拟合一张图作为资格。 | `migration/reports/evidence/rewrite/I0/Canny-independent-model-research/20261111T082853.631774Z-I0-CPU-research-4fb39f2e60` |
| 2026-11-11T08:28:56.710377+00:00 | I0 | nvjpeg2000 SDK私有部署到5090并核对实际loader依赖，结果 SDK_INSTALLED。 | `migration/reports/evidence/rewrite/I0/image-native-private-nvjpeg2000/20261111T082854.767776Z-I0-cuda-setup-9ddac5ce1d` |
| 2026-11-11T08:29:20.405018+00:00 | I0 | nppplus SDK私有部署到5090并核对实际loader依赖，结果 SDK_INSTALLED。 | `migration/reports/evidence/rewrite/I0/image-native-private-nppplus/20261111T082857.026909Z-I0-cuda-setup-c752e717b5` |
| 2026-11-11T08:31:53.338878+00:00 | I0 | 7个真实NPP C1/C3 Canny探针已执行：原Teapot、随机、平台tie、阶跃与常量。探针输出只用于冻结像素语义，尚不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083114.318987Z-I0-cuda-probe-cd9f6b82eb`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083116.683144Z-I0-cuda-probe-5fd2db5d9c`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083119.037651Z-I0-cuda-probe-37b86e6bed`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083121.420435Z-I0-cuda-probe-5c7d1611a5`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083123.704448Z-I0-cuda-probe-b9d765bba4`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083125.997552Z-I0-cuda-probe-801414061d`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083128.337258Z-I0-cuda-probe-39ca14ae6d`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083130.665469Z-I0-cuda-probe-977025c685`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083132.841187Z-I0-cuda-probe-fc0b34e999`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083135.063721Z-I0-cuda-probe-41f1964819`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083137.336481Z-I0-cuda-probe-c89b8c9199`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083139.639857Z-I0-cuda-probe-36b78f77dc`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083141.812993Z-I0-cuda-probe-9094df1cb8`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083144.110875Z-I0-cuda-probe-127b56f35b`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083146.398215Z-I0-cuda-probe-b1243e3cb2`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083148.700800Z-I0-cuda-probe-7ce03cec35`；`migration/reports/evidence/rewrite/I0/Canny-native-contract/20261111T083150.992255Z-I0-cuda-probe-a3c2a3f988` |
| 2026-11-11T08:37:18.774206+00:00 | I0 | 8个真实NPP C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083701.022594Z-I0-cuda-probe-01922cf8bd`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083703.338048Z-I0-cuda-probe-5cfc4ced4f`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083705.471773Z-I0-cuda-probe-8b2ac99078`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083707.599677Z-I0-cuda-probe-7e158ec754`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083709.784692Z-I0-cuda-probe-adfc060a42`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083712.011009Z-I0-cuda-probe-c42a7306f4`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083714.340425Z-I0-cuda-probe-4a6158b2ab`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T083716.521032Z-I0-cuda-probe-42818e638f` |
| 2026-11-11T08:38:00.976973+00:00 | I0 | 原生NPP Canny合同探针构建失败，保留实际编译日志。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract-build/20261111T083758.269289Z-I0-cuda-build-b8acb1f82f` |
| 2026-11-11T08:39:24.487288+00:00 | I0 | 5个真实NPPPlus C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T083913.944671Z-I0-cuda-probe-6eaffe00b0`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T083916.137221Z-I0-cuda-probe-f4db1f5402`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T083918.228023Z-I0-cuda-probe-d2e61b60cc`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T083920.328062Z-I0-cuda-probe-806f176d32`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T083922.407185Z-I0-cuda-probe-8e6687fc1b` |
| 2026-11-11T08:41:31.788719+00:00 | I0 | rocJPEG原始JPEG逐文件实际解码调查完成：10/12文件取得GPU输出；失败格式和HYBRID状态逐项保留，尚未作数值资格。 | `migration/reports/evidence/rewrite/I0/rocJPEG-original-file-decode/20261111T084128.016454Z-I0-rocm-probe-2ee4bb24d3` |
| 2026-11-11T08:42:50.376334+00:00 | I0 | NPP+实际C1 Canny已在5090执行，SDK阻塞解除；与NPP13.2同输入结果不同。Teapot low72/high256：NPP6541非零像素、NPP+1832；传统8连通参考2792。连接语义未冻结，不放宽像素门槛或升级支持。 | `migration/reports/image-I0-Canny-native-probes-plus.json`；`migration/reports/image-I0-Canny-native-probes.json` |
| 2026-11-11T08:42:50.768678+00:00 | I1 | 开始共享HIP图像核心的分阶段候选：先冻结Sobel/L2/NMS合同，再实现C ABI和真实GPU逐元素检查。I0语义调查继续并行；此重叠仅用于候选开发，不跳过I0和整例资格门槛。 | `migration/rewrite/image-canny-stages-contract.json` |
| 2026-11-11T08:44:06.114554+00:00 | I1 | 共享HIP Canny阶段构建失败，实际编译日志已保留。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages-build/20261111T084404.449085Z-I1-rocm-build-c955ca9c80` |
| 2026-11-11T08:45:20.374717+00:00 | I1 | teapot-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T084518.833441Z-I1-rocm-run-13ab8d8435` |
| 2026-11-11T08:45:21.992844+00:00 | I1 | teapot-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T084520.683722Z-I1-rocm-run-aa972dd8e2` |
| 2026-11-11T08:45:23.629732+00:00 | I1 | noise-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T084522.352206Z-I1-rocm-run-194ab26738` |
| 2026-11-11T08:45:25.149243+00:00 | I1 | noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T084523.941161Z-I1-rocm-run-96daebcfae` |
| 2026-11-11T08:45:26.719697+00:00 | I1 | ties-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T084525.444681Z-I1-rocm-run-e8188b7474` |
| 2026-11-11T08:45:27.495645+00:00 | I0 | nvJPEG2000四个原始入口的私有SDK构建/原仓库完整setup baseline：EXECUTED；包括实际文件decode、pipeline、tile ROI、classic/HT可逆编码与原图文件逐字节回环检查。其它类型分支尚未验收。 | `migration/reports/evidence/rewrite/I0/nvJPEG2000-original-build-and-examples/20261111T084513.481474Z-I0-cuda-baseline-1454add055` |
| 2026-11-11T08:45:28.326362+00:00 | I1 | step-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T084527.021031Z-I1-rocm-run-0a7465037b` |
| 2026-11-11T08:45:29.910877+00:00 | I1 | tiny-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T084528.651847Z-I1-rocm-run-791814b0f9` |
| 2026-11-11T08:45:46.202746+00:00 | I1 | teapot-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T084545.321554Z-I1-CPU-reference-d5ff4e9ebc` |
| 2026-11-11T08:45:47.325604+00:00 | I1 | teapot-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T084546.484975Z-I1-CPU-reference-e6aa29f1b0` |
| 2026-11-11T08:45:48.426532+00:00 | I1 | noise-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T084547.619935Z-I1-CPU-reference-6b58aa2608` |
| 2026-11-11T08:45:49.573155+00:00 | I1 | noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T084548.767302Z-I1-CPU-reference-0e48f2d4f8` |
| 2026-11-11T08:45:50.662568+00:00 | I1 | ties-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T084549.891735Z-I1-CPU-reference-cc7ada11ec` |
| 2026-11-11T08:45:51.759118+00:00 | I1 | step-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T084550.953332Z-I1-CPU-reference-91b6e6bf9c` |
| 2026-11-11T08:45:52.827384+00:00 | I1 | tiny-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T084552.041427Z-I1-CPU-reference-ceceffeb9c` |
| 2026-11-11T08:48:58.565512+00:00 | I0 | 3个真实NPP C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T084851.244406Z-I0-cuda-probe-78082ffe23`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T084853.669085Z-I0-cuda-probe-120427a506`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T084856.128507Z-I0-cuda-probe-432de8a4ff` |
| 2026-11-11T08:49:33.399497+00:00 | I0 | 3个真实NPP C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T084926.054449Z-I0-cuda-probe-7a8eee2821`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T084928.588119Z-I0-cuda-probe-cc86d96214`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T084931.058992Z-I0-cuda-probe-055d6d8ca2` |
| 2026-11-11T08:51:00.820080+00:00 | I0 | 5个真实NPPPlus C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085051.043912Z-I0-cuda-probe-1ccc191273`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085052.938837Z-I0-cuda-probe-a0d720fa9b`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085054.885899Z-I0-cuda-probe-735ef560a0`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085056.832032Z-I0-cuda-probe-8b9256128c`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085058.761669Z-I0-cuda-probe-83ae10cad4` |
| 2026-11-11T08:51:32.190516+00:00 | I0 | NPP+局部阈值假设在9/10个原图/研究/独立holdout上逐像素一致；方向相同的等值NMS邻居与强阈值分别检查。模型仍属合同调查，不作为整例资格。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-local-threshold-hypothesis/20261111T085131.257598Z-I0-CPU-research-6abd5ffd89` |
| 2026-11-11T08:51:40.249080+00:00 | I0 | NPP scratch全零与0xff预填充在Teapot C1/C3和随机C1上均给出相同输出，排除了本次初始scratch内容假设；失败定位继续保留。 | `migration/reports/image-I0-Canny-native-probes-fill0.json`；`migration/reports/image-I0-Canny-native-probes-fill255.json` |
| 2026-11-11T08:52:35.901074+00:00 | I0 | NPP+局部模型在9/10个case精确一致，低幅随机holdout的2个边界像素仍失败。记录新边界假设：越界方向邻居退回当前像素，另登记3个未用新seed验证；原失败保留，不用放宽误差收口。 | `migration/reports/image-I0-Canny-local-model.json` |
| 2026-11-11T08:52:46.112946+00:00 | I0 | 3个真实NPPPlus C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085239.946691Z-I0-cuda-probe-46bd37756a`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085242.000245Z-I0-cuda-probe-19516908db`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085243.996088Z-I0-cuda-probe-76285e71dd` |
| 2026-11-11T08:53:25.453218+00:00 | I0 | NPP+局部阈值假设在7/13个原图/研究/独立holdout上逐像素一致；方向相同的等值NMS邻居与强阈值分别检查。模型仍属合同调查，不作为整例资格。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-local-threshold-hypothesis/20261111T085324.544203Z-I0-CPU-research-8836b2b407` |
| 2026-11-11T08:54:28.970080+00:00 | I0 | NPP+局部阈值假设在11/13个原图/研究/独立holdout上逐像素一致；方向相同的等值NMS邻居与强阈值分别检查。模型仍属合同调查，不作为整例资格。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-local-threshold-hypothesis/20261111T085428.000144Z-I0-CPU-research-40cf42122f` |
| 2026-11-11T08:54:55.503113+00:00 | I0 | 边界self假设被新holdout否定，拒绝该合同候选并撤回尚未构建的mask实现；仅保留已独立检查的Sobel/L2/NMS共享核心。下一定位点为原生梯度/方向边界中间结果。 | `migration/reports/image-I0-Canny-local-model-boundary-self.json`；`migration/rewrite/image-canny-local-contract.json` |
| 2026-11-11T08:55:03.716960+00:00 | I1 | teapot-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085502.222884Z-I1-rocm-run-17194139c7` |
| 2026-11-11T08:55:05.298327+00:00 | I1 | teapot-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085504.015170Z-I1-rocm-run-e37a1a6af9` |
| 2026-11-11T08:55:06.887873+00:00 | I1 | noise-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085505.621458Z-I1-rocm-run-21e87503b8` |
| 2026-11-11T08:55:08.458776+00:00 | I1 | noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085507.198447Z-I1-rocm-run-0f141c0b18` |
| 2026-11-11T08:55:09.976113+00:00 | I1 | ties-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085508.744080Z-I1-rocm-run-de241b6af9` |
| 2026-11-11T08:55:11.497665+00:00 | I1 | step-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085510.267956Z-I1-rocm-run-2c0c041423` |
| 2026-11-11T08:55:13.068577+00:00 | I1 | tiny-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085511.813391Z-I1-rocm-run-4fdda68b85` |
| 2026-11-11T08:55:14.596635+00:00 | I1 | holdout-weak-step-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085513.377342Z-I1-rocm-run-b86dbdbb51` |
| 2026-11-11T08:55:16.101990+00:00 | I1 | holdout-weak-cross-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085514.891662Z-I1-rocm-run-b288b6e837` |
| 2026-11-11T08:55:17.672141+00:00 | I1 | holdout-weak-diagonal-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085516.409489Z-I1-rocm-run-9658522761` |
| 2026-11-11T08:55:19.176368+00:00 | I1 | holdout-low-noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085517.968524Z-I1-rocm-run-8e18aafac0` |
| 2026-11-11T08:55:20.732538+00:00 | I1 | holdout-mixed-noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085519.474017Z-I1-rocm-run-838a23f3af` |
| 2026-11-11T08:55:22.220208+00:00 | I1 | border-check91203-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085521.010712Z-I1-rocm-run-eabbd72215` |
| 2026-11-11T08:55:23.729998+00:00 | I1 | border-check40519-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085522.516986Z-I1-rocm-run-a0f3cf3db0` |
| 2026-11-11T08:55:25.240335+00:00 | I1 | border-check83914-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085524.025812Z-I1-rocm-run-a46179a9fc` |
| 2026-11-11T08:55:49.288480+00:00 | I0 | 原生NPP Canny合同探针构建失败，保留实际编译日志。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract-build/20261111T085546.207001Z-I0-cuda-build-c0bda10ee8` |
| 2026-11-11T08:56:37.681776+00:00 | I1 | teapot-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085636.788159Z-I1-CPU-reference-76220d0ee0` |
| 2026-11-11T08:56:38.792916+00:00 | I1 | teapot-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085637.964129Z-I1-CPU-reference-3d8080605a` |
| 2026-11-11T08:56:39.881673+00:00 | I1 | noise-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085639.093549Z-I1-CPU-reference-70d1b40227` |
| 2026-11-11T08:56:41.003011+00:00 | I1 | noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085640.222340Z-I1-CPU-reference-b40c7c2d20` |
| 2026-11-11T08:56:42.114292+00:00 | I1 | ties-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085641.302058Z-I1-CPU-reference-0a74842b02` |
| 2026-11-11T08:56:43.197724+00:00 | I1 | step-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085642.419906Z-I1-CPU-reference-edbf8b796a` |
| 2026-11-11T08:56:44.367594+00:00 | I1 | tiny-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085643.540639Z-I1-CPU-reference-4a0b03ee8d` |
| 2026-11-11T08:56:45.436105+00:00 | I1 | holdout-weak-step-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085644.667308Z-I1-CPU-reference-4f940d37f7` |
| 2026-11-11T08:56:45.741463+00:00 | I0 | 3个真实NPPPlus C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085639.148071Z-I0-cuda-probe-e52f83604f`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085641.273841Z-I0-cuda-probe-159b7c3c33`；`migration/reports/evidence/rewrite/I0/Canny-NPPPlus-contract/20261111T085643.322955Z-I0-cuda-probe-d82d447bf3` |
| 2026-11-11T08:56:46.519745+00:00 | I1 | holdout-weak-cross-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085645.740951Z-I1-CPU-reference-bfefa08ee5` |
| 2026-11-11T08:56:47.589916+00:00 | I1 | holdout-weak-diagonal-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085646.823371Z-I1-CPU-reference-a3d317b95a` |
| 2026-11-11T08:56:48.655729+00:00 | I1 | holdout-low-noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085647.890599Z-I1-CPU-reference-7837aee7cf` |
| 2026-11-11T08:56:49.728339+00:00 | I1 | holdout-mixed-noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085648.954200Z-I1-CPU-reference-3e04b9cc2f` |
| 2026-11-11T08:56:50.791657+00:00 | I1 | border-check91203-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085650.028373Z-I1-CPU-reference-bc6f99de91` |
| 2026-11-11T08:56:51.880268+00:00 | I1 | border-check40519-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085651.096211Z-I1-CPU-reference-f66c0decf0` |
| 2026-11-11T08:56:52.958284+00:00 | I1 | border-check83914-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085652.181461Z-I1-CPU-reference-0196a1c903` |
| 2026-11-11T08:57:11.368781+00:00 | I0 | 记录校正：08:31:53事件文字误写7个，所附实际证据为17个；以逐case封存清单为准。后续探针计数已改为实际循环数量。 |  |
| 2026-11-11T08:57:19.482524+00:00 | I1 | teapot-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085717.997392Z-I1-rocm-run-6b29e5764f` |
| 2026-11-11T08:57:21.052255+00:00 | I1 | teapot-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085719.793882Z-I1-rocm-run-b0d41d8df0` |
| 2026-11-11T08:57:22.648193+00:00 | I1 | noise-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085721.379322Z-I1-rocm-run-7e1e4c74fe` |
| 2026-11-11T08:57:24.260623+00:00 | I1 | noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085722.965610Z-I1-rocm-run-4130ae3356` |
| 2026-11-11T08:57:25.839123+00:00 | I1 | ties-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085724.570066Z-I1-rocm-run-77473c8a42` |
| 2026-11-11T08:57:27.352611+00:00 | I1 | step-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085726.143201Z-I1-rocm-run-07ef82ffcf` |
| 2026-11-11T08:57:28.885275+00:00 | I1 | tiny-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085727.641456Z-I1-rocm-run-a1c28c4188` |
| 2026-11-11T08:57:30.469391+00:00 | I1 | holdout-weak-step-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085729.193237Z-I1-rocm-run-2e5cbee4aa` |
| 2026-11-11T08:57:31.985600+00:00 | I1 | holdout-weak-cross-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085730.775118Z-I1-rocm-run-6bd9d788dc` |
| 2026-11-11T08:57:33.508966+00:00 | I1 | holdout-weak-diagonal-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085732.291197Z-I1-rocm-run-7aa6051200` |
| 2026-11-11T08:57:35.003148+00:00 | I1 | holdout-low-noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085733.789052Z-I1-rocm-run-2881ae6aa6` |
| 2026-11-11T08:57:36.507463+00:00 | I1 | holdout-mixed-noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085735.305455Z-I1-rocm-run-aa400ff0a9` |
| 2026-11-11T08:57:38.018256+00:00 | I1 | border-check91203-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085736.805681Z-I1-rocm-run-2304464003` |
| 2026-11-11T08:57:39.556620+00:00 | I1 | border-check40519-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085738.330416Z-I1-rocm-run-bf9d0690ce` |
| 2026-11-11T08:57:41.040379+00:00 | I1 | border-check83914-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T085739.834921Z-I1-rocm-run-b80662bfd1` |
| 2026-11-11T08:58:16.696837+00:00 | I1 | teapot-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085815.810836Z-I1-CPU-reference-6ba3fdbc8c` |
| 2026-11-11T08:58:17.842053+00:00 | I1 | teapot-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085816.985815Z-I1-CPU-reference-ddc4347da6` |
| 2026-11-11T08:58:18.936725+00:00 | I1 | noise-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085818.128137Z-I1-CPU-reference-fe0d870263` |
| 2026-11-11T08:58:20.072424+00:00 | I1 | noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085819.278482Z-I1-CPU-reference-8bc7fea86b` |
| 2026-11-11T08:58:21.178851+00:00 | I1 | ties-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085820.390723Z-I1-CPU-reference-9f3f97a34c` |
| 2026-11-11T08:58:22.300156+00:00 | I1 | step-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085821.495504Z-I1-CPU-reference-4fb478505a` |
| 2026-11-11T08:58:23.401583+00:00 | I1 | tiny-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085822.611971Z-I1-CPU-reference-d4fb64a71f` |
| 2026-11-11T08:58:24.508704+00:00 | I1 | holdout-weak-step-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085823.716322Z-I1-CPU-reference-c714aaabb4` |
| 2026-11-11T08:58:25.603851+00:00 | I1 | holdout-weak-cross-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085824.817839Z-I1-CPU-reference-135dc51ed8` |
| 2026-11-11T08:58:26.681598+00:00 | I1 | holdout-weak-diagonal-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085825.898282Z-I1-CPU-reference-712bb35fd3` |
| 2026-11-11T08:58:27.767615+00:00 | I1 | holdout-low-noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085826.983587Z-I1-CPU-reference-fb9b65a62f` |
| 2026-11-11T08:58:28.839508+00:00 | I1 | holdout-mixed-noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085828.065408Z-I1-CPU-reference-245202ba92` |
| 2026-11-11T08:58:29.918614+00:00 | I1 | border-check91203-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085829.137961Z-I1-CPU-reference-430b416b2f` |
| 2026-11-11T08:58:30.998073+00:00 | I1 | border-check40519-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085830.220868Z-I1-CPU-reference-f590408823` |
| 2026-11-11T08:58:32.075725+00:00 | I1 | border-check83914-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T085831.297358Z-I1-CPU-reference-38d195d4ea` |
| 2026-11-11T09:00:26.154499+00:00 | I0 | 2个真实NPP C1/C3 Canny合同探针已执行；像素语义调查不等于AMD实现通过。 | `migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T090021.462636Z-I0-cuda-probe-38e48eef08`；`migration/reports/evidence/rewrite/I0/Canny-NPP-contract/20261111T090023.864915Z-I0-cuda-probe-47e10747f7` |
| 2026-11-11T09:01:04.099922+00:00 | I1 | 图像基础实现检查点：PASSED；既有资格/记录器回归、证据封存审计、原始源码与支持计数不变、计划镜像一致分别检查。 | `migration/reports/evidence/rewrite/I1/image-foundation-checkpoint/20261111T090019.878251Z-I1-host-validation-61f279a3b5` |
| 2026-11-11T09:01:33.777310+00:00 | I0 | 真实NPP/NPP+外部Sobel API与独立CPU梯度/整数幅度全数组对照：PASSED；明确X符号映射。此项不证明Canny内部NMS/连接阶段。 | `migration/reports/evidence/rewrite/I0/Canny-native-gradient-comparison/20261111T090132.855172Z-I0-CPU-reference-9a32ea8679` |
| 2026-11-11T09:01:35.078661+00:00 | I0 | 12张原始JPEG均已用独立CPU解码并解析SOF/SOS；rocJPEG成功的10张记录全像素maxAbs/MSE/PSNR，失败2张保留原格式与实际返回值。未按观察结果放宽或签发阈值。 | `migration/reports/evidence/rewrite/I0/JPEG-original-CPU-and-rocJPEG-observation/20261111T090134.230859Z-I0-CPU-reference-4be9098b0c` |
| 2026-11-11T09:02:49.847464+00:00 | I0 | JPEG完整像素观察揭示8张自然图maxAbs16–52、PSNR42.47–51.49dB，未满足初始候选统一门槛。需要先分离IDCT/色彩/chroma upsampling，未调整阈值。两张失败图实际均为CPU可解码的SOF2/10-scan progressive。 | `migration/reports/image-I0-JPEG-CPU-observations.json` |
| 2026-11-11T09:02:50.184581+00:00 | I1 | 当前共享阶段代码已在15输入/4,001,684元素上独立CPU逐值一致；原生NPP/NPP+梯度15数组另验通过。阶段检查点文档明确I0/I1未完成、其它阶段未启动与当前缺口；整例支持数不变。 | `migration/reports/image-I0-I1-checkpoint.md`；`migration/reports/image-I1-Canny-stages-validation.json`；`migration/reports/image-I0-native-gradients-validation.json` |
| 2026-11-11T09:09:11.111435+00:00 | I1 | 固定4705868ef独立复核发现validator两项must-fix：跳过非零rc会漏记失败；np.fromfile会忽略int16文件末尾1字节。当前15实际case的只读数值重放仍一致。另发现SDK已存在prefix分支异常未封存；计划补固定case覆盖、精确字节集合/反向检查及SDK验证复用后复审。 | `migration/reports/image-I0-I1-checkpoint.md` |
| 2026-11-11T09:15:55.256725+00:00 | I0 | nvjpeg2000 私有SDK安装/重用：VERIFIED_REUSE；现有prefix必须逐文件匹配，所有失败封存。 | `migration/reports/evidence/rewrite/I0/image-private-nvjpeg2000-SDK/20261111T091554.321290Z-I0-host-download-d912ac8dc9` |
| 2026-11-11T09:15:55.560054+00:00 | I0 | 真实NPP/NPP+外部Sobel API与独立CPU梯度/整数幅度全数组对照：PASSED；明确X符号映射。此项不证明Canny内部NMS/连接阶段。 | `migration/reports/evidence/rewrite/I0/Canny-native-gradient-comparison/20261111T091554.369562Z-I0-CPU-reference-1b2e1da238` |
| 2026-11-11T09:15:57.366020+00:00 | I0 | nppplus 私有SDK安装/重用：VERIFIED_REUSE；现有prefix必须逐文件匹配，所有失败封存。 | `migration/reports/evidence/rewrite/I0/image-private-nppplus-SDK/20261111T091555.559469Z-I0-host-download-1540be21a1` |
| 2026-11-11T09:16:02.472027+00:00 | I1 | teapot-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091600.956454Z-I1-rocm-run-cf573c2128` |
| 2026-11-11T09:16:04.102422+00:00 | I1 | teapot-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091602.781660Z-I1-rocm-run-0f123db918` |
| 2026-11-11T09:16:05.740630+00:00 | I1 | noise-c3：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091604.437447Z-I1-rocm-run-61c82eecdf` |
| 2026-11-11T09:16:07.360119+00:00 | I1 | noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091606.056534Z-I1-rocm-run-d0d7a87766` |
| 2026-11-11T09:16:08.979001+00:00 | I1 | ties-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091607.667091Z-I1-rocm-run-d24fd1b6ef` |
| 2026-11-11T09:16:10.571438+00:00 | I1 | step-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091609.284009Z-I1-rocm-run-61be4a4ffc` |
| 2026-11-11T09:16:12.170673+00:00 | I1 | tiny-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091610.878302Z-I1-rocm-run-1aab260097` |
| 2026-11-11T09:16:13.757038+00:00 | I1 | holdout-weak-step-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091612.465877Z-I1-rocm-run-ac3ad32263` |
| 2026-11-11T09:16:15.363733+00:00 | I1 | holdout-weak-cross-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091614.064107Z-I1-rocm-run-80940bf50f` |
| 2026-11-11T09:16:16.932798+00:00 | I1 | holdout-weak-diagonal-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091615.656002Z-I1-rocm-run-7f516e7335` |
| 2026-11-11T09:16:18.501871+00:00 | I1 | holdout-low-noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091617.220664Z-I1-rocm-run-4a367fb534` |
| 2026-11-11T09:16:20.115778+00:00 | I1 | holdout-mixed-noise-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091618.789577Z-I1-rocm-run-36dd94f447` |
| 2026-11-11T09:16:21.715961+00:00 | I1 | border-check91203-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091620.426897Z-I1-rocm-run-beba604733` |
| 2026-11-11T09:16:23.321408+00:00 | I1 | border-check40519-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091622.025817Z-I1-rocm-run-9262c2c460` |
| 2026-11-11T09:16:24.883512+00:00 | I1 | border-check83914-c1：真实HIP阶段C ABI执行成功，等待独立CPU逐元素检查。 | `migration/reports/evidence/rewrite/I1/Canny-GPU-stages/20261111T091623.608658Z-I1-rocm-run-e64a72a8bb` |
| 2026-11-11T09:17:05.611155+00:00 | I1 | teapot-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091704.722663Z-I1-CPU-reference-73f0be82f0` |
| 2026-11-11T09:17:06.764817+00:00 | I1 | teapot-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091705.902571Z-I1-CPU-reference-3490af453f` |
| 2026-11-11T09:17:07.874759+00:00 | I1 | noise-c3：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091707.060963Z-I1-CPU-reference-8313e7a259` |
| 2026-11-11T09:17:09.060698+00:00 | I1 | noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091708.215774Z-I1-CPU-reference-f307eed640` |
| 2026-11-11T09:17:10.213329+00:00 | I1 | ties-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091709.392010Z-I1-CPU-reference-f1152bc3cf` |
| 2026-11-11T09:17:11.322221+00:00 | I1 | step-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091710.506554Z-I1-CPU-reference-076693129e` |
| 2026-11-11T09:17:12.477119+00:00 | I1 | tiny-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091711.641428Z-I1-CPU-reference-9a1235be18` |
| 2026-11-11T09:17:13.631434+00:00 | I1 | holdout-weak-step-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091712.798017Z-I1-CPU-reference-648f5441b1` |
| 2026-11-11T09:17:14.747225+00:00 | I1 | holdout-weak-cross-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091713.929977Z-I1-CPU-reference-c1fc1e9f9e` |
| 2026-11-11T09:17:15.871917+00:00 | I1 | holdout-weak-diagonal-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091715.063389Z-I1-CPU-reference-2c5c18095c` |
| 2026-11-11T09:17:17.006959+00:00 | I1 | holdout-low-noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091716.189354Z-I1-CPU-reference-a84b87afb8` |
| 2026-11-11T09:17:18.133340+00:00 | I1 | holdout-mixed-noise-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091717.322273Z-I1-CPU-reference-478225baf2` |
| 2026-11-11T09:17:19.272846+00:00 | I1 | border-check91203-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091718.441749Z-I1-CPU-reference-82e8ddd20e` |
| 2026-11-11T09:17:20.395250+00:00 | I1 | border-check40519-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091719.566996Z-I1-CPU-reference-53bde46972` |
| 2026-11-11T09:17:21.526355+00:00 | I1 | border-check83914-c1：Sobel dx/dy、整数L2、NMS四个完整数组与独立CPU逐元素完全一致；此结论仅覆盖阶段。 | `migration/reports/evidence/rewrite/I1/Canny-stages-independent-CPU/20261111T091720.716158Z-I1-CPU-reference-b0133c204b` |
| 2026-11-11T09:18:05.958984+00:00 | I1 | 图像基础实现检查点：PASSED；既有资格/记录器回归、证据封存审计、原始源码与支持计数不变、计划镜像一致分别检查。 | `migration/reports/evidence/rewrite/I1/image-foundation-checkpoint/20261111T091721.874780Z-I1-host-validation-df57386e26` |
| 2026-11-11T09:18:24.226917+00:00 | I1 | 审查问题已修：固定15 stage和5 native case覆盖，失败rc不跳过/严格非零退出，逐文件精确字节/集合/hash/输入检查。16项正反测试全部通过；重新构建15 GPU/CPU阶段及15 native梯度数组严格复验通过。SDK两包已实际逐文件验证复用，所有失败分支可封存。 | `migration/reports/image-checkpoint-validation.json`；`migration/reports/image-review-4705868ef.json`；`migration/reports/image-I1-Canny-stages-validation.json` |

<!-- IMAGE_EXECUTION:END -->
