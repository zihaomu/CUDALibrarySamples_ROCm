# Watershed：HIP 实验与未收口语义

两个原始入口已运行所有原图，22 件输出与独立项目 CPU 模型逐字节一致。这只证明项目八邻域下降算法正确执行；NPP 的浸没/平台区与边界语义仍有明显差异，因此两项保持 **PARTIAL**，不列入整例通过数。

| 模块 | 原图/产品 | 项目 CPU | 原生分割最小一致率 | 当前状态 |
| --- | ---: | --- | ---: | --- |
| NPP | 5/10 | 全部逐字节一致 | 71.71% | PARTIAL |
| NPP+ | 3/12 | 全部逐字节一致 | 71.71% | PARTIAL |

NPP+ 原生边界模式的最低逐像素一致率为 43.53%。原生标签 ID 不能直接比较，邻域分区一致率见完整 JSON。

证据： [合同](../rewrite/image-watershed-profile.json)、[AMD 执行](image-watershed-runs.json)、[独立 CPU](image-watershed-reference.json)、[22 产品原生比较](image-watershed-native-comparison.json)、[缺图拒绝](image-watershed-negative.json)、[真实 GPU trace](image-watershed-trace.json)。

下一步：实现分桶浸没/平台区分配，对 5090 原例预固定可接受的分割、边界和标签分区阈值后重做完整资格。

2026-11-12 的区域极小值/优先级浸没 CPU 候选已作为[独立研究记录](image-watershed-immersion-research.json)封存：CT skull 与原生分割仅 57.23% 一致、Lena 仅 42.18%，低于当前八邻域下降实现的 71.71% 和 92.51%。该候选没有接入 HIP，不能用于升级支持。下一轮先根据原生差异的图像强度、平台连通块和边界分布定位语义，再固定新算法门槛。
