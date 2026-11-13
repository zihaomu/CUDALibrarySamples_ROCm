# 图像完整实现：逐入口缺口与依赖账本

本表记录当前主表和剩余工程义务。13 项旧整例资格保留；新计划完整源码语义复核尚未结束，不能将静态 token 清单视为完整 CLI 合同。

统计：{'PASSED': 13, 'PARTIAL': 9, 'FAILED': 4}。机器可读的源码 SHA、include 反向依赖、证明和漂移结果见 [inventory JSON](image-completion-inventory.json)。

| 原始入口 | 主表状态 | 后续阶段 | 明确欠项 |
| --- | --- | --- | --- |
| `NPP+/batchedLabelMarkersAndCompression::batchedLabelMarkersAndCompressionNPPPlus.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP+/cannyEdgeDetectorPython::cannyEdgeDetector.py` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP+/distanceTransform::unsignedAndSignedDistanceTransformNPPPlus.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP+/findContour::findContourNPPPlus.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP+/floodFill::floodFillVariousRegionTypesNPPPlus.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP+/watershedSegmentation::watershedSegmentationNPPPlus.cpp` | PARTIAL | IMG-02 | 当前分区/边界与 native 大幅差异尚未解释；平台区、相同高度、4/8 邻域和区域拓扑；完整原图产品及局部边界验收 |
| `NPP/batchedLabelMarkersAndCompression::batchedLabelMarkersAndCompression.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP/distanceTransform::distanceTransform.cpp` | PASSED | IMG-10 | 旧资格覆盖数学用例；原始六个 RAW 文件完整入口仍需实现/验收；六原图输出集合、Voronoi/dtype/所有原模式 |
| `NPP/findContour::findContour.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP/houghLines::houghLines.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP/nppCanny::npp_canny_simple.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP/nppCanny::npp_canny_simple.py` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP/opencvBenchmark::opencvBenchmark.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP/templateMatching::templateMatching.cpp` | PASSED | IMG-10 | 保留现有资格；按原始源码复核完整 CLI/条件分支/文件流程；共享核心变更后重跑受影响用例；最终冷构建复验 |
| `NPP/watershedSegmentation::watershedSegmentation.cpp` | PARTIAL | IMG-02 | 当前分区/边界与 native 大幅差异尚未解释；平台区、相同高度、4/8 邻域和区域拓扑；完整原图产品及局部边界验收 |
| `nvJPEG/Image-Resize-WaterMark::imageResizeWatermark.cpp` | PARTIAL | IMG-03, IMG-04, IMG-05 | progressive 解码仍有 CPU 熵/系数阶段；progressive 编码、源量化表和 APP/COM 继承；resize/watermark 全参数组合和全产品验证 |
| `nvJPEG/Image-Resize::imageResize.cpp` | PARTIAL | IMG-03, IMG-04, IMG-05 | progressive 解码仍有 CPU 熵/系数阶段；progressive 编码、源量化表和 APP/COM 继承；resize/watermark 全参数组合和全产品验证 |
| `nvJPEG/nvJPEG-Decoder-Backend-ROI::nvJPEGROIDecode.cpp` | PARTIAL | IMG-03, IMG-04 | progressive 解码仍有 CPU 熵/系数阶段；完整 backend/ROI/输出格式/自动标定/批处理合同；原始入口与 Python 调用、真实多 slot 调度复验 |
| `nvJPEG/nvJPEG-Decoder-MultipleInstances::nvJPEGDecMultipleInstances.cpp` | PARTIAL | IMG-03, IMG-04 | progressive 解码仍有 CPU 熵/系数阶段；完整 backend/ROI/输出格式/自动标定/批处理合同；原始入口与 Python 调用、真实多 slot 调度复验 |
| `nvJPEG/nvJPEG-Decoder/tests::test_decoder.py` | PARTIAL | IMG-03, IMG-04 | progressive 解码仍有 CPU 熵/系数阶段；完整 backend/ROI/输出格式/自动标定/批处理合同；原始入口与 Python 调用、真实多 slot 调度复验 |
| `nvJPEG/nvJPEG-Decoder::nvjpegDecoder.cpp` | PARTIAL | IMG-03, IMG-04 | progressive 解码仍有 CPU 熵/系数阶段；完整 backend/ROI/输出格式/自动标定/批处理合同；原始入口与 Python 调用、真实多 slot 调度复验 |
| `nvJPEG/nvJPEG-Encoder-MultipleInstances::nvJPEGEncMultipleInstances.cpp` | PARTIAL | IMG-01 | 完整保留集的native/独立CPU像素等价门槛；j0/大尺寸混合输入/IO与线程异常组合；64位transform索引、单图预分配与性能计时合同；当前提交冷检出和最终复审；并行prefix/异步slot/15 CLI/33产品已验 |
| `nvJPEG2000/nvJPEG2000-Decoder-Pipelined::nvjpeg2k_dec_pipelined.cpp` | FAILED | IMG-06, IMG-08, IMG-09 | GPU Tier1/MQ/HT 与完整码块系数链未完成；Part1/HT/NLT3、位深符号/浮点等源码必需模式；真实完整原图、tile/ROI/流水线和错误合同；既有 SDK/构建失败是历史证据，不能代替当前算法缺口 |
| `nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial::nvjpeg2k_decode_tile_partial.cpp` | FAILED | IMG-06, IMG-08, IMG-09 | GPU Tier1/MQ/HT 与完整码块系数链未完成；Part1/HT/NLT3、位深符号/浮点等源码必需模式；真实完整原图、tile/ROI/流水线和错误合同；既有 SDK/构建失败是历史证据，不能代替当前算法缺口 |
| `nvJPEG2000/nvJPEG2000-Decoder::nvjpeg2k_decode.cpp` | FAILED | IMG-06, IMG-08, IMG-09 | GPU Tier1/MQ/HT 与完整码块系数链未完成；Part1/HT/NLT3、位深符号/浮点等源码必需模式；真实完整原图、tile/ROI/流水线和错误合同；既有 SDK/构建失败是历史证据，不能代替当前算法缺口 |
| `nvJPEG2000/nvJPEG2000-Encoder::nvjpeg2k_encode.cpp` | FAILED | IMG-07, IMG-08, IMG-09 | GPU Tier1/MQ/HT 与完整码块系数链未完成；Part1/HT/NLT3、位深符号/浮点等源码必需模式；真实完整原图、tile/ROI/流水线和错误合同；既有 SDK/构建失败是历史证据，不能代替当前算法缺口 |

## 已冻结合同

[多实例 JPEG encoder](../rewrite/image-completion-encoder-contract.json)：原始质量夹取、下载开关、自动标定/状态/双缓冲等义务，七组初始 CUDA 探测。旧 q0 拒绝用例保留历史，但不作为原始语义兼容证明。

## 仍待完成的 IMG-00 工作

- 26-source full default/CLI/error/conditional semantic matrix
- held-out fixtures and numeric thresholds
- actual SDK loader identities for all families
- dependency review for dynamic/Python/external sources

本次证据：`migration/reports/evidence/rewrite/I0/image-completion-26-source-dependency-gap-ledger/20261113T032000.052970Z-I0-CPU-contract-bbaad78034`。当前资格以 `samples.yaml` 为准；组件实验不会自动升级样例。
