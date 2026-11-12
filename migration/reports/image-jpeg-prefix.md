# I5：JPEG 熵编码前缀扫描并行原型

状态：**孤立 GPU 组件 PASSED；未接入原始 JPEG 编码入口，入口资格不变**。

现有 baseline 和优化 Huffman 编码器的 block bit 偏移及 `0xff` byte stuffing 位置各由单线程 GPU kernel 顺序扫描。新增三阶段 tiled HIP 原型：每 256 元素并行扫描、tile 和求前缀、加 tile 基址。`bits` 模式输出每个 block 的 bit 起点和总 bit 数；`stuff` 模式输出每个 byte 的填充后位置和总 byte 数。每种模式的 1、255、256、257、4096、65536 元素输入均与独立 Python 逐元素参考精确一致，12/12 通过。

257 元素 bits 用例的 rocprofv3 实际记录 `scan_tile`、`scan_sums`、`add_bases` 各 1 个 GPU kernel，位于物理 GPU1 `0000:23:00.0`。改变第 128 个 block 长度后，变输入输出与独立参考精确一致，受影响的后缀改变。4097 bit 的非法 block 长度被拒绝，且没有输出文件。首次 Python 验收器日志路径错误在任何数值判断前中断，已按 `INTERRUPTED` 封存，修正后重跑成功；代码版本和命令保存在逐次原始日志中。

[预冻结合同](../rewrite/image-jpeg-prefix-profile.json) · [HIP 构建](image-jpeg-prefix-build.json) · [12 组逐元素结果](image-jpeg-prefix-runs.json) · [真实 GPU trace/变输入/负例](image-jpeg-prefix-trace.json) · [逐步实验记录](image-libraries-progress.md)。

按预先冻结的[性能合同](../rewrite/image-jpeg-prefix-bench-profile.json)，在同一物理 GPU1 上分别检查旧单线程和新 tiled 输出与主机参考精确一致，再对每条路径做 3 次预热、20 次 HIP event 计时，取中位数：[逐次日志](image-jpeg-prefix-benchmark.json)。

| 模式 | 元素数 | 旧单线程中位数 | tiled 中位数 | tiled / 旧 |
| --- | ---: | ---: | ---: | ---: |
| block bits | 256 | 0.014520 ms | 0.015039 ms | 1.036 |
| block bits | 65,536 | 1.357940 ms | 0.059839 ms | 0.044 |
| block bits | 1,048,576 | 21.397400 ms | 0.387511 ms | 0.018 |
| `0xff` stuffing | 256 | 0.038399 ms | 0.015680 ms | 0.408 |
| `0xff` stuffing | 65,536 | 6.431180 ms | 0.059038 ms | 0.009 |
| `0xff` stuffing | 1,048,576 | 98.599400 ms | 0.382472 ms | 0.004 |

这只是隔离前缀阶段的单机实测；小图 bits 路线的三 kernel 启动开销略高。原型尚无 JPEG 整码流集成、全图吞吐和 32 bit 总位数溢出门槛验收，不能据此声称原始入口性能提升。接入生产编码器时应按输入规模选择路径，并重新验收两个 resize 入口和多实例入口、保留旧结果独立对照并重发逐例资格。
