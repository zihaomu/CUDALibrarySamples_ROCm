[![License](https://img.shields.io/badge/License-Apache_2.0-yellowgreen.svg)](LICENSE.md)

# CUDA Library Samples on ROCm

将 NVIDIA CUDA Library Samples 逐例实现为 ROCm 版本，按原例功能选择 AMD 生态库、HIP 算法或明确标注的 CPU/GPU 混合实现。原始 CUDA 样例保留作参考。

[算子支持方式与完整验证记录](migration/reports/support-log-index.md) · [已验收算子清单](migration/reports/operator-support.md) · [构建与复现](migration/usage.md) · [项目文档](migration/README.md)

## 整体支持情况

覆盖 **30 个模块、639 个独立样例入口**；其中 **19 个模块已有整例通过**，共 **131 个按模块去重的算子/功能族**。

| 当前结论 | 入口数 |
| --- | ---: |
| 已通过（PASSED） | 252 |
| 部分支持（PARTIAL） | 24 |
| 尚未通过（FAILED） | 363 |

尚未整例通过 **387 个入口**。通过结论限于该入口登记的原始功能和必需用例；精度、规模、语言、batch 和存储变体不重复增加算子数。未通过原因、部分实现范围和重现日志统一列在[详细记录](migration/reports/support-log-index.md)。

## 模块支持矩阵

路线列对应已通过样例的实际实现。部分支持与失败入口的实现、限制和证据见各模块详情。

| 模块 / 详细记录 | 已验收实现路线 | 算子/功能族 | 通过/总入口 | 部分 | 失败 |
| --- | --- | ---: | ---: | ---: | ---: |
| [cuBLAS](migration/reports/support-log-index/cuBLAS.md) | hipBLAS / rocBLAS + HIP | 52 | 72/82 | 0 | 10 |
| [cuBLASLt](migration/reports/support-log-index/cuBLASLt.md) | hipBLASLt、hipBLAS / rocBLAS + HIP 布局转换 | 1 | 8/20 | 0 | 12 |
| [cuBLASMp](migration/reports/support-log-index/cuBLASMp.md) | MPI + RCCL + HIP | 2 | 2/14 | 4 | 8 |
| [cuDSS](migration/reports/support-log-index/cuDSS.md) | rocSOLVER / rocBLAS + HIP、CPU 符号分析、项目描述符 ABI | 4 | 23/59 | 2 | 34 |
| [cuEST](migration/reports/support-log-index/cuEST.md) | 尚无整例通过 | 0 | 0/51 | 0 | 51 |
| [cuFFT](migration/reports/support-log-index/cuFFT.md) | hipFFT / rocFFT + HIP / HIPRTC；多卡使用 RCCL | 3 | 10/10 | 0 | 0 |
| [cuFFTMp](migration/reports/support-log-index/cuFFTMp.md) | MPI + hipFFT + RCCL + HIP | 1 | 1/20 | 0 | 19 |
| [cuPQC](migration/reports/support-log-index/cuPQC.md) | 项目 HIP SHA 实现 | 2 | 2/6 | 0 | 4 |
| [cuRAND](migration/reports/support-log-index/cuRAND.md) | hipRAND / rocRAND | 4 | 36/36 | 0 | 0 |
| [cuSOLVER](migration/reports/support-log-index/cuSOLVER.md) | hipSOLVER / rocSOLVER + HIP；多卡使用 RCCL | 10 | 23/39 | 4 | 12 |
| [cuSOLVERMp](migration/reports/support-log-index/cuSOLVERMp.md) | 尚无整例通过 | 0 | 0/16 | 2 | 14 |
| [cuSOLVERSp2cuDSS](migration/reports/support-log-index/cuSOLVERSp2cuDSS.md) | 尚无整例通过 | 0 | 0/7 | 0 | 7 |
| [cuSPARSE](migration/reports/support-log-index/cuSPARSE.md) | hipSPARSE / rocSPARSE + hipBLAS + HIP / HIP Graph | 20 | 36/37 | 0 | 1 |
| [cuSPARSELt](migration/reports/support-log-index/cuSPARSELt.md) | 项目 HIP 2:4 裁剪、压缩和稀疏乘法 | 1 | 2/2 | 0 | 0 |
| [cuTENSOR](migration/reports/support-log-index/cuTENSOR.md) | hipTensor、rocBLAS + HIP | 7 | 9/13 | 0 | 4 |
| [cuTENSORMg](migration/reports/support-log-index/cuTENSORMg.md) | hipBLAS + RCCL + HIP | 1 | 1/2 | 0 | 1 |
| [cuTENSORMp](migration/reports/support-log-index/cuTENSORMp.md) | 尚无整例通过 | 0 | 0/3 | 0 | 3 |
| [MathDx/cuBLASDx](migration/reports/support-log-index/MathDx__cuBLASDx.md) | 调用方 HIP kernel 内的协作计算 | 1 | 1/34 | 0 | 33 |
| [MathDx/cuFFTDx](migration/reports/support-log-index/MathDx__cuFFTDx.md) | 调用方 HIP kernel 内的 FFT | 1 | 1/49 | 0 | 48 |
| [MathDx/cuRANDDx](migration/reports/support-log-index/MathDx__cuRANDDx.md) | 尚无整例通过 | 0 | 0/7 | 1 | 6 |
| [MathDx/cuSolverDx](migration/reports/support-log-index/MathDx__cuSolverDx.md) | 调用方 HIP kernel 内的分解和求解 | 4 | 4/42 | 0 | 38 |
| [MathDx/libmathdx](migration/reports/support-log-index/MathDx__libmathdx.md) | 尚无整例通过 | 0 | 0/12 | 0 | 12 |
| [MathDx/nvCOMPDx](migration/reports/support-log-index/MathDx__nvCOMPDx.md) | 尚无整例通过 | 0 | 0/7 | 0 | 7 |
| [NPP](migration/reports/support-log-index/NPP.md) | 项目 HIP 图像处理实现 | 9 | 8/9 | 1 | 0 |
| [NPP+](migration/reports/support-log-index/NPP+.md) | 项目 HIP 图像处理 + ROCm Torch | 5 | 5/6 | 1 | 0 |
| [nvJPEG](migration/reports/support-log-index/nvJPEG.md) | 尚无整例通过 | 0 | 0/7 | 7 | 0 |
| [nvJPEG2000](migration/reports/support-log-index/nvJPEG2000.md) | 尚无整例通过 | 0 | 0/4 | 0 | 4 |
| [nvTIFF](migration/reports/support-log-index/nvTIFF.md) | 尚无整例通过 | 0 | 0/6 | 0 | 6 |
| [nvCOMP](migration/reports/support-log-index/nvCOMP.md) | hipCOMP + 项目 HIP CRC 实现 | 3 | 8/32 | 2 | 22 |
| [nvMatmulHeuristics](migration/reports/support-log-index/nvMatmulHeuristics.md) | 尚无整例通过 | 0 | 0/7 | 0 | 7 |

## 验证范围

- AMD 验证环境为 ROCm 10.1.0 / Radeon AI PRO R9700（gfx1201），CUDA 对照使用双 RTX 5090。版本、设备和逐例执行条件见[环境锁](migration/environments/project.lock.json)与详细记录。
- 每个通过入口均有对应正确性验收。独立 CPU 参考、原生 CUDA 基线与兼容 CUDA 数学对照分别登记；原始工具链缺失时明确保留限制。
- 描述符管理等功能按原例语义统计；CPU 阶段、项目 HIP 重写和生态库调用均在详细记录中标明。
- 性能独立验收，目前没有可发布的合格跨设备速度比。其它设备架构、Windows 与多节点范围尚未验证。

[支持方式、覆盖用例与完整日志](migration/reports/support-log-index.md) · [机器可读清单](migration/samples.yaml) · [性能验证](migration/reports/performance-comparison.md) · [上游项目说明](migration/upstream.md) · [许可证](LICENSE.md)
