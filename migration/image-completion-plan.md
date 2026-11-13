# CUDA Samples on ROCm：剩余图像模块完整实现计划

制定日期：2026-11-13。计划状态：**IN_PROGRESS**；已按用户指令开始实施，整例资格仍按完整合同签发。

基线提交：`672f17cc9a030078569b89ca9a26081db2bb0d5f`，实现分支 `rocm`。本计划细化原 I0–I9 的剩余工作，以 IMG-00–IMG-10 编排后续实施；不重置旧阶段、不替换稳定样例 ID、不删除历史失败记录。

工作区主文档：`doc/cuda_samples_on_rocm_image_completion_plan.md`；仓库发布副本：`migration/image-completion-plan.md`。两份内容保持一致。前序范围和历史实验继续见[原图像计划](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/image-libraries-plan.md)与[实时实验记录](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-libraries-progress.md)。

## 1. 交付目标与当前事实

交付目标是仓库 NPP、NPP+、nvJPEG、nvJPEG2000 的 **26 个原始样例入口**在锁定 AMD 平台完成所需功能，并通过功能等价验收。不是复刻四个 NVIDIA 商业 SDK 的全部 API，也不承诺 NVIDIA 专用硬件标识或压缩码流字节一致。

| 模块 | 已整例通过 | PARTIAL | FAILED | 本轮新增整例目标 |
| --- | ---: | ---: | ---: | ---: |
| NPP | 8/9 | 1 | 0 | 1 |
| NPP+ | 5/6 | 1 | 0 | 1 |
| nvJPEG | 0/7 | 7 | 0 | 7 |
| nvJPEG2000 | 0/4 | 0 | 4 | 4 |
| 合计 | **13/26** | **9** | **4** | **13** |

全项目基线为 252 PASSED、24 PARTIAL、363 FAILED，639 个入口、131 个已验收功能族。若这 13 项全部通过且既有资格没有撤回，项目条件目标为 **265 PASSED、15 PARTIAL、359 FAILED**；功能族数量按实际功能重新去重，不机械加 13。

当前 I1/I2 已在各自声明范围完成；I0/I3/I4/I5/I6 仍进行中，I7/I8/I9 尚未完成。必须准确区分下列成果和欠项：

| 已有成果 | 可以直接复用 | 尚不能据此宣称完成 |
| --- | --- | --- |
| NPP/NPP+ 13 项资格 | 已验 Canny、CCL、contour、distance、flood fill、Hough、NCC、benchmark 的源码、输入和证明 | 新图像计划要求的原始文件流程仍须总复核；特别是旧 NPP EDT 的完整 RAW 入口 |
| Watershed 两入口 | 8 张原图、22 件产品及 CPU/GPU 对照、原生失败证据 | 当前分割最低一致率 71.71%、NPP+ 边界最低 43.53%，不能当作已接受的微小差异 |
| JPEG 解码 | 10 张 baseline 的 rocJPEG 路径；两张 progressive 的 HIP IDCT/色度/RGB | progressive 的熵解码和系数装配仍在 CPU；`cpu_fallback=0` 不等于全过程 GPU |
| JPEG 编码 | baseline 和多实例 `-f` 的 GPU 色彩/FDCT/量化/Huffman/打包；CPU DHT 设计 | progressive 编码、源量化表/APP/COM 继承、完整异步调度和原生 CUDA 对照仍有缺口 |
| 并行 JPEG prefix | 12 组逐元素正确性、GPU trace、6 组隔离计时 | 尚未接入生产路径；不能把单阶段速度比写成整图速度比 |
| JPEG2000 | 主头解析、MQ 算术解码、局部单层 5/3/RCT、CPU/native 原图参考 | 真实 MQ 实验由 CPU 提供 context；缺 GPU EBCOT 和完整码块系数恢复；尚无完整 GPU 图像编解码链 |

事实来源：[逐例主表](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/samples.yaml)、[Watershed](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-watershed.md)、[progressive JPEG](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-progressive.md)、[JPEG encoder](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-jpeg-encoder.md)、[JPEG prefix](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-jpeg-prefix.md)、[JPEG2000 I6](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/image-jpeg2000-I6.md)。本表是上述提交的静态快照，后续结果记入第 10 节和实时主表。

## 2. 支持边界、选型和合理差异

继续执行已获用户认可的[功能等价策略](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/rewrite/image-acceptance-policy.json)：EXACT、NUMERICAL_TOLERANCE、ALGORITHM_VARIANT 分别签发。完整 GPU 执行、合法模式、数据表示、文件/批次完整性和错误行为是硬要求；阈值在候选实现和保留测试集验收前冻结。

| 能力 | 生产路线 | CPU 可以承担 | 必须在 GPU/媒体引擎完成 |
| --- | --- | --- | --- |
| NPP/NPP+ 算法 | 已验项目 HIP 共享核心；Watershed 补分桶浸没/平台区规则 | IO、参数、独立参考 | 图像计算、连通/区域归属、标签和边界生成 |
| JPEG 解码 | rocJPEG 覆盖的格式优先；其余使用项目 HIP decoder | 容器/marker/scan 描述解析、文件和调度 | Huffman 熵解码、progressive 系数累计、反量化/IDCT/颜色输出 |
| JPEG 编码 | 项目 HIP baseline/progressive encoder | 标准头部、APP/COM、基于 GPU 直方图的小型 DHT 设计 | 色彩/采样、FDCT/量化、熵编码、码流位置计算与打包 |
| JPEG2000 | 项目 HIP Part 1/HT codec；固定 OpenJPEG/OpenJPH 作为参考来源 | 容器和 packet 描述解析/组装、IO 和调度 | Tier1/MQ/HT、系数与变换、像素输出；率失真选择的执行归属单独记录 |

OpenJPEG 参考当前固定为 v2.5.4 commit `6c4a29b00211eb0430fa0e5e890f1ce5c80f409f`。新增 OpenJPH 或其它参考必须先固定源码、许可证、构建及二进制哈希，再验证所需模式；本计划不假设某个版本已支持 NLT3。如移植其算法，保留许可，CPU 参考程序与 HIP 生产路径分别构建，并用原生 NVIDIA 或第二独立实现交叉检查。

以下平台差异必须明示：NVIDIA 专用硬件 engine、专有二进制和设备编号无法在 AMD 上原样提供。AUTO/软件后端可映射到实际 AMD 能力，映射及语义写入合同；强制要求不存在的硬件时返回能力错误。若原入口的必需合法模式因此未满足，该入口保留 PARTIAL；只有明确属于平台差异且已被功能等价合同覆盖的项目才可按该合同验收。不能靠关闭源码条件分支、忽略返回码或放宽像素误差获得 26/26。

无损 JPEG2000 的规定表示必须精确；有损编解码允许冻结的误差预算和不同合法码流。Watershed 必须检查区域拓扑与局部边界，不能只取全图相似度。采用有文档依据的算法变体时，单列与厂商差异，仍需证明原样例全部功能和用途成立。

## 3. 实施顺序、依赖与里程碑

默认顺序如下；阶段可在不依赖失败项的部分继续推进，未解决项仍挂在原阶段。单次实验失败后先定位、修复、重跑；无需为正常实现选择反复申请用户确认。

| 阶段 | 对应原阶段 | 可交付结果 | 依赖 | 新增整例上限 | 累计条件目标 |
| --- | --- | --- | --- | ---: | ---: |
| IMG-00 | I0 | 完整缺口、输入/CLI/模式/依赖清单和验收合同 | 当前快照 | 0 | 13/26 |
| IMG-01 | I5 | 完整多实例 JPEG 编码器及生产 prefix/调度 | 00 | 1 | 14/26 |
| IMG-02 | I3 | NPP/NPP+ Watershed 两原入口 | 00 | 2 | 16/26 |
| IMG-03 | I4 | GPU JPEG 熵解码及 progressive 完整像素链 | 00 | 0 | 16/26 |
| IMG-04 | I4 | JPEG 四个解码入口，含 Python/ROI/多实例 | 03 | 4 | 20/26 |
| IMG-05 | I5 | progressive 编码、源表/metadata、两重编码入口 | 01、03、04 | 2 | 22/26 |
| IMG-06 | I6 | 真实 JPEG2000 Part 1 GPU 解码全链 | 00 | 0 | 22/26 |
| IMG-07 | I7 | Part 1 GPU 编码全链及率/质量控制 | 06 的系数和变换合同 | 0 | 22/26 |
| IMG-08 | I7/I8 | HTJ2K、NLT3、浮点/码块等必要扩展 | 06、07 | 0 | 22/26 |
| IMG-09 | I8 | JPEG2000 四个原入口复合验收 | 06、07、08 | 4 | 26/26 |
| IMG-10 | I9 | 后端整理、26 项冷构建/回归、文档和交付 | 所有相关资格 | 0 | 保持 26/26 |

以上数量是依赖全部满足后的目标，不是预记支持数。JPEG2000 可先在独立实验中运行 Part 1 原图；含 HT/NLT3 等欠项的原例不能提前升级。若 Watershed 语义调查卡住，继续 JPEG 的独立任务，不删除两项欠项或伪造最终累计值。

## 4. 各阶段工作包与完成门槛

### IMG-00：冻结剩余合同及依赖

- [ ] 从 26 个原始源码、头文件、CMake/Python 测试重新列举合法 CLI、默认值、输出文件、宏条件、后端选择和错误行为。登记条件是否在冻结构建面中生效及其理由。
- [ ] 给 13 个欠项建立稳定 ID → API/模式 → 实现文件 → fixture → CPU/native 参考 → 资格报告映射；同时审计已通过 13 项是否满足新计划的完整文件流程，不能假定旧数学资格覆盖全部原 CLI。
- [ ] 显式补入 progressive CPU 熵阶段、JPEG2000 缺完整 GPU codec 等算法欠项，避免主表只剩“待复审”或旧 `nvjpeg2k.h` 缺失日志。
- [ ] 核查 5090×2 环境、CUDA/NPP/NPP+/nvJPEG/nvJPEG2000 实际加载版本；定位多实例 JPEG encoder 的原生构建失败，先修复基线构建或记录具体 SDK/API 原因。
- [ ] 设计开发集和保留验收集；固定 seed、文件长度、SHA256、像素/结构门槛、性能测量口径、反向检查。已有原图全部保留，新增输入覆盖旧原图未覆盖的有效模式。
- [ ] 对构建、实例生命周期、共享头文件依赖建立映射；记录新核心变更时必须重跑哪些入口。拟落文件 `migration/rewrite/image-completion-contracts.json` 和逐入口合同，不在计划阶段伪造执行结果。

完成门槛：26 个 ID 全覆盖、13 个欠项无漏项；每个必需模式有实现路线与验收输入来源；未具备参考的模式有独立参考补齐任务。输出报告 `migration/reports/image-completion-contracts.md`。

### IMG-01：把已有 GPU JPEG encoder 收口为完整入口

- [ ] 给当前 `jpeg_full_gpu.hpp`、`jpeg_opt_full_gpu.hpp` 接入经验证的 `jpeg_parallel_prefix.hpp`；按 block 数/字节数分别选择路径，阈值由冻结测量确定，不能只使用 65536 元素的速度比外推。
- [ ] 处理总 bit 数、stuffed byte 数、size_t 分配乘积和超长 block 的溢出；支持合同内合法大图，超出实际能力时在分配/写文件前明确拒绝。验证恰好阈值上下、全 `0xff`、无 `0xff`、零长度错误、计数跨越边界。
- [ ] 以实例/slot 拥有 pinned host buffer、可复用 device workspace、stream/event；实现 prepare→H2D→encode→D2H→write 生命周期，异常和尾 batch 不能泄漏、串用或覆盖缓冲区。
- [ ] 保留原始自然排序、图片数/状态数/线程数、重复运行、输出命名、Q/采样/优化表、自动标定与后端语义；针对原自动选择的实际行为建立独立检查。
- [ ] 去除一次性 CPU RGB 往返中的可避免复制，按实际需要拆分提交与等待；trace 验证多 slot 的有效事件依赖及可观察重叠，不能仅凭两个 stream ID 认定流水线成立。
- [ ] 重跑原七组 CLI/16 产品、优化 Huffman 四组/码表边界，以及受核心改动影响的两个 resize 入口七组 CLI/68 产品；补原入口的大图、混合尺寸、异常输入和反复复用。更新 trace 检查以反映实际调度路径，禁止用固定旧 kernel 数掩盖分支未执行。
- [ ] 同输入与独立 CPU 跨解码、5090 原始入口比较；记录端到端吞吐/延迟/峰值内存和 GPU 阶段用时。JPEG 字节流无需等同，解码表示/模式/量化表须满足合同。

完成门槛：优化与标准表两条路径完整、无 CPU 熵编码、完整实例调度和所有必需 CLI 通过；冷检出和资格复核通过后，才升级 `nvJPEGEncMultipleInstances.cpp`。CPU DHT 表设计按允许的主机步骤明确列出。

### IMG-02：修正 Watershed 算法语义

- [ ] 先用常量平台、双盆地、鞍点、阶梯、等高连接、单行/单列、边缘种子等小输入，对 5090 原生输出定位连通性、平台分配、tie 和 boundary/contrasting 模式；保留当前候选失败，避免重复尝试无依据的优先队列变体。
- [ ] 在独立 CPU 规格模型确定规则后，实现 GPU 分桶浸没、平台连通块处理、区域传播、标签压紧和两种边界输出。检查局部区域、不变像素、ROI/pitch/padding，不能仅核总像素数。
- [ ] 标签编号可按预冻结映射规范化；分区和边界分别验证。对已有原图之外的保留输入使用预定门槛，不能见到结果后提高容差。
- [ ] 重跑 NPP 5 原图/10 产品、NPP+ 3 原图/12 产品、全部输出模式及缺图/非法参数；覆盖真实 GPU trace、变化输入和固定提交重建。

完成门槛：两原入口全部功能满足 EXACT 或已论证的 ALGORITHM_VARIANT 合同；71.71%/43.53% 的旧差异不能直接算作可接受。若新候选仍不满足，阶段保留未完成并记录差异定位与下一实验。

### IMG-03：完整 GPU JPEG 解码核心

- [ ] 明确解析器与熵执行边界：CPU 可产生 scan/restart 描述；生产 GPU 的 context/系数不能从 CPU 解码器提前算好。
- [ ] 实现 Huffman 表、bit reader、byte stuffing、restart、DC predictor；补 AMD 硬件未覆盖且原入口要求的 baseline 软件解码路径。
- [ ] 实现 progressive DC/AC first scan、successive approximation/refinement、EOB run、restart reset、分量/scan 依赖和共享系数累计；一个错误 scan 不得留下可误用输出。
- [ ] 接入已验 HIP 反量化/IDCT/上采样/色彩路径，保留 device 输出供后处理复用；在调用路径和阶段记录中证明生产熵解码不再调用 CPU libjpeg。
- [ ] 用独立 CPU 生成或读取的固定系数与原生 nvJPEG 图像结果两级检查；覆盖原两张 progressive、灰度/彩色、各合法采样、奇数尺寸、不同 scan 脚本及损坏/截断/缺表输入。

完成门槛：原始 12 张图及冻结扩展矩阵全部通过，生产熵阶段在 GPU/媒体引擎；系数级、最终像素级和实际 kernel/device 证据齐全。本阶段是组件完成，不直接增加入口通过数。

### IMG-04：JPEG 四个解码入口

- [ ] 在统一 backend capabilities 中记录输入 coding process、采样、输出格式、ROI/scale 和实际硬件支持；实现原始 backend 枚举到 AMD 的有文档映射。
- [ ] 补解耦 parse/transfer/decode 状态与异步生命周期、真实 batch/多实例自动调度、错误 slot 回收、输入改变后重复调用和 batch 尾部。
- [ ] 完整保留 RGB/BGR、planar/interleaved、YUV/Y、NV12/YUY2 等原入口有效格式与 scale/ROI 组合；逐组合按原始合同确定有效域。合法组合不得因适配器简化被排除。
- [ ] 运行三个 C++ 解码入口和原始 Python 测试；检查 Torch/Python stride、设备指针、CPU/设备拷贝归属、结果文件与命名，不以 C++ probe 代替 Python 原入口。
- [ ] 重跑受共享 decoder 影响的两个 resize 入口，更新所有相关依赖哈希和资格；补原生 CUDA 同输入入口验证及固定提交冷检出。

完成门槛：第 5 节列出的四个解码样例各自全部必需 case 通过。先前记录为“只缺冷复审”的入口仍须补 IMG-03 的 GPU 熵阶段，不沿用遗漏的欠项列表。

### IMG-05：完整重编码、progressive 输出与元数据

- [ ] 实现 GPU progressive JPEG encoding：scan 顺序、DC/AC first/refinement、EOB run、restart 和合法 marker；CPU 仅编排 scan/头部及允许的 DHT 表设计。
- [ ] 源 DQT、采样、编码模式、APP/COM 和原样例复制流程逐项处理；明确 CLI quality 与源表继承的优先级。尺寸变化相关字段按原样例规则更新，不能无条件复制失效 metadata。
- [ ] 将 resize/watermark 的 device 图像直接接到 encoder，验证 resize 像素中心、水印位置/alpha、源模式/表和全部产品文件。
- [ ] 对 CPU/native baseline/progressive 码流双向跨解码；使用结构解析确认确实输出请求模式，防止 progressive 输入被静默降为 baseline。
- [ ] 完整运行两原入口已有 14 组 CLI/68 产品及新增 progressive/metadata/参数交互矩阵，做局部水印/ROI检查和端到端性能记录。

完成门槛：`Image-Resize` 与 `Image-Resize-WaterMark` 原始有效模式全部满足，相关 decoder/encoder 资格与当前源码一致，固定提交复核完成；累计条件目标 22/26。

### IMG-06：JPEG2000 Part 1 完整 GPU 解码

- [ ] 从现有 JP2/J2K 主头扩展到 tile-part、packet header、tag tree、layer/resolution/precinct/codeblock 描述和有界 payload；只支持原样例实际要求的 progression 范围，但必须逐一核对并登记。
- [ ] GPU 自行生成 EBCOT 邻域 context，实现 significance propagation、magnitude refinement、cleanup、符号恢复、raw bypass、终止/重启和原码流所需 coding style；并行粒度从独立码块开始。
- [ ] 将真实码块输出系数与独立 CPU/原生结果核对，逐步从单码块→多码块→完整 tile→原始 2K/4K 图；停止依赖 CPU 捕获的 context 序列作为生产输入。
- [ ] 把当前小尺寸、单层、偶相位 5/3 原型扩展为多级、大尺寸、奇数原点/边界延拓；实现 9/7、反量化、RCT/ICT、符号/位深/分量采样。
- [ ] 接通 packet→GPU tier1→系数→变换→像素链；保留全阶段 descriptor/系数/像素核对和 peak memory，检查错误 packet、truncation 及无效尺寸不产生伪成功。

完成门槛：真实完整原始 JP2/J2K 的无损表示精确、有损达到预冻结标准；原始整图 decode 已能在 GPU 计算路径完成。只覆盖 Part 1 时依然不得签发含 HT/NLT3 欠项的原始入口。

### IMG-07：JPEG2000 Part 1 编码器

- [ ] 实现正向 RCT/ICT、5/3/9/7、量化、bitplane/context、MQ/EBCOT coding pass；保留真实符号/位深、灰度/多分量、非整码块边界。
- [ ] 由编码 pass 统计建立率失真/截断选择，分别实现原样例的 Q-factor、quantization、target-PSNR 等语义，不能将不同参数都映射成同一个任意 scale。
- [ ] 构造合法 packet、tile-part 和 J2K/JP2 容器；header 与实际编码模式、层数、分辨率和码块布局一致。
- [ ] AMD encode→独立 CPU/native decode，以及 CPU/native encode→AMD decode；不能只做项目 encoder 与项目 decoder 的自洽往返。

完成门槛：Part 1 无损和有损全链可用，率/质量结果可解释，真实输入和参数矩阵通过；对应 encoder 仍等待 HT/NLT3 和原入口整体验收。

### IMG-08：HTJ2K、NLT3 与扩展模式

- [ ] 先锁定并实测独立 HT/NLT3 参考能力；缺某种 CPU oracle 时建立标准向量及原生 CUDA 对照，不以“库支持 JPEG2000”推断它支持该扩展。
- [ ] 实现原样例实际要求的 HT 码块 encode/decode 及相关 pass；覆盖 `-ht` 和 `-cblk` 的有效组合，包括 128×32 等源码路径，核查模式 header 与实际 bitstream 一致。
- [ ] 实现 NLT type 3 的标准表示变换/逆变换，核验 FP16/FP32/PFM、位深/符号、字节序/行方向、±0、有限极值以及标准有效域内的特殊值。FP16 按原例转换后的 half 表示比较，不把 FP32→FP16 量化差算成无损解码错误。
- [ ] 覆盖 `-I`、YUV precision 1–16、resolution/LRCP 和实际 API 允许的组合；非法组合有明确错误。不能通过降低 SDK 或关闭 NLT3 宏去掉必需功能。

完成门槛：每个原源码生效分支都有真实 AMD 执行及独立校验；存在实际参考/硬件阻塞时保持具体模式未完成，不宣布四入口齐备。

### IMG-09：JPEG2000 四个完整入口

- [ ] 普通 decoder：全部原 CLI、batch、输出类型和文件；调用链只使用已验证后端。
- [ ] Tile/Partial：decode area、跨 tile ROI、分量坐标和 pitch；输出与独立完整解码裁剪一致，同时用调度/trace证明只处理必要 tile/codeblock，不能只解全图后裁剪。
- [ ] Pipelined：独立 slot/pinned/device workspace、parse/H2D/GPU/D2H 事件依赖、尾 batch、错误 slot、并发实例、变化输入重放和实际流水线重叠。
- [ ] Encoder：BMP/YUV/PFM、classic/HT、码块/质量/可逆/浮点全部有效组合及真实文件产物；跨解码检查图像和编码参数。
- [ ] 四个原始 C++ 程序按同输入在 AMD、独立 CPU 和 5090 完整执行，逐例绑定资格、设备/SDK/二进制/输入身份；重跑正常/错误/边界流程及冷构建。

完成门槛：四入口各自全合同通过后逐个发布；临时组件、单图无损 demo 或局部 CLI 通过不能替代全合同。累计条件目标 26/26。

### IMG-10：后端整理、全量回归与交付

- [ ] 每阶段只在必要位置抽取公共资源/图像描述接口；最后集中整理已验 backend，保留薄兼容层以维持原入口路径。统一 CMake module target、依赖/许可证和安装说明；不提前为规划目录搬迁所有已有代码。
- [ ] 消除两个 JPEG encoder 重复实现，复用同一 transform/entropy/packing 核心；改变源码依赖闭包后重新验收所有使用者，保留历史证明而不沿用已失效资格。
- [ ] 26 原始入口全部回归，包括既有 13 项；特别补核旧 NPP EDT 的原六 RAW 文件流程、NCC 完整 CLI，以及 Python、benchmark、全部文件产物。
- [ ] 从明确 commit 冷检出、按锁定依赖重建，不能依赖上次 artifacts 中的二进制；重建能从 seed/输入 SHA 恢复大 fixture，执行负向验收与变化重放。
- [ ] 独立复审功能、数值 oracle、资源/stream 生命周期和报告结论；修复后重新签发受影响资格。代码评审与运行证明分别记录。
- [ ] 运行全项目源码身份/资格/日志检查；更新主表、算子表、模块页和支持日志。首页仅保留整体支持情况及详细文档入口。

完成门槛：26/26 当前完整资格、全部必须 case 通过、无陈旧源码证明、无未封存实验；执行日志可从新检出重建。Linux/gfx1201/ROCm10.1 的图像范围完成不等于 639 入口全项目完成，也不自动签发 wave64、Windows 或未测平台。

## 5. 十三个欠项与负责阶段

| 稳定 sample ID | 当前状态 | 核心依赖 | 最终验收阶段 |
| --- | --- | --- | --- |
| `nvJPEG/nvJPEG-Encoder-MultipleInstances::nvJPEGEncMultipleInstances.cpp` | PARTIAL | encoder/prefix/资源调度/native baseline | IMG-01 |
| `NPP/watershedSegmentation::watershedSegmentation.cpp` | PARTIAL | 区域/平台/边界语义 | IMG-02 |
| `NPP+/watershedSegmentation::watershedSegmentationNPPPlus.cpp` | PARTIAL | 区域/平台/边界语义 | IMG-02 |
| `nvJPEG/nvJPEG-Decoder::nvjpegDecoder.cpp` | PARTIAL | GPU entropy/完整文件入口 | IMG-03→04 |
| `nvJPEG/nvJPEG-Decoder/tests::test_decoder.py` | PARTIAL | GPU entropy/Python真实调用 | IMG-03→04 |
| `nvJPEG/nvJPEG-Decoder-Backend-ROI::nvJPEGROIDecode.cpp` | PARTIAL | 后端/ROI/解耦流水线 | IMG-03→04 |
| `nvJPEG/nvJPEG-Decoder-MultipleInstances::nvJPEGDecMultipleInstances.cpp` | PARTIAL | GPU entropy/原自动调度 | IMG-03→04 |
| `nvJPEG/Image-Resize::imageResize.cpp` | PARTIAL | decode/progressive encode/源表及metadata | IMG-01、03、04→05 |
| `nvJPEG/Image-Resize-WaterMark::imageResizeWatermark.cpp` | PARTIAL | 上述能力及水印局部语义 | IMG-01、03、04→05 |
| `nvJPEG2000/nvJPEG2000-Decoder::nvjpeg2k_decode.cpp` | FAILED | Part1/HT/NLT3完整解码 | IMG-06、08→09 |
| `nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial::nvjpeg2k_decode_tile_partial.cpp` | FAILED | 完整解码/实际tile和ROI调度 | IMG-06、08→09 |
| `nvJPEG2000/nvJPEG2000-Decoder-Pipelined::nvjpeg2k_dec_pipelined.cpp` | FAILED | 完整解码/真实多slot流水线 | IMG-06、08→09 |
| `nvJPEG2000/nvJPEG2000-Encoder::nvjpeg2k_encode.cpp` | FAILED | Part1/HT/NLT3编码和质量控制 | IMG-07、08→09 |

## 6. 统一验收矩阵

每个入口在实施前固定完整 case 清单，不在本计划中猜测最终输入数量。最低应覆盖以下维度，并检查所有原样例承诺的有效交叉组合；无效组合独立列负例。

| 维度 | 必须证明 |
| --- | --- |
| 数值与表示 | 无损表示精确；有损逐图/逐通道门槛；label规范化后分区和边界；量化/采样/位深/符号/输出模式正确 |
| 输入规模 | 全部原图，奇数尺寸、单行列、tile/MCU边界、小图、大图和混合尺寸；最大合法尺寸的索引/内存能力 |
| 数据完整性 | 文件长度/集合/命名、全部batch结果、ROI外/padding sentinel、完整dtype、metadata关联 |
| 运行路径 | 实际GPU/媒体引擎、生产entropy执行归属、非空trace、真实stream/event依赖、变化输入重放 |
| 负向输入 | 截断/损坏码流、非法mode/参数、缺表、长度溢出、缺图、资源失败；错误退出且无伪成功产品 |
| 验证器反向检查 | 缺/重复case、错SHA、尾字节、错通道/ROI/质量、陈旧源码、错设备、丢batch都应拒绝 |
| 性能 | 同输入/模式/质量、GPU event与端到端计时分别记录；预热、重复、统计分布、峰值内存；不以单kernel加速代替整图结论 |

AMD 使用父工作区锁定的 ROCm10.1 launcher、gfx1201 设备策略；例行优先物理 GPU0/1，物理 GPU3 禁止计算。实际容器、HIP/ROCm版本、PCI 和占用通过现有 guard/snapshot 记录。CUDA 使用获准的 5090×2，明确实际卡号；CPU oracle 在独立参考环境运行。具体 launcher 的可见设备编号以 guard 返回的物理映射为准。

原生 CUDA 不可用时记录 `native_baseline_status`、失败命令和缺少模式；兼容数学参考与原始 vendor 入口分别标注。若该对照属于冻结必需门槛，缺失时不得签发整例资格。

## 7. 实验记录、主表与发布顺序

每次实验使用现有 `tools/moat/experiment.py`。最少记录 `experiment_id`、阶段/样例/case ID、假设、父实验、源码/二进制/SDK/环境/输入 SHA、完整命令、stdout/stderr、返回码、实际设备、CPU/native/GPU产物、比较模式、阈值/实测值、性能测量范围、失败原因及下一动作。较大产物记录本地位置、哈希和重建办法；失败、超时、中断和失败候选同样封存。

每完成一个实现步骤或实验，按以下顺序处理：

1. 封存本次证据与失败原因，更新 `migration/reports/rewrite-experiments.jsonl` 和阶段报告。
2. 通过 `tools/moat/image_progress.py` 写回原 I0–I9 记录，消息前缀标明 IMG 编号；同步本计划第 10 节状态/证据，工作区 `doc` 与仓库副本保持一致。示例：`python3 tools/moat/image_progress.py --phase I5 --message 'IMG-01 …' --evidence <报告路径> <实验路径>`，多证据在同一参数后列出。
3. 组件成功只更新组件报告。完整入口的所有门槛、复审、固定提交证据通过后，先将不可变资格提交 Git，再由 publisher 校验身份后更新 `migration/samples.yaml`；失败或缺模式继续 PARTIAL/FAILED。
4. 重新生成主表、模块 README、逐例页、算子映射和 `migration/reports/support-log-index.md`；新计划链接放在详细支持文档中，首页不加入开发批次流水账。
5. 对源码变化完成受影响回归，执行项目必需检查；验证通过后提交并推送用户 fork 的 `rocm` 分支，用 `tools/moat/control.py advance-head` 更新 MOAT 控制提交。图像批次完成不能清空其它 owed surface。

阶段报告建议路径 `migration/reports/image-completion-IMG-XX.md`；沿用现有细分报告作为证据，不复制或改写封存目录。当前资格状态仅由 catalog 和对应证明决定，不能用计划中的 checkbox 直接改变支持数。

每个源码交付点使用现有工具按依赖顺序：

```text
tools/moat/image_reconcile_plan.py
tools/migration/render.py
tools/migration/seal_sources.py
tools/migration/final_validate.py
tools/moat/audit.py
tools/moat/selected_proofs.py
```

先提交新资格、后发布 catalog 的步骤仍不可省略。纯计划文档修改只检查覆盖、链接、镜像和 diff，不运行 GPU 或把文档检查记成算法通过。

## 8. 工作量与风险调整

这是基于当前缺口的新工程量估计，按熟悉图像编解码和 HIP 的工程人员计；不是 agent 运行时长、GPU 时间或交付日期。原计划总量 32–61 人周不等于现在还需要同样工作量，也不能按 13/26 样例比例直接减半。

| 工作 | 剩余粗估人周 |
| --- | ---: |
| IMG-00 合同/基线盘点 | 0.2–0.4 |
| IMG-01 JPEG encoder生产集成和实例调度 | 1–2 |
| IMG-02 Watershed | 1–3 |
| IMG-03 GPU JPEG entropy/progressive decode | 2–4 |
| IMG-04 四个decode入口 | 1–2 |
| IMG-05 progressive encode与两重编码入口 | 2–4 |
| IMG-06 JPEG2000 Part1 decode | 3–6 |
| IMG-07 JPEG2000 Part1 encode | 3–5 |
| IMG-08 HTJ2K/NLT3/扩展 | 4–8 |
| IMG-09 JPEG2000四入口 | 2–4 |
| IMG-10 整理、回归和交付 | 1–2 |
| 合计 | **约20–40人周，另含前置盘点** |

主要不确定性是 Watershed 未公开语义、GPU progressive refinement、JPEG2000 HT/NLT3 和原生参考能力。IMG-00 结束以及首次完整 2K JPEG2000 GPU 解码后分别重估；任一新模式需要额外算法时写出增量，不能靠减少样例模式维持估算。当前没有新的计算/SDK外部阻塞的完成证明，未核实项仍应按计划逐项核实。

## 9. 最终完成判据

- [ ] 26 个原始入口按冻结功能等价合同整例通过；所有源码必需条件分支有明确结果，没有隐含 CPU 熵回退或不执行的 GPU 路径。
- [ ] AMD/独立 CPU/原始 CUDA 证据覆盖所要求的模式；合理差异逐项有配置、阈值与实测，原有失败留档。
- [ ] 已通过 13 项参与受影响回归和完整原例流程复核；新提交资格与当前依赖源码一致。
- [ ] 从提交冷检出可重建依赖、fixture 和所有验证；资源/异步/错误路径/多实例语义通过。
- [ ] 主表、算子支持表、模块页、计划与详细日志一致；性能报告区分组件和端到端，无未经测量的 NVIDIA 对等性能结论。
- [ ] 用户 fork 交付完成，工作区干净；图像范围完成单独标注，未验证平台和其它模块欠项保持原状态。

若存在无法实现且未被功能等价合同覆盖的必需硬件/模式，必须保留具体缺口并说明原因，目标仍未达成，不能为了填写完成而删掉该合同。

## 10. 执行状态与接续点

以下是本计划的工作包状态；已有组件成果见第 1 节，不能据此把新工作包标为完成。

| 阶段 | 当前状态 | 本阶段最新证据/接续点 |
| --- | --- | --- |
| IMG-00 | IN_PROGRESS | 最新步骤和证据见下方实时记录 |
| IMG-01 | IN_PROGRESS | 最新步骤和证据见下方实时记录 |
| IMG-02 | PLANNED | 已有两入口及失败比较；下一步平台/tie/边界语义定位 |
| IMG-03 | PLANNED | 已有GPU像素阶段；下一步GPU entropy系数链 |
| IMG-04 | PLANNED | 等待03与原backend/pipeline/调度补齐 |
| IMG-05 | PLANNED | baseline已可运行；下一步progressive模式/源表metadata |
| IMG-06 | PLANNED | 已有MQ/5/3组件；下一步真实码块context和完整系数 |
| IMG-07 | PLANNED | 待Part1编码链 |
| IMG-08 | PLANNED | 待HT/NLT3参考能力与实现 |
| IMG-09 | PLANNED | 待完整codec、tile/pipeline和四原入口 |
| IMG-10 | PLANNED | 各阶段保留回归证据，最终冷检出收口 |

| 日期 | 更新 | 支持计数变化 |
| --- | --- | --- |
| 2026-11-13 | 基于 `672f17cc9` 核对现状、设计全部后续工作及验收依赖；仅文档交付 | 无：图像13/9/4，全项目252/24/363 |

<!-- IMAGE_COMPLETION:START -->

### 实时实施记录

| 时间（UTC） | 阶段 | 状态 | 实施结果 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-11-13T02:36:39.655382+00:00 | IMG-00 | IN_PROGRESS | 开始执行：已核对9a7b12b58及固定MOAT源码，当前图像13/26通过。先建立26入口剩余合同与源码依赖账本，优先复核多实例encoder原始CLI和CUDA基线。 | `migration/image-completion-plan.md` |
| 2026-11-13T02:40:40.226225+00:00 | IMG-00 | IN_PROGRESS | 冻结多实例 encoder 原始 CLI/下载/线程/状态/资源义务；明确旧 q0 拒绝用例与原始夹取语义不同。七组 CUDA 探测先只作观察，不签发整例。 | `migration/rewrite/image-completion-encoder-contract.json`；`migration/reports/evidence/rewrite/I0/completion-encoder-source-contract/20261113T024039.223304Z-I0-CPU-contract-040852bad0` |
| 2026-11-13T02:41:00.165884+00:00 | IMG-00 | IN_PROGRESS | 5090 原始 nvJPEG 多实例 encoder 使用未修改 CMake/C++20 构建：BUILT。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-CMake-CXX20/20261113T024052.431041Z-I0-cuda-build-361fbe3168` |
| 2026-11-13T02:41:02.910916+00:00 | IMG-00 | IN_PROGRESS | 原始 CUDA encoder natural-three：OBSERVED，收集 3 件 JPEG；解码/数值比较待独立参考。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-natural-three/20261113T024100.571136Z-I0-cuda-native-c221dd0932` |
| 2026-11-13T02:41:05.586156+00:00 | IMG-00 | IN_PROGRESS | 原始 CUDA encoder repeat-seven：OBSERVED，收集 7 件 JPEG；解码/数值比较待独立参考。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-repeat-seven/20261113T024103.295735Z-I0-cuda-native-216c2f78c3` |
| 2026-11-13T02:41:08.172278+00:00 | IMG-00 | IN_PROGRESS | 原始 CUDA encoder optimized-444：OBSERVED，收集 3 件 JPEG；解码/数值比较待独立参考。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-optimized-444/20261113T024105.977419Z-I0-cuda-native-91a248212f` |
| 2026-11-13T02:41:10.759633+00:00 | IMG-00 | IN_PROGRESS | 原始 CUDA encoder quality-clamp-low：OBSERVED，收集 3 件 JPEG；解码/数值比较待独立参考。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-quality-clamp-low/20261113T024108.559052Z-I0-cuda-native-655d9e539f` |
| 2026-11-13T02:41:13.349482+00:00 | IMG-00 | IN_PROGRESS | 原始 CUDA encoder quality-clamp-high：OBSERVED，收集 3 件 JPEG；解码/数值比较待独立参考。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-quality-clamp-high/20261113T024111.160256Z-I0-cuda-native-13bce6086e` |
| 2026-11-13T02:41:15.901606+00:00 | IMG-00 | IN_PROGRESS | 原始 CUDA encoder download-no-write：OBSERVED，收集 0 件 JPEG；解码/数值比较待独立参考。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-download-no-write/20261113T024113.731237Z-I0-cuda-native-489038f4e0` |
| 2026-11-13T02:41:18.467159+00:00 | IMG-00 | IN_PROGRESS | 原始 CUDA encoder device-only：OBSERVED，收集 0 件 JPEG；解码/数值比较待独立参考。 | `migration/reports/evidence/rewrite/I0/completion-encoder-original-device-only/20261113T024116.268380Z-I0-cuda-native-3b01b10c75` |
| 2026-11-13T02:42:08.427328+00:00 | IMG-00 | IN_PROGRESS | 建立26入口当前资格、源码SHA、本地include反向依赖与算法欠项账本；确认13 PASSED/9 PARTIAL/4 FAILED。完整语义矩阵和保留验收集仍未完成，阶段保持IN_PROGRESS。 | `migration/reports/image-completion-inventory.json`；`migration/reports/image-completion-IMG-00.md`；`migration/reports/evidence/rewrite/I0/image-completion-26-source-dependency-gap-ledger/20261113T024207.341488Z-I0-CPU-contract-6f01c9842c` |
| 2026-11-13T02:42:39.282342+00:00 | IMG-00 | IN_PROGRESS | 19件原生 CUDA JPEG 的独立解码、文件SHA/长度、尺寸/采样/质量量化检查：PASSED；native与CPU像素差异仅实测留档，未据此事后放宽验收阈值。 | `migration/reports/evidence/rewrite/I0/native-encoder-nineteen-products-independent-decode/20261113T024238.241618Z-I0-CPU-reference-6948045edf`；`migration/reports/image-completion-encoder-native-reference.json` |
| 2026-11-13T02:44:59.488598+00:00 | IMG-01 | IN_PROGRESS | 冻结生产 prefix 的16组逐元素/总数/错误门槛：包括零长度、4097长度和真实4Gbit累计溢出；组件尚未接入入口。 | `migration/rewrite/image-checked-prefix-profile.json`；`migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-error-contract/20261113T024458.474774Z-I5-CPU-contract-3ef142d023` |
| 2026-11-13T02:45:16.634614+00:00 | IMG-01 | IN_PROGRESS | 带非法块长度和64位累计检查的生产 prefix 构建：BUILT。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-build/20261113T024513.305912Z-I5-rocm-build-71bb082fc7` |
| 2026-11-13T02:47:25.936350+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-1：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024723.675703Z-I5-rocm-probe-5c51989184` |
| 2026-11-13T02:47:28.206920+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-255：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024726.310305Z-I5-rocm-probe-0dba0e720d` |
| 2026-11-13T02:47:30.453416+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-256：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024728.547733Z-I5-rocm-probe-12c4f1e692` |
| 2026-11-13T02:47:32.649179+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-257：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024730.800502Z-I5-rocm-probe-3bdcc2d435` |
| 2026-11-13T02:47:34.896086+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-4096：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024733.000344Z-I5-rocm-probe-958ab40e8e` |
| 2026-11-13T02:47:37.171148+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-65536：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024735.235894Z-I5-rocm-probe-7eedd8d7ba` |
| 2026-11-13T02:47:39.430782+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-1：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024737.526397Z-I5-rocm-probe-3c56df071d` |
| 2026-11-13T02:47:41.655937+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-255：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024739.779104Z-I5-rocm-probe-44a9ae3b55` |
| 2026-11-13T02:47:43.896045+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-256：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024741.984737Z-I5-rocm-probe-ad21cde6d3` |
| 2026-11-13T02:47:46.146980+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-257：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024744.243998Z-I5-rocm-probe-eea9e9c0a5` |
| 2026-11-13T02:47:48.370494+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-4096：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024746.491564Z-I5-rocm-probe-bc246e3d5f` |
| 2026-11-13T02:47:50.626605+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-65536：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024748.718919Z-I5-rocm-probe-b7b8404e62` |
| 2026-11-13T02:47:52.807705+00:00 | IMG-01 | IN_PROGRESS | checked prefix empty-rejected：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024750.973558Z-I5-rocm-probe-4335894022` |
| 2026-11-13T02:47:55.047463+00:00 | IMG-01 | IN_PROGRESS | checked prefix zero-length-rejected：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024753.144173Z-I5-rocm-probe-fe2b437d90` |
| 2026-11-13T02:47:57.283916+00:00 | IMG-01 | IN_PROGRESS | checked prefix 4097-length-rejected：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024755.395512Z-I5-rocm-probe-ded4f7ce22` |
| 2026-11-13T02:47:59.505666+00:00 | IMG-01 | IN_PROGRESS | checked prefix uint32-bit-total-overflow：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T024757.615067Z-I5-rocm-probe-d8868fe3f4` |
| 2026-11-13T02:48:45.508448+00:00 | IMG-01 | IN_PROGRESS | 冻结异步slot的14组开发验证：单像素/单行列/奇数/MCU边界、Q1/75/100/90/80/95、标准/优化Huffman、两slot六任务复用和不下载模式；与旧串行核心逐字节比较。 | `migration/rewrite/image-encoder-pipeline-profile.json`；`migration/reports/evidence/rewrite/I5/async-JPEG-slot-exact-reuse-contract/20261113T024844.517343Z-I5-CPU-contract-148b46b701` |
| 2026-11-13T02:48:59.750023+00:00 | IMG-01 | IN_PROGRESS | 异步JPEG slot候选构建：BUILT。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-build/20261113T024855.351683Z-I5-rocm-build-f8766400e0` |
| 2026-11-13T02:49:17.536429+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x1-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024915.222918Z-I5-rocm-probe-901ce66531` |
| 2026-11-13T02:49:19.811118+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x1-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024917.887337Z-I5-rocm-probe-81223456bf` |
| 2026-11-13T02:49:22.080385+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x257-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024920.159352Z-I5-rocm-probe-21acc358f6` |
| 2026-11-13T02:49:24.371537+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x257-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024922.429709Z-I5-rocm-probe-2307baa96c` |
| 2026-11-13T02:49:26.650681+00:00 | IMG-01 | IN_PROGRESS | 异步slot 257x1-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024924.726708Z-I5-rocm-probe-687e2502c7` |
| 2026-11-13T02:49:28.928237+00:00 | IMG-01 | IN_PROGRESS | 异步slot 257x1-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024927.002049Z-I5-rocm-probe-16b4b2c19a` |
| 2026-11-13T02:49:31.173416+00:00 | IMG-01 | IN_PROGRESS | 异步slot 17x19-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024929.278724Z-I5-rocm-probe-4646859ba5` |
| 2026-11-13T02:49:33.425462+00:00 | IMG-01 | IN_PROGRESS | 异步slot 17x19-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024931.520090Z-I5-rocm-probe-b86306158f` |
| 2026-11-13T02:49:35.732076+00:00 | IMG-01 | IN_PROGRESS | 异步slot 256x257-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024933.757686Z-I5-rocm-probe-67e43bcc34` |
| 2026-11-13T02:49:38.031036+00:00 | IMG-01 | IN_PROGRESS | 异步slot 256x257-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024936.060923Z-I5-rocm-probe-18758c95b8` |
| 2026-11-13T02:49:40.423721+00:00 | IMG-01 | IN_PROGRESS | 异步slot 511x509-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024938.377324Z-I5-rocm-probe-1625c49a4d` |
| 2026-11-13T02:49:42.804230+00:00 | IMG-01 | IN_PROGRESS | 异步slot 511x509-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024940.763954Z-I5-rocm-probe-73bf64c189` |
| 2026-11-13T02:49:45.038121+00:00 | IMG-01 | IN_PROGRESS | 异步slot device-only-0：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024943.134617Z-I5-rocm-probe-59979138d6` |
| 2026-11-13T02:49:47.252102+00:00 | IMG-01 | IN_PROGRESS | 异步slot device-only-1：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T024945.384583Z-I5-rocm-probe-852abe20ec` |
| 2026-11-13T02:53:51.159682+00:00 | IMG-00 | IN_PROGRESS | 19件原生 CUDA JPEG 的独立解码、文件SHA/长度、尺寸/采样/质量量化检查：PASSED；native与CPU像素差异仅实测留档，未据此事后放宽验收阈值。 | `migration/reports/evidence/rewrite/I0/native-encoder-nineteen-products-independent-decode/20261113T025350.082438Z-I0-CPU-reference-e0e697180c`；`migration/reports/image-completion-encoder-native-reference.json` |
| 2026-11-13T02:53:56.702288+00:00 | IMG-01 | IN_PROGRESS | 异步JPEG slot候选构建：BUILT。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-build/20261113T025352.334445Z-I5-rocm-build-930d10cabf` |
| 2026-11-13T02:54:24.542178+00:00 | IMG-01 | IN_PROGRESS | 复审修复后的5处提交中途分配故障注入：PASSED；失败slot排空并禁止复用，新slot恢复执行。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-allocation-fault-recovery/20261113T025420.137678Z-I5-rocm-negative-29a13b9bae` |
| 2026-11-13T02:56:16.748212+00:00 | IMG-00 | IN_PROGRESS | 19件原生 CUDA JPEG 的独立解码、文件SHA/长度、尺寸/采样/质量量化检查：PASSED；native与CPU像素差异仅实测留档，未据此事后放宽验收阈值。 | `migration/reports/evidence/rewrite/I0/native-encoder-nineteen-products-independent-decode/20261113T025615.684993Z-I0-CPU-reference-a898451bfd`；`migration/reports/image-completion-encoder-native-reference.json` |
| 2026-11-13T02:56:20.494080+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x1-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025618.016478Z-I5-rocm-probe-250ca4bfc6` |
| 2026-11-13T02:56:22.997073+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x1-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025620.856624Z-I5-rocm-probe-346b9652c7` |
| 2026-11-13T02:56:25.475679+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x257-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025623.361807Z-I5-rocm-probe-1ed7c73e6b` |
| 2026-11-13T02:56:27.963169+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x257-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025625.825486Z-I5-rocm-probe-d381a8dc22` |
| 2026-11-13T02:56:30.459032+00:00 | IMG-01 | IN_PROGRESS | 异步slot 257x1-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025628.317695Z-I5-rocm-probe-e262b235e2` |
| 2026-11-13T02:56:33.004695+00:00 | IMG-01 | IN_PROGRESS | 异步slot 257x1-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025630.825578Z-I5-rocm-probe-ad54f4b51a` |
| 2026-11-13T02:56:35.474848+00:00 | IMG-01 | IN_PROGRESS | 异步slot 17x19-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025633.358459Z-I5-rocm-probe-5076776409` |
| 2026-11-13T02:56:37.940643+00:00 | IMG-01 | IN_PROGRESS | 异步slot 17x19-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025635.827411Z-I5-rocm-probe-45bca3dabc` |
| 2026-11-13T02:56:40.413185+00:00 | IMG-01 | IN_PROGRESS | 异步slot 256x257-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025638.298820Z-I5-rocm-probe-c37fc68407` |
| 2026-11-13T02:56:42.881085+00:00 | IMG-01 | IN_PROGRESS | 异步slot 256x257-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025640.757678Z-I5-rocm-probe-26b463b876` |
| 2026-11-13T02:56:45.456330+00:00 | IMG-01 | IN_PROGRESS | 异步slot 511x509-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025643.225914Z-I5-rocm-probe-9f4313fd37` |
| 2026-11-13T02:56:48.077066+00:00 | IMG-01 | IN_PROGRESS | 异步slot 511x509-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025645.795513Z-I5-rocm-probe-7446b63122` |
| 2026-11-13T02:56:50.522726+00:00 | IMG-01 | IN_PROGRESS | 异步slot device-only-0：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025648.417062Z-I5-rocm-probe-ab487cfd86` |
| 2026-11-13T02:56:52.941575+00:00 | IMG-01 | IN_PROGRESS | 异步slot device-only-1：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T025650.850259Z-I5-rocm-probe-3c0bf7db07` |
| 2026-11-13T02:57:12.337621+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace 511x509-standard：FAILED，实际kernel 162，跨stream重叠对数 41；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T025709.763871Z-I5-rocm-trace-5a0ac337a2` |
| 2026-11-13T02:57:14.970104+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace 511x509-optimized：FAILED，实际kernel 192，跨stream重叠对数 85；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T025712.699461Z-I5-rocm-trace-1fd0bbdde9` |
| 2026-11-13T02:57:17.510905+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace device-only-0：FAILED，实际kernel 168，跨stream重叠对数 45；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T025715.326858Z-I5-rocm-trace-962e504b30` |
| 2026-11-13T02:57:20.014665+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace device-only-1：FAILED，实际kernel 198，跨stream重叠对数 51；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T025717.866016Z-I5-rocm-trace-6c0d64ede0` |
| 2026-11-13T03:00:13.505222+00:00 | IMG-01 | IN_PROGRESS | 实际HIP copy参数观察器构建：BUILT；用于覆盖ROCm把小传输实现为kernel的路径。 | `migration/reports/evidence/rewrite/I5/async-JPEG-copy-argument-observer/20261113T030011.944792Z-I5-rocm-build-c2c88c75c8` |
| 2026-11-13T03:00:16.518153+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace 511x509-standard：PASSED，实际kernel 96，跨stream重叠对数 35；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T030013.865048Z-I5-rocm-trace-bcd36cd356` |
| 2026-11-13T03:00:19.233689+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace 511x509-optimized：PASSED，实际kernel 102，跨stream重叠对数 36；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T030016.920210Z-I5-rocm-trace-3b749467f0` |
| 2026-11-13T03:00:21.820438+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace device-only-0：PASSED，实际kernel 96，跨stream重叠对数 24；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T030019.573260Z-I5-rocm-trace-efb6174192` |
| 2026-11-13T03:00:24.428057+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace device-only-1：PASSED，实际kernel 102，跨stream重叠对数 15；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T030022.172423Z-I5-rocm-trace-725993e0e0` |
| 2026-11-13T03:01:39.821920+00:00 | IMG-01 | IN_PROGRESS | 冻结v2候选15组原始CLI/扩展合同：质量和n/r夹取、先截断输入再扩展states、单图重复、实际自动标定、help位置和错误返回；标定搜索及双slot映射差异明确登记。 | `migration/rewrite/image-encoder-instances-v2-profile.json`；`migration/reports/evidence/rewrite/I5/async-original-encoder-CLI-contract/20261113T030138.807149Z-I5-CPU-contract-a8ef1c0b07` |
| 2026-11-13T03:01:56.144484+00:00 | IMG-01 | IN_PROGRESS | v2原始CLI候选构建：BUILT；正式入口尚未切换。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-build/20261113T030151.464018Z-I5-rocm-build-48abdbf04b` |
| 2026-11-13T03:02:27.362037+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI natural-three：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030225.042892Z-I5-rocm-original-candidate-a98b9ae9f3` |
| 2026-11-13T03:02:29.688001+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI repeat-seven：PASSED，产品 7；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030227.730149Z-I5-rocm-original-candidate-b708d1fd5c` |
| 2026-11-13T03:02:31.983806+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI optimized-444：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030230.024567Z-I5-rocm-original-candidate-114f99a894` |
| 2026-11-13T03:02:34.253839+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI quality-clamp-low：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030232.343531Z-I5-rocm-original-candidate-a7caeb5a52` |
| 2026-11-13T03:02:36.555700+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI quality-clamp-high：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030234.598593Z-I5-rocm-original-candidate-151b5566f1` |
| 2026-11-13T03:02:38.816401+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI download-no-write：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030236.899721Z-I5-rocm-original-candidate-0f2a7ed5fd` |
| 2026-11-13T03:02:41.075910+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI device-only：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030239.145306Z-I5-rocm-original-candidate-bcd36e122d` |
| 2026-11-13T03:02:43.332131+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI truncate-before-state-expansion：PASSED，产品 4；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030241.424110Z-I5-rocm-original-candidate-e2002aa132` |
| 2026-11-13T03:02:45.522521+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI negative-n-zero-r-clamps：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030243.663781Z-I5-rocm-original-candidate-0d4778a2b6` |
| 2026-11-13T03:02:47.820317+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI single-input-repeats：PASSED，产品 7；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030245.859058Z-I5-rocm-original-candidate-7ea858a422` |
| 2026-11-13T03:02:50.286619+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI auto-calibration：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030248.163482Z-I5-rocm-original-candidate-505fae7d24` |
| 2026-11-13T03:02:52.296404+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI help-anywhere：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030250.631610Z-I5-rocm-original-candidate-54d21a56c5` |
| 2026-11-13T03:02:54.289253+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI hardware-unavailable：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030252.618505Z-I5-rocm-original-candidate-d8ecfddbb3` |
| 2026-11-13T03:02:56.324171+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI negative-states：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030254.617474Z-I5-rocm-original-candidate-c8419a2baf` |
| 2026-11-13T03:02:58.338990+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI missing-input：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030256.659380Z-I5-rocm-original-candidate-37bcb309c3` |
| 2026-11-13T03:03:16.749687+00:00 | IMG-01 | IN_PROGRESS | 带非法块长度和64位累计检查的生产 prefix 构建：BUILT。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-build/20261113T030313.586034Z-I5-rocm-build-b3abb36226` |
| 2026-11-13T03:04:13.659453+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-1：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030411.406001Z-I5-rocm-probe-a5e1ea144e` |
| 2026-11-13T03:04:15.968942+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-255：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030414.030426Z-I5-rocm-probe-a5eb8bf945` |
| 2026-11-13T03:04:18.242273+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-256：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030416.329235Z-I5-rocm-probe-13e7ed83fa` |
| 2026-11-13T03:04:20.514567+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-257：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030418.598557Z-I5-rocm-probe-87ecdb5e80` |
| 2026-11-13T03:04:22.771162+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-4096：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030420.861133Z-I5-rocm-probe-11eea8d610` |
| 2026-11-13T03:04:25.005968+00:00 | IMG-01 | IN_PROGRESS | checked prefix bits-65536：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030423.119140Z-I5-rocm-probe-666b261bf0` |
| 2026-11-13T03:04:27.260138+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-1：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030425.339053Z-I5-rocm-probe-2c201dc334` |
| 2026-11-13T03:04:29.492370+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-255：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030427.611409Z-I5-rocm-probe-8312e641ba` |
| 2026-11-13T03:04:31.686922+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-256：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030429.820268Z-I5-rocm-probe-227e1f0f48` |
| 2026-11-13T03:04:33.886410+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-257：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030432.042006Z-I5-rocm-probe-0ff12ceea3` |
| 2026-11-13T03:04:36.101266+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-4096：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030434.239337Z-I5-rocm-probe-d9c7837834` |
| 2026-11-13T03:04:38.323090+00:00 | IMG-01 | IN_PROGRESS | checked prefix stuff-65536：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030436.453575Z-I5-rocm-probe-7420f9ebe1` |
| 2026-11-13T03:04:40.505809+00:00 | IMG-01 | IN_PROGRESS | checked prefix empty-rejected：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030438.670708Z-I5-rocm-probe-16c792c6e3` |
| 2026-11-13T03:04:42.693188+00:00 | IMG-01 | IN_PROGRESS | checked prefix zero-length-rejected：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030440.833395Z-I5-rocm-probe-48b744c1a8` |
| 2026-11-13T03:04:44.962916+00:00 | IMG-01 | IN_PROGRESS | checked prefix 4097-length-rejected：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030443.048648Z-I5-rocm-probe-a2e294106a` |
| 2026-11-13T03:04:47.182089+00:00 | IMG-01 | IN_PROGRESS | checked prefix uint32-bit-total-overflow：PASSED；错误模式仅通过显式拒绝，不能进入码流打包。 | `migration/reports/evidence/rewrite/I5/checked-JPEG-prefix-exact-and-guards/20261113T030445.317613Z-I5-rocm-probe-f7f0f8e674` |
| 2026-11-13T03:04:59.066176+00:00 | IMG-01 | IN_PROGRESS | prefix超uint32元素数稀疏文件 stuff：PASSED；分配/读取内容前拒绝，验证复审修复。 | `migration/reports/evidence/rewrite/I5/checked-prefix-oversize-file-rejection/20261113T030457.075975Z-I5-rocm-negative-0f2d993dd2` |
| 2026-11-13T03:05:01.280835+00:00 | IMG-01 | IN_PROGRESS | prefix超uint32元素数稀疏文件 bits：PASSED；分配/读取内容前拒绝，验证复审修复。 | `migration/reports/evidence/rewrite/I5/checked-prefix-oversize-file-rejection/20261113T030459.416869Z-I5-rocm-negative-517f24b97f` |
| 2026-11-13T03:06:26.185063+00:00 | IMG-01 | IN_PROGRESS | v2 CLI natural-three 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030623.922498Z-I5-rocm-reference-37d3afcc2f` |
| 2026-11-13T03:06:28.458302+00:00 | IMG-01 | IN_PROGRESS | v2 CLI repeat-seven 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，7件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030626.553277Z-I5-rocm-reference-84694aca1d` |
| 2026-11-13T03:06:30.723217+00:00 | IMG-01 | IN_PROGRESS | v2 CLI optimized-444 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030628.805341Z-I5-rocm-reference-bb79aa6878` |
| 2026-11-13T03:06:32.969719+00:00 | IMG-01 | IN_PROGRESS | v2 CLI quality-clamp-low 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030631.072950Z-I5-rocm-reference-5f56380947` |
| 2026-11-13T03:06:35.205847+00:00 | IMG-01 | IN_PROGRESS | v2 CLI quality-clamp-high 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030633.316241Z-I5-rocm-reference-1ba8e5d445` |
| 2026-11-13T03:06:37.453621+00:00 | IMG-01 | IN_PROGRESS | v2 CLI truncate-before-state-expansion 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，4件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030635.564406Z-I5-rocm-reference-a6fe5d6ce7` |
| 2026-11-13T03:06:39.696300+00:00 | IMG-01 | IN_PROGRESS | v2 CLI negative-n-zero-r-clamps 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030637.790027Z-I5-rocm-reference-0d996fc8a7` |
| 2026-11-13T03:06:41.943870+00:00 | IMG-01 | IN_PROGRESS | v2 CLI single-input-repeats 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，7件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T030640.049384Z-I5-rocm-reference-c67bcd681b` |
| 2026-11-13T03:07:18.563366+00:00 | IMG-01 | IN_PROGRESS | 独立复审修复与当前候选实现/测试/传输证据已汇总至IMG-01报告；主表仍13整例通过，准备正式入口整合及新资格。 | `migration/reports/image-completion-IMG-01.md` |
| 2026-11-13T03:07:54.573803+00:00 | IMG-01 | IN_PROGRESS | v2接入原始C++路径后的构建：BUILT；等待当前源码整合验收与资格发布。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-build/20261113T030749.806455Z-I5-rocm-build-de99467a31` |
| 2026-11-13T03:08:10.630446+00:00 | IMG-01 | IN_PROGRESS | 候选15组CLI与33件混合尺寸JPEG全部通过，独立限定复审通过；现已将v2接入正式C++路径，开始当前入口重建、复验与新资格，旧资格不作为新源码证明。 | `rocm/ported/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp`；`migration/reports/image-encoder-instances-v2-comparison.json` |
| 2026-11-13T03:09:19.635962+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI natural-three：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030916.992727Z-I5-rocm-original-candidate-b86ec84d65` |
| 2026-11-13T03:09:22.045365+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI repeat-seven：PASSED，产品 7；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030920.018043Z-I5-rocm-original-candidate-971e5c9a1f` |
| 2026-11-13T03:09:24.597906+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI optimized-444：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030922.495545Z-I5-rocm-original-candidate-485a837020` |
| 2026-11-13T03:09:26.826926+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI quality-clamp-low：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030924.954413Z-I5-rocm-original-candidate-9a80c64061` |
| 2026-11-13T03:09:29.148017+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI quality-clamp-high：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030927.160990Z-I5-rocm-original-candidate-24841f699e` |
| 2026-11-13T03:09:31.560105+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI download-no-write：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030929.610735Z-I5-rocm-original-candidate-8dac097028` |
| 2026-11-13T03:09:33.865009+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI device-only：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030931.909343Z-I5-rocm-original-candidate-5972ef7ac8` |
| 2026-11-13T03:09:36.353339+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI truncate-before-state-expansion：PASSED，产品 4；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030934.207830Z-I5-rocm-original-candidate-a968234465` |
| 2026-11-13T03:09:38.773352+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI negative-n-zero-r-clamps：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030936.804573Z-I5-rocm-original-candidate-c75f1c064f` |
| 2026-11-13T03:09:41.059522+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI single-input-repeats：PASSED，产品 7；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030939.120672Z-I5-rocm-original-candidate-6fef0da5d3` |
| 2026-11-13T03:09:43.731132+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI auto-calibration：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030941.405021Z-I5-rocm-original-candidate-c330bf7877` |
| 2026-11-13T03:09:45.808535+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI help-anywhere：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030944.082224Z-I5-rocm-original-candidate-152bc38889` |
| 2026-11-13T03:09:47.880791+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI hardware-unavailable：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030946.146086Z-I5-rocm-original-candidate-535ab6127f` |
| 2026-11-13T03:09:50.082322+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI negative-states：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030948.322217Z-I5-rocm-original-candidate-b28856e82e` |
| 2026-11-13T03:09:52.107440+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI missing-input：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T030950.411946Z-I5-rocm-original-candidate-4cf769e7cf` |
| 2026-11-13T03:10:11.534238+00:00 | IMG-01 | IN_PROGRESS | v2 CLI natural-three 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031008.822279Z-I5-rocm-reference-2c1804e273` |
| 2026-11-13T03:10:14.504472+00:00 | IMG-01 | IN_PROGRESS | v2 CLI repeat-seven 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，7件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031011.897519Z-I5-rocm-reference-42080f73c2` |
| 2026-11-13T03:10:17.227195+00:00 | IMG-01 | IN_PROGRESS | v2 CLI optimized-444 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031014.866671Z-I5-rocm-reference-94c31db75a` |
| 2026-11-13T03:10:20.004538+00:00 | IMG-01 | IN_PROGRESS | v2 CLI quality-clamp-low 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031017.578671Z-I5-rocm-reference-2bd613aa4c` |
| 2026-11-13T03:10:22.889023+00:00 | IMG-01 | IN_PROGRESS | v2 CLI quality-clamp-high 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031020.363595Z-I5-rocm-reference-54bbe91981` |
| 2026-11-13T03:10:25.142595+00:00 | IMG-01 | IN_PROGRESS | v2 CLI truncate-before-state-expansion 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，4件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031023.239272Z-I5-rocm-reference-d30f74637d` |
| 2026-11-13T03:10:28.079845+00:00 | IMG-01 | IN_PROGRESS | v2 CLI negative-n-zero-r-clamps 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031025.482880Z-I5-rocm-reference-77c3a08448` |
| 2026-11-13T03:10:30.289072+00:00 | IMG-01 | IN_PROGRESS | v2 CLI single-input-repeats 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，7件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T031028.426258Z-I5-rocm-reference-243d97ef03` |
| 2026-11-13T03:12:19.087540+00:00 | IMG-01 | IN_PROGRESS | 正式入口trace repeat-seven：PASSED；多线程实际kernel/stream、设备模式和首图变化重放逐项记录。 | `migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T031215.898114Z-I5-rocm-trace-c01c1ac536` |
| 2026-11-13T03:12:21.902920+00:00 | IMG-01 | IN_PROGRESS | 正式入口trace optimized-444：PASSED；多线程实际kernel/stream、设备模式和首图变化重放逐项记录。 | `migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T031219.466873Z-I5-rocm-trace-de04e1e868` |
| 2026-11-13T03:12:24.517313+00:00 | IMG-01 | IN_PROGRESS | 正式入口trace device-only：PASSED；多线程实际kernel/stream、设备模式和首图变化重放逐项记录。 | `migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T031222.250720Z-I5-rocm-trace-86eecf6368` |
| 2026-11-13T03:13:20.034998+00:00 | IMG-01 | IN_PROGRESS | 正式入口20项子集资格封存：15 CLI、33产品、3真实多线程trace、变化输入及组件故障/传输证明；完整保留集/大索引/性能/冷构建未完成，保持PARTIAL。 | `migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T031319.007294Z-I5-composite-subset-qualification-b306444164` |
| 2026-11-13T03:16:43.668389+00:00 | IMG-01 | IN_PROGRESS | 复审发现的重复已封存case覆盖漏洞已修复：完整冻结ID/逐case产品集合绑定；11项删减/重复反向检查 PASSED。 | `migration/reports/evidence/rewrite/I5/async-encoder-qualification-coverage-negatives/20261113T031642.620876Z-I5-CPU-negative-e309436a78` |
| 2026-11-13T03:16:58.295246+00:00 | IMG-01 | IN_PROGRESS | 正式入口20项子集资格封存：15 CLI、33产品、3真实多线程trace、变化输入及组件故障/传输证明；完整保留集/大索引/性能/冷构建未完成，保持PARTIAL。 | `migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T031657.268240Z-I5-composite-subset-qualification-fd52687b9f` |
| 2026-11-13T03:19:18.125210+00:00 | IMG-01 | IN_PROGRESS | 已将新异步编码器20项当前子集资格发布到主表；原始CUDA基线恢复，完整等价/性能等欠项明示，图像整例计数仍13/26。 | `migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T031657.268240Z-I5-composite-subset-qualification-fd52687b9f`；`migration/reports/image-encoder-instances-v2-publication.json` |
| 2026-11-13T03:19:37.758250+00:00 | IMG-00 | IN_PROGRESS | 建立26入口当前资格、源码SHA、本地include反向依赖与算法欠项账本；确认13 PASSED/9 PARTIAL/4 FAILED。完整语义矩阵和保留验收集仍未完成，阶段保持IN_PROGRESS。 | `migration/reports/image-completion-inventory.json`；`migration/reports/image-completion-IMG-00.md`；`migration/reports/evidence/rewrite/I0/image-completion-26-source-dependency-gap-ledger/20261113T031936.668243Z-I0-CPU-contract-0d8048f7fb` |
| 2026-11-13T03:20:01.177022+00:00 | IMG-00 | IN_PROGRESS | 建立26入口当前资格、源码SHA、本地include反向依赖与算法欠项账本；确认13 PASSED/9 PARTIAL/4 FAILED。完整语义矩阵和保留验收集仍未完成，阶段保持IN_PROGRESS。 | `migration/reports/image-completion-inventory.json`；`migration/reports/image-completion-IMG-00.md`；`migration/reports/evidence/rewrite/I0/image-completion-26-source-dependency-gap-ledger/20261113T032000.052970Z-I0-CPU-contract-bbaad78034` |
| 2026-11-13T03:22:49.497598+00:00 | IMG-01 | IN_PROGRESS | 当前正式入口子集已发布；全项目一致性、4836条封存实验、42项既有完整重写资格及新增JPEG子集传递证明均通过，无未封存/遗留RUNNING。整例仍13/26；本次源码/证据检查点准备推送fork。 | `migration/reports/final-validation.json`；`migration/reports/rewrite-evidence-audit.json`；`migration/reports/rewrite-selected-proof-audit.json`；`migration/reports/image-encoder-instances-v2-selected-proof.json` |
| 2026-11-13T03:29:26.128687+00:00 | IMG-01 | IN_PROGRESS | 冻结剩余16组线程/状态/重复/混合尺寸和错误合同；新增1x1、513x511、19x17固定seed BMP，覆盖j0及中途写失败、坏DIB/截断文件。 | `migration/rewrite/image-encoder-runtime-profile.json`；`migration/reports/evidence/rewrite/I5/encoder-remaining-runtime-contract/20261113T032925.043389Z-I5-CPU-contract-1d35c27820` |
| 2026-11-13T03:32:15.185379+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 n0-s0-j1：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033212.206554Z-I5-rocm-original-entry-80e23a721a` |
| 2026-11-13T03:32:17.815181+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 threads-exceed-states：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033215.577203Z-I5-rocm-original-entry-4c232fc065` |
| 2026-11-13T03:32:20.405455+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 states-exceed-threads：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033218.166397Z-I5-rocm-original-entry-0f33f19ce8` |
| 2026-11-13T03:32:23.545652+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 three-runs：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033220.765400Z-I5-rocm-original-entry-11181df99f` |
| 2026-11-13T03:32:29.221430+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 j0-hardware-concurrency：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033223.904865Z-I5-rocm-original-entry-067609262a` |
| 2026-11-13T03:32:32.197069+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 gpu-and-unavailable-hardware：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033229.575582Z-I5-rocm-original-entry-4e5c821d82` |
| 2026-11-13T03:32:35.180648+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 mixed-size-slot-growth-reuse：PASSED，实际产品 17；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033232.540483Z-I5-rocm-original-entry-bb0efa2692` |
| 2026-11-13T03:32:37.719881+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 single-large-repeated：PASSED，实际产品 19；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033235.514595Z-I5-rocm-original-entry-ca273b8be8` |
| 2026-11-13T03:32:39.771275+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033238.056885Z-I5-rocm-original-entry-22b4b950d9` |
| 2026-11-13T03:32:41.981595+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 DIB-length-beyond-file：FAILED，实际产品 1；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033240.100213Z-I5-rocm-original-entry-5163b05382` |
| 2026-11-13T03:32:43.991437+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 zero-width-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033242.303139Z-I5-rocm-original-entry-68f69b75ef` |
| 2026-11-13T03:32:46.084041+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 invalid-numeric-CLI：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033244.321541Z-I5-rocm-original-entry-9a3984dc24` |
| 2026-11-13T03:32:48.118255+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 empty-directory：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033246.413886Z-I5-rocm-original-entry-760aff058e` |
| 2026-11-13T03:32:50.128419+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 output-path-is-file：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033248.438243Z-I5-rocm-original-entry-6361a0698d` |
| 2026-11-13T03:32:52.408557+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 write-failure-after-GPU：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033250.454396Z-I5-rocm-original-entry-74caf1d2b8` |
| 2026-11-13T03:32:54.620534+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-last-mixed-input：PASSED，实际产品 2；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033252.756761Z-I5-rocm-original-entry-941ad4f14e` |
| 2026-11-13T03:33:12.473015+00:00 | IMG-01 | IN_PROGRESS | 16组扩展合同首次执行15通过1失败：DIB声明长度超过文件被错误接受；保留失败原证据。读取器现校验完整DIB及像素偏移，等待重建重跑；阶段保持IN_PROGRESS。 | `migration/reports/image-encoder-runtime-runs.json`；`rocm/common/image/jpeg_encoder_instances_v2.hpp` |
| 2026-11-13T03:33:20.188416+00:00 | IMG-01 | IN_PROGRESS | v2接入原始C++路径后的构建：BUILT；等待当前源码整合验收与资格发布。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-build/20261113T033315.363651Z-I5-rocm-build-84cd74664a` |
| 2026-11-13T03:34:02.696084+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 n0-s0-j1：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033359.674081Z-I5-rocm-original-entry-4053afeb32` |
| 2026-11-13T03:34:05.407110+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 threads-exceed-states：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033403.097065Z-I5-rocm-original-entry-203bedff19` |
| 2026-11-13T03:34:08.014272+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 states-exceed-threads：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033405.761144Z-I5-rocm-original-entry-16dc9a58af` |
| 2026-11-13T03:34:11.138490+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 three-runs：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033408.369239Z-I5-rocm-original-entry-5877f3f9ac` |
| 2026-11-13T03:34:16.725696+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 j0-hardware-concurrency：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033411.485657Z-I5-rocm-original-entry-fcd43eb231` |
| 2026-11-13T03:34:19.850285+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 gpu-and-unavailable-hardware：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033417.078105Z-I5-rocm-original-entry-b1d5df1634` |
| 2026-11-13T03:34:22.925357+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 mixed-size-slot-growth-reuse：PASSED，实际产品 17；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033420.192166Z-I5-rocm-original-entry-d00135b248` |
| 2026-11-13T03:34:25.489870+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 single-large-repeated：PASSED，实际产品 19；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033423.268370Z-I5-rocm-original-entry-e9f05b2a80` |
| 2026-11-13T03:34:27.593104+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033425.843886Z-I5-rocm-original-entry-6e40def883` |
| 2026-11-13T03:34:29.629249+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 DIB-length-beyond-file：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033427.932206Z-I5-rocm-original-entry-ad5f75f337` |
| 2026-11-13T03:34:31.700116+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 zero-width-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033429.956653Z-I5-rocm-original-entry-ecbdee6967` |
| 2026-11-13T03:34:33.771810+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 invalid-numeric-CLI：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033432.025234Z-I5-rocm-original-entry-cf648c0089` |
| 2026-11-13T03:34:35.842459+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 empty-directory：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033434.100657Z-I5-rocm-original-entry-577609ec1d` |
| 2026-11-13T03:34:37.912151+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 output-path-is-file：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033436.182523Z-I5-rocm-original-entry-d31dc4740d` |
| 2026-11-13T03:34:40.215515+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 write-failure-after-GPU：PASSED，实际产品 1；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033438.234622Z-I5-rocm-original-entry-2c3c643ce5` |
| 2026-11-13T03:34:42.562282+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-last-mixed-input：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033440.576597Z-I5-rocm-original-entry-318342f7fd` |
| 2026-11-13T03:35:05.171645+00:00 | IMG-01 | IN_PROGRESS | 冻结单图预分配合同：标准/优化重复/设备模式3组，计时区间分离、每slot一次RGB上传、稳态零扩容、全部GPU作业和独立产品核对。 | `migration/rewrite/image-encoder-preallocation-profile.json`；`migration/reports/evidence/rewrite/I5/JPEG-single-input-preallocation-contract/20261113T033504.133219Z-I5-CPU-contract-2efe1caa98` |
| 2026-11-13T03:36:09.359130+00:00 | IMG-01 | IN_PROGRESS | 16组运行合同修复后全部通过。已实现单图slot预热和固定device RGB复用，资源准备/编码写盘/销毁分别计时；每个请求仍走完整GPU编码，待真实trace及回归验收。 | `migration/reports/image-encoder-runtime-runs.json`；`migration/rewrite/image-encoder-preallocation-profile.json`；`rocm/common/image/jpeg_encoder_pipeline.hpp` |
| 2026-11-13T03:36:16.913893+00:00 | IMG-01 | IN_PROGRESS | 异步JPEG slot候选构建：BUILT。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-build/20261113T033612.468029Z-I5-rocm-build-566b5917c6` |
| 2026-11-13T03:36:42.573731+00:00 | IMG-01 | IN_PROGRESS | v2接入原始C++路径后的构建：BUILT；等待当前源码整合验收与资格发布。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-build/20261113T033637.717347Z-I5-rocm-build-3725c511e2` |
| 2026-11-13T03:37:27.686984+00:00 | IMG-01 | IN_PROGRESS | 单图预分配 prepared-standard：PASSED；准备/稳态/端到端计时和实际传输、kernel逐项保存。 | `migration/reports/evidence/rewrite/I5/JPEG-single-input-preallocation/20261113T033724.702511Z-I5-rocm-trace-3585d0f477` |
| 2026-11-13T03:37:30.778080+00:00 | IMG-01 | IN_PROGRESS | 单图预分配 prepared-optimized-repeated：PASSED；准备/稳态/端到端计时和实际传输、kernel逐项保存。 | `migration/reports/evidence/rewrite/I5/JPEG-single-input-preallocation/20261113T033728.042534Z-I5-rocm-trace-a8233d1a8e` |
| 2026-11-13T03:37:33.519833+00:00 | IMG-01 | IN_PROGRESS | 单图预分配 prepared-device-only：PASSED；准备/稳态/端到端计时和实际传输、kernel逐项保存。 | `migration/reports/evidence/rewrite/I5/JPEG-single-input-preallocation/20261113T033731.134330Z-I5-rocm-trace-efaa08fe1a` |
| 2026-11-13T03:37:56.150814+00:00 | IMG-01 | IN_PROGRESS | 固定输入slot所有权/占用拒绝/普通提交失效/重新准备：PASSED；修改原CPU向量不污染已准备device输入。 | `migration/reports/evidence/rewrite/I5/JPEG-prepared-input-ownership/20261113T033751.577785Z-I5-rocm-probe-a6110a493a` |
| 2026-11-13T03:38:00.993231+00:00 | IMG-01 | IN_PROGRESS | 复审修复后的5处提交中途分配故障注入：PASSED；失败slot排空并禁止复用，新slot恢复执行。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-allocation-fault-recovery/20261113T033756.670396Z-I5-rocm-negative-80cb06be49` |
| 2026-11-13T03:38:03.848001+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x1-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033801.501572Z-I5-rocm-probe-812dd8807a` |
| 2026-11-13T03:38:06.395696+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x1-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033804.216332Z-I5-rocm-probe-50a4a1b61f` |
| 2026-11-13T03:38:08.961856+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x257-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033806.782299Z-I5-rocm-probe-4ede7b7090` |
| 2026-11-13T03:38:11.539626+00:00 | IMG-01 | IN_PROGRESS | 异步slot 1x257-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033809.344970Z-I5-rocm-probe-2069078290` |
| 2026-11-13T03:38:14.098129+00:00 | IMG-01 | IN_PROGRESS | 异步slot 257x1-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033811.889677Z-I5-rocm-probe-6ddd0a3de3` |
| 2026-11-13T03:38:16.672209+00:00 | IMG-01 | IN_PROGRESS | 异步slot 257x1-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033814.453244Z-I5-rocm-probe-e202191937` |
| 2026-11-13T03:38:19.138480+00:00 | IMG-01 | IN_PROGRESS | 异步slot 17x19-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033817.020377Z-I5-rocm-probe-3c821886c1` |
| 2026-11-13T03:38:21.646319+00:00 | IMG-01 | IN_PROGRESS | 异步slot 17x19-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033819.485778Z-I5-rocm-probe-b3d2487812` |
| 2026-11-13T03:38:24.211602+00:00 | IMG-01 | IN_PROGRESS | 异步slot 256x257-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033821.979251Z-I5-rocm-probe-77e9796ad6` |
| 2026-11-13T03:38:26.760648+00:00 | IMG-01 | IN_PROGRESS | 异步slot 256x257-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033824.542658Z-I5-rocm-probe-90b0af9d2d` |
| 2026-11-13T03:38:29.365360+00:00 | IMG-01 | IN_PROGRESS | 异步slot 511x509-standard：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033827.093580Z-I5-rocm-probe-56e22fb80e` |
| 2026-11-13T03:38:31.979684+00:00 | IMG-01 | IN_PROGRESS | 异步slot 511x509-optimized：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033829.695777Z-I5-rocm-probe-108f861782` |
| 2026-11-13T03:38:34.444957+00:00 | IMG-01 | IN_PROGRESS | 异步slot device-only-0：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033832.319804Z-I5-rocm-probe-d6c071144a` |
| 2026-11-13T03:38:36.936553+00:00 | IMG-01 | IN_PROGRESS | 异步slot device-only-1：PASSED；组件结果不提升整例资格。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-numeric-reuse/20261113T033834.793785Z-I5-rocm-probe-751ad9486a` |
| 2026-11-13T03:38:39.004922+00:00 | IMG-01 | IN_PROGRESS | 实际HIP copy参数观察器构建：BUILT；用于覆盖ROCm把小传输实现为kernel的路径。 | `migration/reports/evidence/rewrite/I5/async-JPEG-copy-argument-observer/20261113T033837.375611Z-I5-rocm-build-c94f0cf8f5` |
| 2026-11-13T03:38:41.830324+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace 511x509-standard：PASSED，实际kernel 96，跨stream重叠对数 28；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T033839.357705Z-I5-rocm-trace-3293c5dbe0` |
| 2026-11-13T03:38:44.645845+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace 511x509-optimized：PASSED，实际kernel 102，跨stream重叠对数 33；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T033842.231733Z-I5-rocm-trace-8c6bd4d219` |
| 2026-11-13T03:38:47.321014+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace device-only-0：PASSED，实际kernel 96，跨stream重叠对数 21；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T033844.988726Z-I5-rocm-trace-e9a7ab6397` |
| 2026-11-13T03:38:49.925488+00:00 | IMG-01 | IN_PROGRESS | 候选独立进程trace device-only-1：PASSED，实际kernel 102，跨stream重叠对数 17；copy表保存以核对设备模式。 | `migration/reports/evidence/rewrite/I5/async-JPEG-slot-trace/20261113T033847.670103Z-I5-rocm-trace-323ec956bf` |
| 2026-11-13T03:38:52.585972+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI natural-three：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033850.366542Z-I5-rocm-original-candidate-60eccd03aa` |
| 2026-11-13T03:38:55.022329+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI repeat-seven：PASSED，产品 7；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033852.953726Z-I5-rocm-original-candidate-91e0938c43` |
| 2026-11-13T03:38:57.373872+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI optimized-444：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033855.371266Z-I5-rocm-original-candidate-8ee3b398a8` |
| 2026-11-13T03:38:59.725145+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI quality-clamp-low：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033857.733326Z-I5-rocm-original-candidate-5f72c4ffd6` |
| 2026-11-13T03:39:02.050638+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI quality-clamp-high：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033900.079969Z-I5-rocm-original-candidate-217b83fb45` |
| 2026-11-13T03:39:04.326669+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI download-no-write：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033902.393114Z-I5-rocm-original-candidate-5d73ec0a8f` |
| 2026-11-13T03:39:06.708087+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI device-only：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033904.708082Z-I5-rocm-original-candidate-1c01f1dfd4` |
| 2026-11-13T03:39:09.058314+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI truncate-before-state-expansion：PASSED，产品 4；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033907.085209Z-I5-rocm-original-candidate-b3747e2bd9` |
| 2026-11-13T03:39:11.373643+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI negative-n-zero-r-clamps：PASSED，产品 3；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033909.400005Z-I5-rocm-original-candidate-0fc716aee4` |
| 2026-11-13T03:39:13.707965+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI single-input-repeats：PASSED，产品 7；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033911.734921Z-I5-rocm-original-candidate-0978844a20` |
| 2026-11-13T03:39:18.086957+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI auto-calibration：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033914.064331Z-I5-rocm-original-candidate-12cc7a6f2a` |
| 2026-11-13T03:39:20.145111+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI help-anywhere：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033918.425997Z-I5-rocm-original-candidate-0c285d530a` |
| 2026-11-13T03:39:22.227027+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI hardware-unavailable：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033920.492474Z-I5-rocm-original-candidate-782cfe574c` |
| 2026-11-13T03:39:24.308813+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI negative-states：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033922.580896Z-I5-rocm-original-candidate-f4613aad37` |
| 2026-11-13T03:39:26.402733+00:00 | IMG-01 | IN_PROGRESS | v2候选CLI missing-input：PASSED，产品 0；仍待正式入口整合验收。 | `migration/reports/evidence/rewrite/I5/async-original-encoder-candidate-CLI/20261113T033924.653377Z-I5-rocm-original-candidate-2d08f1620c` |
| 2026-11-13T03:39:29.362728+00:00 | IMG-01 | IN_PROGRESS | v2 CLI natural-three 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033926.846486Z-I5-rocm-reference-cb7044c895` |
| 2026-11-13T03:39:32.146994+00:00 | IMG-01 | IN_PROGRESS | v2 CLI repeat-seven 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，7件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033929.733028Z-I5-rocm-reference-6d641939db` |
| 2026-11-13T03:39:34.940385+00:00 | IMG-01 | IN_PROGRESS | v2 CLI optimized-444 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033932.531011Z-I5-rocm-reference-162fbc4a97` |
| 2026-11-13T03:39:37.642138+00:00 | IMG-01 | IN_PROGRESS | v2 CLI quality-clamp-low 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033935.293539Z-I5-rocm-reference-0e3a682c28` |
| 2026-11-13T03:39:40.338159+00:00 | IMG-01 | IN_PROGRESS | v2 CLI quality-clamp-high 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033937.992119Z-I5-rocm-reference-df4428fcf1` |
| 2026-11-13T03:39:42.600712+00:00 | IMG-01 | IN_PROGRESS | v2 CLI truncate-before-state-expansion 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，4件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033940.699488Z-I5-rocm-reference-b0b3eb781e` |
| 2026-11-13T03:39:45.300089+00:00 | IMG-01 | IN_PROGRESS | v2 CLI negative-n-zero-r-clamps 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，3件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033942.947267Z-I5-rocm-reference-bcccbf0d3b` |
| 2026-11-13T03:39:47.569947+00:00 | IMG-01 | IN_PROGRESS | v2 CLI single-input-repeats 的全部JPEG与已验旧GPU核心同输入/有效模式逐字节对比：PASSED，7件。 | `migration/reports/evidence/rewrite/I5/async-original-CLI-byte-regression/20261113T033945.660924Z-I5-rocm-reference-b779aba103` |
| 2026-11-13T03:39:50.734724+00:00 | IMG-01 | IN_PROGRESS | 正式入口trace repeat-seven：PASSED；多线程实际kernel/stream、设备模式和首图变化重放逐项记录。 | `migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T033948.008552Z-I5-rocm-trace-178ac12203` |
| 2026-11-13T03:39:53.482978+00:00 | IMG-01 | IN_PROGRESS | 正式入口trace optimized-444：PASSED；多线程实际kernel/stream、设备模式和首图变化重放逐项记录。 | `migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T033951.091772Z-I5-rocm-trace-801dc22b1b` |
| 2026-11-13T03:39:56.224643+00:00 | IMG-01 | IN_PROGRESS | 正式入口trace device-only：PASSED；多线程实际kernel/stream、设备模式和首图变化重放逐项记录。 | `migration/reports/evidence/rewrite/I5/async-original-entry-multithread-trace/20261113T033953.881911Z-I5-rocm-trace-54278cec14` |
| 2026-11-13T03:39:59.439100+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 n0-s0-j1：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033956.726180Z-I5-rocm-original-entry-dcfd63ec2b` |
| 2026-11-13T03:40:02.036081+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 threads-exceed-states：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T033959.803330Z-I5-rocm-original-entry-85b5f4224e` |
| 2026-11-13T03:40:04.579705+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 states-exceed-threads：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034002.376744Z-I5-rocm-original-entry-f2e1a69b9a` |
| 2026-11-13T03:40:07.670934+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 three-runs：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034004.939267Z-I5-rocm-original-entry-77841f3e84` |
| 2026-11-13T03:40:12.380696+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 j0-hardware-concurrency：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034008.025446Z-I5-rocm-original-entry-5fd02aed4e` |
| 2026-11-13T03:40:15.396439+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 gpu-and-unavailable-hardware：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034012.733842Z-I5-rocm-original-entry-2650553af9` |
| 2026-11-13T03:40:18.363330+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 mixed-size-slot-growth-reuse：PASSED，实际产品 17；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034015.748378Z-I5-rocm-original-entry-19246adcdf` |
| 2026-11-13T03:40:20.852074+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 single-large-repeated：PASSED，实际产品 19；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034018.705226Z-I5-rocm-original-entry-f21044392a` |
| 2026-11-13T03:40:22.871200+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034021.197536Z-I5-rocm-original-entry-f256fb6609` |
| 2026-11-13T03:40:24.932936+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 DIB-length-beyond-file：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034023.202508Z-I5-rocm-original-entry-35608950ad` |
| 2026-11-13T03:40:26.988989+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 zero-width-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034025.267306Z-I5-rocm-original-entry-20d4ac2a42` |
| 2026-11-13T03:40:29.031601+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 invalid-numeric-CLI：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034027.321964Z-I5-rocm-original-entry-f0b4c6b9e8` |
| 2026-11-13T03:40:31.053520+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 empty-directory：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034029.361876Z-I5-rocm-original-entry-80ba7cb643` |
| 2026-11-13T03:40:33.094608+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 output-path-is-file：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034031.385949Z-I5-rocm-original-entry-a207d23a66` |
| 2026-11-13T03:40:35.373852+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 write-failure-after-GPU：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034033.426261Z-I5-rocm-original-entry-e9ad036418` |
| 2026-11-13T03:40:37.667484+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-last-mixed-input：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034035.703646Z-I5-rocm-original-entry-6cd5d0a787` |
| 2026-11-13T03:40:54.223191+00:00 | IMG-01 | IN_PROGRESS | 完整冻结ID/逐case产品集合绑定扩展到运行与预分配：16项删减/重复反向检查 PASSED。 | `migration/reports/evidence/rewrite/I5/async-encoder-qualification-coverage-negatives/20261113T034053.094961Z-I5-CPU-negative-149228277d` |
| 2026-11-13T03:41:15.826864+00:00 | IMG-01 | IN_PROGRESS | 正式入口40项子集资格封存：原20项加16组线程/混合尺寸/错误合同、3预分配trace和固定输入生命周期；完整保留集/大索引/性能/冷构建未完成，保持PARTIAL。 | `migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T034114.794705Z-I5-composite-subset-qualification-3579a00bfa` |
| 2026-11-13T03:42:58.518101+00:00 | IMG-01 | IN_PROGRESS | 证据复审发现两个缺口：新runtime/预分配未封存两个build报告，runtime聚合未独立绑定产品集合。已加入双binary/build SHA与实际命令校验、逐case产品名/数量/唯一性及删除runtime产品反向检查；首版40项资格保留但不发布，重跑受影响证据。 | `tools/moat/image_encoder_runtime.py`；`tools/moat/image_encoder_preallocation.py`；`tools/moat/qualify_image_encoder_instances_v2.py` |
| 2026-11-13T03:43:04.491448+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 n0-s0-j1：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034301.484491Z-I5-rocm-original-entry-6e9a8caca1` |
| 2026-11-13T03:43:07.124761+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 threads-exceed-states：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034304.879287Z-I5-rocm-original-entry-80aa5e934c` |
| 2026-11-13T03:43:09.684869+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 states-exceed-threads：PASSED，实际产品 4；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034307.481908Z-I5-rocm-original-entry-5291d7113f` |
| 2026-11-13T03:43:12.736431+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 three-runs：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034310.039134Z-I5-rocm-original-entry-3944c5042b` |
| 2026-11-13T03:43:17.894522+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 j0-hardware-concurrency：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034313.087202Z-I5-rocm-original-entry-8b7bd77f0a` |
| 2026-11-13T03:43:20.888243+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 gpu-and-unavailable-hardware：PASSED，实际产品 3；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034318.268142Z-I5-rocm-original-entry-251279c815` |
| 2026-11-13T03:43:23.854946+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 mixed-size-slot-growth-reuse：PASSED，实际产品 17；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034321.249278Z-I5-rocm-original-entry-f1ffeca27b` |
| 2026-11-13T03:43:26.352044+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 single-large-repeated：PASSED，实际产品 19；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034324.189214Z-I5-rocm-original-entry-c62d7ad1e9` |
| 2026-11-13T03:43:28.394138+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034326.700623Z-I5-rocm-original-entry-462affd85d` |
| 2026-11-13T03:43:30.438756+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 DIB-length-beyond-file：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034328.733293Z-I5-rocm-original-entry-50b4b2c8be` |
| 2026-11-13T03:43:32.489345+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 zero-width-BMP：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034330.775132Z-I5-rocm-original-entry-ee4ab059d0` |
| 2026-11-13T03:43:34.516548+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 invalid-numeric-CLI：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034332.825374Z-I5-rocm-original-entry-0b14ad8432` |
| 2026-11-13T03:43:36.534796+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 empty-directory：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034334.857412Z-I5-rocm-original-entry-c1c9a70919` |
| 2026-11-13T03:43:38.553322+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 output-path-is-file：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034336.867170Z-I5-rocm-original-entry-3a43e477f3` |
| 2026-11-13T03:43:40.868775+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 write-failure-after-GPU：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034338.901594Z-I5-rocm-original-entry-c172a4ffd8` |
| 2026-11-13T03:43:43.148613+00:00 | IMG-01 | IN_PROGRESS | 扩展原入口 truncated-last-mixed-input：PASSED，实际产品 0；异常/部分输出亦保留。 | `migration/reports/evidence/rewrite/I5/encoder-remaining-runtime/20261113T034341.222166Z-I5-rocm-original-entry-0b3b1b31a0` |
| 2026-11-13T03:43:46.315070+00:00 | IMG-01 | IN_PROGRESS | 单图预分配 prepared-standard：PASSED；准备/稳态/端到端计时和实际传输、kernel逐项保存。 | `migration/reports/evidence/rewrite/I5/JPEG-single-input-preallocation/20261113T034343.598727Z-I5-rocm-trace-b57bc5c4a6` |
| 2026-11-13T03:43:49.407883+00:00 | IMG-01 | IN_PROGRESS | 单图预分配 prepared-optimized-repeated：PASSED；准备/稳态/端到端计时和实际传输、kernel逐项保存。 | `migration/reports/evidence/rewrite/I5/JPEG-single-input-preallocation/20261113T034346.679786Z-I5-rocm-trace-824d49feb2` |
| 2026-11-13T03:43:52.066775+00:00 | IMG-01 | IN_PROGRESS | 单图预分配 prepared-device-only：PASSED；准备/稳态/端到端计时和实际传输、kernel逐项保存。 | `migration/reports/evidence/rewrite/I5/JPEG-single-input-preallocation/20261113T034349.769292Z-I5-rocm-trace-3b0f0fac3b` |
| 2026-11-13T03:43:56.764352+00:00 | IMG-01 | IN_PROGRESS | 固定输入slot所有权/占用拒绝/普通提交失效/重新准备：PASSED；修改原CPU向量不污染已准备device输入。 | `migration/reports/evidence/rewrite/I5/JPEG-prepared-input-ownership/20261113T034352.516881Z-I5-rocm-probe-424030ce0e` |
| 2026-11-13T03:44:09.191656+00:00 | IMG-01 | IN_PROGRESS | 完整冻结ID/逐case产品集合绑定扩展到运行与预分配：17项删减/重复反向检查 PASSED。 | `migration/reports/evidence/rewrite/I5/async-encoder-qualification-coverage-negatives/20261113T034408.082260Z-I5-CPU-negative-68694cab6e` |
| 2026-11-13T03:44:25.455367+00:00 | IMG-01 | IN_PROGRESS | 正式入口40项子集资格封存：原20项加16组线程/混合尺寸/错误合同、3预分配trace和固定输入生命周期；完整保留集/大索引/性能/冷构建未完成，保持PARTIAL。 | `migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T034424.399537Z-I5-composite-subset-qualification-ff819aa0cd` |
| 2026-11-13T03:45:35.963738+00:00 | IMG-01 | IN_PROGRESS | 已将异步编码器40项当前子集资格发布到主表；线程/混合尺寸/错误合同和单图预分配证据补齐，图像整例计数仍13/26。 | `migration/reports/evidence/rewrite/I5/nvJPEG_nvJPEG-Encoder-MultipleInstances__nvJPEGEncMultipleInstances.cpp/20261113T034424.399537Z-I5-composite-subset-qualification-ff819aa0cd`；`migration/reports/image-encoder-instances-v2-publication.json` |

<!-- IMAGE_COMPLETION:END -->
