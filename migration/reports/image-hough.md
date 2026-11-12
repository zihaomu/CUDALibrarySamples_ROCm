# Hough Lines 完整图像入口实施记录

状态：**冷子身份验收已补强，整例资格待独立复审和发布**。目前主表 PARTIAL，不计入 PASSED 样例或已验收算子族。

入口：`NPP/houghLines::houghLines.cpp`。项目使用共享 HIP C1 Canny（Sobel、整数 L2、NMS、本项目局部阈值）和 HIP Hough 累加及峰提取；CPU 只排序 GPU 提取的候选线、绘制原例的 PPM、做原例真值提示和计时打印。原 CUDA 源码保留。

## 固定范围与结果

| 验收面 | 结果与证据 |
| --- | --- |
| 原始 CUDA | [5090 原生完整执行](image-I3-native-originals.json)：未修改源码、真实 NPP/CUDA 二进制及 GPU 回执，默认 1024×768 合成图输出完整 PPM、检测 10 条线、五条真值各两条 |
| 冻结合同 | [14 项合同](image-hough-contracts.json)与[固定输入](../rewrite/image-hough-profile.json)：默认/无计时合成图、五种 8u RAW、六类错误与 help |
| HIP 构建与全入口 | [当前构建](image-hough-build.json)、[14 次真实 GPU CLI](image-hough-runs.json)及[5 个非默认有效参数流程](image-hough-options.json)：共享 Canny、180 个角度×1 像素 rho 投票、3×3 局部峰、确定性票数排序；19/19 返回码符合合同 |
| 独立 CPU | [全量验证](image-hough-validation.json)：14/14；另 5/5 非默认参数；逐字节重建合成图和 RAW、Canny、rho/theta 投票与全部峰、完整线列表、诊断 CSV 与每个 PPM 字节；错误/帮助诊断单列 |
| GPU 运行语义 | [19 项实际设备合同](image-hough-runtime.json)与[逐峰 CPU 验证](image-hough-runtime-validation.json)：非默认/默认流、原图→清零→恢复同一输入缓冲，返回全部峰逐项重算；null/host/短物理分配/重叠/错误参数/未对齐/销毁流均拒绝且输入输出存储不变；8192² 空边缘实际执行超过2³²逻辑投票工作量，256² 半格双点只在分开FP32乘加下产生 `(147,49,2)` 峰。[跨设备空流](image-hough-foreign-stream.json)在物理GPU0仅建流，物理GPU1存储保持并拒绝外流 |
| 真实 GPU 分发 | [rocprofv3 trace](image-hough-trace.json)：物理 GPU1 的 Sobel、NMS、局部阈值、投票、GPU 峰提取均有非空网格与正时长；追踪下完整 PPM 未变 |
| 干净检出 | [新版固定提交冷重放](image-hough-cold.json)：45 条子记录重新执行并封存；资格门从子归档核实际运行与追踪命令、stdout、CPU 完整峰、GPU PCI/网格/时长/计数及产品，并核每组合同状态、backend、outcome、case 和父身份，通过 |
| 资格门反向检查 | [20 项变异](image-hough-qualification-checks.json)通过，包括配对改写冷子 PPM、runtime、runtime-validation、foreign-stream、trace、合同状态、构建结果与 manifest 身份；旧 11/12/16 项记录保留为历史 |
| 交叉厂商 | [完整差异](image-hough-native-comparison.json)：双方默认图都是 10 条线，五真值均覆盖；项目相对原生有 **10,627 个 RGB 像素不同**，红色线像素 IoU **0.23946**。部分 rho 偏 1 像素，故仅声明固定项目算法变体，不声称 NPP 逐像素一致 |

首次 HIP 编译对镜像数学头里的 `cosf/sinf` 设备重载失败；对应构建失败证据保留。项目改用固定 180 项 float32 三角表，后续编译和上述 GPU/CPU 验收通过。当前源代码补了实际设备地址范围、流和重叠检查。首次低票数非默认参数产生1196条峰，原例 stdout 按设计不列出超过40条的线，导致独立逐峰验收缺口；项目增加完整诊断 `hough_lines.csv`，同时保留原 stdout 行为。历史验收失败记录保留；修正后 19 CLI、CPU、运行合同、原生比较及 trace 均重验通过。

## 完成资格前剩余门槛

首次固定提交三范围复审均退回：大尺寸投票启动、未对齐指针、FP32融合半格、五参数命令来源、冷子输出、构建与原生CUDA收据/trace来源存在门槛缺口。第二次复审又发现冷 runtime/trace 子记录只核封存哈希，且原错位测试与span不足混杂；第三次验收复审发现冷合同状态和构建 manifest 结果可配对伪造。修正代码已添加足量实际分配与完整地址范围证明、冷子运行/trace重算、所有45子身份和状态核验。新版45子记录冷重放和20项反例已通过，真实失败和退回证据保留。剩余三范围独立复审、组合资格 Git 锚定、发布门测试，随后同步主表、算子支持表和首页。缺任何一项时保持 PARTIAL。

原始案例允许 `-t/-m/-cl/-ch/-n` 参数和 `-i/-w/-h` 文件模式。当前固定矩阵覆盖默认、无计时、五种 RAW、错误和 help；新增五种有效非默认参数覆盖票数阈值、最大线数截断、Canny 阈值、计时与组合输入。运行合同覆盖同一缓冲内容变化与恢复、多尺寸和无边线。资格门仍需固定源码独立审查。

所有命令、镜像/物理设备、源码哈希、stdout/stderr 和文件 SHA256 见各项封存 experiment。逐步骤时间线见[实施记录](image-libraries-progress.md)。
