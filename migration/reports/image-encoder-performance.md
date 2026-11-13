# 多实例 JPEG 编码性能与分配峰值

固定输入与测量合同见 [profile](../rewrite/image-encoder-performance-profile.json)。AMD 为物理 GPU1 gfx1201/ROCm10.1；CUDA 为 5090 物理 GPU1。每项 2 次预热、7 次无 profiler 独立进程测量。墙钟在各机器启动目标进程前开始、等待其退出后结束，包含进程启动、准备、编码和相应 IO；不含 SSH 和输入传输。

| 场景 | AMD 中位墙钟 ms | CUDA 中位墙钟 ms | AMD 设备动态峰值 bytes | CUDA 设备动态峰值 bytes | AMD pinned 峰值 bytes | CUDA pinned 峰值 bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| small-device-standard | 390.022 | 415.285 | 436076 | 83230720 | 76320 | 9437216 |
| small-download-optimized | 337.012 | 410.291 | 784604 | 83230720 | 100104 | 9437216 |
| medium-device-standard | 290.718 | 374.709 | 30067532 | 90832896 | 3713568 | 18874400 |
| medium-download-optimized | 264.664 | 369.645 | 22010200 | 84539392 | 1893460 | 9437216 |
| medium-write-optimized | 259.043 | 375.169 | 30053260 | 90832896 | 4069908 | 18874400 |
| large-download-standard | 756.18 | 776.39 | 1801787056 | 762259456 | 246163064 | 509607968 |

进程吞吐、全部 7 次结果、MAD/min/max/p95 和目标 PID 的 CPU RSS 分别见 [AMD v2](image-encoder-performance-v2-amd.json) 与 [CUDA v2](image-encoder-performance-v2-native.json)。两侧内部计时定义不同，仅保留原 stdout，不据此声明 GPU 内核加速；进程墙钟也受不同主机 CPU/启动开销影响。

[峰值重建](image-encoder-memory-summary.json) 使用独立 profiler 运行，按分配地址、大小和释放时间重建存活区间。它是被追踪 API 的 allocation 峰值，不代表驱动保留内存或总 VRAM。AMD runtime pool、CUDA static device 和 pinned API 分开记录；不同类别峰值不能直接相加。全部应用 device/pinned 分配已退还，runtime 保留项单列。

旧 `image-encoder-performance-{amd,native}.json` 的 `child_max_RSS_KiB` 是 wrapper 全部历史子进程的累计峰值，可能含 ldd/nvidia-smi；不能归属于编码器。旧结果保留。v2 通过 `wait4` 读取目标 PID RSS；[反向检查](image-encoder-performance-controls.json) 证明 128 MiB 准备进程不会污染小目标进程峰值。墙钟与独立 allocation 记录未因该修复失效。

这些性能观察没有设“必须快于 CUDA”的通过门槛；数值、完整功能和生产 GPU 归属另行验收。
