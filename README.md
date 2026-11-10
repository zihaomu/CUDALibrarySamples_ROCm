[![License](https://img.shields.io/badge/License-Apache_2.0-yellowgreen.svg)](https://opensource.org/licenses/Apache-2.0)

# CUDA Library Samples on ROCm

对照 NVIDIA CUDA Library Samples，逐例选择 AMD/ROCm 生态中适合的库并实现。每例公开实际使用库、实现程度、正确性结果、CUDA 对照及失败原因。保留 CUDA 原始源码作为参考；AMD 实验固定 ROCm 10.1.0 / Radeon AI PRO R9700（gfx1201），CUDA 对照使用双 RTX 5090 机器。

[B4–B8 实时验收](migration/reports/batches4-8.md) · [后续批次计划与能力边界](migration/roadmap.md) · [支持方式与详细日志总表](migration/reports/support-log-index.md) · [模块支持矩阵](#模块支持矩阵) · [已验收算子](#已验收算子与验证范围) · [未通过的具体原因](#未通过和不支持的具体原因) · [设计与实施日志](migration/design.md) · [执行交付报告](migration/reports/plan-execution.md) · [逐例清单](migration/samples.yaml) · [环境锁](migration/environments/project.lock.json)

## 当前结果

上游固定为 `8b0573b11d183d9b3a36cd2955aa31c16cc61b95`。静态审计覆盖 **866 个源文件、477 个构建定义、639 个独立可执行/脚本源入口**。链接辅助文件、外部 SDK binding、架构/静态链接/通信变体另存元数据，不重复计入入口分母；没有在所有专有 SDK 条件下展开并执行每个构建配置。

PASSED: 174；PARTIAL: 6；FAILED: 456；BLOCKED: 1；UNSUPPORTED: 2；NOT_STARTED: 0；IN_PROGRESS: 0。

`PASSED` 只表示该行明确登记的原始功能和必需用例通过，不能推及整库、其它精度/规模或性能。`PARTIAL` 包括已运行但尚无独立数值验收的端口；`FAILED` 保留真实失败日志和重试条件。不存在“HIPIFY 退出成功即迁移成功”的统计。

专项证据：[M1 双端数值对照](migration/reports/m1-comparison.json)、[BLAS 三方对照](migration/reports/blas-three-way.json)、[稀疏 expected 检查](migration/reports/sparse-original-validation.json)、[新增双端数值/分布对照](migration/reports/additional-comparison.json)、[AMD 生态探针](migration/reports/native-probes.json)、[选型与缺口](migration/reports/ecosystem-decisions.md)、[最终一致性检查](migration/reports/final-validation.json)。**M0–M5 已逐批执行并记录结果；按逐例登记范围的成功率为 27.23%，失败/部分完成仍在分母。**

性能仅选择 6 个 GEMM profile；AMD GPU 有其它任务，空闲资格检查失败，因此 [性能报告](migration/reports/performance-comparison.md) 标为 BLOCKED，仅保留原始计时，不发布合格速度比。

**第二批已收口：17/17 个样例、45 个输入 case。** [详细验收报告](migration/reports/batch2.md) 包含稀疏 3 项、BLAS 8 项、tensor 4 项与 solver 2 项的 CPU/CUDA 对照、原始规模与边界检查。`rotmg` 的原生缩放错误及项目 GPU 修正[单独记录](migration/reports/rotmg-scale-fix.md)；大张量 fixture 支持按 seed 和 SHA256 完整重建。

**第三批已收口：8/8 个样例、26 个输入 case，ROCm/独立 CPU/CUDA 三方通过。** [第三批详细验收与复现](migration/reports/batch3.md) 覆盖 CG、BiCGSTAB、五对角批量求解、4 项 solver 与 SpVV Graph Capture/Replay；包含 meig/未排序配对检查、2000 个实际 GPU 图节点、输入变化重放，以及 24 项反向检查。

## 已验收算子与验证范围

**9 个模块已有整例通过，覆盖 94 个按模块去重的算子/功能族，对应 174 个通过的样例入口。**

计数按数学算子或原例核心功能归并；同模块的精度、尺寸、语言、batch、存储格式和算法变体不重复增加算子数。例如 cuRAND 是 4 种分布、36 个 generator/distribution profile；cuDSS simple 的 3 种语言入口算 1 个功能族。跨模块总数保留不同库接口的实现，GEMM 可分别出现在 cuBLAS 与 cuBLASLt。每个族至少有一个通过独立验收的样例，支持范围限于下表和逐例 required cases。

| 模块 | 已验收算子/功能族数 | 已验收算子/功能 | 通过样例 | 验证范围 |
| --- | ---: | --- | ---: | --- |
| [cuBLAS](cuBLAS/README.md) | 52 | `amax`、`amin`、`asum`、`axpy`、`copy`、`dgmm`、`dot`、`dotc`、`gbmv`、`geam`、`gemm`、`gemv`、`ger`、`hbmv`、`hemm`、`hemv`、`her`、`her2`、`her2k`、`herk`、`herkx`、`hpmv`、`hpr`、`hpr2`、`nrm2`、`rot`、`rotg`、`rotm`、`rotmg`、`sbmv`、`scal`、`spmv`、`spr`、`spr2`、`swap`、`symm`、`symv`、`syr`、`syr2`、`syr2k`、`syrk`、`syrkx`、`tbmv`、`tbsv`、`tpmv`、`tpsv`、`tpttr`、`trmm`、`trmv`、`trsm`、`trsv`、`trttp` | 67 | 固定教学输入与所列扩展 cases；第二批含并列/空索引、旋转 flags、batch/grouped 和正负 alpha；rotmg 极端缩放使用明确登记的 HIP 修正。其它精度/API 仍逐例管理。 |
| [cuBLASLt](cuBLASLt/README.md) | 1 | `GEMM` | 3 | 3 个 profile：FP32 SGEMM、HSH FP16 input/output + FP32 compute 的 pointer-array 与 strided batch。 |
| [cuDSS](cuDSS/README.md) | 1 | `稀疏 SPD 直接求解` | 3 | 原始 FP64 5×5 SPD/CSR：C++、Fortran、CUDA Fortran 改写共 3 入口；CPU 稀疏符号分析 + GPU CSRRF 数值分解/求解。 |
| [cuFFT](cuFFT/README.md) | 3 | `C2C 复数 FFT`、`FFT 窗口过滤 callback`、`R2C/C2R 实数 FFT` | 10 | 10 个 profile：原始单卡/双卡 C2C、实数正逆变换和 legacy/离线 SPIR-V/HIPRTC callback。1D 多卡使用 hipFFT + RCCL + HIP。 |
| [cuPQC](cuPQC/README.md) | 2 | `SHA-256`、`SHA3-256` | 2 | SHA-256 单线程与 SHA3-256 的 32-lane 协作 GPU kernel；各 14 输入与 hashlib 精确一致，PQC 其它算法未实现。 |
| [cuRAND](cuRAND/README.md) | 4 | `lognormal`、`normal`、`poisson`、`uniform` | 36 | 4 种分布 × 9 个 generator = 36 个 profile；原始参数、库内重复性和解析分布矩通过，跨库不要求逐位同序列。 |
| [cuSOLVER](cuSOLVER/README.md) | 8 | `Cholesky 分解`、`LU 分解/求解`、`QR 分解`、`QR 的 Q 应用`、`QR 的 Q 生成`、`SVD`、`对称特征分解`、`广义对称特征分解` | 17 | 原始固定教学矩阵；检查 status/info、特征值/奇异值、重构、求解残差与正交性。第三批覆盖 batched SVD/未排序特征对、索引/值域/全量/空区间与实际 meig。 |
| [cuSPARSE](cuSPARSE/README.md) | 18 | `SpVV Graph Capture/Replay`、`axpby`、`bicgstab`、`cg`、`coosort`、`dense2sparse`、`gather`、`gpsvinterleavedbatch`、`rot`、`scatter`、`sddmm`、`sparse2dense`、`spgemm`、`spmm`、`spmv`、`spsm`、`spsv`、`spvv` | 31 | CSR/COO/SELL/blocked-ELL 等已登记格式与 batched 变体；SpVV/SpGEMM/reuse 数值变化与 CSR 结构；第三批 CG/BiCGSTAB 的独立求解、残差/收敛，gpsv 的逐 batch interleaved 布局，以及真实 GPU 图捕获/输入变化 replay。 |
| [cuTENSOR](cuTENSOR/README.md) | 5 | `三元逐元素运算`、`二元逐元素运算`、`张量 contraction`、`张量 permutation`、`张量 reduction` | 5 | FP32：contraction 用 rocBLAS + HIP；其它已通过的逐元素/permutation/reduction 使用 hipTensor。逐例记录原始 extents 与扩展小尺寸、全部输出 CPU 检查；contraction 的原始规模另为抽样验收。 |

以下仅有子集/能力探针，**不计入上述整例支持数**：

| 模块 | 已验证子集 | 原始样例尚缺什么 |
| --- | --- | --- |
| nvCOMP | hipCOMP LZ4 单 chunk，128/32768/65536 字节 GPU byte-exact 往返 | 现代 status/options、完整 batch/manager 与其它 codec；1 PARTIAL、0 PASSED |
| nvJPEG | rocJPEG hardware backend：64×64 baseline JPEG → RGB，CPU libjpeg 最大像素差 2 | 全部原始输入/格式、CLI、batch、多实例、ROI、编码；1 PARTIAL、0 PASSED |
| NPP | RPP HIP U8 c1/c3、32×24 identity resize 探针 | 原始 Canny、distance transform、label/watershed 等算子未实现；0 PASSED |

逐个算子族与样例的可追溯映射见 [operator-support.json](migration/reports/operator-support.json)；失败仍按具体入口和原因保留。

## 模块支持矩阵

下表覆盖全部 30 个库级模块。“已验收算子族”按上文口径去重；“通过/总入口”是原始 sample 数，二者分别统计。部分完成、失败、明确不支持、前置条件阻塞分别列出；每个模块链接包含全部原始样例的实际库、代码、逐例原因和证据。候选库不计为实际使用库。

| 模块 | 实际/候选 AMD 路线 | 已验收算子族 | 通过/总入口 | 部分 | 失败 | 不支持 | 阻塞 | 当前范围及未通过原因 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| [cuBLAS](cuBLAS/README.md) | HIP GPU packed conversion → HIP runtime; hipBLAS + HIP scale fix → rocBLAS; hipBLAS → rocBLAS | 52 | 67/82 | 0 | 15 | 0 | 0 | 常规运算与第二批索引/旋转/batch 已验收；rotmg 原生重复缩放错误由项目 HIP GPU 修正。Emulation、3m、部分 Ex/packed 转换仍有接口/算法改写缺口。 |
| [cuBLASLt](cuBLASLt/README.md) | hipBLASLt; hipBLASLt → hipBLASLt native | 1 | 3/20 | 0 | 17 | 0 | 0 | FP32 与两种 HSH FP16 batch 路径验证通过；高级 scale/quantization、grouped/autotune 接口及 FP8 格式不能按名字强行等同。 |
| [cuBLASMp](cuBLASMp/README.md) | 候选：rocBLAS, RCCL, MPI | 0 | 0/14 | 0 | 14 | 0 | 0 | 已验证双卡 hipBLAS/RCCL 基础计算，但原始 MPI 进程网格、block-cyclic 数据分布、各精度和高级 profile 尚未实现。 |
| [cuDSS](cuDSS/README.md) | rocSOLVER + rocBLAS via ISO_C_BINDING/C ABI → GPU CSRRF sparse Cholesky; CPU sparse symbolic graph; rocSOLVER CSRRF + rocBLAS → GPU sparse Cholesky; CPU sparse symbolic analysis | 1 | 3/59 | 0 | 56 | 0 | 0 | simple 的 C++/Fortran 用 CPU 稀疏符号图 + rocSOLVER CSRRF GPU 数值分解/求解；高级 descriptor、Schur、分布式、allocator 等 API 尚未完整改写。 |
| [cuEST](cuEST/README.md) | 候选：unresolved | 0 | 0/51 | 0 | 51 | 0 | 0 | 原始 GPU 电子结构 context、积分/梯度、DF/XC/PCM 等 vendor SDK 尚无本项目 AMD 绑定/算法实现；hipBLAS 本身不提供这些高层算子。 |
| [cuFFT](cuFFT/README.md) | hipFFT + RCCL + HIP → Two GPU radix decomposition and GPU merge; hipFFT → rocFFT; hipFFT/rocFFT JIT callbacks + HIP compiler SPIR-V → rocFFT SPIR-V JIT integration; hipFFT/rocFFT JIT callbacks + HIPRTC → rocFFT SPIR-V JIT integration | 3 | 10/10 | 0 | 0 | 0 | 0 | 原始单卡、双卡、legacy/JIT callback 分别实现；1D Xt 不支持的单 batch 路径改用 hipFFT + RCCL + GPU 合并，JIT 使用 SPIR-V。 |
| [cuFFTMp](cuFFTMp/README.md) | 候选：hipFFT, rocFFT, GPU-aware MPI | 0 | 0/20 | 0 | 20 | 0 | 0 | MPI/Fortran/NVSHMEM 与原始 slab/pencil/reshape 分布接口仍有绑定和实现缺口；双卡 Xt 的成功范围单独报告。 |
| [cuPQC](cuPQC/README.md) | HIP runtime + custom device SHA implementation → HIP/gfx1201 | 2 | 2/6 | 0 | 4 | 0 | 0 | SHA2/SHA3 使用自有 HIP 设备实现且独立摘要完全一致；ML-KEM/ML-DSA/Merkle/Poseidon2 仍需设备算法与 API 改写。 |
| [cuRAND](cuRAND/README.md) | hipRAND → rocRAND | 4 | 36/36 | 0 | 0 | 0 | 0 | 36 个 generator/distribution 的原始参数、重复性与解析分布矩均验证；MT19937 初始化需较长时限，跨库序列不要求相同。 |
| [cuSOLVER](cuSOLVER/README.md) | hipSOLVER + hipBLAS → rocSOLVER/rocBLAS; hipSOLVER → rocSOLVER; hipSOLVER → rocSOLVER/rocBLAS | 8 | 17/39 | 4 | 18 | 0 | 0 | 基础分解、Xgeqrf/Xpotrf、gesvdjBatched、syevjBatched、syevdx/sygvdx 已验收；后四项检查逐batch重构/配对、meig与选区。Xgeev三例仍需排除CPU兼容路径，gesvdaStridedBatched仍需确认近似算法与残差语义，保留PARTIAL；Mg、IRS等其它入口缺AMD改写或oracle。 |
| [cuSOLVERMp](cuSOLVERMp/README.md) | 候选：rocSOLVER, rocBLAS, MPI, RCCL | 0 | 0/16 | 0 | 16 | 0 | 0 | 分布式 LU/Cholesky/特征值等需要 MPI/通信及算法层改写；不能以单卡 hipSOLVER 作为成功。 |
| [cuSOLVERSp2cuDSS](cuSOLVERSp2cuDSS/README.md) | 候选：hipSOLVER, rocSOLVER (subset) | 0 | 0/7 | 0 | 7 | 0 | 0 | 原例对比两个 NVIDIA 稀疏直接求解 API；没有完成保持两条路线及对应配置语义的 AMD 改写。 |
| [cuSPARSE](cuSPARSE/README.md) | hipSPARSE + HIP Graph → rocSPARSE + HIP runtime; hipSPARSE + HIP format adapter → rocSPARSE + HIP runtime; hipSPARSE + hipBLAS → rocSPARSE/rocBLAS; hipSPARSE → rocSPARSE | 18 | 31/37 | 0 | 6 | 0 | 0 | CSR/COO/blocked ELL、SpVV/SpGEMM/reuse、CG/BiCGSTAB、gpsvInterleavedBatch 与真实 SpVV Graph Capture/Replay 已通过独立 CPU 和 CUDA 验收。BSR SDDMM、部分新转换/custom operator 与其它原始入口仍失败，不能推及整个库。 |
| [cuSPARSELt](cuSPARSELt/README.md) | hipSPARSELt+hipSPARSE | 0 | 0/2 | 0 | 0 | 2 | 0 | hipSPARSELt 已编译并真实运行，gfx1201 kernel 数据缺失；锁定源码的支持架构列表也不接受 gfx1201，不能用 dense GEMM 代替结构化稀疏。 |
| [cuTENSOR](cuTENSOR/README.md) | hipTensor; rocBLAS + HIP → FP32 GEMM and GPU tensor permutations | 5 | 5/13 | 0 | 8 | 0 | 0 | hipTensor 的 binary/trinary、permutation、reduction 原始 extents 与小尺寸全部输出通过 CPU/CUDA；FP32 contraction 架构 gate 缺口由 rocBLAS + HIP 排列补足；其它高级/绑定场景仍失败。 |
| [cuTENSORMg](cuTENSORMg/README.md) | 候选：hipTensor, RCCL, MPI | 0 | 0/2 | 0 | 2 | 0 | 0 | 单进程跨卡 tensor 分区/布局/通信 API 尚未实现；单卡 hipTensor 不等同 Mg。 |
| [cuTENSORMp](cuTENSORMp/README.md) | 候选：hipTensor, MPI, RCCL | 0 | 0/3 | 0 | 3 | 0 | 0 | 原始 MPI tensor 描述与分布式算法尚未改写；RCCL 基础可行性不等同原始 Mp profile。 |
| [MathDx/cuBLASDx](MathDx/cuBLASDx/README.md) | 候选：rocWMMA, Composable Kernel | 0 | 0/34 | 0 | 34 | 0 | 0 | 需要设备内可调用的 GEMM/TRSM、shared/register/pipeline/fusion 重写；rocWMMA/CK 是候选，host hipBLAS 不算 Dx 等价实现。 |
| [MathDx/cuFFTDx](MathDx/cuFFTDx/README.md) | 候选：unresolved device FFT | 0 | 0/49 | 0 | 49 | 0 | 0 | 需要设备内 FFT 与融合算法；host hipFFT/rocFFT 的成功不能替代这些 device-callable profile。 |
| [MathDx/cuRANDDx](MathDx/cuRANDDx/README.md) | 候选：rocRAND device API | 0 | 0/7 | 0 | 7 | 0 | 0 | rocRAND device API 是候选；原始 DSL、PCG/Philox rounds、subsequence/ordering 与设备端组合行为尚未逐例实现。 |
| [MathDx/cuSolverDx](MathDx/cuSolverDx/README.md) | 候选：unresolved device solver | 0 | 0/42 | 0 | 42 | 0 | 0 | 原始线程/块级设备求解与融合需要自有 HIP/设备算法；host rocSOLVER 不作为成功替代。 |
| [MathDx/libmathdx](MathDx/libmathdx/README.md) | 候选：HIPRTC + device algorithms | 0 | 0/12 | 0 | 12 | 0 | 0 | HIPRTC 已在 FFT JIT 路线验证，但不自带原始 libmathdx 的各设备算法生成器/描述 DSL，尚未等价改写。 |
| [MathDx/nvCOMPDx](MathDx/nvCOMPDx/README.md) | 候选：hipCOMP algorithm reuse (device API unresolved) | 0 | 0/7 | 0 | 7 | 0 | 0 | hipCOMP 的 host API 不等于 device-callable nvCOMPDx；原始设备融合/CPU互通/ANS 等需要专门重写。 |
| [NPP](NPP/README.md) | 候选：RPP HIP, rocPRIM | 0 | 0/9 | 0 | 9 | 0 | 0 | RPP HIP 小型 resize 能力已探测；原始 Canny、distance transform、label/watershed 等特殊算子未完成等价实现，不能由 resize 推广。 |
| [NPP+](NPP+/README.md) | 候选：RPP HIP, rocPRIM | 0 | 0/6 | 0 | 6 | 0 | 0 | 原始高级轮廓/距离/分割及 Python 绑定尚未改写；RPP/rocPRIM 只是候选组件。 |
| [nvJPEG](nvJPEG/README.md) | rocJPEG | 0 | 0/7 | 1 | 5 | 0 | 1 | rocJPEG 硬件 baseline RGB decode 与 CPU libjpeg 对照通过；原例全部输入/多实例/ROI/编码与 resize-watermark 流程尚未覆盖。 |
| [nvJPEG2000](nvJPEG2000/README.md) | 候选：unresolved | 0 | 0/4 | 0 | 4 | 0 | 0 | rocJPEG 的 JPEG decode 不能替代 JPEG2000；原始 GPU codec/多阶段/metadata 接口没有 AMD 实现，CPU OpenJPEG 不计成功。 |
| [nvTIFF](nvTIFF/README.md) | 候选：unresolved | 0 | 0/6 | 0 | 6 | 0 | 0 | 原始 TIFF GPU codec 与多页/GeoTIFF/options 等接口未改写；CPU TIFF 容器处理不能冒充 GPU codec。 |
| [nvCOMP](nvCOMP/README.md) | hipCOMP | 0 | 0/32 | 1 | 31 | 0 | 0 | hipCOMP 已源码构建、LZ4 GPU 往返验证；现代 nvCOMP 状态/选项/manager/API 代际差异及各 codec 仍未覆盖全部原始 profile。 |
| [nvMatmulHeuristics](nvMatmulHeuristics/README.md) | 候选：hipBLASLt heuristics (subset) | 0 | 0/7 | 0 | 7 | 0 | 0 | hipBLASLt heuristic 已在 M1 验证；原始配置格式/模型与搜索接口未完整迁移，Origami 仅为待验收候选。 |

## 未通过和不支持的具体原因

“本项目尚未实现/验收”与“锁定版本和硬件确实不支持”分别记录。当前只有 hipSPARSELt 的 2 个样例满足后者的证据条件；其它失败需按 API、构建、数值或执行错误继续定位，不能泛化为 ROCm 不支持。

| 当前结论 | 入口数 | 具体原因 | 证据与恢复条件 |
| --- | ---: | --- | --- |
| FAILED / `BUILD_ERROR` | 378 | 自动移植稿未完成 API/枚举/类型/链接适配。例如 Lt grouped/scale/layout、FP4 观察代码、MathDx device DSL 和特殊 SDK 仍有编译缺口；不据此宣称硬件不支持。 | 各模块 README 列出首个有效编译错误；需完成保持原语义的 AMD 改写再验收。 |
| FAILED / `BINDING_OR_FRONTEND_MIGRATION_REQUIRED` | 73 | Fortran/Python 的 NVIDIA module、CUDA Fortran device 语法或 Python vendor 绑定尚未改写；前端/import 尝试失败。 | [语言资格记录](migration/reports/languages.json)；需补 AMD C ABI/ISO_C_BINDING 或真实 GPU Python 绑定。 |
| FAILED / `RUNTIME_ERROR` | 4 | 已编译但执行失败：包括原始 Xgetrf 路径、BSR SDDMM、SELL SpSV，以及 tensor cache/einsum/padding 场景；具体参数/架构/实现原因见逐例日志。 | [原始 profile 尝试](migration/reports/original-rocm-latest.json)；修复失败调用，重新做独立数值检查。 |
| FAILED / `TIMEOUT` | 1 | cuTENSOR trinary contraction 在记录的时限内未结束，未获得合格结果。 | [逐例报告](migration/sample-reports/cuTENSOR/contraction_trinary.cu.md)；定位执行/规模问题后重跑。 |
| PARTIAL / `INDEPENDENT_VALIDATION_PENDING` | 4 | 剩余为 Xgeev 三例与 gesvdaStridedBatched：需排除 CPU 兼容执行，或确认近似算法和 residual norm 语义，并补齐对应独立验收。第三批稀疏与图捕获已通过。 | 逐例 required cases 保留缺项；补 CPU/数学参考和边界检查，返回 0 不能代替验收。 |
| PARTIAL / `SEMANTIC_GAP` | 2 | LZ4 和 JPEG 仅完成上述子集，尚未保留完整原样例的 API、输入和执行流程。 | [能力探针](migration/reports/native-probes.json)、[JPEG 像素对照](migration/reports/rocjpeg-cpu.json)；补完整原始功能。 |
| UNSUPPORTED / `HW_UNSUPPORTED` | 2 | 锁定 ROCm 10.1.0 hipSPARSELt/gfx1201 缺 Tensile kernel bundle；实际运行报错且固定源码的架构 gate 拒绝该目标。 | [实测与源码证据](cuSPARSELt/README.md)；需匹配 kernel bundle、新实现或受支持 GPU，不能以 dense GEMM 替代。 |
| BLOCKED / `ENV_MISSING_DEP` | 1 | nvJPEG Python 测试的 imports 已通过，但 AMD decoder 可执行文件/完整 CLI 测试前置条件尚未实现。 | [逐例报告](migration/sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md)；补 GPU 可执行文件后执行原始测试。 |

已验收模块内部也保留具体限制：hipTensor FP32 原生 contraction 的架构 gate 失败由 rocBLAS + HIP 保持精度的路线补足；hipFFT 单 batch 1D Xt 缺口由两卡分解/通信/合并补足。cuFFTMp/cuBLASMp/cuSOLVERMp/cuTENSORMg/Mp 的原始分布式算法，以及 MathDx 的设备内融合仍未完成；JPEG2000/TIFF 未找到并实现完整 AMD GPU codec 路线。上述原因在模块矩阵中逐项展示。


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
