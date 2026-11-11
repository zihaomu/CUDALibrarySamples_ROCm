# 图像库 I0/I1 当前实现检查点

状态：**IN_PROGRESS，未完成 I0/I1，未新增整例资格**。完整设计与每步实验见 [实施计划](../image-libraries-plan.md) 和 [实时记录](image-libraries-progress.md)。I2–I9 尚未开始。

| 已落地内容 | 实际结果 | 范围与证据 |
| --- | --- | --- |
| 原始材料清单 | 26 入口、24 构建定义、186 图像/参考资产 SHA 已固定 | [合同清单](../rewrite/image-contracts.json)；目前 CLI/API 是静态提示，完整语义矩阵仍待冻结 |
| 共享 HIP 图像阶段与 C ABI | 15 张输入、4,001,684 个 dx/dy/L2/NMS 数组元素与独立 CPU 完全一致 | [实现说明](../../rocm/common/image/README.md)、[逐例检查](image-I1-Canny-stages-validation.json)；尚无最终 Canny mask |
| 原生梯度交叉检查 | NPP C3 两张、NPP+ C1 三张，15 组完整梯度/幅度数组与独立 CPU 一致 | [原生梯度结果](image-I0-native-gradients-validation.json)；明确 native X=-dx、Y=dy，不外推到内部 NMS/连接 |
| 原生 NPP+/nvJPEG2000 SDK | 官方包 SHA 核验、私有安装、实际链接与运行 | [本地 SDK](image-I0-private-SDKs.json)、[5090 SDK](image-I0-native-private-SDKs.json)；SDK 二进制未发布到 Git |
| nvJPEG2000 四个原始入口 | 原始 CMake 构建与仓库 setup 自检通过；13 个实际输出文件 | [原生基线](image-I0-native-JPEG2000-originals.json)：整图/pipeline/512×512 ROI、classic/HT 无损编码回环；NLT/FP/YUV/quality 分支尚待补齐，AMD codec 尚未实现 |
| rocJPEG 原图实际解码 | HARDWARE 10/12 文件取得输出，HYBRID 创建返回 -12 | [实际调用](image-I0-rocJPEG-files.json)、[CPU 与完整像素测量](image-I0-JPEG-CPU-observations.json)；两张失败文件均为 CPU 可解码的 SOF2/10-scan progressive JPEG |
| 基础设施回归与审计 | 12 项既有资格/记录器与 16 项图像正反测试通过，封存审计、原始源码/支持计数不变、计划镜像检查通过 | [检查点验证](image-checkpoint-validation.json)；没有签发新的样例资格 |

## 需要继续解决的问题

1. **Canny 最终 mask**：NPP 13.2 与 NPP+ 0.10 同字节输入的最终行为不同。NPP+ 局部阈值模型在 13 个研究/独立输入中 11 个逐像素一致，其余两张共 3 个边界像素不一致；[失败坐标](image-I0-Canny-local-model.json)保留。边界 self 替换假设被新 holdout 否定，[候选合同已拒绝](../rewrite/image-canny-local-contract.json)，未保留对应 mask 实现。原生外部梯度已证明一致，下一步检查方向量化、NMS 边界和阈值阶段，随后完成三种真实调用入口与原始 Python 8 分辨率/1000 次循环。
2. **JPEG 像素规则**：10 张硬件成功图的 RGB 与独立 Pillow/libjpeg-turbo 完整比较中，8 张自然图 maxAbs 为 16–52，PSNR 为 42.47–51.49 dB。当前仅是测量，不能按初始候选 maxAbs≤2/PSNR≥48 dB 签发资格。需要分离 IDCT、色彩和 chroma upsampling，冻结一致输出规则；不能直接放宽误差。两张 progressive 文件仍需 GPU 熵/重建路径。
3. **尚未完成的 I0 范围**：其余入口完整 CLI/default/输入分支合同、全部 CPU/原生基线、JPEG/JPEG2000 GPU 熵编解码纵向原型、最终输入与阈值矩阵仍待实现。下载 SDK 或通过原生自检不替代这些步骤。

项目总量仍为 **241 PASSED / 23 PARTIAL / 375 FAILED**；本计划 26 个图像入口仍为 **2 PASSED / 8 PARTIAL / 16 FAILED**。性能、wave64、Windows 以及尚未验证的码流分支均未新增支持声明。

三项独立审查已批准固定代码 `66abeeebf9080ed99fa65bae98423cdc3679acec`，此前验收器/SDK 复现问题已修复并完成 16 项正反测试及真实数据复验。见[审查记录](image-independent-review.json)与[原始问题](image-review-4705868ef.json)。批准不代表 I0/I1 或任何原始 Canny 样例已完成。
