# CUDA Samples on ROCm：后续多批支持计划与能力边界

日期：2026-11-10。文档状态：**B4–B8 正在按实时表实施；B9–B15 尚未启动。以下正文保留原始计划基线**。

[12 批总览](#batches) · [当前无法等价支持的项目与原因](#limits) · [验收与日志规则](#acceptance) · [473 项逐例去向](#inventory)

<!-- B4B8_PROGRESS:START -->

**B4–B8 实施更新：** B4 8/8；B5 0/4；B6 0/4；B7 0/5；B8 0/5。当前主表 174 个样例通过。[实时验收表](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/batches4-8.md)。以下 166/473 等数字为原始计划基线；本更新不改写历史计划。

<!-- B4B8_PROGRESS:END -->

## 1. 当前基线与计划目标

基线提交：`7ef677909e8d32a796c6d205dacbd74a02c44ba6`。639 个入口中，**166 PASSED、6 PARTIAL、464 FAILED、2 UNSUPPORTED、1 BLOCKED**；已有 9 个合格模块、91 个按模块去重的算子/功能族。473 个入口尚未整例通过。第二批 17 例/45 cases、第三批 8 例/26 cases 已完成。M0–M5 “已执行”包含真实失败，不等于全库已支持。

后续按“接口修复与已知数学 → 布局/高级语义 → codec/科学算法 → 多进程/设备内计算”推进。每例优先 AMD 官方库，兼容层不适合时直接使用 roc*，需要项目 HIP/CPU 阶段时公开写明。所有原始 CUDA 源码/构建定义保持不变；新代码与观测适配独立保存。

AMD 固定 ROCm 10.1.0 immutable foundation（镜像 `sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03`）、R9700/gfx1201；HIP 7.16 为正常组件版本。CUDA 对照使用 nvidia-5090x2、CUDA 13.4.92/sm_120。物理 GPU3 禁止计算；每次启动按 PCI 映射及动态预约选卡，不沿用上批空闲假设。多节点和独占性能资源目前没有完成资格验证。

**“不可能支持”的准确边界：** 现有证据能够证明某个锁定版本/硬件/现成 API 路线不可用，或某种 NVIDIA 专属执行/二进制契约不能原样搬到 AMD；不能由此证明一个通用数学、图像或压缩算法在 AMD 上永远无法实现。第 4 节逐项说明“无法保持的是什么、证据是什么、改变什么条件可以恢复”。

本次只制定与发布计划，不启动新 GPU 实验，不改变逐例 status/required cases，不把 65 个候选预先算作通过。支持范围与全部 log 见[统一索引](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/support-log-index.md)，机读计划见[roadmap.json](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/roadmap.json)。

<a id="batches"></a>

## 2. 十二批候选总览

近期 B4–B6：16 个样例；中期 B7–B11：29 个；条件研究 B12–B15：20 个；合计 **65 个互不重复候选**，其余 **408 个未通过入口**归入带原因的门槛/研究队列。候选量不等于保证成功量，批次也不等于新增数学算子族。

| 批次 | 阶段 / 风险 | 主题 | 样例候选 | 首要依赖 |
| --- | --- | --- | ---: | --- |
| [B4](#b4) | 近期 / 低到中 | 基础 API 修复与两种稀疏格式 | 8 | 已有 BLAS、QR、CSR 数值验收基础 |
| [B5](#b5) | 近期 / 中，cache 项需先探针 | 张量布局、einsum 与 contraction 执行语义 | 4 | 第二批 tensor 与既有 rocBLAS + HIP contraction 路线 |
| [B6](#b6) | 近期 / 中 | 64 位求解器接口与三角求逆 | 4 | 已有 LU、SVD、选区特征分解参考 |
| [B7](#b7) | 中期 / 中到高 | Grouped GEMM 与算法搜索/调优 | 5 | B4；已验收 hipBLASLt HSH 与 SGEMM |
| [B8](#b8) | 中期 / 高 | 高级稀疏转换、内存策略与自定义运算 | 5 | B4 的格式桥接；已有 HIPRTC/SPIR-V 经验 |
| [B9](#b9) | 中期 / 中到高 | LZ4/Snappy 从单 chunk 探针扩展到原始流程 | 8 | 现有 hipCOMP LZ4 单 chunk 往返；先建立 codec/包格式互操作探针 |
| [B10](#b10) | 中期 / 中到高 | JPEG 解码完整输入流程、ROI 和后处理 | 6 | 现有 rocJPEG baseline + RPP resize 探针；B5 的 stride/padding 检查可复用 |
| [B11](#b11) | 中期门槛批 / 高；通过能力门槛后再实施 | 稀疏直接求解从 SPD 子集扩展 | 5 | 已有 CPU 符号分析 + GPU CSRRF；先建立一般/对称矩阵数值分解能力 |
| [B12](#b12) | 条件研究 / 高 | 多进程多 GPU BLAS 与数据分布 | 6 | MPI + RCCL 环境与至少两张允许使用的 AMD 卡；先通过通信/分布探针 |
| [B13](#b13) | 条件研究 / 很高 | 多 GPU 分解/FFT/张量算法 | 6 | B12 的分布和通信基础；对应单卡参考；按 Mg 与 Mp 分别实现执行模型 |
| [B14](#b14) | 条件研究 / 很高 | MathDx 设备内算子四个试点 | 4 | 分别建立 AMD 设备端 ABI、协作粒度与原始 oracle；不能使用 host 库调用替代 |
| [B15](#b15) | 条件研究 / 高 | 图像基础算法的 GPU 重写试点 | 4 | RPP 格式/stride 探针；先做各算法 GPU 能力探针和 CPU oracle |

**排期顺序：** B4 → B5 → B6；B7/B8/B9 可按设备与 SDK 条件选先后，随后 B10；B11 必须先补一般稀疏数值能力。B12/B13 依赖多 rank 多卡，B14/B15 各自先做一个设备内/图像算子探针。GPU 共享预约和 vendor SDK 会影响工期，当前不承诺日历日期。

每批分为“源码/能力核对 → 最小真实 GPU 探针 → 锁定 case → 实现 → AMD/独立 CPU/CUDA 验收 → 反向检查 → 文档及 fork 发布”。门槛失败时记录失败与恢复条件，继续可独立推进的批次；不把缺能力项强行降精度或改执行模型来凑通过率。

<a id="b4"></a>

### B4：基础 API 修复与两种稀疏格式（8 例）

**候选路线：** hipBLAS/rocBLAS；hipSOLVER；HIP 格式桥接 + hipSPARSE/rocSPARSE。

**开始门槛：** 先核对 hipBLAS Ex 的 computeType/const 指针签名；修复 ormqr 观测代码中的不存在变量 X。稀疏原生 NOT_IMPLEMENTED 保留为历史失败，再验证 GPU 格式桥接。

**验收：** BLAS 全输出 CPU 参考、HERK 共轭/对角虚部/三角区、packed 布局与 padding；QR 重构/Q 应用/求解残差；SELL 填充槽与三角属性、BSR 块内行列序和 alpha/beta。格式转换与数值计算均留在 GPU。

**case 草案：** original；nonzero-beta；transpose/conjugate；lower/upper；padded-lda/不规则阶数；稀疏 changed-values、unit-diagonal、block-order、存储的零值。每项只登记适用组合。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuBLAS/Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu.md) | FAILED |
| [`cuBLAS/Extensions/CherkEx/cublas_CherkEx_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/CherkEx/cublas_CherkEx_example.cu.md) | FAILED |
| [`cuBLAS/Extensions/CsyrkEx/cublas_CsyrkEx_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/CsyrkEx/cublas_CsyrkEx_example.cu.md) | FAILED |
| [`cuBLAS/Extensions/trttp/cublas_trttp_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/trttp/cublas_trttp_example.cu.md) | FAILED |
| [`cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu.md) | FAILED |
| [`cuSOLVER/ormqr/cusolver_ormqr_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/ormqr/cusolver_ormqr_example.cu.md) | FAILED |
| [`cuSPARSE/spsv_sell/spsv_sell_example.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spsv_sell/spsv_sell_example.c.md) | FAILED |
| [`cuSPARSE/sddmm_bsr/sddmm_bsr_example.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/sddmm_bsr/sddmm_bsr_example.c.md) | FAILED |

B4 中 packed↔triangular 两例登记为项目 HIP GPU 实现；其余优先生态库。`ormqr` 两端旧日志的 `X is undefined` 来自项目观测适配，修复该问题不应表述为 AMD 数学库不支持。

<a id="b5"></a>

### B5：张量布局、einsum 与 contraction 执行语义（4 例）

**候选路线：** hipTensor 优先；FP32 路线不满足时使用 rocBLAS + HIP 排列/分块；项目层 cache 适配须明确登记。

**开始门槛：** 先核验 dtype、host/device 指针、stride/padding 和原始规模内存。cache 必须有真实可复用对象与失效规则；不能删除 cache 调用后称原例通过。

**验收：** 原始规模保持，必要时分块流式 CPU 参考；小尺寸全量检查，原始规模的检查覆盖率逐例公开。trinary 检查收缩顺序、alpha/beta 与全部语义输出；einsum 限于原例实现的语法；cache 验证冷启动/命中/进程重启/失效和结果一致。

**case 草案：** 原始 profile；小尺寸非整齐 extents；非零 beta；非零 padding/非连续 stride；cache 文件不存在、有效与损坏、描述变化；原始 einsum 的 5 个表达式。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuTENSOR/elementwise_permute_padding.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/elementwise_permute_padding.cu.md) | FAILED |
| [`cuTENSOR/einsum.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/einsum.cu.md) | FAILED |
| [`cuTENSOR/contraction_trinary.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/contraction_trinary.cu.md) | FAILED |
| [`cuTENSOR/contraction_plan_cache.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/contraction_plan_cache.cu.md) | FAILED |

原始 padding 样例重复给 `paddingLeft` 赋值，`paddingRight` 对应项实际默认为 0：保留这个原始 case，再独立添加左右非零 case，不能静默把注释当运行事实。trinary 的 A、D 各约 4 GiB，须另计中间张量/workspace；不据旧超时日志直接判硬件不支持。einsum 只要求原例 5 个表达式，原 parser 的 ellipsis/broadcast TODO 不计作已支持。

<a id="b6"></a>

### B6：64 位求解器接口与三角求逆（4 例）

**候选路线：** hipSOLVER 能保留契约时使用；否则优先直接 rocSOLVER 的对应 GPU API。

**开始门槛：** 确认安装包中的真实 64 位函数、pivot/info 类型与 workspace 单位。Xgetrf 的 algo0/algo1 和无 pivot 分支分别核验，不能把两种选项无说明映射成同一路径。

**验收：** PA=LU、Ax=b；三角逆 AA^{-1}=I；SVD 重构与正交性；选区 meig 与特征对残差。不得以小矩阵可用为由静默截断 int64 接口；未保持的选项继续 PARTIAL。

**case 草案：** original；pivot/no-pivot（原例适用时）；singular-info；padded leading dimension；选区 index/value/all/empty；upper/lower/unit diagonal。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu.md) | FAILED |
| [`cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu.md) | FAILED |
| [`cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu.md) | FAILED |
| [`cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu.md) | FAILED |

<a id="b7"></a>

### B7：Grouped GEMM 与算法搜索/调优（5 例）

**候选路线：** hipBLAS Grouped Ex、hipBLASLt/hipBLASLtExt + 项目搜索驱动。

**开始门槛：** 先检查所需 grouped、compute type、算法枚举/计时入口是否可用；CUDA algorithm ID 不跨库照搬。原例 autotune 必须真实搜索，不能固定一次 GEMM 代替。

**验收：** 异构 group/尺寸/alpha/beta、完整输出参考；搜索候选各自正确，workspace 限制生效，所选算法可重放。性能排名只有空闲资格通过后才发布。

**case 草案：** 不同 group 大小；transpose；workspace=0/受限；多候选；无可用候选；重复选型。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu.md) | FAILED |
| [`cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu.md) | FAILED |
| [`cuBLASLt/LtHSHgemmGroupedSimple/main.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtHSHgemmGroupedSimple/main.cpp.md) | FAILED |
| [`cuBLASLt/LtSgemmCustomFind/main.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtSgemmCustomFind/main.cu.md) | FAILED |
| [`cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp.md) | FAILED |

<a id="b8"></a>

### B8：高级稀疏转换、内存策略与自定义运算（5 例）

**候选路线：** hipSPARSE/rocSPARSE + HIP 格式/对称展开；自定义 op 使用 HIPRTC 或设备 HIP 实现。

**开始门槛：** 逐项核对格式转换、SpGEMM 内存预算语义、symmetric 存储、自定义乘加行为。函数名缺失不能直接判硬件不支持。

**验收：** CSR/COO 结构和数值、索引基数、对称三角只计一次；SpGEMM 分块/预算不能忽略；custom op 必须真的在 GPU 数值路径生效，保留设备执行模型。

**case 草案：** empty rows；index-base0/1；非均匀行长；内存预算变化；上下三角；普通运算与自定义乘加产生不同结果。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuSPARSE/spmat_convert/spmat_convert_example.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmat_convert/spmat_convert_example.c.md) | FAILED |
| [`cuSPARSE/spgemm_mem/spgemm_mem_example.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spgemm_mem/spgemm_mem_example.c.md) | FAILED |
| [`cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c.md) | FAILED |
| [`cuSPARSE/spmvop_csr/spmv_csr_op_example.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmvop_csr/spmv_csr_op_example.c.md) | FAILED |
| [`cuSPARSE/spmm_csr_op/spmm_csr_op_example.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c.md) | FAILED |

<a id="b9"></a>

### B9：LZ4/Snappy 从单 chunk 探针扩展到原始流程（8 例）

**候选路线：** 锁定 hipCOMP + 项目 API/metadata 适配；原例明确的 CPU 编解码阶段保留独立 CPU codec。

**开始门槛：** 检查现代 nvCOMP 的 batch、status/options、manager 和 header/bitstream 语义；先跑两个库间互解，不能只证明同库 round-trip。

**验收：** 逐 chunk 真实长度/status、最大输出尺寸、变长 batch、空/重复/随机输入及截断损坏数据；原始 CPU/GPU 阶段分工保留。若 quickstart 暴露其它未支持 codec，只验 LZ4 不得把整例改 PASSED。

**case 草案：** 原始默认配置；batch1/多 chunk/不等长；0/1/边界长度；CPU→GPU、GPU→CPU 互操作；损坏/截断流；重复执行。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`nvCOMP/examples/low_level_quickstart_example.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/low_level_quickstart_example.cpp.md) | PARTIAL |
| [`nvCOMP/examples/high_level_quickstart_example.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/high_level_quickstart_example.cpp.md) | FAILED |
| [`nvCOMP/examples/lz4_cpu_compression.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/lz4_cpu_compression.cu.md) | FAILED |
| [`nvCOMP/examples/lz4_cpu_decompression.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/lz4_cpu_decompression.cu.md) | FAILED |
| [`nvCOMP/examples/snappy_cpu_compression.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/snappy_cpu_compression.cu.md) | FAILED |
| [`nvCOMP/examples/snappy_cpu_decompression.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/snappy_cpu_decompression.cu.md) | FAILED |
| [`nvCOMP/benchmarks/benchmark_lz4_chunked.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_lz4_chunked.cu.md) | FAILED |
| [`nvCOMP/benchmarks/benchmark_snappy_chunked.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_snappy_chunked.cu.md) | FAILED |

<a id="b10"></a>

### B10：JPEG 解码完整输入流程、ROI 和后处理（6 例）

**候选路线：** rocJPEG + RPP/HIP；Python 只作为真实 GPU CLI 的测试驱动。

**开始门槛：** 先遍历原始 JPEG 输入集合和 format/backend 参数，测 hardware/software 路线的实际支持；明确 progressive、subsampling、ROI 的缺口。

**验收：** CPU libjpeg 参考与颜色/布局容差、所有原始输入、batch/多实例/ROI、文件读写与退出码；resize/watermark 检查组合结果；Python imports 通过不代替 GPU 测试。JPEG encoder 不在该批。

**case 草案：** 原始 corpus；各可用输出布局；ROI 边界；batch/多实例重复；无效输入；resize 尺寸与 watermark alpha；CLI 成功/失败。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp.md) | PARTIAL |
| [`nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp.md) | FAILED |
| [`nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp.md) | FAILED |
| [`nvJPEG/Image-Resize/imageResize.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/Image-Resize/imageResize.cpp.md) | FAILED |
| [`nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp.md) | FAILED |
| [`nvJPEG/nvJPEG-Decoder/tests/test_decoder.py`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md) | BLOCKED |

<a id="b11"></a>

### B11：稀疏直接求解从 SPD 子集扩展（5 例）

**候选路线：** CPU 稀疏符号分析 + rocSOLVER/其它经过锁定验证的 GPU 稀疏数值路线；项目配置适配。

**开始门槛：** batch/uniform/reordering 原例有 SPD；residual 默认 GENERAL、get_set 使用 SYMMETRIC 和多项配置。必须逐例保留矩阵类别、pivot、配置与查询，不可全部改成 SPD。

**验收：** 不转 dense；符号图/排列正确，逐 batch 残差；配置改变必须对应真实行为；查询返回真实数据；一般/不定矩阵失败行为可解释。仅 SPD 通过不能推广到其它三类。

**case 草案：** 原始矩阵类型；不同 sparsity/batch 大小；结构相同值变化；重排序前后；奇异/不定矩阵；config set/get 与内存/排列信息。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuDSS/simple_batch/simple_batch.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_batch/simple_batch.cpp.md) | FAILED |
| [`cuDSS/simple_uniform_batch/simple_uniform_batch.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_uniform_batch/simple_uniform_batch.cpp.md) | FAILED |
| [`cuDSS/simple_reordering_phase/simple_reordering_phase.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_reordering_phase/simple_reordering_phase.cpp.md) | FAILED |
| [`cuDSS/simple_residual/simple_residual.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_residual/simple_residual.cpp.md) | FAILED |
| [`cuDSS/simple_get_set/simple_get_set.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_get_set/simple_get_set.cpp.md) | FAILED |

此批是能力扩展研究目标，不能沿用“所有例子均为 SPD”的假设。尤其 `simple_residual` 默认是 GENERAL，`simple_get_set` 是 SYMMETRIC 并查询重排序/匹配/内存信息；先导库不满足时，保持失败/部分完成并给出缺口。

<a id="b12"></a>

### B12：多进程多 GPU BLAS 与数据分布（6 例）

**候选路线：** MPI + RCCL + hipBLAS/rocBLAS + 分布/重分布实现。

**开始门槛：** 多 rank 使用不同 GPU；block-cyclic/进程网格与原始 collective 语义先验收。物理 GPU3 排除；多节点 profile 需要实际多节点，不以同机模拟冒充。

**验收：** 各 rank 本地分片与全局重构参考；AllGather/AllReduce/ReduceScatter 实际执行；通信顺序与同步正确；不能只把已有双卡 GEMM 探针换名字。

**case 草案：** 2 rank 与不同进程网格；非整齐分片；不同 collective；重分布往返；重复执行；错误 rank/设备参数。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuBLASMp/geadd.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/geadd.cu.md) | FAILED |
| [`cuBLASMp/gemr2d.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/gemr2d.cu.md) | FAILED |
| [`cuBLASMp/gemm.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/gemm.cu.md) | FAILED |
| [`cuBLASMp/matmul_ag.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/matmul_ag.cu.md) | FAILED |
| [`cuBLASMp/matmul_ar.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/matmul_ar.cu.md) | FAILED |
| [`cuBLASMp/matmul_rs.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/matmul_rs.cu.md) | FAILED |

<a id="b13"></a>

### B13：多 GPU 分解/FFT/张量算法（6 例）

**候选路线：** rocSOLVER/hipFFT/hipBLAS + MPI/RCCL + 项目分布式算法。

**开始门槛：** 确认真正的跨 GPU 数值分解、FFT transpose/reshape、张量分区算法；只有分发输入再在一张卡计算不能算原例成功。

**验收：** 所有设备实际参与计算；LU/Cholesky 残差、FFT 全局布局与归一化、tensor 全局输出；原始 Mg 单进程和 Mp 多进程语义分别保留。

**case 草案：** 原始 descriptor/进程模型；不均匀分片；不同矩阵/FFT 尺寸；回传布局；重复同步；奇异/非SPD状态。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu.md) | FAILED |
| [`cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu.md) | FAILED |
| [`cuSOLVERMp/mp_getrf_getrs.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_getrf_getrs.c.md) | FAILED |
| [`cuSOLVERMp/mp_potrf_potrs.c`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_potrf_potrs.c.md) | FAILED |
| [`cuFFTMp/samples/c2c/cufftmp_c2c.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/c2c/cufftmp_c2c.cu.md) | FAILED |
| [`cuTENSORMg/contraction_multi_gpu.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSORMg/contraction_multi_gpu.cu.md) | FAILED |

<a id="b14"></a>

### B14：MathDx 设备内算子四个试点（4 例）

**候选路线：** HIP 设备函数；GEMM 候选 rocWMMA/CK；RNG 候选 rocRAND device；FFT/求解设备算法按实际适用性实现。

**开始门槛：** 明确 warp/thread/block/共享内存与布局；需要证明函数在原始 kernel 内被调用。原 CUDA vendor SDK 基线缺失时单列 BLOCKED，使用自有 CUDA 实现须另标。

**验收：** 设备内计算/协作执行和数学结果同时通过；非32线程、共享内存边界、RNG counter/subsequence、求解 info 等按原例检查；host GEMM/FFT/solver 通过不计 Dx 通过。

**case 草案：** 原始模板/线程块配置；不同合法维度；边界/奇异输入；协作粒度变化；RNG 序列属性；共享内存边界。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu.md) | FAILED |
| [`MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block.cu.md) | FAILED |
| [`MathDx/cuRANDDx/01_introduction/philox_thread_api.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu.md) | FAILED |
| [`MathDx/cuSolverDx/01_Linear_Solve/potrf_block.cu`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_block.cu.md) | FAILED |

<a id="b15"></a>

### B15：图像基础算法的 GPU 重写试点（4 例）

**候选路线：** RPP 可用 primitives + rocPRIM/HIP；CPU OpenCV 仅作参考。

**开始门槛：** 逐算子验证可用 primitive；Canny 的梯度/NMS/滞后连接、距离变换度量、flood-fill 连通性都要保持。resize 成功不表示这些算法已有实现。

**验收：** 完整像素/掩码对照，边界模式/阈值/连通性、batch/ROI/stride；不能只用 CPU OpenCV 执行再把图复制到 GPU。

**case 草案：** 原始图像；全零/单点/边界/非连续输入；阈值变化；不同模板尺寸；连通性/距离度量；确定性。

| 原始样例 / 现有日志与原因 | 当前状态 |
| --- | --- |
| [`NPP/nppCanny/npp_canny_simple.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/nppCanny/npp_canny_simple.cpp.md) | FAILED |
| [`NPP/templateMatching/templateMatching.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/templateMatching/templateMatching.cpp.md) | FAILED |
| [`NPP/distanceTransform/distanceTransform.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/distanceTransform/distanceTransform.cpp.md) | FAILED |
| [`NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp`](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp.md) | FAILED |


## 3. 未进入这 65 个样例的工作

其余队列不是“永远不做”。优先完成相关先导批次、检查实际 API/硬件能力，再选择 4–8 个入口组成新的批次。每个队列的当前失败样例都在第 8 节，不遗漏未通过入口。

| 队列 | 待做内容 | 升级成执行批次的条件 |
| --- | --- | --- |
| 低精度/算法语义 | 其余 3m、BF16x9、动态 mantissa emulation、FP8/MXFP8/NVFP4、planar complex/特殊 int8 布局 | 先核编码、scale 粒度、累加/舍入、合法 dtype 和 gfx1201 kernel；必须区分原生硬件、软件仿真和数学近似。不能用普通 GEMM 宣称已保留这些特性。 |
| solver 高级算法 | Xgesvdp/Xgesvdr、mixed-precision IRS、稀疏 QR、一般/复数/不定稀疏直接求解 | 有可运行 GPU 算法和原始接口/精度策略参考；CSRRF 的适用前提逐项满足。 |
| tensor 高级与 Python | block-sparse、3XTF32/JIT/cache、PyTorch/TensorFlow binding | 原始稀疏结构、计算精度、真实 JIT 和设备执行都被保留；单纯 NumPy/CPU 或 dense 改写不够。 |
| 其它 codec/媒体 | Cascaded/RLE、实验性 Deflate/GZIP/ZSTD 解码、CRC/GDS/manager、JPEG encoder/JPEG2000/TIFF | 先有正确方向的 GPU codec/CRC/I/O 路径及 CPU/CUDA 互操作语料。CPU 编码或容器解析可作为原例已有阶段，但不能代替原例要求的 GPU codec。 |
| NPP/NPP+ 其它算法 | 连通域、轮廓、Hough、watershed、签名距离变换、Python bindings | 先用 B15 建立 GPU 图像 pipeline、边界与 CPU oracle，再逐算子实现。 |
| 稀疏直接求解高级接口 | Schur complement、复杂重排序、allocator、hybrid memory/execute、线程回调、各种语言 | 不能把配置当装饰；数值路径、真实内存/线程/配置行为和错误处理均需独立验证。 |
| nvMatmulHeuristics | 配置生成/发现、runtime/能耗估计、SM carveout | hipBLASLt heuristics/Origami 仅是候选；先确认可用的 AMD 模型、测量与资源控制，不能只返回任意算法替代。 |
| 其余 MathDx/libmathdx/nvCOMPDx | 融合设备算子、JIT 生成器、device compression | B14 设备内试点成功后按算法扩展；不能跨用 host API 算作设备融合。 |
| cuPQC 非 SHA | ML-KEM、ML-DSA、Merkle、Poseidon2 | 独立 GPU 算法、标准已知答案/互操作测试；不能从 SHA-256/SHA3 推及其它算法，也不因样例正确就承诺安全审计/生产资格。 |
| cuEST 51 个入口 | 积分/梯度、DF/XC/PCM 等科学 API 与绑定 | 专项算法实现与独立科学参考；需要单列研发计划，不能用 BLAS 本身替代高层科学算子。 |

<a id="limits"></a>

## 4. 当前不能等价支持的项目、原因与恢复条件

### 4.1 已有明确证据的路线边界

| 编号 | 不能直接支持的内容 | 证据及原因 | 保留/替代方式与恢复条件 |
| --- | --- | --- | --- |
| U1 | 锁定 hipSPARSELt 在 gfx1201 上的原生 prune/compress/matmul 两个样例 | 已实际运行缺 kernel；锁定源码目标检查也拒绝 gfx1201。[实测与架构检查](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/upstream-support/hipsparselt-gfx1201-configure.log)、[归档目标列表](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/upstream-support/hipsparselt_supported_architectures.cmake)。 | 当前保持 2 UNSUPPORTED。换有匹配 kernel 的 GPU/SDK，或实现真实结构化稀疏 GPU 路线后重验；dense GEMM 不能冒充原生结构化稀疏。 |
| U2 | 通过当前 hipSOLVER `Xgeev` 兼容路径获得纯 GPU 一般特征分解 | AMD 官方说明该路线转 CPU LAPACK；AMD 上能运行不是 GPU 算法证据。[hipSOLVER General eigensolvers](https://rocm.docs.amd.com/projects/hipSOLVER/en/latest/reference/intro.html#general-eigensolvers)。 | Xgeev 三例保持 PARTIAL，第四例保留现有构建失败。可以另记“CPU 功能可用”，但不计 GPU；恢复需原生/自有 GPU 一般特征求解并验证左右特征向量等契约。 |
| U3 | 用当前 `gesvdaStridedBatched` 包装实现原始近似 SVD + residual norm 契约 | 官方说明其 partial SVD 为精确算法且不计算残差范数。[hipSOLVER Partial SVD](https://rocm.docs.amd.com/projects/hipSOLVER/en/latest/reference/intro.html#partial-svd-functions)。 | 保持 PARTIAL；另写满足原始算法与残差语义的 GPU 实现，或明确只交付“数学子集”。不能仅补打印一个残差就宣称算法语义等价。 |
| U4 | 用锁定 hipCOMP 直接完成 Bitcomp、ANS、GDeflate 的原 codec/bitstream 互操作 | 固定 commit 支持表把三者标为未支持；Deflate/GZIP/ZSTD 也只有实验性解码，不能推成双向。[固定 hipCOMP 支持表](https://github.com/ROCm/hipCOMP-core/blob/03df9f7369211ee15d370817165224c73fdc9a46/README.md#algorithm-support)。 | 当前是“库路线缺失”，原例仍 FAILED，不扩大为硬件 UNSUPPORTED。通用算法并非永远不可做；需独立兼容 GPU codec、公开格式与 CUDA/CPU 互解证据。 |
| U5 | 在 AMD 上原样复现 CUDA Green Context 的 NVIDIA SM 资源契约/ABI | 原例使用 cudaDevSmResourceSplitByCount、cudaGreenCtxCreate 和专属 stream/context；普通 SGEMM 不包含这些功能。[原始样例](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuBLASLt/LtSgemmGreenContext/sample_cublasLt_LtSgemmGreenCtx.cu)。 | 原 NVIDIA 对象/SM 资源语义不能原样成为 AMD 对象；可研究 AMD CU 资源控制的功能替代，但需单列语义适配证据，不能默认 stream 顶替。 |

### 4.2 尚无充分证据判成“不可能”的内容

| 内容 | 当前结论与限制 | 下一步证据门槛 |
| --- | --- | --- |
| cuSPARSE 通用压缩内存分配 | 旧草稿只暴露未适配的 CUDA 符号。HIP 也定义 VMM/分配属性，结构字段存在并不说明压缩真的可用；当前不足以宣称硬件不支持。 | 检查锁定 runtime 的属性/枚举，真实 create/map/query，验证压缩属性被采纳和正确性；不能用普通未压缩 hipMalloc 假装通过。[HIP VMM](https://rocm.docs.amd.com/projects/HIP/en/latest/how-to/hip_runtime_api/memory_management/virtual_memory.html)。 |
| JPEG 编码、JPEG2000、TIFF | 现有 rocJPEG 路线提供 JPEG 解码，不是这三类 GPU codec 的实现；这不是这些编码数学上不可实现的证明。[rocJPEG 定位](https://rocm.docs.amd.com/projects/rocJPEG/en/latest/)。 | 新 GPU codec 或自有实现；分别核验输入精度、码流、质量、metadata/ROI/多页；CPU OpenJPEG/libtiff 只能作为容器/参考阶段。 |
| hipTensor FP32 contraction 与 gfx1201 | 项目原生路线曾报 ARCH_MISMATCH，但 rocBLAS + HIP 的数学替代已验收一个原始 profile。不能把这次原生缺口推广成所有 tensor 不可支持。 | B5 保留 dtype 与布局，检查每个后端实际支持；JIT/cache/稀疏布局功能需另外实现，不能只看数学结果。 |
| FP8/FP4/MX/BF16x9/3XTF32 | 格式、缩放、舍入、硬件指令和算法并不自动跨厂商等价；旧编译失败不构成永久不支持。 | 显式数据格式转换与软件/原生精度证据；需要保留原始精度策略，软件仿真必须标注且不承诺原生性能。 |
| NVIDIA 设备二进制、私有 descriptor/cache、算法 ID | NVIDIA 机器码/驱动对象/不透明缓存不能不经转换直接视作 AMD 可执行对象；算法编号和性能选择不是跨库通用协议。 | 有源代码时做 AMD 重写并记录边界；需要私有算法/格式但没有合法可用实现或参考时保持阻塞。可替代的是功能契约，不是宣称二进制可互换。 |
| 多节点通信、NVSHMEM 特有语义、distributed allocator | 本项目当前没有合格多节点验收环境；RCCL 的存在不等于原始分布式算法与所有网络能力可用。 | 原模型需要的节点数、NIC/驱动、GPU-aware MPI/通信路径与数据分布逐项实测。单机两卡通过不当作多节点通过。 |
| MathDx / NPP / cuEST / cuPQC | 原始前端/SDK/算法大多尚未改写，是研发缺口。不能由缺 NVIDIA 头文件推出 AMD 不能做相同数学功能。 | 按设备执行/科学/图像/密码契约开发与独立验证，先小试点后扩展；见 B14/B15 与研究队列。 |

**范围结论：没有证据支持把其余 471 个未通过入口统统标为硬件“不可能支持”。** 现有清单仅 2 项具有锁定栈 UNSUPPORTED 结论；U2–U5 是具体路线/契约边界，原始状态继续保持。未来升级库也必须新建环境/依赖锁和实测证据，不能覆盖旧失败记录。

## 5. 全部 30 模块的去向

| 模块 | PASSED / 总入口 | 尚未通过 | 已选批次 / 后续方向 |
| --- | ---: | ---: | --- |
| [cuBLAS](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuBLAS/README.md) | 62/82 | 20 | B4、B7、G-PRECISION 低精度/算法探针 |
| [cuBLASLt](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuBLASLt/README.md) | 3/20 | 17 | B7、G-PRECISION 低精度/算法探针、R-API 后续能力调查、U5 NVIDIA 执行契约 |
| [cuBLASMp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuBLASMp/README.md) | 0/14 | 14 | B12、G-DISTRIBUTED 分布式门槛 |
| [cuDSS](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuDSS/README.md) | 3/59 | 56 | B11、G-DISTRIBUTED 分布式门槛、R-SPARSE-DIRECT 专项研究 |
| [cuEST](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuEST/README.md) | 0/51 | 51 | R-SCIENCE 专项研究 |
| [cuFFT](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuFFT/README.md) | 10/10 | 0 | 现有登记 profile 已验收；只保留回归与扩展 case，暂不新增批次。 |
| [cuFFTMp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuFFTMp/README.md) | 0/20 | 20 | B13、G-DISTRIBUTED 分布式门槛 |
| [cuPQC](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuPQC/README.md) | 2/6 | 4 | R-PQC 专项研究 |
| [cuRAND](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuRAND/README.md) | 36/36 | 0 | 现有登记 profile 已验收；只保留回归与扩展 case，暂不新增批次。 |
| [cuSOLVER](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuSOLVER/README.md) | 16/39 | 23 | B13、B6、B4、G-DISTRIBUTED 分布式门槛、R-SOLVER 算法研究、R-SPARSE-QR 专项研究、U2 GPU 路线缺口、U3 近似语义缺口 |
| [cuSOLVERMp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuSOLVERMp/README.md) | 0/16 | 16 | B13、G-DISTRIBUTED 分布式门槛 |
| [cuSOLVERSp2cuDSS](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuSOLVERSp2cuDSS/README.md) | 0/7 | 7 | R-SPARSE-QR 专项研究 |
| [cuSPARSE](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuSPARSE/README.md) | 29/37 | 8 | B4、B8、G-VMM 先做能力探针 |
| [cuSPARSELt](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuSPARSELt/README.md) | 0/2 | 2 | U1 当前栈原生不可用 |
| [cuTENSOR](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuTENSOR/README.md) | 5/13 | 8 | B5、G-TENSOR 高级功能/绑定 |
| [cuTENSORMg](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuTENSORMg/README.md) | 0/2 | 2 | B13、G-DISTRIBUTED 分布式门槛 |
| [cuTENSORMp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuTENSORMp/README.md) | 0/3 | 3 | G-DISTRIBUTED 分布式门槛 |
| [MathDx/cuBLASDx](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/MathDx/cuBLASDx/README.md) | 0/34 | 34 | B14、R-DX 设备算法研究 |
| [MathDx/cuFFTDx](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/MathDx/cuFFTDx/README.md) | 0/49 | 49 | B14、R-DX 设备算法研究 |
| [MathDx/cuRANDDx](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/MathDx/cuRANDDx/README.md) | 0/7 | 7 | B14、R-DX 设备算法研究 |
| [MathDx/cuSolverDx](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/MathDx/cuSolverDx/README.md) | 0/42 | 42 | B14、R-DX 设备算法研究 |
| [MathDx/libmathdx](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/MathDx/libmathdx/README.md) | 0/12 | 12 | R-DX 设备算法研究 |
| [MathDx/nvCOMPDx](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/MathDx/nvCOMPDx/README.md) | 0/7 | 7 | R-DX 设备算法研究 |
| [NPP](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/NPP/README.md) | 0/9 | 9 | B15、R-VISION 算法研究 |
| [NPP+](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/NPP+/README.md) | 0/6 | 6 | B15、R-VISION 算法研究 |
| [nvJPEG](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/nvJPEG/README.md) | 0/7 | 7 | B10、G-CODEC 新增 GPU codec |
| [nvJPEG2000](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/nvJPEG2000/README.md) | 0/4 | 4 | G-CODEC 新增 GPU codec |
| [nvTIFF](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/nvTIFF/README.md) | 0/6 | 6 | G-CODEC 新增 GPU codec |
| [nvCOMP](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/nvCOMP/README.md) | 0/32 | 32 | B9、G-CODEC-DIR 先核方向、G-COMPRESS codec/API 探针、U4 codec 路线不可用 |
| [nvMatmulHeuristics](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/nvMatmulHeuristics/README.md) | 0/7 | 7 | G-HEURISTICS 模型与硬件门槛 |

<a id="acceptance"></a>

## 6. 每批必须满足的验收与日志要求

1. **启动前锁定契约。** 固定原始样例路径/source hash、dtype/layout/执行模型、必需 case 和误差规则；先写 `batchN` 清单再跑。本文 case 是设计草案，不能根据输出好坏事后删除必需 case。
2. **分开报告能力。** 头文件/链接存在、GPU 实际执行、独立数值通过、原始完整功能、性能资格分别记录。候选库没有运行证据时不写成“已使用成功”。
3. **保留原始规模与语义。** 小尺寸可用于调试与全量 CPU oracle；不能只跑缩小输入就宣称原始 profile 通过。原始大规模如只抽样检查，明确抽样策略/覆盖率，不能称全输出通过。缓存、allocator、设备内调用、多 rank/多 GPU 不能省略。
4. **三方核对。** AMD 与 5090 CUDA 使用共享输入或可重建输入 hash；CPU 独立参考检查全部适用输出、结构与残差。跨库 RNG 不要求同序列，压缩/JPEG/密码分别按码流互操作、像素容差和已知答案验收。CUDA vendor SDK 基线缺失明确记 BLOCKED，同实现 CUDA 另记范围。
5. **反向检查。** 注入有限值错误、NaN、布局/indices 错误、错误 info、空图/假缓存等适用错误，确认 oracle 拒绝；不能使用程序自身 expected 输出作为唯一参考。
6. **数值和性能分开。** 共享卡可做正确性；只有通过空闲/资源资格且重复统计有效才发布速度比。现有 6 个 GEMM 性能结果仍 BLOCKED，本计划不自动解除。
7. **每步更新 MD。** 每个实现步骤后追加设计实施日志；每批更新 sample status、actual/backend library、源码、reason、required/passed cases、CPU/CUDA 证明和恢复条件。失败也要归档，状态不靠口头总结改变。
8. **统一证据。** 每个样例/输入保留 build.log、run.log、commands.json、environment、源码/输入 hash、结构化误差/阈值/info 与实际 GPU/图/通信语义；小型文本入 Git，大二进制记 hash/生成方法。更新支持方式与详细 log 总表，再提交并校验 fork 首页。

每批可交付 PASSED、PARTIAL、FAILED、BLOCKED 或有充分范围证据的 UNSUPPORTED；交付的要求是实现结果、证据和原因完整。不能以“执行完计划”替代“每个目标都成功”。

## 7. 数量预期、资源和发布方式

- **近期条件上限：** B4–B6 的 16 个候选若都保留原始功能并通过验收，样例可从 166 增至 182。它们当前仍为未通过，文档没有预先增加支持数。
- **全部候选条件上限：** 65 例若最终全部合格，样例上限为 231；条件研究批次不提供成功保证。91 个算子/功能族不能简单加 65，batch/dtype/布局/API 变体需按现有规则去重。
- **资源：** B4–B11 主要单 GPU 正确性；B12/B13 至少两卡且部分必须多进程/多节点；B14 需设备编译/JIT 工具链；codec/媒体需语料、CPU 参考库和独立 CUDA SDK。所有依赖使用项目 overlay，不修改共享 foundation。
- **调度：** 每批完成后根据真正失败 gate、GPU 可用性和新库版本调整后续优先级，更新本文版本。没有实测依据时不承诺固定日期或吞吐。
- **文件：** 用户工作区 `doc/cuda_samples_on_rocm_roadmap.md`；fork 可读副本 `migration/roadmap.md`；机器清单 `migration/roadmap.json`；原始设计 `doc/cuda_samples_on_rocm_design.md` / `migration/design.md`。本计划通过 `python3 tools/migration/roadmap.py` 从逐例清单生成；生成不会执行 GPU，也不会修改实测状态。

参考依据：本仓库的逐例/环境锁/原生失败日志优先于浮动文档。hipCOMP 使用固定 commit `03df9f7369211ee15d370817165224c73fdc9a46`，hipTensor 与架构材料来自固定 `380ea3ec237d03c4a384b4ed4c49fda82d9f81dd`；其它 AMD 官方文档于 2026-11-10 核对，latest 内容不能替代锁定镜像中的实际能力。hipBLAS Ex/hipBLASLt/rocSOLVER 的 API 是候选路线依据，不是本批新增成功证据。

- [实际库选择、成功边界与恢复条件](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/ecosystem-decisions.md)
- [完整样例支持方式与日志](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/support-log-index.md)
- [项目环境锁](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/environments/project.lock.json) · [可选库固定版本](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/environments/optional-dependencies.lock.json)
- [hipBLAS Ex API](https://rocm.docs.amd.com/projects/hipBLAS/en/latest/reference/hipblas-api-functions.html#blas-extensions) · [hipBLASLt](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/index.html) · [rocSOLVER LAPACK](https://rocm.docs.amd.com/projects/rocSOLVER/en/latest/reference/lapack.html)

<a id="inventory"></a>

## 8. 473 个未通过入口的逐项计划索引

以下是 2026-11-10 的计划基线，不是新的执行结果。每项都有批次或门槛/研究队列；链接打开原始详细错误、支持方式和历史 log。`U*` 是“当前指定路线不满足原契约”的计划分类，**不自动把 FAILED/PARTIAL 改成 UNSUPPORTED**。只有清单现有的 2 个 hipSPARSELt 项已具有 UNSUPPORTED 实测证据。

### cuBLAS

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/bf16x9_sgemm/cublas_sgemm_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/bf16x9_sgemm/cublas_sgemm_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/gemm_grading/grade_blas3.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/gemm_grading/grade_blas3.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/gemm_grading/test_blas3.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/gemm_grading/test_blas3.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Extensions/CherkEx/cublas_CherkEx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/CherkEx/cublas_CherkEx_example.cu.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [Extensions/CsyrkEx/cublas_CsyrkEx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/CsyrkEx/cublas_CsyrkEx_example.cu.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu.md) | FAILED | B7 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu.md) | FAILED | B7 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Extensions/tpttr/cublas_tpttr_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Extensions/trttp/cublas_trttp_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Extensions/trttp/cublas_trttp_example.cu.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Level-3/gemm3m/cublas_gemm3m_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |

### cuBLASLt

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [LtBlk128x128Fp8Matmul/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtBlk128x128Fp8Matmul/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtBlk128x128Fp8gemmGroupedSimple/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtBlk128x128Fp8gemmGroupedSimple/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtDgemmEmulated/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtDgemmEmulated/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtDgemmPresetAlgo/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtDgemmPresetAlgo/main.cpp.md) | FAILED | R-API 后续能力调查 | 保留既有具体错误和恢复条件，完成相关先导批次后再锁定样例与 cases。 |
| [LtFp8CustomFind/main.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtFp8CustomFind/main.cu.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtFp8Matmul/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtFp8Matmul/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtFp8gemmGroupedSimple/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtFp8gemmGroupedSimple/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtHSHgemmGroupedSimple/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtHSHgemmGroupedSimple/main.cpp.md) | FAILED | B7 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [LtIgemmTensor/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtIgemmTensor/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtMxfp8Matmul/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtMxfp8Matmul/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtMxfp8gemmGroupedSimple/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtMxfp8gemmGroupedSimple/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtNvfp4Matmul/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtNvfp4Matmul/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtNvfp4gemmGroupedSimple/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtNvfp4gemmGroupedSimple/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtPlanarComplex/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtPlanarComplex/main.cpp.md) | FAILED | G-PRECISION 低精度/算法探针 | 保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。 |
| [LtSgemmCustomFind/main.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtSgemmCustomFind/main.cu.md) | FAILED | B7 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [LtSgemmGreenContext/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtSgemmGreenContext/main.cpp.md) | FAILED | U5 NVIDIA 执行契约 | CUDA SM/Green Context 不是普通 GEMM 数值功能；精确契约不能用默认 stream 替代。 |
| [LtSgemmSimpleAutoTuning/main.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp.md) | FAILED | B7 | 明确候选；先通过对应批次入口门槛，尚未实施。 |

### cuBLASMp

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [geadd.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/geadd.cu.md) | FAILED | B12 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [gemm.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/gemm.cu.md) | FAILED | B12 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [gemr2d.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/gemr2d.cu.md) | FAILED | B12 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [matmul_ag.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/matmul_ag.cu.md) | FAILED | B12 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [matmul_ar.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/matmul_ar.cu.md) | FAILED | B12 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [matmul_rs.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/matmul_rs.cu.md) | FAILED | B12 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [symm.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/symm.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [syr2k.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/syr2k.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [syrk.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/syrk.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [syrkx.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/syrkx.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [tp_matmul.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/tp_matmul.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [tradd.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/tradd.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [trmm.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/trmm.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [trsm.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuBLASMp/trsm.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |

### cuDSS

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [fortran/batch/batch.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/batch/batch.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/dense_matrix_helpers/dense_matrix_helpers.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/dense_matrix_helpers/dense_matrix_helpers.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/get_set/get_set.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/get_set/get_set.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/high_precision/high_precision.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/high_precision/high_precision.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/hybrid_execute_mode/hybrid_execute_mode.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/hybrid_execute_mode/hybrid_execute_mode.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/hybrid_memory_mode/hybrid_memory_mode.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/hybrid_memory_mode/hybrid_memory_mode.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/memory_handler/memory_handler.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/memory_handler/memory_handler.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/mg_mode/mg_mode.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/mg_mode/mg_mode.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [fortran/mgmn_mode/mgmn_mode.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/mgmn_mode/mgmn_mode.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [fortran/multithreaded_mode/multithreaded_mode.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/multithreaded_mode/multithreaded_mode.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/reordering_phase/reordering_phase.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/reordering_phase/reordering_phase.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/residual/residual.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/residual/residual.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/schur_complement/schur_complement.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/schur_complement/schur_complement.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/simple_complex/simple_complex.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/simple_complex/simple_complex.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [fortran/uniform_batch/uniform_batch.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/fortran/uniform_batch/uniform_batch.f90.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/batch/batch.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/batch/batch.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/get_set/get_set.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/get_set/get_set.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/high_precision/high_precision.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/high_precision/high_precision.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/hybrid_execute_mode/hybrid_execute_mode.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/hybrid_execute_mode/hybrid_execute_mode.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/hybrid_memory_mode/hybrid_memory_mode.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/hybrid_memory_mode/hybrid_memory_mode.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/memory_handler/memory_handler.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/memory_handler/memory_handler.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/mg_mode/mg_mode.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/mg_mode/mg_mode.cuf.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [nvfortran/mgmn_mode/mgmn_mode.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/mgmn_mode/mgmn_mode.cuf.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [nvfortran/multithreaded_mode/multithreaded_mode.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/multithreaded_mode/multithreaded_mode.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/reordering_phase/reordering_phase.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/reordering_phase/reordering_phase.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/residual/residual.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/residual/residual.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/schur_complement/schur_complement.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/schur_complement/schur_complement.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/simple_complex/simple_complex.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/simple_complex/simple_complex.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [nvfortran/uniform_batch/uniform_batch.cuf](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/nvfortran/uniform_batch/uniform_batch.cuf.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_batch/simple_batch.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_batch/simple_batch.cpp.md) | FAILED | B11 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_complex/simple_complex.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_complex/simple_complex.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_get_set/simple_get_set.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_get_set/simple_get_set.cpp.md) | FAILED | B11 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [simple_high_precision/simple_high_precision.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_high_precision/simple_high_precision.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_hybrid_execute_mode/simple_hybrid_execute_mode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_hybrid_execute_mode/simple_hybrid_execute_mode.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_hybrid_memory_mode/simple_hybrid_memory_mode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_hybrid_memory_mode/simple_hybrid_memory_mode.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_matrix_market/simple_matrix_market.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_matrix_market/simple_matrix_market.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_memory_handler/simple_memory_handler.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_memory_handler/simple_memory_handler.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_mg_mode/simple_mg_mode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_mg_mode/simple_mg_mode.cpp.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [simple_mgmn_distributed_matrix/simple_mgmn_distributed_matrix.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_mgmn_distributed_matrix/simple_mgmn_distributed_matrix.cpp.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [simple_mgmn_mode/simple_mgmn_mode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_mgmn_mode/simple_mgmn_mode.cpp.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [simple_multithreaded_mode/simple_multithreaded_mode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_multithreaded_mode/simple_multithreaded_mode.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_pinned_memory_handler/simple_pinned_memory_handler.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_pinned_memory_handler/simple_pinned_memory_handler.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_reordering_phase/simple_reordering_phase.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_reordering_phase/simple_reordering_phase.cpp.md) | FAILED | B11 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [simple_residual/simple_residual.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_residual/simple_residual.cpp.md) | FAILED | B11 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [simple_schur_complement/simple_schur_complement.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_schur_complement/simple_schur_complement.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [simple_uniform_batch/simple_uniform_batch.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/simple_uniform_batch/simple_uniform_batch.cpp.md) | FAILED | B11 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [test_communication_layer/test_communication_layer.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/test_communication_layer/test_communication_layer.cu.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |
| [test_threading_layer/test_threading_layer.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuDSS/test_threading_layer/test_threading_layer.cu.md) | FAILED | R-SPARSE-DIRECT 专项研究 | 矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。 |

### cuEST

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [c_examples/examples/0_context/basic_multigpu_usage/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/0_context/basic_multigpu_usage/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/0_context/basic_multistream_usage/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/0_context/basic_multistream_usage/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/0_context/basic_usage/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/0_context/basic_usage/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/0_context/user_owned_resources/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/0_context/user_owned_resources/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/1_basic_data_structures/ao_basis/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ao_basis/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/1_basic_data_structures/ao_basis_general/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ao_basis_general/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/1_basic_data_structures/ao_shells/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ao_shells/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/1_basic_data_structures/ecp_atom/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ecp_atom/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/1_basic_data_structures/ecp_shells/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ecp_shells/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/1_basic_data_structures/xc_grid/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/1_basic_data_structures/xc_grid/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/1_basic_data_structures/xc_grid_general/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/1_basic_data_structures/xc_grid_general/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/2_one_electron_integrals/one_electron_gradients/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/one_electron_gradients/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/2_one_electron_integrals/one_electron_integrals/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/one_electron_integrals/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/2_one_electron_integrals/property_gradients/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/property_gradients/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/2_one_electron_integrals/property_integrals/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/property_integrals/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/3_density_fitting/core_df_jk/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/3_density_fitting/core_df_jk/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/3_density_fitting/core_df_jk_gradients/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/3_density_fitting/core_df_jk_gradients/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/3_density_fitting/df_mo_integrals/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/3_density_fitting/df_mo_integrals/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/3_density_fitting/nonsymmetric_core_df_k/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/3_density_fitting/nonsymmetric_core_df_k/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/4_exchange_correlation/advanced_local_xc_gradient/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/4_exchange_correlation/advanced_local_xc_gradient/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/4_exchange_correlation/advanced_local_xc_potential/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/4_exchange_correlation/advanced_local_xc_potential/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/4_exchange_correlation/local_xc_gradient/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/4_exchange_correlation/local_xc_gradient/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/4_exchange_correlation/local_xc_potential/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/4_exchange_correlation/local_xc_potential/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/4_exchange_correlation/nonlocal_xc_gradient/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/4_exchange_correlation/nonlocal_xc_gradient/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/4_exchange_correlation/nonlocal_xc_potential/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/4_exchange_correlation/nonlocal_xc_potential/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/5_effective_core_potentials/ecp_gradients/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/5_effective_core_potentials/ecp_gradients/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/5_effective_core_potentials/ecp_integrals/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/5_effective_core_potentials/ecp_integrals/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/6_pcm/pcm_gradients/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/6_pcm/pcm_gradients/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [c_examples/examples/6_pcm/pcm_potential/main.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/c_examples/examples/6_pcm/pcm_potential/main.c.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/0_context/basic_multistream_usage/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/0_context/basic_multistream_usage/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/0_context/basic_usage/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/0_context/basic_usage/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/0_context/user_owned_resources/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/0_context/user_owned_resources/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/1_basic_data_structures/ao_basis/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/1_basic_data_structures/ao_basis/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/1_basic_data_structures/ao_shells/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/1_basic_data_structures/ao_shells/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/2_one_electron_integrals/one_electron_gradients/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/2_one_electron_integrals/one_electron_gradients/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/2_one_electron_integrals/one_electron_integrals/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/2_one_electron_integrals/one_electron_integrals/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/2_one_electron_integrals/property_gradients/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/2_one_electron_integrals/property_gradients/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/2_one_electron_integrals/property_integrals/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/2_one_electron_integrals/property_integrals/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/3_density_fitting/core_df_jk/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/3_density_fitting/core_df_jk/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/3_density_fitting/core_df_jk_gradient_rhf/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/3_density_fitting/core_df_jk_gradient_rhf/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/3_density_fitting/core_df_jk_gradient_uhf/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/3_density_fitting/core_df_jk_gradient_uhf/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/3_density_fitting/df_mo_integrals/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/3_density_fitting/df_mo_integrals/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/3_density_fitting/nonsymmetric_core_df_k/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/3_density_fitting/nonsymmetric_core_df_k/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/4_exchange_correlation/local_xc_gradient/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/4_exchange_correlation/local_xc_gradient/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/4_exchange_correlation/local_xc_potential/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/4_exchange_correlation/local_xc_potential/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/4_exchange_correlation/nonlocal_xc_gradient/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/4_exchange_correlation/nonlocal_xc_gradient/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/4_exchange_correlation/nonlocal_xc_potential/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/4_exchange_correlation/nonlocal_xc_potential/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/5_effective_core_potentials/ecp_gradients/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/5_effective_core_potentials/ecp_gradients/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/5_effective_core_potentials/ecp_integrals/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/5_effective_core_potentials/ecp_integrals/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/6_pcm/pcm_gradients/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/6_pcm/pcm_gradients/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |
| [python_examples/6_pcm/pcm_potential/run.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuEST/python_examples/6_pcm/pcm_potential/run.py.md) | FAILED | R-SCIENCE 专项研究 | 高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。 |

### cuFFTMp

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [Fortran_samples/c2c/cufftmp_c2c.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/c2c/cufftmp_c2c.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Fortran_samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Fortran_samples/c2c_pencils/cufftmp_c2c_pencils.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/c2c_pencils/cufftmp_c2c_pencils.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Fortran_samples/r2c_c2r/cufftmp_r2c.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/r2c_c2r/cufftmp_r2c.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Fortran_samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Fortran_samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Fortran_samples/r2c_c2r_shared_scratch/cufftmp_r2c_workarea.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/r2c_c2r_shared_scratch/cufftmp_r2c_workarea.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Fortran_samples/reshape/cufftmp_reshape.f90](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/Fortran_samples/reshape/cufftmp_reshape.f90.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [JAX_FFT/tests/fft_test.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/JAX_FFT/tests/fft_test.py.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/c2c/cufftmp_c2c.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/c2c/cufftmp_c2c.cu.md) | FAILED | B13 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/c2c_no_descriptors_cufftMpMakePlan/cufftmp_c2c_no_descriptors_cufftMpMakePlan.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/c2c_no_descriptors_cufftMpMakePlan/cufftmp_c2c_no_descriptors_cufftMpMakePlan.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/c2c_pencils/cufftmp_c2c_pencils.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/c2c_pencils/cufftmp_c2c_pencils.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/r2c_c2r/cufftmp_r2c_c2r.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/r2c_c2r/cufftmp_r2c_c2r.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/r2c_c2r_pencils_cufftMpMakePlan/cufftmp_r2c_c2r_pencils_cufftMpMakePlan.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/r2c_c2r_pencils_cufftMpMakePlan/cufftmp_r2c_c2r_pencils_cufftMpMakePlan.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/r2c_c2r_shared_scratch/cufftmp_r2c_c2r_shared_scratch.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/r2c_c2r_shared_scratch/cufftmp_r2c_c2r_shared_scratch.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/r2c_c2r_slabs_GROMACS/cufftmp_r2c_c2r_slabs_GROMACS.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/r2c_c2r_slabs_GROMACS/cufftmp_r2c_c2r_slabs_GROMACS.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [samples/reshape/cufftmp_reshape.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuFFTMp/samples/reshape/cufftmp_reshape.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |

### cuPQC

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [example_merkle.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuPQC/example_merkle.cu.md) | FAILED | R-PQC 专项研究 | 需 GPU 密码/哈希算法、KAT/边界与互操作；现有 SHA 通过不能推广。 |
| [example_ml_dsa.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuPQC/example_ml_dsa.cu.md) | FAILED | R-PQC 专项研究 | 需 GPU 密码/哈希算法、KAT/边界与互操作；现有 SHA 通过不能推广。 |
| [example_ml_kem.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuPQC/example_ml_kem.cu.md) | FAILED | R-PQC 专项研究 | 需 GPU 密码/哈希算法、KAT/边界与互操作；现有 SHA 通过不能推广。 |
| [example_poseidon2.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuPQC/example_poseidon2.cu.md) | FAILED | R-PQC 专项研究 | 需 GPU 密码/哈希算法、KAT/边界与互操作；现有 SHA 通过不能推广。 |

### cuSOLVER

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [MgGetrf/cusolver_MgGetrf_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu.md) | FAILED | B13 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [MgPotrf/cusolver_MgPotrf_example1.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu.md) | FAILED | B13 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [MgPotrf/cusolver_MgPotrf_example2.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example2.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [MgSyevd/cusolver_MgSyevd_example1.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example1.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [MgSyevd/cusolver_MgSyevd_example2.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example2.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [MgSyevd/cusolver_MgSyevd_example3.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example3.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [Xgeev/cusolver_Xgeev_example1.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example1.cu.md) | PARTIAL | U2 GPU 路线缺口 | 具体执行差异与恢复条件见 U2；保留当前原始尝试结果。 |
| [Xgeev/cusolver_Xgeev_example2.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example2.cu.md) | PARTIAL | U2 GPU 路线缺口 | 具体执行差异与恢复条件见 U2；保留当前原始尝试结果。 |
| [Xgeev/cusolver_Xgeev_example3.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example3.cu.md) | PARTIAL | U2 GPU 路线缺口 | 具体执行差异与恢复条件见 U2；保留当前原始尝试结果。 |
| [Xgeev/cusolver_Xgeev_example4.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example4.cu.md) | FAILED | U2 GPU 路线缺口 | 具体执行差异与恢复条件见 U2；保留当前原始尝试结果。 |
| [Xgesvd/cusolver_Xgesvd_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu.md) | FAILED | B6 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Xgesvdp/cusolver_Xgesvdp_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu.md) | FAILED | R-SOLVER 算法研究 | 精度迭代改进、极分解/随机SVD等各自需要算法与 oracle；先完成 B6。 |
| [Xgesvdr/cusolver_Xgesvdr_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgesvdr/cusolver_Xgesvdr_example.cu.md) | FAILED | R-SOLVER 算法研究 | 精度迭代改进、极分解/随机SVD等各自需要算法与 oracle；先完成 B6。 |
| [Xgetrf/cusolver_Xgetrf_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu.md) | FAILED | B6 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Xsyevdx/cusolver_Xsyevdx_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu.md) | FAILED | B6 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Xtrtri/cusolver_Xtrtri_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu.md) | FAILED | B6 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [csrqr/cusolver_csrqr_example1.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/csrqr/cusolver_csrqr_example1.cu.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [csrqr/cusolver_csrqr_example2.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/csrqr/cusolver_csrqr_example2.cu.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [gesv/cusolver_irs_expert_cuda-10.2.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/gesv/cusolver_irs_expert_cuda-10.2.cu.md) | FAILED | R-SOLVER 算法研究 | 精度迭代改进、极分解/随机SVD等各自需要算法与 oracle；先完成 B6。 |
| [gesv/cusolver_irs_expert_cuda-11.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/gesv/cusolver_irs_expert_cuda-11.cu.md) | FAILED | R-SOLVER 算法研究 | 精度迭代改进、极分解/随机SVD等各自需要算法与 oracle；先完成 B6。 |
| [gesv/cusolver_irs_lapack.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/gesv/cusolver_irs_lapack.cu.md) | FAILED | R-SOLVER 算法研究 | 精度迭代改进、极分解/随机SVD等各自需要算法与 oracle；先完成 B6。 |
| [gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu.md) | PARTIAL | U3 近似语义缺口 | 原契约差异与恢复条件见 U3；保留现有 PARTIAL。 |
| [ormqr/cusolver_ormqr_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVER/ormqr/cusolver_ormqr_example.cu.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |

### cuSOLVERMp

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [mp_gels.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_gels.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_geqrf.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_geqrf.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_geqrf_orgqr.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_geqrf_orgqr.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_gesvd.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_gesvd.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_getrf_getrs.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_getrf_getrs.c.md) | FAILED | B13 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [mp_laset.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_laset.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_newton_schulz.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_newton_schulz.cpp.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_ormqr.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_ormqr.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_polar.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_polar.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_potrf_potrs.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_potrf_potrs.c.md) | FAILED | B13 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [mp_potrf_potrs_fp32.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_potrf_potrs_fp32.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_potrf_potrs_fp32emulation.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_potrf_potrs_fp32emulation.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_syevd.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_syevd.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_sygst.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_sygst.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_sygvd.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_sygvd.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [mp_sytrd_stedc_ormtr.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERMp/mp_sytrd_stedc_ormtr.c.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |

### cuSOLVERSp2cuDSS

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [csreigs2cuDSS_dcomplex.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERSp2cuDSS/csreigs2cuDSS_dcomplex.cpp.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [csreigvsi2cuDSS_double.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERSp2cuDSS/csreigvsi2cuDSS_double.cpp.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [cuSolverRf2cuDSS_double.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERSp2cuDSS/cuSolverRf2cuDSS_double.cpp.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [cuSolverSp2cuDSS_dcomplex.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_dcomplex.cpp.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [cuSolverSp2cuDSS_double.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_double.cpp.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [cuSolverSp2cuDSS_float.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_float.cpp.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |
| [cuSolverSp2cuDSS_scomplex.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_scomplex.cpp.md) | FAILED | R-SPARSE-QR 专项研究 | 需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。 |

### cuSPARSE

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [compression/compression_example.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/compression/compression_example.cpp.md) | FAILED | G-VMM 先做能力探针 | HIP 有 VMM/压缩属性结构；需实测压缩分配是否生效，不能因旧 CUDA 符号未映射就判硬件不支持。 |
| [sddmm_bsr/sddmm_bsr_example.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/sddmm_bsr/sddmm_bsr_example.c.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [spgemm_mem/spgemm_mem_example.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spgemm_mem/spgemm_mem_example.c.md) | FAILED | B8 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [spmat_convert/spmat_convert_example.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmat_convert/spmat_convert_example.c.md) | FAILED | B8 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [spmm_csr_op/spmm_csr_op_example.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c.md) | FAILED | B8 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [spmv_symmetric_csr/spmv_symmetric_example.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c.md) | FAILED | B8 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [spmvop_csr/spmv_csr_op_example.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spmvop_csr/spmv_csr_op_example.c.md) | FAILED | B8 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [spsv_sell/spsv_sell_example.c](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSE/spsv_sell/spsv_sell_example.c.md) | FAILED | B4 | 明确候选；先通过对应批次入口门槛，尚未实施。 |

### cuSPARSELt

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [matmul/matmul_example.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSELt/matmul/matmul_example.cpp.md) | UNSUPPORTED | U1 当前栈原生不可用 | 锁定 gfx1201 kernel/架构 gate 缺失；只对该版本/路线判定。 |
| [matmul_advanced/matmul_advanced_example.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp.md) | UNSUPPORTED | U1 当前栈原生不可用 | 锁定 gfx1201 kernel/架构 gate 缺失；只对该版本/路线判定。 |

### cuTENSOR

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [python/cutensor/tensorflow/einsum_test.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/python/cutensor/tensorflow/einsum_test.py.md) | FAILED | G-TENSOR 高级功能/绑定 | block-sparse、JIT 数值模式和框架绑定需专门适配，不能只做 dense 数学替代。 |
| [python/cutensor/torch/einsum_test.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/python/cutensor/torch/einsum_test.py.md) | FAILED | G-TENSOR 高级功能/绑定 | block-sparse、JIT 数值模式和框架绑定需专门适配，不能只做 dense 数学替代。 |
| [blocksparse.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/blocksparse.cu.md) | FAILED | G-TENSOR 高级功能/绑定 | block-sparse、JIT 数值模式和框架绑定需专门适配，不能只做 dense 数学替代。 |
| [contraction_jit.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/contraction_jit.cu.md) | FAILED | G-TENSOR 高级功能/绑定 | block-sparse、JIT 数值模式和框架绑定需专门适配，不能只做 dense 数学替代。 |
| [contraction_plan_cache.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/contraction_plan_cache.cu.md) | FAILED | B5 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [contraction_trinary.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/contraction_trinary.cu.md) | FAILED | B5 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [einsum.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/einsum.cu.md) | FAILED | B5 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [elementwise_permute_padding.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSOR/elementwise_permute_padding.cu.md) | FAILED | B5 | 明确候选；先通过对应批次入口门槛，尚未实施。 |

### cuTENSORMg

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [blog_post.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSORMg/blog_post.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [contraction_multi_gpu.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSORMg/contraction_multi_gpu.cu.md) | FAILED | B13 | 明确候选；先通过对应批次入口门槛，尚未实施。 |

### cuTENSORMp

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [cutensorMp_contraction.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSORMp/cutensorMp_contraction.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [cutensorMp_redistribute.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSORMp/cutensorMp_redistribute.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |
| [cutensorMp_unfold_fold.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/cuTENSORMp/cutensorMp_unfold_fold.cu.md) | FAILED | G-DISTRIBUTED 分布式门槛 | B12/B13 基础后再扩展；多节点需实际网络/多节点证据。 |

### MathDx/cuBLASDx

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [01_gemm_introduction/introduction_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu.md) | FAILED | B14 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [01_gemm_introduction/introduction_pipeline.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/01_gemm_introduction/introduction_pipeline.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_gemm_precisions/simple_gemm_fp32.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_fp32.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_gemm_precisions/simple_gemm_fp8.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_fp8.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_gemm_precisions/simple_gemm_int8_int8_int32.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_int8_int8_int32.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_gemm_precisions/simple_gemm_mixed_precision.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_mixed_precision.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_gemm_complex/simple_gemm_cfp16.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/03_gemm_complex/simple_gemm_cfp16.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_gemm_complex/simple_gemm_std_complex_fp32.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/03_gemm_complex/simple_gemm_std_complex_fp32.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_gemm_blockdim/blockdim_gemm_fp16.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_gemm_batched/batched_gemm_fp64.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/05_gemm_batched/batched_gemm_fp64.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [06_gemm_leading_dimension/simple_gemm_leading_dimensions.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/06_gemm_leading_dimension/simple_gemm_leading_dimensions.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_gemm_transform/simple_gemm_transform.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/07_gemm_transform/simple_gemm_transform.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [08_gemm_decoupled_io_and_compute/simple_gemm_fp32_decoupled.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/08_gemm_decoupled_io_and_compute/simple_gemm_fp32_decoupled.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [09_gemm_custom_layout/simple_gemm_aat.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/09_gemm_custom_layout/simple_gemm_aat.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [09_gemm_custom_layout/simple_gemm_custom_layout.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/09_gemm_custom_layout/simple_gemm_custom_layout.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [10_gemm_block_performance/single_gemm_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/10_gemm_block_performance/single_gemm_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [11_gemm_device_performance/device_gemm_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/11_gemm_device_performance/device_gemm_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [12_gemm_device_partial_sums/gemm_device_partial_sums.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/12_gemm_device_partial_sums/gemm_device_partial_sums.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [13_gemm_fft/gemm_fft.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/13_gemm_fft/gemm_fft.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [13_gemm_fft/gemm_fft_fp16.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/13_gemm_fft/gemm_fft_fp16.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [13_gemm_fft/gemm_fft_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/13_gemm_fft/gemm_fft_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [14_gemm_fused/fused_gemm_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/14_gemm_fused/fused_gemm_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [14_gemm_fused/gemm_fusion.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/14_gemm_fused/gemm_fusion.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [15_nvrtc/nvrtc_gemm.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/15_nvrtc/nvrtc_gemm.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [15_nvrtc/nvrtc_trsm.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/15_nvrtc/nvrtc_trsm.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [16_dgemm_emulation/dgemm_emulation.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/16_dgemm_emulation/dgemm_emulation.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [17_trsm/trsm_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/17_trsm/trsm_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [17_trsm/trsm_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/17_trsm/trsm_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [18_tensor_transform/gemm_conj_transpose.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/18_tensor_transform/gemm_conj_transpose.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [18_tensor_transform/trsm_conj_transpose.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/18_tensor_transform/trsm_conj_transpose.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [19_gemm_batched/batched_gemm.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/19_gemm_batched/batched_gemm.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [19_gemm_batched/batched_gemm_pipeline.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/19_gemm_batched/batched_gemm_pipeline.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [21_sgemm_emulation_pipeline/sgemm_emulation_pipeline.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuBLASDx/21_sgemm_emulation_pipeline/sgemm_emulation_pipeline.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |

### MathDx/cuFFTDx

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [00_introduction_example/introduction_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/00_introduction_example/introduction_example.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_simple_fft_thread/simple_fft_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/01_simple_fft_thread/simple_fft_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_simple_fft_thread/simple_fft_thread_fp16.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/01_simple_fft_thread/simple_fft_thread_fp16.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_simple_fft_thread/simple_fft_thread_lto.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/01_simple_fft_thread/simple_fft_thread_lto.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block.cu.md) | FAILED | B14 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [02_simple_fft_block/simple_fft_block_block_dim.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_block_dim.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_c2r.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_c2r.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_c2r_fp16.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_c2r_fp16.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_c2r_lto.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_c2r_lto.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_cub_io.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_cub_io.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_fp16.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_fp16.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_half2.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_half2.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_r2c.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_r2c.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_r2c_fp16.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_r2c_fp16.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_shared.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_shared.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_simple_fft_block/simple_fft_block_std_complex.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_std_complex.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_block_fft_performance/block_fft_lto_ptx_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/03_block_fft_performance/block_fft_lto_ptx_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_block_fft_performance/block_fft_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/03_block_fft_performance/block_fft_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_block_fft_performance/block_fft_performance_many.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/03_block_fft_performance/block_fft_performance_many.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_nvrtc_fft/nvrtc_fft_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_nvrtc_fft/nvrtc_fft_block_lto.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_block_lto.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_nvrtc_fft/nvrtc_fft_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_nvrtc_fft/nvrtc_fft_thread_lto.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_thread_lto.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_nvrtc_fft/nvrtc_query_autotune_lto.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_query_autotune_lto.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_nvrtc_fft/nvrtc_query_database_fft_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_query_database_fft_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_nvrtc_fft/nvrtc_query_database_fft_block_lto.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_query_database_fft_block_lto.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_fft_Xd/fft_2d.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_fft_Xd/fft_2d_r2c_c2r.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d_r2c_c2r.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_fft_Xd/fft_2d_single_kernel.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d_single_kernel.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_fft_Xd/fft_2d_single_kernel_block_dim.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d_single_kernel_block_dim.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_fft_Xd/fft_3d.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_3d.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_fft_Xd/fft_3d_box_single_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_3d_box_single_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_fft_Xd/fft_3d_cube_single_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_3d_cube_single_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [06_convolution/convolution.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/06_convolution/convolution.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [06_convolution/convolution_padded.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/06_convolution/convolution_padded.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [06_convolution/convolution_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/06_convolution/convolution_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [06_convolution/convolution_r2c_c2r.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/06_convolution/convolution_r2c_c2r.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_convolution_3d/convolution_3d.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_convolution_3d/convolution_3d_c2r.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_c2r.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_convolution_3d/convolution_3d_padded.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_padded.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_convolution_3d/convolution_3d_padded_r2c.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_padded_r2c.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_convolution_3d/convolution_3d_r2c.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_r2c.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [08_mixed_precision/mixed_precision_fft_1d.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_1d.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [08_mixed_precision/mixed_precision_fft_2d.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [09_introduction_lto_example/introduction_lto_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/09_introduction_lto_example/introduction_lto_example.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [09_introduction_lto_example/lto_query_database_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/09_introduction_lto_example/lto_query_database_example.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [10_cufft_device_api_example/cufft_device_api_lto_helper/cufft_device_api_lto_helper.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/10_cufft_device_api_example/cufft_device_api_lto_helper/cufft_device_api_lto_helper.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [10_cufft_device_api_example/cufft_device_api_example.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/10_cufft_device_api_example/cufft_device_api_example.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [lto_helper/cufftdx_cufft_lto_helper.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuFFTDx/lto_helper/cufftdx_cufft_lto_helper.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |

### MathDx/cuRANDDx

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [01_introduction/philox_thread_api.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu.md) | FAILED | B14 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [02_thread_api/mrg_two_distributions_thread_api.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/02_thread_api/mrg_two_distributions_thread_api.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_thread_api/pcg_thread_api.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/02_thread_api/pcg_thread_api.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_thread_api/philox_random_bits_thread_api.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/02_thread_api/philox_random_bits_thread_api.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_thread_api/sobol_thread_api.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/02_thread_api/sobol_thread_api.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_thread_api/xorwow_init_and_generate_thread_api.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/02_thread_api/xorwow_init_and_generate_thread_api.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_nvrtc/nvrtc_pcg_thread_api.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuRANDDx/03_nvrtc/nvrtc_pcg_thread_api.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |

### MathDx/cuSolverDx

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [00_Introduction/posv_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/00_Introduction/posv_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/gesv_batched_partial_pivot_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_partial_pivot_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/gesv_batched_partial_pivot_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_partial_pivot_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/gesv_batched_wo_pivot_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_wo_pivot_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/gesv_batched_wo_pivot_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_wo_pivot_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/getrf_partial_pivot_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/getrf_partial_pivot_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/getrf_wo_pivot_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/getrf_wo_pivot_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/gtsv_batched_wo_pivot_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gtsv_batched_wo_pivot_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/gtsv_batched_wo_pivot_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gtsv_batched_wo_pivot_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/posv_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/posv_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/potrf_batched_cluster.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_batched_cluster.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/potrf_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [01_Linear_Solve/potrf_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_block.cu.md) | FAILED | B14 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [01_Linear_Solve/potrf_runtime_ld_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_runtime_ld_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_Least_Squares/gels_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/02_Least_Squares/gels_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_Least_Squares/gels_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/02_Least_Squares/gels_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_Orthogonal_Factors/geqrf_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/geqrf_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_Orthogonal_Factors/geqrf_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/geqrf_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_Orthogonal_Factors/ungqr_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/ungqr_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_Orthogonal_Factors/ungqr_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/ungqr_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_Orthogonal_Factors/unmqr_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/unmqr_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_Orthogonal_Factors/unmqr_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/unmqr_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_Symmetric_Eigenvalues/heev_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/heev_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_Symmetric_Eigenvalues/heev_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/heev_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_Symmetric_Eigenvalues/hegst_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/hegst_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_Symmetric_Eigenvalues/hegst_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/hegst_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_Symmetric_Eigenvalues/hegv_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/hegv_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_Symmetric_Eigenvalues/htev_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/htev_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_Symmetric_Eigenvalues/htev_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/htev_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_Singular_Value_Decomposition/bdsvd_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/bdsvd_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_Singular_Value_Decomposition/bdsvd_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/bdsvd_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_Singular_Value_Decomposition/gesvd_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/gesvd_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_Singular_Value_Decomposition/gesvd_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/gesvd_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_BLAS/trsm_batched_block.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_BLAS/trsm_batched_thread.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/07_BLAS/trsm_batched_thread.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [07_BLAS/trsm_batched_thread_advanced.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/07_BLAS/trsm_batched_thread_advanced.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [08_NVRTC/nvrtc_potrs.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [09_Performance/geqrf_batched_performance.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/09_Performance/geqrf_batched_performance.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [10_Advanced/blocked_potrf.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/10_Advanced/blocked_potrf.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [10_Advanced/cga_blocked_potrf_right_looking.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/10_Advanced/cga_blocked_potrf_right_looking.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [10_Advanced/cga_tsqrhr.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/10_Advanced/cga_tsqrhr.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [10_Advanced/reg_least_squares.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/cuSolverDx/10_Advanced/reg_least_squares.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |

### MathDx/libmathdx

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [cublasdx.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cublasdx.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cublasdx_pipeline.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cublasdx_pipeline.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cublasdx_pipelining_callback.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cublasdx_pipelining_callback.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cublasdx_tensor.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cublasdx_tensor.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cufftdx.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cufftdx.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cufftdx_heuristics.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cufftdx_heuristics.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [curanddx.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/curanddx.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cusolverdx_potrf.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cusolverdx_potrf.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cusolverdx_potrs.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cusolverdx_potrs.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [cusolverdx_trsm.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/cusolverdx_trsm.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [nvcompdx.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/nvcompdx.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [nvcompdx_batch.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/libmathdx/nvcompdx_batch.cpp.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |

### MathDx/nvCOMPDx

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [01_introduction/lz4_gpu_compression_introduction.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/nvCOMPDx/01_introduction/lz4_gpu_compression_introduction.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [02_lz4_gpu/lz4_gpu_compression_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/nvCOMPDx/02_lz4_gpu/lz4_gpu_compression_decompression.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_ans_gpu/ans_gpu_compression_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_compression_decompression.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [04_ans_gpu/ans_gpu_decompression_reduction.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_decompression_reduction.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |
| [05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/MathDx/nvCOMPDx/05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu.md) | FAILED | R-DX 设备算法研究 | B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。 |

### NPP

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [distanceTransform/distanceTransform.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/distanceTransform/distanceTransform.cpp.md) | FAILED | B15 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [findContour/findContour.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/findContour/findContour.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [houghLines/houghLines.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/houghLines/houghLines.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [nppCanny/npp_canny_simple.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/nppCanny/npp_canny_simple.cpp.md) | FAILED | B15 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [nppCanny/npp_canny_simple.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/nppCanny/npp_canny_simple.py.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [opencvBenchmark/opencvBenchmark.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/opencvBenchmark/opencvBenchmark.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [templateMatching/templateMatching.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/templateMatching/templateMatching.cpp.md) | FAILED | B15 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [watershedSegmentation/watershedSegmentation.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP/watershedSegmentation/watershedSegmentation.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |

### NPP+

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [cannyEdgeDetectorPython/cannyEdgeDetector.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [findContour/findContourNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP+/findContour/findContourNPPPlus.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |
| [floodFill/floodFillVariousRegionTypesNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp.md) | FAILED | B15 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [watershedSegmentation/watershedSegmentationNPPPlus.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp.md) | FAILED | R-VISION 算法研究 | 先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。 |

### nvJPEG

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [Image-Resize-WaterMark/imageResizeWatermark.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp.md) | FAILED | B10 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [Image-Resize/imageResize.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/Image-Resize/imageResize.cpp.md) | FAILED | B10 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp.md) | FAILED | B10 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp.md) | FAILED | B10 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [nvJPEG-Decoder/tests/test_decoder.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md) | BLOCKED | B10 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [nvJPEG-Decoder/nvjpegDecoder.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp.md) | PARTIAL | B10 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |

### nvJPEG2000

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG2000/nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvJPEG2000-Decoder/nvjpeg2k_decode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvJPEG2000-Encoder/nvjpeg2k_encode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvJPEG2000/nvJPEG2000-Encoder/nvjpeg2k_encode.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |

### nvTIFF

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvTIFF/nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvTIFF/nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvTIFF-Decode/nvtiff_decode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvTIFF/nvTIFF-Decode/nvtiff_decode.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvTIFF-Encode-Options/nvtiff_encode_options.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvTIFF/nvTIFF-Encode-Options/nvtiff_encode_options.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |
| [nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvTIFF/nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp.md) | FAILED | G-CODEC 新增 GPU codec | rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。 |

### nvCOMP

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [benchmarks/benchmark_ans_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_ans_chunked.cu.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [benchmarks/benchmark_bitcomp_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_bitcomp_chunked.cu.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [benchmarks/benchmark_bitcomp_cpu.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_bitcomp_cpu.cu.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [benchmarks/benchmark_cascaded_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_cascaded_chunked.cu.md) | FAILED | G-COMPRESS codec/API 探针 | 先验收 B9；其余 codec、GDS、CRC、manager/streaming/CPU互操作逐项设计。 |
| [benchmarks/benchmark_crc32.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_crc32.cpp.md) | FAILED | G-COMPRESS codec/API 探针 | 先验收 B9；其余 codec、GDS、CRC、manager/streaming/CPU互操作逐项设计。 |
| [benchmarks/benchmark_deflate_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_deflate_chunked.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [benchmarks/benchmark_gdeflate_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_gdeflate_chunked.cu.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [benchmarks/benchmark_gdeflate_cpu.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_gdeflate_cpu.cpp.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [benchmarks/benchmark_gzip_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_gzip_chunked.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [benchmarks/benchmark_gzip_streaming.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_gzip_streaming.cpp.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [benchmarks/benchmark_lz4_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_lz4_chunked.cu.md) | FAILED | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [benchmarks/benchmark_python.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_python.py.md) | FAILED | G-COMPRESS codec/API 探针 | 先验收 B9；其余 codec、GDS、CRC、manager/streaming/CPU互操作逐项设计。 |
| [benchmarks/benchmark_snappy_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_snappy_chunked.cu.md) | FAILED | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [benchmarks/benchmark_zstd_chunked.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/benchmarks/benchmark_zstd_chunked.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [examples/bitcomp_native_lossy.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/bitcomp_native_lossy.cu.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [examples/deflate_cpu_compression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/deflate_cpu_compression.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [examples/deflate_cpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/deflate_cpu_decompression.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [examples/gdeflate_cpu_compression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/gdeflate_cpu_compression.cu.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [examples/gdeflate_cpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/gdeflate_cpu_decompression.cu.md) | FAILED | U4 codec 路线不可用 | 具体 codec 路线边界见 U4；保留当前失败证据。 |
| [examples/gzip_gpu_compression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/gzip_gpu_compression.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [examples/gzip_gpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/gzip_gpu_decompression.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [examples/high_level_quickstart_example.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/high_level_quickstart_example.cpp.md) | FAILED | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [examples/low_level_quickstart_example.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/low_level_quickstart_example.cpp.md) | PARTIAL | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [examples/lz4_cpu_compression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/lz4_cpu_compression.cu.md) | FAILED | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [examples/lz4_cpu_compression_high_level.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/lz4_cpu_compression_high_level.cpp.md) | FAILED | G-COMPRESS codec/API 探针 | 先验收 B9；其余 codec、GDS、CRC、manager/streaming/CPU互操作逐项设计。 |
| [examples/lz4_cpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/lz4_cpu_decompression.cu.md) | FAILED | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [examples/nvcomp_crc32.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/nvcomp_crc32.cu.md) | FAILED | G-COMPRESS codec/API 探针 | 先验收 B9；其余 codec、GDS、CRC、manager/streaming/CPU互操作逐项设计。 |
| [examples/nvcomp_gds.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/nvcomp_gds.cu.md) | FAILED | G-COMPRESS codec/API 探针 | 先验收 B9；其余 codec、GDS、CRC、manager/streaming/CPU互操作逐项设计。 |
| [examples/snappy_cpu_compression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/snappy_cpu_compression.cu.md) | FAILED | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [examples/snappy_cpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/snappy_cpu_decompression.cu.md) | FAILED | B9 | 明确候选；先通过对应批次入口门槛，尚未实施。 |
| [examples/zstd_cpu_compression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/zstd_cpu_compression.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |
| [examples/zstd_cpu_decompression.cu](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvCOMP/examples/zstd_cpu_decompression.cu.md) | FAILED | G-CODEC-DIR 先核方向 | 按第 4 节核对编码/解码方向与互操作；不能混为整例支持。 |

### nvMatmulHeuristics

| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |
| --- | --- | --- | --- |
| [1_gemm_heuristics.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvMatmulHeuristics/1_gemm_heuristics.cpp.md) | FAILED | G-HEURISTICS 模型与硬件门槛 | hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。 |
| [2_discovery.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvMatmulHeuristics/2_discovery.cpp.md) | FAILED | G-HEURISTICS 模型与硬件门槛 | hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。 |
| [3_energy_discovery.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvMatmulHeuristics/3_energy_discovery.cpp.md) | FAILED | G-HEURISTICS 模型与硬件门槛 | hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。 |
| [4_runtime_estimation.cpp](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvMatmulHeuristics/4_runtime_estimation.cpp.md) | FAILED | G-HEURISTICS 模型与硬件门槛 | hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。 |
| [5_get_configs.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvMatmulHeuristics/5_get_configs.py.md) | FAILED | G-HEURISTICS 模型与硬件门槛 | hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。 |
| [6_get_configs_ex.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvMatmulHeuristics/6_get_configs_ex.py.md) | FAILED | G-HEURISTICS 模型与硬件门槛 | hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。 |
| [7_smem_carveout.py](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/sample-reports/nvMatmulHeuristics/7_smem_carveout.py.md) | FAILED | G-HEURISTICS 模型与硬件门槛 | hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。 |
