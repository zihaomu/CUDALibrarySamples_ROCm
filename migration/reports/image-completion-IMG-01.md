# IMG-01：多实例 JPEG 编码器实施记录

状态：**IN_PROGRESS**。新异步实现已接入正式C++入口；本轮单图预分配和扩展运行合同通过，40项当前子集资格已发布为PARTIAL。完整入口尚有下列欠项，图像当前仍为 **13 PASSED、9 PARTIAL、4 FAILED**。当前[资格摘要](image-encoder-instances-v2-qualification.json)与[发布记录](image-encoder-instances-v2-publication.json)绑定已提交代码和不可变证据。

| 工作 | 当前结果 | 完整证据 |
| --- | --- | --- |
| 原始 CUDA CMake/C++20 构建、7 CLI 探测 | 运行成功；19 JPEG 独立解码、尺寸/采样/量化通过 | [原生运行](image-completion-encoder-native.json)、[独立参考](image-completion-encoder-native-reference.json) |
| checked prefix | 16/16：逐元素/总数精确，非法长度和真实4Gbit累计溢出拒绝 | [结果](image-checked-prefix-runs.json) |
| 超uint32元素数输入 | 两个稀疏文件在读取/分配内容前拒绝 | [结果](image-checked-prefix-oversize.json) |
| 异步 slot | 14/14、84次编码；72个下载产品与旧核心逐字节一致；预热后工作区不增长 | [结果](image-encoder-pipeline-runs.json) |
| 中途分配失败 | 5处故障均禁止复用失败slot，新slot恢复执行 | [结果](image-encoder-pipeline-faults.json) |
| GPU 与传输 trace | 4/4；每6图96个标准/102个优化算法kernel；实际跨stream重叠；device-only只有元数据D2H | [trace和copy参数](image-encoder-pipeline-trace.json) |
| 原始C++入口接入v2 | 15/15：夹取、下载、输入截断/重复、自动标定、help与错误返回 | [逐例](image-encoder-instances-v2-runs.json) |
| CLI混合尺寸产品回归 | 33/33完整码流与旧GPU核心逐字节一致，参考BMP由独立Pillow读取 | [逐例比较](image-encoder-instances-v2-comparison.json) |
| 正式入口trace与变化重放 | 3/3；实际多线程/多stream、设备模式无payload传输、首图变化只影响对应任务 | [逐例](image-encoder-instances-v2-trace.json) |
| 扩展运行合同 | 16/16：j0、线程/状态交互、重复run、混合尺寸复用、损坏BMP、目录/写盘错误；错误批次不报告成功 | [逐例](image-encoder-runtime-runs.json)、[冻结合同](../rewrite/image-encoder-runtime-profile.json) |
| 单图预分配 | 3/3真实trace；标准19图仅两次RGB上传；每run每slot一次上传，稳态零工作区扩容；26件输出与旧串行核心精确一致 | [逐例](image-encoder-preallocation-runs.json)、[冻结合同](../rewrite/image-encoder-preallocation-profile.json) |
| 固定输入生命周期 | 独立device副本、占用拒绝、普通start使准备失效、重新prepare均通过 | [结果](image-encoder-prepared-lifecycle.json) |

实现位于 `rocm/common/image/jpeg_checked_prefix.hpp`、`jpeg_encoder_pipeline.hpp`、`jpeg_encoder_instances_v2.hpp`。原始 CUDA 文件不变；CPU 只承担输入/marker处理和基于GPU直方图的优化DHT设计。

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

## 尚未完成的入口验收

- 正式C++入口整合、40项当前子集资格、多线程trace和输入变化重放已完成；仍需最终完整资格。
- 扩展16组mixed尺寸、j0/状态、损坏BMP和IO错误已通过；线程创建失败采用取消/join路径并经代码复审，仍需资源失败的完整边界审计。
- 最大尺寸的生产64位索引；当前明确拒绝超出旧transform索引容量的输入。
- 单图预分配与计时边界已通过；无profiler的端到端性能分布、峰值内存及prefix分派阈值测量尚未完成，不能与vendor直接比较。
- 保留验收集、完整CPU/native等价门槛、冷检出重建和最终复审。

IMG-00的26入口语义审计及IMG-02–IMG-10仍未完成。阶段状态和每次实验见[完整计划](../image-completion-plan.md)及[实时实验记录](image-libraries-progress.md)。
