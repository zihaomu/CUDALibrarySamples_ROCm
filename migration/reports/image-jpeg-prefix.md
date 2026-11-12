# I5：JPEG 熵编码前缀扫描并行原型

状态：**孤立 GPU 组件 PASSED；未接入原始 JPEG 编码入口，入口资格不变**。

现有 baseline 和优化 Huffman 编码器的 block bit 偏移及 `0xff` byte stuffing 位置各由单线程 GPU kernel 顺序扫描。新增三阶段 tiled HIP 原型：每 256 元素并行扫描、tile 和求前缀、加 tile 基址。`bits` 模式输出每个 block 的 bit 起点和总 bit 数；`stuff` 模式输出每个 byte 的填充后位置和总 byte 数。每种模式的 1、255、256、257、4096、65536 元素输入均与独立 Python 逐元素参考精确一致，12/12 通过。

257 元素 bits 用例的 rocprofv3 实际记录 `scan_tile`、`scan_sums`、`add_bases` 各 1 个 GPU kernel，位于物理 GPU1 `0000:23:00.0`。改变第 128 个 block 长度后，变输入输出与独立参考精确一致，受影响的后缀改变。4097 bit 的非法 block 长度被拒绝，且没有输出文件。首次 Python 验收器日志路径错误在任何数值判断前中断，已按 `INTERRUPTED` 封存，修正后重跑成功；代码版本和命令保存在逐次原始日志中。

[预冻结合同](../rewrite/image-jpeg-prefix-profile.json) · [HIP 构建](image-jpeg-prefix-build.json) · [12 组逐元素结果](image-jpeg-prefix-runs.json) · [真实 GPU trace/变输入/负例](image-jpeg-prefix-trace.json) · [逐步实验记录](image-libraries-progress.md)。

该原型尚无与旧单线程 kernel 的隔离性能对照、长输入溢出门槛及 JPEG 整码流集成验证。三 kernel 的固定启动开销可能使小图更慢，不能据此声称性能提升。接入生产编码器后，必须重新验收两个 resize 入口和多实例入口、保留旧结果独立对照并重发逐例资格。
