# IMG-01：多实例 JPEG 编码器实施记录

状态：**IN_PROGRESS**。宽索引、自适应prefix与显存预检已接入正式入口并重建重验；当前48项PARTIAL子集已封存，待固定提交发布。完整入口尚有下列欠项，图像当前仍为 **13 PASSED、9 PARTIAL、4 FAILED**。[资格摘要](image-encoder-instances-v2-qualification.json)与[发布记录](image-encoder-instances-v2-publication.json)保留各自源码身份和发布状态。

| 工作 | 当前结果 | 完整证据 |
| --- | --- | --- |
| 原始 CUDA CMake/C++20 构建、7 CLI 探测 | 运行成功；19 JPEG 独立解码、尺寸/采样/量化通过 | [原生运行](image-completion-encoder-native.json)、[独立参考](image-completion-encoder-native-reference.json) |
| checked prefix | 16/16：逐元素/总数精确，非法长度和真实4Gbit累计溢出拒绝 | [结果](image-checked-prefix-runs.json) |
| 超uint32元素数输入 | 两个稀疏文件在读取/分配内容前拒绝 | [结果](image-checked-prefix-oversize.json) |
| 异步 slot | 14/14、84次编码；72个下载产品与旧核心逐字节一致；预热后工作区不增长 | [结果](image-encoder-pipeline-runs.json) |
| 中途分配失败 | 5处故障均禁止复用失败slot，新slot恢复执行 | [结果](image-encoder-pipeline-faults.json) |
| GPU 与传输 trace | 4/4；按独立JPEG参考推导6图实际算法kernel数；实际跨stream重叠；device-only只有元数据D2H | [trace和copy参数](image-encoder-pipeline-trace.json) |
| 原始C++入口接入v2 | 15/15：夹取、下载、输入截断/重复、自动标定、help与错误返回 | [逐例](image-encoder-instances-v2-runs.json) |
| CLI混合尺寸产品回归 | 33/33完整码流与旧GPU核心逐字节一致，参考BMP由独立Pillow读取 | [逐例比较](image-encoder-instances-v2-comparison.json) |
| 正式入口trace与变化重放 | 3/3；实际多线程/多stream、设备模式无payload传输、首图变化只影响对应任务 | [逐例](image-encoder-instances-v2-trace.json) |
| 扩展运行合同 | 16/16：j0、线程/状态交互、重复run、混合尺寸复用、损坏BMP、目录/写盘错误；错误批次不报告成功 | [逐例](image-encoder-runtime-runs.json)、[冻结合同](../rewrite/image-encoder-runtime-profile.json) |
| 单图预分配 | 3/3真实trace；标准19图仅两次RGB上传；每run每slot一次上传，稳态零工作区扩容；26件输出与旧串行核心精确一致 | [逐例](image-encoder-preallocation-runs.json)、[冻结合同](../rewrite/image-encoder-preallocation-profile.json) |
| 固定输入生命周期 | 独立device副本、占用拒绝、普通start使准备失效、重新prepare均通过 | [结果](image-encoder-prepared-lifecycle.json) |
| 独立宽索引候选 | 6/6实际图，54对数组、每侧408,329,636字节精确；18/18最大尺寸坐标通过独立Python参考和GPU trace；已接入正式入口，所有原40项及新增8组大图重验完成 | [逐图数组](image-encoder-wide-runs.json)、[坐标](image-encoder-wide-indices.json)、[冻结合同](../rewrite/image-encoder-wide-profile.json) |
| checked prefix分派测量 | 28组交替event测量+5组边界，完整CPU偏移/元数据通过；预登记5%连续优势规则选择bits≤128、stuff≤64串行，其余分块 | [逐例测量](image-prefix-dispatch-runs.json)、[冻结选择](../rewrite/image-prefix-dispatch-selection.json) |
| prefix保留边界 | 23组阈值前/等/后、分布、无效/溢出/空输入及22项host指针/计数拒绝通过；实际1或3算法kernel与冻结分派相符 | [逐例trace](image-prefix-holdout-runs.json)、[冻结保留集](../rewrite/image-prefix-holdout-profile.json) |
| 大图正式入口 | 8组、24产品；7组原协议通过，窄图1组按下述独立参考模式修订通过；65535横/竖轴Q100源像素精确 | [原始结果含失败](image-encoder-large-runs.json)、[参考修订](image-jpeg-reference-amendment.json) |
| CPU重建模式 | 6个新seed保留输入均通过；窄图三个产品maxAbs3，门槛保持4/1/2/48/.995；原maxAbs82失败保留 | [冻结修订](../rewrite/image-jpeg-reference-modes-profile.json)、[新保留集](image-jpeg-reference-modes-heldout.json) |
| 扩展覆盖检查 | 18个缺失/重复/错SHA/错误修订反例均拒绝，加完整正例，共19项通过 | [结果](image-encoder-extension-negatives.json) |
| 工作区容量 | 24组合法几何+5组非法输入通过独立Python64位参考；实际GPU1可用/总显存查询和阈值上下、复用边界通过；未进行巨大分配 | [容量结果](image-encoder-capacity.json)、[冻结合同](../rewrite/image-encoder-capacity-profile.json) |

实现位于 `rocm/common/image/jpeg_checked_prefix.hpp`、`jpeg_encoder_pipeline.hpp`、`jpeg_encoder_instances_v2.hpp`。原始 CUDA 文件不变；CPU 只承担输入/marker处理和基于GPU直方图的优化DHT设计。

宽索引、prefix和容量组件已在独立试验后接入当前工作区pipeline，正式入口当前源码回归已通过。容量预检计算必需常驻buffer下限并计入slot已拥有显存，在新图像工作区分配前拒绝明显超限；动态entropy缓冲和并发占用仍可能产生实际分配失败，不能把下限当成峰值内存。优化Huffman的uint32直方图另有`63*blocks <= UINT32_MAX`能力界限。算法kernel数量现在由独立串行参考JPEG的MCU数、去stuff后的entropy字节数和冻结阈值推导，不能继续套用每图固定16/17。

新slot使用pinned输入/输出/元数据、可复用device workspace和HIP event推进。每个声明state映射到两个有独立stream的slot。自动线程标定进行真实测量，使用按CPU资源限定的二倍搜索，连续下降后停止；这些差异在[冻结候选合同](../rewrite/image-encoder-instances-v2-profile.json)明示，未声称厂商内部调度或性能一致。强制不存在的硬件后端返回能力错误。

初次四组trace验证失败是验证器错误地把ROCm内部拷贝/填充kernel计入算法数，并假定小拷贝必有DMA表。修正后单列全部运行时kernel，使用测试专用`hipMemcpyAsync`实参观察器核对大小/方向；原失败记录不改写。此次重叠观测不构成端到端加速结论。

单图模式现在先为两个slot分别准备工作区和私有device RGB，再开始请求任务的计时；重复任务仍执行GPU色彩/FDCT/熵编码，不复用成品JPEG。普通`start`会使该固定输入准备状态失效。`TIMING`分别输出准备、编码/写盘、含销毁的单run执行耗时；其中`end_to_end_ms`从该run开始到资源销毁结束，不含进程启动、CLI解析和目录枚举。完整进程墙钟时间由实验命令记录，正式性能报告须单列。多图模式仍在编码区间包含读取与按需扩容。自动标定据此使用实际编码区间，搜索策略仍为已声明变体。

本轮三个带profiler的观察值如下，仅用于检查计时边界，不能与原生CUDA直接比较，也不是性能分布：

| case | 准备ms | 编码/写盘ms | 端到端ms | 实际算法kernel | RGB上传 |
| --- | ---: | ---: | ---: | ---: | ---: |
| prepared-standard，19请求 | 169.9430 | 9.3138 | 186.2830 | 336，含2次准备 | 2 |
| prepared-optimized-repeated，7请求×2runs | 37.6894 | 6.4252 | 51.2991 | 306，含4次准备 | 4 |
| prepared-device-only，19请求 | 164.9970 | 7.9879 | 180.3820 | 336，含2次准备 | 2 |

多run的耗时为程序选中的最佳run；kernel/拷贝统计是整个进程所有run的合计。原始逐次记录和产品SHA保留于上述证据目录。

## 独立复审与修复

按固定MOAT `pr-review`，独立review agent分别检查内核、资源生命周期和验证器；v2线程/取消/CLI候选的限定复审未发现新的必须修复问题。已修复的问题及复验：

1. `start`/`poll`中途异常遗留可复用状态：增加Preparing/Failed、同步排空和禁止复用；5处GPU故障注入通过。
2. prefix探针元素数向unsigned截断：读取/分配前拒绝；16组回归和两个稀疏超大文件通过。初审对`n*sizeof(unsigned)`乘法溢出的判断已撤回，`sizeof`会提升到size_t。
3. libjpeg外部依赖遗漏：纳入构建SHA；核心probe用dladdr核对实际加载路径和SHA。
4. 原生参考信任可变摘要：绑定封存结果、输入SHA、命令/5090收据及远端/本地产品身份。
5. JSON/Pillow/shape异常绕过封存：每case捕获并记录失败。
6. device-only进程混入旧参考下载：参考改为独立进程，再验证候选实际copy参数。
7. 聚合资格只检查case数量可能漏测：绑定冻结case ID和逐例产品集合，新增11项重复/缺失反向检查；发布时再次核查传递源码闭包，并把原始CUDA构建证据加入Git锚定引用。首版未发布资格保留，新资格替代后才更新主表。
8. 扩展运行检查首次15/16通过，发现BMP声明DIB长度超文件却被接受；读取器现要求完整DIB在文件内且像素offset位于DIB之后。首次失败保留，修复重建后16/16通过。
9. 新准备/复用/计时逻辑完成MOAT独立只读复审，未发现剩余必须修复问题；运行证据另行绑定当前资格。
10. 扩展证据复审发现：新运行记录未封存候选/参考build报告，runtime聚合未独立核对产品集合。现绑定两侧binary/build SHA和实际命令，核对成功case产品名称、数量与唯一性，新增删减runtime产品的反向检查；失败case仍允许保留已完成的部分输出。16组runtime、3组trace及生命周期重跑通过，17项反向检查通过，独立复审确认两项已关闭。首版40项资格未发布，修复后新资格才提交并发布。

11. CPU参考库身份复审发现仅验证预期文件，未绑定实际加载libjpeg；现用dladdr逐次记录路径并验证SHA。6个保留输入和3个修订产品重跑通过；另一个真实libjpeg经LD_LIBRARY_PATH注入后可完整解码，但资格身份门槛拒绝。4项正反检查通过，独立复审确认关闭；旧未发布资格及旧参考实验保留。

## CPU参考模式修订

libjpeg-turbo 在4:2:0下仅当降采样宽度大于2时启用精细上采样；stb在极窄图仍做垂直三角插值。原1×65500随机图的两种默认CPU重建出现maxAbs82，完整失败保持封存。采用独立libjpeg熵解码/ISLOW IDCT输出最近邻YCbCr，再由独立Python实现明确的边缘夹取三角重建/RGB601；6个新seed输入（宽1/2/3/4/5/17、Q1/80/100）先按原门槛通过，随后才用于三个历史产品的新验收。产品字节、GPU编码和数值门槛均未改变，修订仅解决CPU参考的重建模式差异，不代替完整CPU/native编码质量对照。

## 尚未完成的入口验收

- 正式C++入口整合、48项当前子集资格、多线程trace和输入变化重放已完成；仍需最终完整资格。
- 扩展16组mixed尺寸、j0/状态、损坏BMP和IO错误已通过；线程创建失败采用取消/join路径并经代码复审，仍需资源失败的完整边界审计。
- 宽索引、容量预检已接入正式入口，14组slot、5故障/4trace、全部运行合同与8组大图重验通过。坐标验收不代表65535×65535整图可装入设备。
- 单图预分配与计时边界已通过；prefix分派阈值测量和保留边界已通过；无profiler的端到端性能分布、峰值内存尚未完成，不能与vendor直接比较。
- 保留验收集、完整CPU/native等价门槛、冷检出重建和最终复审。

IMG-00的26入口语义审计及IMG-02–IMG-10仍未完成。阶段状态和每次实验见[完整计划](../image-completion-plan.md)及[实时实验记录](image-libraries-progress.md)。
