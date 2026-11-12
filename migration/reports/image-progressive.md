# I4 progressive JPEG GPU 像素路径

当前六个关联入口仍为 **PARTIAL**。原始 `cat.jpg` 与 `img9.jpg` 的 progressive 熵解码和系数装配由 libjpeg-turbo 在 CPU 完成；反量化、8×8 IDCT、色度采样与 RGB 生成由项目 HIP kernel 在 AMD GPU 完成。当前实现会将 GPU 像素回读到 host 后再次传回现有图像管线，性能尚未验收。

| 原始图 | HIP vs 独立 libjpeg-turbo 非平滑 RGB 参考 | 固定门槛 |
| --- | --- | --- |
| `cat.jpg` | maxAbs 2；PSNR 60.76 dB | maxAbs ≤4；PSNR ≥50 dB |
| `img9.jpg` | maxAbs 3；PSNR 61.39 dB | maxAbs ≤4；PSNR ≥50 dB |

两张图的 HIP 像素均满足预冻结门槛；实际 profiler 记录 3 个 IDCT kernel 和 1 个 RGB kernel，位于获准的物理 AMD GPU，插桩前后输出 SHA 相同。完整解码器的 12 张原图均产出：10 张走 rocJPEG 硬件，2 张 progressive 走上述项目 GPU 路径，`cpu_fallback=0`。隔离后的六个 C++/Python 关联入口共 42 组既有流程重新运行，独立 CPU 与同输入 CUDA 数学对照均通过。

这些结果尚未签发整例资格。原生 nvJPEG backend 枚举、解耦流水线、多实例自动调度和图像重新编码等缺口因入口而异；当前旧 B10 验证器把 progressive CPU 回退写成固定原因，不能用于新路径的最终出版。新复合证明仅确认上述子集，冷检出与独立复审仍待执行。

证据：[预冻结合同](../rewrite/image-progressive-gpu-profile.json)、[原型两图数值](image-progressive-runs.json)、[实际 GPU trace](image-progressive-trace.json)、[完整入口12图](image-progressive-original-corpus.json)、[六入口子集资格](image-progressive-subset-qualifications.json)、[逐步实验](image-libraries-progress.md)。每次构建、失败和重试的 stdout/stderr、源码 SHA、设备快照在对应 `migration/reports/evidence/rewrite/I4/` 目录；失败的首次编译与布尔元数据验收也保留。
