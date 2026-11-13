# 项目文档

| 文档 | 内容 |
| --- | --- |
| [项目首页](../README.md) | 当前支持规模、模块矩阵和验证边界 |
| [支持方式与验证记录](reports/support-log-index.md) | 全部入口的实现方式、覆盖用例、成功/失败原因、源码、CPU/CUDA结果和完整日志 |
| [已验收算子清单](reports/operator-support.md) | 按模块去重的算子/功能族，以及对应样例和验证范围 |
| [构建与复现](usage.md) | 环境、构建命令、输入与证据复现 |
| [性能验证](reports/performance-comparison.md) | 独立的性能测量条件及结论 |
| [上游项目说明](upstream.md) | NVIDIA原始项目介绍、库列表和许可证 |
| [图像库完整支持方案](image-libraries-plan.md) | NPP/NPP+/JPEG/JPEG2000共26入口的重写路线、阶段、验收与实验日志要求 |
| [剩余图像完整实现计划](image-completion-plan.md) | IMG-00–IMG-10实施状态和每次实验同步记录 |
| [图像缺口与依赖账本](reports/image-completion-IMG-00.md) | 26入口当前资格、依赖和算法/运行语义欠项 |
| [JPEG编码器实施报告](reports/image-completion-IMG-01.md) | 异步slot、并行prefix、原生CUDA与独立解码、复审修复和剩余验收 |
| [开发与实验历史](history/README.md) | 计划、批次记录、失败/重试、勘误和交付归档 |

支持文档由 `migration/samples.yaml` 生成：`python3 tools/migration/render.py`。原始CUDA源码、已封存实验及其hash保持可追溯。
