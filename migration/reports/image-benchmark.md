# NPP/OpenCV benchmark 完整入口实施记录

状态：**PARTIAL，整例资格待签发**。当前仅确认 HIP 四算子完整 C++ 流程、6 组 CLI 与独立 CPU 数值，尚不计入 PASSED 或已验收算子族。

入口：`NPP/opencvBenchmark::opencvBenchmark.cpp`。项目 C++ 入口保留原始 2048×1024 RAW 镜像平铺、4096×2048 默认规模、4 个算子、GPU kernel 与端到端计时、OpenCV 单线程与多线程计时、5 轮取中位数及 `-i/-w/-h/-n` 参数。AMD 计算使用 HIP C1 Canny、项目 HIP Gaussian 5×5、half bilinear resize、RGB→gray。CPU 列使用与 5090 原生 benchmark **同一固定源码提交**的 OpenCV 4.12.0 C++ 私有构建；200 个文件 SHA256/大小及 ROCm10 容器实际动态加载已核。[依赖记录](image-I3-rocm-OpenCV.json)

| 验收面 | 当前结果 |
| --- | --- |
| 原始 5090 | [未修改 CUDA 原例](image-I3-benchmark-native.json)已实际构建和完成默认 4096×2048、每次20轮、四算子及 OpenCV CPU 流程。其原始 stdout、GPU/SDK/库身份封存。 |
| 冻结 CLI | [6 组合同](image-benchmark-contracts.json)：128×96、129×97、原始默认4096×2048，另3个错误 CLI。 |
| HIP 构建和执行 | [真实编译](image-benchmark-build.json)与[6 组 GPU CLI](image-benchmark-runs.json)均成功；有效运行分别保存 4 个完整 RAW 输出。 |
| 独立数值 | [6 组 CPU 检查](image-benchmark-validation.json)通过。Gaussian 与项目整数卷积、Canny 与独立 Sobel/NMS/阈值模型、resize 与 OpenCV bilinear、RGB→gray 与 OpenCV C++ 对应模型逐全量输出检查。奇数尺寸 resize 最大差1灰度级、平均差0.002；默认规模三项颜色/滤波/resize全量精确。 |
| 当前跨实现差异 | [封存 stdout 重算](image-benchmark-native-comparison.json)确认同一输入/4096×2048/20×5/同一 OpenCV 构建和四算子顺序。默认 Canny 的 ROCm 与 OpenCV Canny 平均绝对差 6.7539；默认 ROCm 与原生 NPP 都报 546308 边缘像素，OpenCV 为 324128。原生 NPP Gaussian 相对 OpenCV 的均差 1.70，而项目 Gaussian 相对同版 OpenCV 参考为 0。原始 NPP 像素文件并未输出，不能据计数或均差推断两家输出逐像素一致。 |
| 实际设备语义 | [三新增核18项合同](image-benchmark-runtime.json)通过：普通/零输入/恢复/默认流、主机指针/不足物理分配/别名/非法尺寸/销毁流等拒绝与输出保持。首轮暴露被拒流后有效启动误报历史 HIP 错误，修复并保留失败实验。 |
| 真实 GPU 分发 | [rocprof trace](image-benchmark-trace.json)确认四算子及 Canny Sobel/NMS/阈值，六类 kernel 各13次，PCI/网格/时间和四个产品 SHA 已核。 |
| 性能 | 原始 GPU/OpenCV 时间及比率保存在各自 stdout；尚无同负载空闲设备、重复测量、同步与统计资格，**不发布跨 GPU 加速比**。 |

首次全尺度 CPU 验证误读了实验归档的大文件策略：大于4 MiB 的 RAW 输出保留在原始 artifact，并在 seal 中登记完整 SHA256，精简 archive 不复制这些字节。该失败检查及修正后重新验收均保留；当前验收从 manifest 指向原始 artifact，并核对 seal 与产品 SHA。

固定提交首次冷检出已完成九项重跑和18项子封存，但最终比较错误地把随实验 ID 改变的 OpenCV 依赖回执视为源码固定字节，故该轮最终状态 FAILED，证据保留。已把该检查改成固定源码 hash、OpenCV commit 和200个文件实际校验，等待重跑。剩余：固定提交冷检出；独立复审、组合资格与先 Git 锚定后发布。任一缺口未闭合时维持 PARTIAL。命令、源码 hash、物理设备、stdout/stderr 和产品 SHA 见逐实验封存；实施时间线见[图像库进展](image-libraries-progress.md)。
