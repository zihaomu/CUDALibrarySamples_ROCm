# IMG-01：多实例 JPEG 编码器实施记录

状态：**IN_PROGRESS**。组件和候选验证不等于原始入口整例资格；图像当前仍为 **13 PASSED、9 PARTIAL、4 FAILED**。

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

实现位于 `rocm/common/image/jpeg_checked_prefix.hpp`、`jpeg_encoder_pipeline.hpp`、`jpeg_encoder_instances_v2.hpp`。原始 CUDA 文件不变；CPU 只承担输入/marker处理和基于GPU直方图的优化DHT设计。

新slot使用pinned输入/输出/元数据、可复用device workspace和HIP event推进。每个声明state映射到两个有独立stream的slot。自动线程标定进行真实测量，使用按CPU资源限定的二倍搜索，连续下降后停止；这些差异在[冻结候选合同](../rewrite/image-encoder-instances-v2-profile.json)明示，未声称厂商内部调度或性能一致。强制不存在的硬件后端返回能力错误。

初次四组trace验证失败是验证器错误地把ROCm内部拷贝/填充kernel计入算法数，并假定小拷贝必有DMA表。修正后单列全部运行时kernel，使用测试专用`hipMemcpyAsync`实参观察器核对大小/方向；原失败记录不改写。此次重叠观测不构成端到端加速结论。

## 独立复审与修复

按固定MOAT `pr-review`，独立review agent分别检查内核、资源生命周期和验证器；v2线程/取消/CLI候选的限定复审未发现新的必须修复问题。已修复的问题及复验：

1. `start`/`poll`中途异常遗留可复用状态：增加Preparing/Failed、同步排空和禁止复用；5处GPU故障注入通过。
2. prefix探针元素数向unsigned截断：读取/分配前拒绝；16组回归和两个稀疏超大文件通过。初审对`n*sizeof(unsigned)`乘法溢出的判断已撤回，`sizeof`会提升到size_t。
3. libjpeg外部依赖遗漏：纳入构建SHA；核心probe用dladdr核对实际加载路径和SHA。
4. 原生参考信任可变摘要：绑定封存结果、输入SHA、命令/5090收据及远端/本地产品身份。
5. JSON/Pillow/shape异常绕过封存：每case捕获并记录失败。
6. device-only进程混入旧参考下载：参考改为独立进程，再验证候选实际copy参数。
7. 聚合资格只检查case数量可能漏测：绑定冻结case ID和逐例产品集合，新增11项重复/缺失反向检查；发布时再次核查传递源码闭包，并把原始CUDA构建证据加入Git锚定引用。首版未发布资格保留，新资格替代后才更新主表。

## 尚未完成的入口验收

- 正式C++入口整合、当前提交资格重签、原入口多线程trace和输入变化重放。
- mixed尺寸工作区增长/复用、j0与状态交互、损坏BMP及IO/线程异常。
- 最大尺寸的生产64位索引；当前明确拒绝超出旧transform索引容量的输入。
- 单图全部预分配与计时边界、端到端性能分布；当前吞吐包含资源初始化，不能与vendor直接比较。
- 保留验收集、完整CPU/native等价门槛、冷检出重建和最终复审。

IMG-00的26入口语义审计及IMG-02–IMG-10仍未完成。阶段状态和每次实验见[完整计划](../image-completion-plan.md)及[实时实验记录](image-libraries-progress.md)。
