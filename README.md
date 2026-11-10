[![License](https://img.shields.io/badge/License-Apache_2.0-yellowgreen.svg)](https://opensource.org/licenses/Apache-2.0)

# CUDA Library Samples on ROCm

[MOAT 重写计划](migration/moat-rewrite-plan.md) · [重写实时进展与实验日志](migration/reports/rewrite-progress.md)

对照 NVIDIA CUDA Library Samples，逐例选择 AMD/ROCm 生态中适合的库并实现。每例公开实际使用库、实现程度、正确性结果、CUDA 对照及失败原因。保留 CUDA 原始源码作为参考；AMD 实验固定 ROCm 10.1.0 / Radeon AI PRO R9700（gfx1201），CUDA 对照使用双 RTX 5090 机器。

[B12–B15 实施与缺口](migration/reports/batches12-15.md) · [B9–B11 验收](migration/reports/batches9-11.md) · [B4–B8 验收](migration/reports/batches4-8.md) · [后续批次计划与能力边界](migration/roadmap.md) · [支持方式与详细日志总表](migration/reports/support-log-index.md) · [模块支持矩阵](#模块支持矩阵) · [已验收算子](#已验收算子与验证范围) · [未通过的具体原因](#未通过和不支持的具体原因) · [设计与实施日志](migration/design.md) · [执行交付报告](migration/reports/plan-execution.md) · [逐例清单](migration/samples.yaml) · [环境锁](migration/environments/project.lock.json)

## 当前结果

上游固定为 `8b0573b11d183d9b3a36cd2955aa31c16cc61b95`。静态审计覆盖 **866 个源文件、477 个构建定义、639 个独立可执行/脚本源入口**。链接辅助文件、外部 SDK binding、架构/静态链接/通信变体另存元数据，不重复计入入口分母；没有在所有专有 SDK 条件下展开并执行每个构建配置。

PASSED: 231；PARTIAL: 23；FAILED: 385；BLOCKED: 0；UNSUPPORTED: 0；NOT_STARTED: 0；IN_PROGRESS: 0。

`PASSED` 只表示该行明确登记的原始功能和必需用例通过，不能推及整库、其它精度/规模或性能。`PARTIAL` 包括数值子集已通过但原始功能/执行合同仍有缺口，或已运行尚缺独立验收的端口；`FAILED` 保留真实失败日志和重试条件。不存在“HIPIFY 退出成功即迁移成功”的统计。

专项证据：[M1 双端数值对照](migration/reports/m1-comparison.json)、[BLAS 三方对照](migration/reports/blas-three-way.json)、[稀疏 expected 检查](migration/reports/sparse-original-validation.json)、[新增双端数值/分布对照](migration/reports/additional-comparison.json)、[AMD 生态探针](migration/reports/native-probes.json)、[选型与缺口](migration/reports/ecosystem-decisions.md)、[最终一致性检查](migration/reports/final-validation.json)。**M0–M5 已逐批执行并记录结果；按逐例登记范围的成功率为 36.15%，失败/部分完成仍在分母。**

性能仅选择 6 个 GEMM profile；AMD GPU 有其它任务，空闲资格检查失败，因此 [性能报告](migration/reports/performance-comparison.md) 标为 BLOCKED，仅保留原始计时，不发布合格速度比。

**第二批已收口：17/17 个样例、45 个输入 case。** [详细验收报告](migration/reports/batch2.md) 包含稀疏 3 项、BLAS 8 项、tensor 4 项与 solver 2 项的 CPU/CUDA 对照、原始规模与边界检查。`rotmg` 的原生缩放错误及项目 GPU 修正[单独记录](migration/reports/rotmg-scale-fix.md)；大张量 fixture 支持按 seed 和 SHA256 完整重建。

**第三批已收口：8/8 个样例、26 个输入 case，ROCm/独立 CPU/CUDA 三方通过。** [第三批详细验收与复现](migration/reports/batch3.md) 覆盖 CG、BiCGSTAB、五对角批量求解、4 项 solver 与 SpVV Graph Capture/Replay；包含 meig/未排序配对检查、2000 个实际 GPU 图节点、输入变化重放，以及 24 项反向检查。

**B4–B8：26/26 个样例、92/92 个预登记用例验收通过。** [逐例实际库、限制与详细日志](migration/reports/batches4-8.md)。3项CUDA新API在已安装SDK缺失，原生基线保持FAILED，兼容CUDA数学基线通过。

| 批次 | 样例通过 | 用例通过 |
| --- | ---: | ---: |
| B4 | 8/8 | 32/32 |
| B5 | 4/4 | 12/12 |
| B6 | 4/4 | 15/15 |
| B7 | 5/5 | 15/15 |
| B8 | 5/5 | 18/18 |

**B9–B11实施结果：** B9 6/8 整例通过、2 部分支持；B10 0/6 整例通过、6 部分支持；B11 4/5 整例通过、1 部分支持。[逐例支持方式、缺口与日志](migration/reports/batches9-11.md)。CPU progressive fallback、完整NVBENCH框架与cuDSS配置/查询缺口保留PARTIAL。

**B12–B15：** B12 2整例、4部分支持、36/36cases；B13 3整例、3部分支持、36/36cases；B14 3整例、1部分支持、24/24cases；B15 1整例、3部分支持、24/24cases。[实际路线、逐例限制与详细日志](migration/reports/batches12-15.md)。原始vendor基线与兼容CUDA数学对照分别记录。

**MOAT R1–R2：8/8 个原始样例满足复合验收门槛，51 个预登记输入。** [逐例路线、原生/兼容 CUDA 区分与完整实验入口](migration/reports/rewrite-R1-R2.md)。支持计数以已写入主表的资格为准；失败、重试和证据勘误保留。

**MOAT R3：2 个原PARTIAL整例收口（NCC原始文件harness、rank-r batched SVD），15个输入、24项输出故障注入、18项实际运行边界。** [实际路线与详细实验](migration/reports/rewrite-R3.md)；[原24项逐例合同复审与剩余缺口](migration/reports/rewrite-R3-gaps.md)。静态合同审查不算新增GPU成功。

## 已验收算子与验证范围

**18 个模块已有整例通过，覆盖 117 个按模块去重的算子/功能族，对应 231 个通过的样例入口。**

计数按数学算子或原例核心功能归并；同模块的精度、尺寸、语言、batch、存储格式和算法变体不重复增加算子数。例如 cuRAND 是 4 种分布、36 个 generator/distribution profile；cuDSS simple 的 3 种语言入口算 1 个功能族。跨模块总数保留不同库接口的实现，GEMM 可分别出现在 cuBLAS 与 cuBLASLt。每个族至少有一个通过独立验收的样例，支持范围限于下表和逐例 required cases。

| 模块 | 已验收算子/功能族数 | 已验收算子/功能 | 通过样例 | 验证范围 |
| --- | ---: | --- | ---: | --- |
| [cuBLAS](cuBLAS/README.md) | 52 | `amax`、`amin`、`asum`、`axpy`、`copy`、`dgmm`、`dot`、`dotc`、`gbmv`、`geam`、`gemm`、`gemv`、`ger`、`hbmv`、`hemm`、`hemv`、`her`、`her2`、`her2k`、`herk`、`herkx`、`hpmv`、`hpr`、`hpr2`、`nrm2`、`rot`、`rotg`、`rotm`、`rotmg`、`sbmv`、`scal`、`spmv`、`spr`、`spr2`、`swap`、`symm`、`symv`、`syr`、`syr2`、`syr2k`、`syrk`、`syrkx`、`tbmv`、`tbsv`、`tpmv`、`tpsv`、`tpttr`、`trmm`、`trmv`、`trsm`、`trsv`、`trttp` | 72 | 固定教学profile与所列扩展cases；含复杂rank-k类型化适配、HIP GPU packed转换、FP32分组batched及FP64项目策略调优。rotmg极端缩放使用HIP修正；调优/批量变体按同一数学族去重。 |
| [cuBLASLt](cuBLASLt/README.md) | 1 | `GEMM` | 8 | 既有6个profile为FP32 SGEMM、HSH pointer-array/strided、grouped分发及custom-find/autotune。MOAT新资格分别登记FP16 planar负偏移转换/FP32 3M/FP16输出，以及真实COL32/COL4 packing + native INT8/INT32 GemmEx；按样例链接与资格状态限定范围。 |
| [cuBLASMp](cuBLASMp/README.md) | 2 | `block-cyclic 重分布`、`分布式 GEADD` | 2 | 已登记FP64 GEADD与1024阶block-cyclic重分布/往返；双MPI进程和不同GPU实际通信。GEMM子矩阵与低精度collective/quantized scale模式等缺口保持PARTIAL，未覆盖多节点。 |
| [cuDSS](cuDSS/README.md) | 2 | `稀疏直接求解`、`稀疏重排序与求解` | 14 | FP64 CSR：simple、异构/均匀batch、重排后完整求解及GENERAL多RHS残差；CPU符号/matching + rocSOLVER CSRRF或项目HIP CSR pivot LU。MOAT新增8个真实ISO_C_BINDING Fortran入口，uniform保留GPU factor并选择性重算，residual应用实际检查；原CUDA Fortran工具链仍缺。CPP重排严格METIS向量不同及get_set缺项保持PARTIAL，不把历史analysis-only计为完整求解。规模/动态pivot按逐例范围。 |
| [cuFFT](cuFFT/README.md) | 3 | `C2C 复数 FFT`、`FFT 窗口过滤 callback`、`R2C/C2R 实数 FFT` | 10 | 10 个 profile：原始单卡/双卡 C2C、实数正逆变换和 legacy/离线 SPIR-V/HIPRTC callback。1D 多卡使用 hipFFT + RCCL + HIP。 |
| [cuFFTMp](cuFFTMp/README.md) | 1 | `多进程 slab C2C FFT` | 1 | 双MPI rank，原始16³及不均匀17×13×9；hipFFT本地YZ/X FFT + RCCL Send/Recv + HIP pack/unpack/归一化，完整频域与逆变换输出。 |
| [cuPQC](cuPQC/README.md) | 2 | `SHA-256`、`SHA3-256` | 2 | SHA-256 单线程与 SHA3-256 的 32-lane 协作 GPU kernel；各 14 输入与 hashlib 精确一致，PQC 其它算法未实现。 |
| [cuRAND](cuRAND/README.md) | 4 | `lognormal`、`normal`、`poisson`、`uniform` | 36 | 4 种分布 × 9 个 generator = 36 个 profile；原始参数、库内重复性和解析分布矩通过，跨库不要求逐位同序列。 |
| [cuSOLVER](cuSOLVER/README.md) | 10 | `Cholesky 分解`、`LU 分解/求解`、`QR 分解`、`QR 的 Q 应用`、`QR 的 Q 生成`、`SVD`、`三角矩阵求逆`、`多 GPU LU 分解/求解`、`对称特征分解`、`广义对称特征分解` | 23 | B13补611阶双GPU LU/pivot/solve，tile256列分布+RCCL+HIP，全部CPU重构/残差；MgPotrf及Mp原始descriptor缺口另列。原始FP64教学矩阵；status/info、全量分解/重构、残差、正交性、未排序配对及实际meig检查。B6增加64位LU/三角求逆；SVD/eigen typed接口显式INT_MAX限制。 |
| [cuSPARSE](cuSPARSE/README.md) | 20 | `SpVV Graph Capture/Replay`、`axpby`、`bicgstab`、`cg`、`coosort`、`dense2sparse`、`gather`、`gpsvinterleavedbatch`、`rot`、`scatter`、`sddmm`、`sparse2dense`、`spgemm`、`spmat`、`spmm`、`spmv`、`spmvop`、`spsm`、`spsv`、`spvv` | 36 | 已登记CSR/COO/SELL/BSR等格式、CG/BiCG残差/收敛、gpsv布局和真实Graph replay。B8补CSR→CSC、对称展开、HIP GPU预算分块SpGEMM和融合custom op；3项CUDA新API缺失，使用明确标注的兼容数学基线。 |
| [cuSPARSELt](cuSPARSELt/README.md) | 1 | `2:4 结构化稀疏 GEMM（含裁剪/压缩）` | 2 | 默认FP16 A/B/C/bias、FP32累积；项目HIP 4×4 TILE最大L1裁剪、实际packed values/metadata及只读压缩数据的稀疏乘法，basic GPU搜索，advanced双batch/stride/bias/ReLU。14输入CPU/原生稀疏数学对照及两个原CUDA程序另验；原生hipSPARSELt/gfx1201失败另存，不声明原生加速/opaque格式兼容。 |
| [cuTENSOR](cuTENSOR/README.md) | 7 | `三元逐元素运算`、`二元逐元素运算`、`张量 contraction`、`张量 einsum`、`张量 permutation`、`张量 plan cache`、`张量 reduction` | 9 | FP32：hipTensor逐元素/排列/规约；rocBLAS+HIP contraction；B5补HIP padding、einsum路由、三输入收缩和真实GPU分块搜索/持久化缓存。B2/B5全部原始规模输出均有全量FP64 CPU检查；早期M3 contraction仅抽样的历史证据另保留。 |
| [cuTENSORMg](cuTENSORMg/README.md) | 1 | `多 GPU 张量 contraction` | 1 | 单进程双GPU；原始4096 extents/2048 block及i,k / k,j / i,j，hipBLAS + RCCL，全部FP64 CPU参考；其它分区/精度/多节点不外推。 |
| [MathDx/cuBLASDx](MathDx/cuBLASDx/README.md) | 1 | `设备内 GEMM` | 1 | HIP调用方kernel内协作GEMM三阶段、128点双FFT、32阶complex上三角Cholesky/shared LDA33；原生SDK25.6版本差异与兼容CUDA数学对照分开。RNG LEGACY逐位合同仍PARTIAL。 |
| [MathDx/cuFFTDx](MathDx/cuFFTDx/README.md) | 1 | `设备内 C2C FFT` | 1 | HIP调用方kernel内协作128点双C2C FFT、ElementsPerThread=8/共32线程及扩展线程块；全部CPU频谱输出与兼容CUDA数学基线。 |
| [MathDx/cuSolverDx](MathDx/cuSolverDx/README.md) | 4 | `设备内 Cholesky 分解/求解`、`设备内 complex Cholesky`、`设备内 partial-pivot LU`、`设备内三角求解` | 4 | HIP调用方kernel内complex Cholesky；MOAT新增complex FP32 48×32 pivot LU、complex FP64 32阶双batch POSV、FP64 right/lower 32×33 TRSM。原生MathDx26.06.1原例实际device输出、同字节HIP与独立CPU分别记录；只按已通过样例的登记范围统计。 |
| [NPP](NPP/README.md) | 2 | `Euclidean 距离变换/Voronoi`、`零均值 NCC` | 2 | 精确Euclidean距离/Voronoi/整数截断；NCC原始2048×1024 RAW、全部CLI、完整score/GPU argmax、PGM与HIP-event计时已收口，常量模板/图块按原生大图路径实测；Canny原生像素策略与其它未完成入口继续逐例记录。 |
| [nvCOMP](nvCOMP/README.md) | 3 | `CRC32`、`LZ4`、`Snappy` | 7 | hipCOMP LZ4/Snappy原生批处理；CPU↔GPU与hipCOMP↔nvCOMP双向互解、逐chunk status/实际长度、空/边界/损坏流；LZ4 native manager/factory +项目CRC32C及100 raw buffers。独立CRC32入口采用项目HIP IEEE/PKZIP算法，与zlib及真实nvCOMP逐chunk比较，空输入按原生语义拒绝；具体资格见逐例状态。完整NVBENCH框架仍单列PARTIAL。 |

以下仅有子集/能力探针，**不计入上述整例支持数**：

| 模块 | 已验证子集 | 原始样例尚缺什么 |
| --- | --- | --- |
| nvJPEG | rocJPEG baseline 解码；B10真实CLI/布局/缩放/ROI/多实例/后处理逐例验收 | progressive缺少原生GPU后端；显式CPU fallback/encode另标注；6 PARTIAL、0 PASSED |
| NPP | 精确Euclidean距离/Voronoi已整例通过；Canny与NCC有数值子集 | 原生Canny像素策略、NCC文件harness及其它尚未完成合同按逐例状态记录 |

逐个算子族与样例的可追溯映射见 [operator-support.json](migration/reports/operator-support.json)；失败仍按具体入口和原因保留。

## 模块支持矩阵

下表覆盖全部 30 个库级模块。“已验收算子族”按上文口径去重；“通过/总入口”是原始 sample 数，二者分别统计。部分完成、失败、明确不支持、前置条件阻塞分别列出；每个模块链接包含全部原始样例的实际库、代码、逐例原因和证据。候选库不计为实际使用库。

| 模块 | 实际/候选 AMD 路线 | 已验收算子族 | 通过/总入口 | 部分 | 失败 | 不支持 | 阻塞 | 当前范围及未通过原因 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| [cuBLAS](cuBLAS/README.md) | HIP GPU packed conversion → HIP runtime; hipBLAS + HIP scale fix → rocBLAS; hipBLAS + project search/group dispatch → rocBLAS; hipBLAS → rocBLAS; hipBLAS/rocBLAS three real SGEMMs + HIP Hermitian triangle epilogue; hipBLAS/rocBLAS three real SGEMMs + HIP complex split/merge; hipBLAS/rocBLAS three real SGEMMs + HIP symmetric triangle epilogue | 52 | 72/82 | 0 | 10 | 0 | 0 | 常规运算与第二批索引/旋转/batch 已验收；rotmg 原生重复缩放错误由项目 HIP GPU 修正。Emulation、3m、部分 Ex/packed 转换仍有接口/算法改写缺口。 |
| [cuBLASLt](cuBLASLt/README.md) | HIP COL32/COL4 packing/unpacking + native hipBLAS GemmEx INT8/INT32 → rocBLAS; HIP negative-offset FP16 planar conversion + hipBLAS/rocBLAS FP32 3M + HIP FP16 output; hipBLASLt; hipBLASLt + project search/group dispatch → hipBLASLt/rocBLAS; hipBLASLt → hipBLASLt native | 1 | 8/20 | 0 | 12 | 0 | 0 | FP32 与两种 HSH FP16 batch 路径验证通过；高级 scale/quantization、grouped/autotune 接口及 FP8 格式不能按名字强行等同。 |
| [cuBLASMp](cuBLASMp/README.md) | MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization; MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD; MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip; MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization; MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization; MPI + RCCL distribution + hipBLAS FP32 local GEMM | 2 | 2/14 | 4 | 8 | 0 | 0 | B12原始FP64 GEADD与block-cyclic重分布/往返通过；MPI双rank使用不同GPU及真实RCCL。GEMM原始B子矩阵offset、FP16 collective舍入/FP8/FP4 scale和完整CLI保持PARTIAL；没有多节点资格。 |
| [cuDSS](cuDSS/README.md) | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter → rocSOLVER/HIP runtime; CPU symbolic min-degree + project HIP CSR pivot LU/solve via shared C ABI → CPU analysis + HIP preparation; rocSOLVER + rocBLAS via ISO_C_BINDING/C ABI → GPU CSRRF sparse Cholesky; CPU sparse symbolic graph; rocSOLVER CSRRF + rocBLAS → GPU sparse Cholesky; CPU sparse symbolic analysis; standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only | 2 | 14/59 | 2 | 43 | 0 | 0 | simple三语言及B11的异构/均匀batch、重排序analysis-only、1000阶GENERAL双RHS已验收：CPU sparse symbolic/matching + rocSOLVER CSRRF或HIP CSR pivot LU。get_set保留完整cuDSS超级面板/16字段内存/原顺序DIAG语义缺口；小例性能和大规模动态pivot、Schur/分布式/allocator等未资格化。 |
| [cuEST](cuEST/README.md) | 候选：unresolved | 0 | 0/51 | 0 | 51 | 0 | 0 | 原始 GPU 电子结构 context、积分/梯度、DF/XC/PCM 等 vendor SDK 尚无本项目 AMD 绑定/算法实现；hipBLAS 本身不提供这些高层算子。 |
| [cuFFT](cuFFT/README.md) | hipFFT + RCCL + HIP → Two GPU radix decomposition and GPU merge; hipFFT → rocFFT; hipFFT/rocFFT JIT callbacks + HIP compiler SPIR-V → rocFFT SPIR-V JIT integration; hipFFT/rocFFT JIT callbacks + HIPRTC → rocFFT SPIR-V JIT integration | 3 | 10/10 | 0 | 0 | 0 | 0 | 原始单卡、双卡、legacy/JIT callback 分别实现；1D Xt 不支持的单 batch 路径改用 hipFFT + RCCL + GPU 合并，JIT 使用 SPIR-V。 |
| [cuFFTMp](cuFFTMp/README.md) | MPI + hipFFT local YZ/X FFT + RCCL Send/Recv + HIP slab transpose/scale | 1 | 1/20 | 0 | 19 | 0 | 0 | B13 MPI双rank/不同GPU：原始16³和不均匀17×13×9经native hipFFT + GPU slab转换 + RCCL Send/Recv，频域和逆变换全量通过；其它分布/多节点未覆盖。 |
| [cuPQC](cuPQC/README.md) | HIP runtime + custom device SHA implementation → HIP/gfx1201 | 2 | 2/6 | 0 | 4 | 0 | 0 | SHA2/SHA3 使用自有 HIP 设备实现且独立摘要完全一致；ML-KEM/ML-DSA/Merkle/Poseidon2 仍需设备算法与 API 改写。 |
| [cuRAND](cuRAND/README.md) | hipRAND → rocRAND | 4 | 36/36 | 0 | 0 | 0 | 0 | 36 个 generator/distribution 的原始参数、重复性与解析分布矩均验证；MT19937 初始化需较长时限，跨库序列不要求相同。 |
| [cuSOLVER](cuSOLVER/README.md) | HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads; HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads; hipBLAS Dtrsm_64 + HIP diagonal/info adapter → rocBLAS/HIP runtime; hipSOLVER + hipBLAS → rocSOLVER/rocBLAS; hipSOLVER → rocSOLVER; hipSOLVER → rocSOLVER/rocBLAS; hipSOLVER/rocSOLVER native full GPU SVD + HIP rank projection and FP64 residual → rocSOLVER + project HIP; rocSOLVER ILP64; rocSOLVER dgesvd + checked dimension bridge; rocSOLVER dsyevx + checked dimension bridge | 10 | 23/39 | 4 | 12 | 0 | 0 | 基础分解、Xgeqrf/Xpotrf、gesvdjBatched、syevjBatched、syevdx/sygvdx 已验收；后四项检查逐batch重构/配对、meig与选区。Xgeev三例仍需排除CPU兼容路径，gesvdaStridedBatched仍需确认近似算法与残差语义，保留PARTIAL；Mg、IRS等其它入口缺AMD改写或oracle。 B13另完成611阶MgGetrf双GPU/tile256列分布与GPU pivot/solve；MgPotrf输入descriptor仍PARTIAL。 |
| [cuSOLVERMp](cuSOLVERMp/README.md) | MPI + RCCL + HIP column-distributed partial-row-pivot LU/solve; MPI + RCCL + HIP distributed column Cholesky/solve | 0 | 0/16 | 2 | 14 | 0 | 0 | MPI + RCCL + HIP真实分布列LU/Cholesky与求解、残差已验收；原始二维process-grid、子矩阵offset与随机SPD profile未完整等价，两例PARTIAL。 |
| [cuSOLVERSp2cuDSS](cuSOLVERSp2cuDSS/README.md) | 候选：hipSOLVER, rocSOLVER (subset) | 0 | 0/7 | 0 | 7 | 0 | 0 | 原例对比两个 NVIDIA 稀疏直接求解 API；没有完成保持两条路线及对应配置语义的 AMD 改写。 |
| [cuSPARSE](cuSPARSE/README.md) | HIP GPU budgeted CSR SpGEMM adapter → HIP runtime; HIP GPU fused custom SpMM add/mul/epilogue → HIP runtime; HIP GPU fused custom SpMV epilogue → HIP runtime; HIP symmetric expansion + rocSPARSE v2 → rocSPARSE/HIP runtime; hipSPARSE + HIP Graph → rocSPARSE + HIP runtime; hipSPARSE + HIP format adapter → rocSPARSE + HIP runtime; hipSPARSE + hipBLAS → rocSPARSE/rocBLAS; hipSPARSE Csr2cscEx2 → rocSPARSE/HIP runtime; hipSPARSE → rocSPARSE | 20 | 36/37 | 0 | 1 | 0 | 0 | CSR/COO/blocked ELL、SpVV/SpGEMM/reuse、CG/BiCGSTAB、gpsvInterleavedBatch 与真实 SpVV Graph Capture/Replay 已通过独立 CPU 和 CUDA 验收。BSR SDDMM、部分新转换/custom operator 与其它原始入口仍失败，不能推及整个库。 |
| [cuSPARSELt](cuSPARSELt/README.md) | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul → HIP GPU; CPU descriptor/constant-mask setup only | 1 | 2/2 | 0 | 0 | 0 | 0 | hipSPARSELt 已编译并真实运行，gfx1201 kernel 数据缺失；锁定源码的支持架构列表也不接受 gfx1201，不能用 dense GEMM 代替结构化稀疏。 |
| [cuTENSOR](cuTENSOR/README.md) | HIP GPU permutation/padding → HIP runtime; hipTensor; hipTensor + rocBLAS + HIP → hipTensor/rocBLAS; rocBLAS + HIP tensor adapter → rocBLAS/HIP runtime; rocBLAS + HIP tiled-plan/cache adapter → rocBLAS/HIP runtime; rocBLAS + HIP → FP32 GEMM and GPU tensor permutations | 7 | 9/13 | 0 | 4 | 0 | 0 | hipTensor 的 binary/trinary、permutation、reduction 原始 extents 与小尺寸全部输出通过 CPU/CUDA；FP32 contraction 架构 gate 缺口由 rocBLAS + HIP 排列补足；其它高级/绑定场景仍失败。 |
| [cuTENSORMg](cuTENSORMg/README.md) | hipBLAS FP32 partitioned contraction + RCCL AllGather; single process with two GPU threads | 1 | 1/2 | 0 | 1 | 0 | 0 | B13保留4096 extents/2048 block、i,k / k,j / i,j及单进程双GPU，hipBLAS + RCCL输入分布/完整输出通过FP64 CPU；其它类型/分区及性能不外推。 |
| [cuTENSORMp](cuTENSORMp/README.md) | 候选：hipTensor, MPI, RCCL | 0 | 0/3 | 0 | 3 | 0 | 0 | 原始 MPI tensor 描述与分布式算法尚未改写；RCCL 基础可行性不等同原始 Mp profile。 |
| [MathDx/cuBLASDx](MathDx/cuBLASDx/README.md) | HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases) | 1 | 1/34 | 0 | 33 | 0 | 0 | HIP调用方kernel内FP64 32³ GEMM，shared/register-accumulate/register-store三阶段及协作/共享内存通过；其余设备融合模板未移植。公开MathDx25.6缺当前上游新API，兼容CUDA数学与vendor失败分开。 |
| [MathDx/cuFFTDx](MathDx/cuFFTDx/README.md) | HIP cooperative device radix-2 C2C FFT | 1 | 1/49 | 0 | 48 | 0 | 0 | HIP设备内128点双C2C FFT、原始32线程/每线程8元素和扩展合法线程块/尺寸通过；其它模板仍需实现。原生SDK版本不匹配不冒充vendor基线成功。 |
| [MathDx/cuRANDDx](MathDx/cuRANDDx/README.md) | rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal | 0 | 0/7 | 1 | 6 | 0 | 0 | rocRAND设备Philox4x32-10原生引擎与独立整数oracle逐word通过；显式53bit Box-Muller数学通过。原生normal头/overlay接口差异及NVIDIA LEGACY逐位host/device序列未等价，PARTIAL。 |
| [MathDx/cuSolverDx](MathDx/cuSolverDx/README.md) | HIP caller-kernel cooperative complex FP32 partial-pivot LU → project HIP device algorithm; HIP caller-kernel cooperative complex FP64 Cholesky and solve → project HIP device algorithm; HIP caller-kernel cooperative real FP64 right/lower triangular solve → project HIP device algorithm; HIP cooperative device complex FP64 upper Cholesky, shared LDA33 | 4 | 4/42 | 0 | 38 | 0 | 0 | HIP设备内32阶complex FP64上三角Cholesky、shared LDA33/256线程与非SPD info通过；其它求解DSL未改写。 |
| [MathDx/libmathdx](MathDx/libmathdx/README.md) | 候选：HIPRTC + device algorithms | 0 | 0/12 | 0 | 12 | 0 | 0 | HIPRTC 已在 FFT JIT 路线验证，但不自带原始 libmathdx 的各设备算法生成器/描述 DSL，尚未等价改写。 |
| [MathDx/nvCOMPDx](MathDx/nvCOMPDx/README.md) | 候选：hipCOMP algorithm reuse (device API unresolved) | 0 | 0/7 | 0 | 7 | 0 | 0 | hipCOMP 的 host API 不等于 device-callable nvCOMPDx；原始设备融合/CPU互通/ANS 等需要专门重写。 |
| [NPP](NPP/README.md) | HIP NCC/full original CLI/RAW input/PGM annotation/HIP-event timing → project HIP kernels; HIP exact separable Euclidean distance/Voronoi/integer truncation kernels; HIP three-channel Sobel/NMS/connected hysteresis kernels | 2 | 2/9 | 1 | 6 | 0 | 0 | 精确Euclidean距离/Voronoi位移/整数截断通过，原始两图浮点/整数结果与native NPP逐像素一致。Canny原始图仍有1995/921600像素差异，NCC原始注释图/CLI/计时框架未移植，保留PARTIAL；RPP检查未提供这些对应API，改用HIP。 |
| [NPP+](NPP+/README.md) | HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata | 0 | 0/6 | 1 | 5 | 0 | 0 | HIP等值/gradient/range/boundary五种连接区域试点及GPU面积/bbox/边界统计通过；缺原生NPP+ SDK，完整paint/metadata/边界语义未等价，PARTIAL；其它入口未实现。 |
| [nvJPEG](nvJPEG/README.md) | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode → rocJPEG/HIP runtime + libjpeg-turbo | 0 | 0/7 | 6 | 1 | 0 | 0 | B10 六个入口的baseline硬件解码、9布局/缩放/RGB ROI/native batch/多实例、HIP Lanczos/水印与真实CLI/Python测试已验收。原始12张图中2张progressive明确CPU libjpeg fallback，锁定rocJPEG HYBRID返回-12；GPU progressive、部分原例调度/decoupled/backend控制未等价，6项仍PARTIAL；JPEG编码为CPU。 |
| [nvJPEG2000](nvJPEG2000/README.md) | 候选：unresolved | 0 | 0/4 | 0 | 4 | 0 | 0 | rocJPEG 的 JPEG decode 不能替代 JPEG2000；原始 GPU codec/多阶段/metadata 接口没有 AMD 实现，CPU OpenJPEG 不计成功。 |
| [nvTIFF](nvTIFF/README.md) | 候选：unresolved | 0 | 0/6 | 0 | 6 | 0 | 0 | 原始 TIFF GPU codec 与多页/GeoTIFF/options 等接口未改写；CPU TIFF 容器处理不能冒充 GPU codec。 |
| [nvCOMP](nvCOMP/README.md) | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter → hipCOMP/HIP runtime + independent CPU codecs; project HIP IEEE/PKZIP CRC32; CPU file I/O and reference → HIP GPU CRC32 kernel | 3 | 7/32 | 2 | 23 | 0 | 0 | B9 LZ4/Snappy 6个原始例子通过：hipCOMP native batch/manager，CPU liblz4/Snappy阶段、跨厂商RAW block GPU互解及损坏流检查。2个benchmark仅codec/基础文件CLI通过，完整NVBENCH框架未移植；其它codec/高级API仍缺。 |
| [nvMatmulHeuristics](nvMatmulHeuristics/README.md) | 候选：hipBLASLt heuristics (subset) | 0 | 0/7 | 0 | 7 | 0 | 0 | hipBLASLt heuristic 已在 M1 验证；原始配置格式/模型与搜索接口未完整迁移，Origami 仅为待验收候选。 |

## 未通过和不支持的具体原因

“本项目尚未实现/验收”与“锁定版本和硬件确实不支持”分别记录。当前只有 hipSPARSELt 的 2 个样例满足后者的证据条件；其它失败需按 API、构建、数值或执行错误继续定位，不能泛化为 ROCm 不支持。

| 当前结论 | 入口数 | 具体原因 | 证据与恢复条件 |
| --- | ---: | --- | --- |
| FAILED / `BUILD_ERROR` | 320 | 自动移植稿未完成 API/枚举/类型/链接适配。例如 Lt grouped/scale/layout、FP4 观察代码、MathDx device DSL 和特殊 SDK 仍有编译缺口；不据此宣称硬件不支持。 | 各模块 README 列出首个有效编译错误；需完成保持原语义的 AMD 改写再验收。 |
| FAILED / `BINDING_OR_FRONTEND_MIGRATION_REQUIRED` | 65 | Fortran/Python 的 NVIDIA module、CUDA Fortran device 语法或 Python vendor 绑定尚未改写；前端/import 尝试失败。 | [语言资格记录](migration/reports/languages.json)；需补 AMD C ABI/ISO_C_BINDING 或真实 GPU Python 绑定。 |
| FAILED / `RUNTIME_ERROR` | 0 | 已编译但执行失败：包括原始 Xgetrf 路径、BSR SDDMM、SELL SpSV，以及 tensor cache/einsum/padding 场景；具体参数/架构/实现原因见逐例日志。 | [原始 profile 尝试](migration/reports/original-rocm-latest.json)；修复失败调用，重新做独立数值检查。 |
| FAILED / `TIMEOUT` | 0 | cuTENSOR trinary contraction 在记录的时限内未结束，未获得合格结果。 | [逐例报告](migration/sample-reports/cuTENSOR/contraction_trinary.cu.md)；定位执行/规模问题后重跑。 |
| PARTIAL / `INDEPENDENT_VALIDATION_PENDING` | 3 | 剩余为 Xgeev 三例与 gesvdaStridedBatched：需排除 CPU 兼容执行，或确认近似算法和 residual norm 语义，并补齐对应独立验收。第三批稀疏与图捕获已通过。 | 逐例 required cases 保留缺项；补 CPU/数学参考和边界检查，返回 0 不能代替验收。 |
| PARTIAL / `SEMANTIC_GAP` | 0 | LZ4 和 JPEG 仅完成上述子集，尚未保留完整原样例的 API、输入和执行流程。 | [能力探针](migration/reports/native-probes.json)、[JPEG 像素对照](migration/reports/rocjpeg-cpu.json)；补完整原始功能。 |
| PARTIAL / `VALIDATED_B9_B11_SUBSET` | 9 | B9两个NVBENCH框架、B10原生GPU progressive及部分调度/流水线、B11完整配置/查询语义仍未等价。 | [逐例B9–B11缺口与日志](migration/reports/batches9-11.md)；缺失功能补齐后重验，不把CPU fallback当完整GPU支持。 |
| PARTIAL / `VALIDATED_B12_B15_SUBSET` | 10 | B12部分子矩阵/低精度collective、B13部分原始descriptor、B14 RNG LEGACY序列和B15原生像素/metadata/文件harness合同仍有缺口。 | [逐例B12–B15缺口与日志](migration/reports/batches12-15.md)；完整数值与兼容CUDA数学通过不代表所有原始合同均已等价。 |
| UNSUPPORTED / `HW_UNSUPPORTED` | 0 | 锁定 ROCm 10.1.0 hipSPARSELt/gfx1201 缺 Tensile kernel bundle；实际运行报错且固定源码的架构 gate 拒绝该目标。 | [实测与源码证据](cuSPARSELt/README.md)；需匹配 kernel bundle、新实现或受支持 GPU，不能以 dense GEMM 替代。 |
| BLOCKED / `ENV_MISSING_DEP` | 0 | nvJPEG Python 测试的 imports 已通过，但 AMD decoder 可执行文件/完整 CLI 测试前置条件尚未实现。 | [逐例报告](migration/sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md)；补 GPU 可执行文件后执行原始测试。 |
**MOAT R4：IEEE/PKZIP CRC32 GPU实现，6数值+1原生空chunk拒绝。** [详细日志与资格](migration/reports/rewrite-R4.md)。

**MOAT R5：8个标准Fortran来源入口完成真实语言绑定、批选择重算及应用残差检查。** [逐例范围、CUDA工具链限制和日志](migration/reports/rewrite-R5.md)。

**MOAT R7：两个默认FP16结构化2:4样例通过，新增1个功能族。** [真实GPU裁剪/压缩/稀疏乘法、原生边界与日志](migration/reports/rewrite-R7.md)。

**MOAT 本轮累计新增21项整例资格、撤销1项旧资格，支持211→231（净增20）。** R6基础探针与候选源码调查不计样例支持；R5尚有65个前端及额外1个C++合同缺口。[R6路线与边界](migration/reports/rewrite-R6.md) · [剩余408项的原因、路线、实验和成本](migration/reports/rewrite-remaining-assessment.md) · [全阶段实时进展](migration/reports/rewrite-progress.md)。

**R8回归与交付：** [当前源码依赖审计、干净检出复现及未完成范围](migration/reports/rewrite-R8.md)。


已验收模块内部也保留具体限制：hipTensor FP32 原生 contraction 的架构 gate 失败由 rocBLAS + HIP 保持精度的路线补足；hipFFT 单 batch 1D Xt 缺口由两卡分解/通信/合并补足。B12–B15已完成登记范围的分布/设备内GPU与图像数值试点；部分原始descriptor、低精度通信、RNG LEGACY、原生NPP像素与文件/metadata合同仍保持PARTIAL，多节点与其它未覆盖入口未完成；JPEG2000/TIFF 未找到并实现完整 AMD GPU codec 路线。上述原因在模块矩阵中逐项展示。


## 构建与复现

先核对物理 GPU 占用及共享预约；**HIP ordinal 2 对应物理 GPU0**，ordinal 3 对应物理 GPU1。项目 `device_guard.py` 按 PCI 地址校验；物理 GPU3 排除计算，预约卡也会拒绝。历史使用错误 ordinal 的结果已标记，不能用于验收。

```bash
HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh
python3 tools/migration/compare.py
python3 tools/migration/render.py
```

M1 的独立 CMake/CTest（在锁定 ROCm 10.1.0 容器中，并先运行 guard）：

```bash
python tools/migration/device_guard.py
cmake -S rocm -B build/rocm -DCMAKE_BUILD_TYPE=Release
cmake --build build/rocm -j2
ctest --test-dir build/rocm --output-on-failure
```

原始 profile 批量构建：`bulk_run.py --families cuBLAS cuSPARSE ...`；先在锁定容器中运行 `bootstrap_sdk.py` 建项目 overlay。hipCOMP/hipTensor 的锁定源码重建使用 `bash tools/migration/build_optional.sh`。`python3 tools/migration/restore_observations.py` 从归档恢复 CUDA 输出观测/fixture 适配副本，原始 CUDA 树保持不变。每例复现链接在库级表中的“详情”；命令、原始日志、source/fixture hash 和环境随证据保存。[最终源码与 fixture 身份](migration/source-tree.json) 包含可恢复的内容寻址源码；大输出保留于 artifacts，输入生成方法/hash 在报告中。

## 状态解释

`NOT_STARTED` 未开始；`IN_PROGRESS` 实施中；`PARTIAL` 部分功能或仅运行通过；`PASSED` 登记的必需正确性用例全部通过；`FAILED` 实际尝试失败；`BLOCKED` 前置条件缺失；`UNSUPPORTED` 有指定版本/硬件的必要能力缺失证据。L0 无实现、L1 有源码、L2 编译通过、L3 AMD 执行通过、L4 必需正确性用例通过。性能单独登记。

## 上游 CUDA Library Samples 说明

以下保留原 CUDA 项目介绍与资源。现有子目录中的 NVIDIA 构建说明适用于 CUDA 原版；ROCm 构建与实验命令会随对应实现补充。

The **CUDA Library Samples** repository contains various examples that demonstrate the use of GPU-accelerated libraries in CUDA. These libraries enable high-performance computing in a wide range of applications, including math operations, image processing, signal processing, linear algebra, and compression. The samples included cover:

- **Math and Image Processing Libraries**
- **cuBLAS** (Basic Linear Algebra Subprograms)
- **cuTENSOR** (Tensor Linear Algebra)
- **cuSPARSE** (Sparse Matrix Operations)
- **cuSOLVER** (Dense and Sparse Solvers)
- **cuFFT** (Fast Fourier Transform)
- **cuRAND** (Random Number Generation)
- **NPP** (Image and Video Processing)
- **nvJPEG** (JPEG Encode/Decode)
- **nvCOMP** (Data Compression)
- **and more...**

## About

The CUDA Library Samples are provided by NVIDIA Corporation as Open Source software, released under the Apache 2.0 License. These examples showcase how to leverage GPU-accelerated libraries for efficient computation across various fields.

For more information on the available libraries and their uses, visit [GPU Accelerated Libraries](https://developer.nvidia.com/gpu-accelerated-libraries).

## Library Examples

Explore the examples of each CUDA library included in this repository:

- [cuBLAS - GPU-accelerated basic linear algebra (BLAS) library](cuBLAS/)
- [cuBLASLt - Lightweight BLAS library](cuBLASLt/)
- [cuBLASMp - Multi-process BLAS library](cuBLASMp/)
- [cuBLASDx - Device-side BLAS extensions](MathDx/cuBLASDx/)
- [cuDSS - GPU-accelerated linear solvers](cuDSS/)
- [cuEST - GPU-accelerated quantum chemistry](cuEST/)
- [cuFFT - Fast Fourier Transforms](cuFFT/)
- [cuFFTMp - Multi-process FFT](cuFFTMp/)
- [cuFFTDx - Device-side FFT extensions](MathDx/cuFFTDx/)
- [cuPQC - Post-Quantum Cryptography device library](cuPQC/)
- [cuRAND - Random number generation](cuRAND/)
- [cuSOLVER - Dense and sparse direct solvers](cuSOLVER/)
- [cuSOLVERMp - Multi-process solvers](cuSOLVERMp/)
- [cuSOLVERSp2cuDSS - Transition example from cuSOLVERSp/Rf to cuDSS](cuSOLVERSp2cuDSS/)
- [cuSPARSE - BLAS for sparse matrices](cuSPARSE/)
- [cuSPARSELt - Lightweight BLAS for sparse matrices](cuSPARSELt/)
- [cuTENSOR - Tensor linear algebra library](cuTENSOR/)
- [cuTENSORMg - Multi-GPU tensor linear algebra](cuTENSORMg/)
- [libmathdx - C API for JIT compilation of MathDx device functions](MathDx/libmathdx/)
- [NPP - GPU-accelerated image, video, and signal processing functions](NPP/)
- [NPP+ - C++ extensions for NPP](NPP+/)
- [nvJPEG - High-performance JPEG encode/decode](nvJPEG/)
- [nvJPEG2000 - JPEG2000 encoding/decoding](nvJPEG2000/)
- [nvTIFF - TIFF encoding/decoding](nvTIFF/)
- [nvCOMP - Data compression and decompression](nvCOMP/)

Each sample provides a practical use case for how to apply these libraries in real-world scenarios, showcasing the power and flexibility of CUDA for a wide variety of computational needs.

## Additional Resources

For more information and documentation on CUDA libraries, please visit:

- [CUDA Toolkit Documentation](https://docs.nvidia.com/cuda/)
- [NVIDIA Developer Zone](https://developer.nvidia.com/)
- [CUDA Samples](https://github.com/NVIDIA/cuda-samples)

## Contributing

We welcome contributions to **CUDA Library Samples**. To contribute to **CUDA Library Samples** and make pull requests,
follow the guidelines outlined in the [Contributing](./CONTRIBUTING.md) document.

## License

The CUDA Library Samples are distributed under the Apache 2.0 License. For more details, refer to the LICENSE.md file.

The old code that was originally distributed under the 3-clause "New" BSD license is available at bsd3_main branch and is no longer maintained.
