# NPP/OpenCV benchmark 完整入口实施记录

状态：**PASSED / L4**。[组合资格](image-benchmark-qualification.json)与[三份独立复审](image-benchmark-review.json)已签发：HIP 四算子 C++ 原流程、6 组 CLI、独立 CPU 全量数值、18 项设备运行合同、原生 5090 对照、真实 GPU trace、35 项反例和固定提交 19 子冷检出通过。计入 NPP 已验收的 Gaussian、Canny、半尺寸双线性缩放和 RGB 灰度功能族；Canny 与该模块既有入口按一族去重。

入口：`NPP/opencvBenchmark::opencvBenchmark.cpp`。项目 C++ 入口保留原始 2048×1024 RAW 镜像平铺、4096×2048 默认规模、4 个算子、GPU kernel 与端到端计时、OpenCV 单线程与多线程计时、5 轮取中位数及 `-i/-w/-h/-n` 参数。AMD 计算使用 HIP C1 Canny、项目 HIP Gaussian 5×5、half bilinear resize、RGB→gray。CPU 列使用与 5090 原生 benchmark **同一固定源码提交**的 OpenCV 4.12.0 C++ 私有构建；200 个文件 SHA256/大小及 ROCm10 容器实际动态加载已核。[依赖记录](image-I3-rocm-OpenCV.json)

| 验收面 | 当前结果 |
| --- | --- |
| 原始 5090 | [未修改 CUDA 原例](image-I3-benchmark-native.json)已实际构建和完成默认 4096×2048、每次20轮、四算子及 OpenCV CPU 流程。其原始 stdout、GPU/SDK/库身份封存。 |
| 冻结合同 | [6 组 CLI 与数学政策](../rewrite/image-benchmark-profile.json)：128×96、129×97、原始默认4096×2048，另3个错误 CLI；Gaussian 系数/边界/舍入、Canny 变体、resize/RGB 容差及性能声明边界明确登记。数学政策是复审后补全的合同，旧粗合同与重验历史保留。 |
| HIP 构建和执行 | [真实编译](image-benchmark-build.json)与[6 组 GPU CLI](image-benchmark-runs.json)均成功；有效运行分别保存 4 个完整 RAW 输出。 |
| 独立数值 | [6 组 CPU 检查](image-benchmark-validation.json)通过。项目 Gaussian 与独立整数卷积、Canny 与独立 Sobel/NMS/阈值模型、resize 与 OpenCV bilinear、RGB→gray 与 OpenCV 对应模型逐全量输出检查；另核 GPU stdout 四行均差与 Canny 双方计数。奇数尺寸 resize 最大差1灰度级、平均差0.001953；默认规模四项目产品与项目 CPU 数值全量精确。错误 CLI 的原命令、输入、诊断与空产品均绑定检查。 |
| 当前跨实现差异 | [封存 stdout 重算](image-benchmark-native-comparison.json)确认同一输入/4096×2048/20×5/同一 OpenCV 构建和四算子顺序，且原生编译/运行/收集命令均成功。项目 Gaussian 的 replicate 边界与整数 binomial 变体相对 OpenCV 默认 REFLECT_101：small 均差0.109375、odd 0.061376、原始默认0.0004425；原生 NPP 相对 OpenCV 默认均差1.70。默认 Canny ROCm 相对 OpenCV 均差6.7539；原生 NPP 和 ROCm 都报546308边缘像素，OpenCV为324128。原始 NPP 像素文件未输出，不能据计数或均差推断两家逐像素一致。 |
| 实际设备语义 | [三新增核18项合同](image-benchmark-runtime.json)通过：普通/零输入/恢复/默认流、主机指针/不足物理分配/别名/非法尺寸/销毁流等拒绝与输出保持。首轮暴露被拒流后有效启动误报历史 HIP 错误，修复并保留失败实验。 |
| 真实 GPU 分发 | [rocprof trace](image-benchmark-trace.json)确认四算子及 Canny Sobel/NMS/阈值，六类 kernel 各13次，PCI/网格/时间和四个产品 SHA 已核。 |
| 资格反例 | [35项正反检查](image-benchmark-negative.json)拒绝原生失败状态/非零编译运行收集、CLI 案例互换、裁剪构建依赖，以及配对篡改CPU数值、runtime行、trace计数、原生统计与冷检出重复子项及把真实执行或编译替换为 echo/true；冷子源码依赖名与固定提交字节、实际运行命令及四类原始 `ldd` 输出另有反例。动态链接器在每次运行、runtime和trace前核实际GPU/OpenCV库路径与SHA。 |
| 性能 | 原始 GPU/OpenCV 时间及比率保存在各自 stdout；尚无同负载空闲设备、重复测量、同步与统计资格，**不发布跨 GPU 加速比**。 |

首次全尺度 CPU 验证误读了实验归档的大文件策略：大于4 MiB 的 RAW 输出保留在原始 artifact，并在 seal 中登记完整 SHA256，精简 archive 不复制这些字节。该失败检查及修正后重新验收均保留；当前验收从 manifest 指向原始 artifact，并核对 seal 与产品 SHA。

固定提交首次冷检出完成九项重跑和18项子封存，但最终比较误把随实验 ID 改变的依赖回执视为固定源码，故最终 FAILED；后续冷检出通过。独立复审又以成对篡改封存报告复现组合资格的假通过：原资格门只信报告状态，未从产品、原始命令、CSV和冷子结果独立重算。现已补复算和25项正反例，历史复审 REQUEST_CHANGES 与失败保留。随后固定提交冷检出的前九项成功，第十项反例因隔离检出无法读取上轮未归档的完整冷 raw 而失败；已把该反例限制为纯身份结构测试，完整 raw 独立重算仍在组合资格中，失败证据保留。原生 CUDA 的执行工作目录曾被错当成 clone 路径，另一次冷检出在最后反例失败；失败与修复均已封存。最终源码提交 `67f7dd83316b8a912c20f939f3ea209645ee74f6` 的10任务/19子证据冷检出已 PASSED，组合资格独立复算为 True。动态库身份门首次把 scp 复制的同 SHA SONAME 文件误判为不同路径，失败运行已恢复封存并改为核实际加载文件。剩余：独立复审、组合资格与 Git 锚定后发布。任一缺口未闭合时维持 PARTIAL。命令、源码 hash、物理设备、stdout/stderr 和产品 SHA 见逐实验封存；实施时间线见[图像库进展](image-libraries-progress.md)。

随后独立复审发现该源码的原生 nvcc 编译命令未固定，以及冷子源码依赖名/哈希、合同 profile、运行命令和状态可成对伪造。现已在资格门绑定六条原生命令、各类完整依赖集合与固定提交字节、生成报告与子封存语义、冷合同和六组原始 CLI；31项反例通过。修复后的固定源码 `a08e9e09db428045724c913a207cd3880cfde964` 冷检出10任务/19子记录PASSED，完整原始记录复算True；待新一轮复审和组合资格。旧成功冷证据只作历史记录。

第三项复审发现六组CLI、runtime、trace与冷运行的加载库身份只信汇总JSON，没有从本次 `ldd` stdout 重算。现已逐次解析原始输出的三条目标库路径，绑定构建库SHA和固定OpenCV回执，并以四类篡改反例验证拒绝；35项反例通过。固定源码 `a389b711d5ecd3e1b30ff199296662d6aa077ca7` 冷检出10任务/19子记录PASSED，完整原始记录复算True；待再次复审。

发布器核对时发现其整例必需用例和文字仍写旧25项，已同步为实际35项。该源码变化使前一冷检出只作历史证据，须再做固定提交冷检出和复审。

发布器修订后的固定源码 `96b9c5f0f695ba018783613a770889e89a7acb61` 冷检出10任务/19子记录PASSED，原始记录复算True；当时仍待独立复审与最终资格。

最终三份复审均 APPROVED，12/12 组合门通过，资格封存先入 Git；发布器再次核验22份引用记录、当前实现字节与所有必需用例后升级整例为 PASSED/L4。原生 NPP 仅提供统计和计时，不产生可逐像素比对的产品；跨设备性能比率未验收。
