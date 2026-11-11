# 算子支持方式与完整验证记录

[返回项目首页](../../README.md) · [构建与复现](../usage.md) · [机器可读记录](support-log-index.json)

覆盖 **639 个样例入口**：249 PASSED、22 PARTIAL、368 FAILED、0 UNSUPPORTED、0 BLOCKED。全部 30 个模块逐项列出实现方式、范围/原因、AMD 日志、CUDA 日志与验收报告。数据直接来自 [逐例清单](../samples.yaml)，[JSON 索引](support-log-index.json) 另含全部历史证据路径、源码 SHA256、已通过/必需用例及恢复条件。

**查阅方式：** 先看状态和“支持范围/失败原因”，再看实际库与实现源码。AMD 栏优先链接与当前源码 hash 匹配的选定验收日志；未通过项链接实际尝试。`build.log` 是编译/链接记录，`run.log` 是程序输出，`<case>/run.log` 是对应输入的输出。命令与环境位于同目录的 `commands.json` 和 `*.environment.json`，从“证据目录”进入。缺少运行日志时会明确标注，不将编译/import 成功视作 GPU 通过。

CUDA 栏注明“当前验收记录”“专项对照记录”或“原始/历史尝试”；只有该行 `CUDA comparison = PASSED` 才表示已完成登记范围的对照。CPU 验收报告保存误差、阈值、残差等结构化检查，不要求每个样例另有一个 CPU 文本 log。所有历史失败与重试记录保留在“详情”。大二进制输出按 hash/生成方法保存，未全部提交 Git。

实现方式是逐例登记值：库 API 迁移、生态库 + 项目 HIP、算法流程重写、执行语义适配或未实现语言绑定；**实际库名称和逐例范围决定具体支持边界**。例如 cuDSS 的 CPU 符号分析 + GPU CSRRF、rotmg 的项目 HIP 修正，不因同样标为 PASSED 而隐去区别。

原始 CUDA baseline 与 CUDA 数学对照分列：原语言工具链缺失时，即使兼容 C++ API 对照通过，原语言 baseline 仍保留 BLOCKED。每个入口的实际误差、残差、阈值和逐项检查结果在 CPU/复合验收 JSON 中；日志包含对应命令、环境和源码/输入 hash。GPU 计时不等于性能资格，[性能验证](performance-comparison.md)单独登记。

图像库后续重写的逐步实验见 [图像库执行记录](image-libraries-progress.md)；候选阶段检查与原生能力调查不增加本表的整例通过数。

## 已验收算子与验证范围

**19 个模块已有整例通过，覆盖 126 个按模块去重的算子/功能族，对应 249 个通过的样例入口。**

计数按数学算子或原例核心功能归并；同模块的精度、尺寸、语言、batch、存储格式和算法变体不重复增加算子数。例如 cuRAND 是 4 种分布、36 个 generator/distribution profile；cuDSS simple 的 3 种语言入口算 1 个功能族。跨模块总数保留不同库接口的实现，GEMM 可分别出现在 cuBLAS 与 cuBLASLt。每个族至少有一个通过独立验收的样例，支持范围限于下表和逐例 required cases。

| 模块 | 已验收算子/功能族数 | 已验收算子/功能 | 通过样例 | 验证范围 |
| --- | ---: | --- | ---: | --- |
| [cuBLAS](../../cuBLAS/README.md) | 52 | `amax`、`amin`、`asum`、`axpy`、`copy`、`dgmm`、`dot`、`dotc`、`gbmv`、`geam`、`gemm`、`gemv`、`ger`、`hbmv`、`hemm`、`hemv`、`her`、`her2`、`her2k`、`herk`、`herkx`、`hpmv`、`hpr`、`hpr2`、`nrm2`、`rot`、`rotg`、`rotm`、`rotmg`、`sbmv`、`scal`、`spmv`、`spr`、`spr2`、`swap`、`symm`、`symv`、`syr`、`syr2`、`syr2k`、`syrk`、`syrkx`、`tbmv`、`tbsv`、`tpmv`、`tpsv`、`tpttr`、`trmm`、`trmv`、`trsm`、`trsv`、`trttp` | 72 | 固定教学profile与所列扩展cases；含复杂rank-k类型化适配、HIP GPU packed转换、FP32分组batched及FP64项目策略调优。rotmg极端缩放使用HIP修正；调优/批量变体按同一数学族去重。 |
| [cuBLASLt](../../cuBLASLt/README.md) | 1 | `GEMM` | 8 | 既有6个profile为FP32 SGEMM、HSH pointer-array/strided、grouped分发及custom-find/autotune。MOAT新资格分别登记FP16 planar负偏移转换/FP32 3M/FP16输出，以及真实COL32/COL4 packing + native INT8/INT32 GemmEx；按样例链接与资格状态限定范围。 |
| [cuBLASMp](../../cuBLASMp/README.md) | 2 | `block-cyclic 重分布`、`分布式 GEADD` | 2 | 已登记FP64 GEADD与1024阶block-cyclic重分布/往返；双MPI进程和不同GPU实际通信。GEMM子矩阵与低精度collective/quantized scale模式等缺口保持PARTIAL，未覆盖多节点。 |
| [cuDSS](../../cuDSS/README.md) | 4 | `CSR 矩阵描述符管理`、`稀疏直接求解`、`稀疏重排序与求解`、`稠密矩阵描述符管理` | 23 | FP64 CSR：simple、异构/均匀batch、重排后完整求解及GENERAL多RHS残差；CPU符号/matching + rocSOLVER CSRRF或项目HIP CSR pivot LU。R9新增9个矩阵helper入口（按稠密/CSR两种描述符功能去重，batch与语言不另计）：项目host描述符＋真实HIP数据/指针表，非GPU求解算法；MOAT另有8个真实ISO_C_BINDING Fortran求解入口，uniform保留GPU factor并选择性重算，residual应用实际检查；原CUDA Fortran工具链仍缺。CPP重排严格METIS向量不同及get_set缺项保持PARTIAL，不把历史analysis-only计为完整求解。规模/动态pivot按逐例范围。 |
| [cuFFT](../../cuFFT/README.md) | 3 | `C2C 复数 FFT`、`FFT 窗口过滤 callback`、`R2C/C2R 实数 FFT` | 10 | 10 个 profile：原始单卡/双卡 C2C、实数正逆变换和 legacy/离线 SPIR-V/HIPRTC callback。1D 多卡使用 hipFFT + RCCL + HIP。 |
| [cuFFTMp](../../cuFFTMp/README.md) | 1 | `多进程 slab C2C FFT` | 1 | 双MPI rank，原始16³及不均匀17×13×9；hipFFT本地YZ/X FFT + RCCL Send/Recv + HIP pack/unpack/归一化，完整频域与逆变换输出。 |
| [cuPQC](../../cuPQC/README.md) | 2 | `SHA-256`、`SHA3-256` | 2 | SHA-256 单线程与 SHA3-256 的 32-lane 协作 GPU kernel；各 14 输入与 hashlib 精确一致，PQC 其它算法未实现。 |
| [cuRAND](../../cuRAND/README.md) | 4 | `lognormal`、`normal`、`poisson`、`uniform` | 36 | 4 种分布 × 9 个 generator = 36 个 profile；原始参数、库内重复性和解析分布矩通过，跨库不要求逐位同序列。 |
| [cuSOLVER](../../cuSOLVER/README.md) | 10 | `Cholesky 分解`、`LU 分解/求解`、`QR 分解`、`QR 的 Q 应用`、`QR 的 Q 生成`、`SVD`、`三角矩阵求逆`、`多 GPU LU 分解/求解`、`对称特征分解`、`广义对称特征分解` | 23 | B13补611阶双GPU LU/pivot/solve，tile256列分布+RCCL+HIP，全部CPU重构/残差；MgPotrf及Mp原始descriptor缺口另列。原始FP64教学矩阵；status/info、全量分解/重构、残差、正交性、未排序配对及实际meig检查。B6增加64位LU/三角求逆；SVD/eigen typed接口显式INT_MAX限制。 |
| [cuSPARSE](../../cuSPARSE/README.md) | 20 | `SpVV Graph Capture/Replay`、`axpby`、`bicgstab`、`cg`、`coosort`、`dense2sparse`、`gather`、`gpsvinterleavedbatch`、`rot`、`scatter`、`sddmm`、`sparse2dense`、`spgemm`、`spmat`、`spmm`、`spmv`、`spmvop`、`spsm`、`spsv`、`spvv` | 36 | 已登记CSR/COO/SELL/BSR等格式、CG/BiCG残差/收敛、gpsv布局和真实Graph replay。B8补CSR→CSC、对称展开、HIP GPU预算分块SpGEMM和融合custom op；3项CUDA新API缺失，使用明确标注的兼容数学基线。 |
| [cuSPARSELt](../../cuSPARSELt/README.md) | 1 | `2:4 结构化稀疏 GEMM（含裁剪/压缩）` | 2 | 默认FP16 A/B/C/bias、FP32累积；项目HIP 4×4 TILE最大L1裁剪、实际packed values/metadata及只读压缩数据的稀疏乘法，basic GPU搜索，advanced双batch/stride/bias/ReLU。14输入CPU/原生稀疏数学对照及两个原CUDA程序另验；原生hipSPARSELt/gfx1201失败另存，不声明原生加速/opaque格式兼容。 |
| [cuTENSOR](../../cuTENSOR/README.md) | 7 | `三元逐元素运算`、`二元逐元素运算`、`张量 contraction`、`张量 einsum`、`张量 permutation`、`张量 plan cache`、`张量 reduction` | 9 | FP32：hipTensor逐元素/排列/规约；rocBLAS+HIP contraction；B5补HIP padding、einsum路由、三输入收缩和真实GPU分块搜索/持久化缓存。B2/B5全部原始规模输出均有全量FP64 CPU检查；早期M3 contraction仅抽样的历史证据另保留。 |
| [cuTENSORMg](../../cuTENSORMg/README.md) | 1 | `多 GPU 张量 contraction` | 1 | 单进程双GPU；原始4096 extents/2048 block及i,k / k,j / i,j，hipBLAS + RCCL，全部FP64 CPU参考；其它分区/精度/多节点不外推。 |
| [MathDx/cuBLASDx](../../MathDx/cuBLASDx/README.md) | 1 | `设备内 GEMM` | 1 | HIP调用方kernel内协作GEMM三阶段、128点双FFT、32阶complex上三角Cholesky/shared LDA33；原生SDK25.6版本差异与兼容CUDA数学对照分开。RNG LEGACY逐位合同仍PARTIAL。 |
| [MathDx/cuFFTDx](../../MathDx/cuFFTDx/README.md) | 1 | `设备内 C2C FFT` | 1 | HIP调用方kernel内协作128点双C2C FFT、ElementsPerThread=8/共32线程及扩展线程块；全部CPU频谱输出与兼容CUDA数学基线。 |
| [MathDx/cuSolverDx](../../MathDx/cuSolverDx/README.md) | 4 | `设备内 Cholesky 分解/求解`、`设备内 complex Cholesky`、`设备内 partial-pivot LU`、`设备内三角求解` | 4 | HIP调用方kernel内complex Cholesky；MOAT新增complex FP32 48×32 pivot LU、complex FP64 32阶双batch POSV、FP64 right/lower 32×33 TRSM。原生MathDx26.06.1原例实际device输出、同字节HIP与独立CPU分别记录；只按已通过样例的登记范围统计。 |
| [NPP](../../NPP/README.md) | 5 | `Euclidean 距离变换/Voronoi`、`三通道 Canny`、`等值八连接 CCL 与标签压缩`、`轮廓/闭环有序几何与重建`、`零均值 NCC` | 6 | 精确Euclidean距离/Voronoi/整数截断与完整NCC已通过；C3 Canny使用项目HIP经典8连接强种子滞后变体，C++/Python三PNG与10次原流程、22组CPU精确mask及native完整差异、stream/并发/错误/trace/冷重放和复审通过。原图比NPP少4328个弱边缘像素（IoU0.6323），不声明native mask逐点兼容；其它入口单列。 等值八连接CCL与GPU标签压缩覆盖所有值（含0）、两个真实C++入口、单图/异构batch及NPP+默认/条件编译模式；原生NPP/NPP+分区失败独立记录，项目按CPU正确分区验收。 轮廓采用项目HIP有向像素单元边、GPU闭环排序及geometry驱动重建；保持原例三/四RAW、范围/bypass与有序诊断，22全量输入和15实际流程55文件验收。此表示非NPP专有packed ABI，原生分区差异与历史ABI1失败另存。 |
| [NPP+](../../NPP+/README.md) | 4 | `Unsigned EDT 与子像素 signed 距离/Voronoi`、`单通道 Canny`、`等值八连接 CCL 与标签压缩`、`轮廓/闭环有序几何与重建` | 4 | 项目HIP C1 Sobel3/整数L2/NMS/局部阈值，ROCm Torch/C ABI；原例8分辨率、5次预热/1000测量和PNG/CSV，31组CPU精确mask及native API比较，stream/并发/非法span/trace与独立审查。native内部精确一致，3外圈差异按项目边界定义接受；无跨设备性能结论。其它入口单列。 等值八连接CCL与GPU标签压缩覆盖所有值（含0）、两个真实C++入口、单图/异构batch及NPP+默认/条件编译模式；原生NPP/NPP+分区失败独立记录，项目按CPU正确分区验收。 轮廓采用项目HIP有向像素单元边、GPU闭环排序及geometry驱动重建；保持原例三/四RAW、范围/bypass与有序诊断，22全量输入和15实际流程55文件验收。此表示非NPP专有packed ABI，原生分区差异与历史ABI1失败另存。 距离变换为项目HIP exact unsigned EDT与预固定的线性阈值交点signed点集距离；完整五图12RAW、30输入及确定性site/Voronoi、4流程48文件、运行/冷检出验收。signed与NPP+闭源算法差异明确单列，非vendor逐位一致；项目CPU/GPU30输入maxAbs=0。 |
| [nvCOMP](../../nvCOMP/README.md) | 3 | `CRC32`、`LZ4`、`Snappy` | 8 | hipCOMP LZ4/Snappy原生批处理；CPU↔GPU与hipCOMP↔nvCOMP双向互解、逐chunk status/实际长度、空/边界/损坏流；LZ4 native manager/factory +项目CRC32C及100 raw buffers。独立CRC32入口采用项目HIP IEEE/PKZIP算法，与zlib及真实nvCOMP逐chunk比较，空输入按原生语义拒绝；具体资格见逐例状态。R9 CRC32 benchmark保留CLI/默认16GiB/CSV/完整GPU搜索和最终重算；四个小输入同字节三方，默认各后端RNG独立CPU验收，性能及完整32GiB complete扫描未验收。完整NVBENCH框架仍单列PARTIAL。 |

以下仅有子集/能力探针，**不计入上述整例支持数**：

| 模块 | 已验证子集 | 原始样例尚缺什么 |
| --- | --- | --- |
| nvJPEG | rocJPEG baseline 解码；CLI/布局/缩放/ROI/多实例/后处理逐例验收 | progressive缺少原生GPU后端；显式CPU fallback/encode另标注；6 PARTIAL、0 PASSED |

逐个算子族与样例的可追溯映射见 [operator-support.json](../../migration/reports/operator-support.json)；失败仍按具体入口和原因保留。

## 未整例通过的原因

尚未整例通过不表示算法永远不能在 AMD 上实现。以下按当前逐例结论汇总；具体失败调用、已覆盖子集与重试条件见后面的模块记录。

| 当前结论 | 原因编码 | 入口数 | 说明 |
| --- | --- | ---: | --- |
| FAILED | `BINDING_OR_FRONTEND_MIGRATION_REQUIRED` | 57 | 原始语言前端或 vendor 绑定尚未完成迁移。 |
| FAILED | `BUILD_ERROR` | 311 | 当前移植稿的 API、类型、链接或算法实现未完成，实际构建失败。 |
| PARTIAL | `INDEPENDENT_VALIDATION_PENDING` | 3 | 尚未完成对应独立数值及实际执行路径验收。 |
| PARTIAL | `VALIDATED_B12_B15_SUBSET` | 9 | 已有验收子集，原始 descriptor、低精度通信、序列或像素语义仍有缺口。 |
| PARTIAL | `VALIDATED_B9_B11_SUBSET` | 9 | 已有验收子集，原例框架、调度或配置/查询语义仍有缺口。 |
| PARTIAL | `VENDOR_PERMUTATION_POLICY_DIFFERS` | 1 | 置换/排序策略未满足原始 vendor 合同。 |

## 逐入口实现、结果与日志

模块导航：[cuBLAS](#module-0) · [cuBLASLt](#module-1) · [cuBLASMp](#module-2) · [cuDSS](#module-3) · [cuEST](#module-4) · [cuFFT](#module-5) · [cuFFTMp](#module-6) · [cuPQC](#module-7) · [cuRAND](#module-8) · [cuSOLVER](#module-9) · [cuSOLVERMp](#module-10) · [cuSOLVERSp2cuDSS](#module-11) · [cuSPARSE](#module-12) · [cuSPARSELt](#module-13) · [cuTENSOR](#module-14) · [cuTENSORMg](#module-15) · [cuTENSORMp](#module-16) · [MathDx/cuBLASDx](#module-17) · [MathDx/cuFFTDx](#module-18) · [MathDx/cuRANDDx](#module-19) · [MathDx/cuSolverDx](#module-20) · [MathDx/libmathdx](#module-21) · [MathDx/nvCOMPDx](#module-22) · [NPP](#module-23) · [NPP+](#module-24) · [nvJPEG](#module-25) · [nvJPEG2000](#module-26) · [nvTIFF](#module-27) · [nvCOMP](#module-28) · [nvMatmulHeuristics](#module-29)

<a id="module-0"></a>

## cuBLAS

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [Extensions/AxpyEx/cublas_AxpyEx_example.cu](../sample-reports/cuBLAS/Extensions/AxpyEx/cublas_AxpyEx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-8b0831d666f2) |
| [Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu](../sample-reports/cuBLAS/Extensions/Cherk3mEx/cublas_Cherk3mEx_example.cu.md) | PASSED / 7/7 | hipBLAS/rocBLAS three real SGEMMs + HIP Hermitian triangle epilogue / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-efcb80a73116) |
| [Extensions/CherkEx/cublas_CherkEx_example.cu](../sample-reports/cuBLAS/Extensions/CherkEx/cublas_CherkEx_example.cu.md) | PASSED / 4/4 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-edb12d5041ad) |
| [Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu](../sample-reports/cuBLAS/Extensions/Csyrk3mEx/cublas_Csyrk3mEx_example.cu.md) | PASSED / 7/7 | hipBLAS/rocBLAS three real SGEMMs + HIP symmetric triangle epilogue / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-46058545057d) |
| [Extensions/CsyrkEx/cublas_CsyrkEx_example.cu](../sample-reports/cuBLAS/Extensions/CsyrkEx/cublas_CsyrkEx_example.cu.md) | PASSED / 4/4 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-87696bb54546) |
| [Extensions/DotEx/cublas_DotEx_example.cu](../sample-reports/cuBLAS/Extensions/DotEx/cublas_DotEx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-f87f3df88493) |
| [Extensions/DotEx/cublas_DotcEx_example.cu](../sample-reports/cuBLAS/Extensions/DotEx/cublas_DotcEx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-d8f54d1cbcb1) |
| [Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu](../sample-reports/cuBLAS/Extensions/GemmBatchedEx/cublas_GemmBatchedEx_example.cu.md) | PASSED / 4/4 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-1960c3ecdf64) |
| [Extensions/GemmEx/cublas_GemmEx_example.cu](../sample-reports/cuBLAS/Extensions/GemmEx/cublas_GemmEx_example.cu.md) | PASSED / 5/5 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-c58da716b916) |
| [Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu](../sample-reports/cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu.md) | PASSED / 3/3 | hipBLAS + project search/group dispatch / rocBLAS；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-dc82829edfbe) |
| [Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu](../sample-reports/cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu.md) | PASSED / 3/3 | hipBLAS + project search/group dispatch / rocBLAS；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-58780abbc4c5) |
| [Extensions/GemmStridedBatchedEx/cublas_GemmStridedBatchedEx_example.cu](../sample-reports/cuBLAS/Extensions/GemmStridedBatchedEx/cublas_GemmStridedBatchedEx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-4a692bc831f9) |
| [Extensions/Nrm2Ex/cublas_Nrm2Ex_example.cu](../sample-reports/cuBLAS/Extensions/Nrm2Ex/cublas_Nrm2Ex_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-353164b7a1f2) |
| [Extensions/RotEx/cublas_RotEx_example.cu](../sample-reports/cuBLAS/Extensions/RotEx/cublas_RotEx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-b483dfe69db4) |
| [Extensions/ScalEx/cublas_ScalEx_example.cu](../sample-reports/cuBLAS/Extensions/ScalEx/cublas_ScalEx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-c16d3309c24a) |
| [Extensions/dgmm/cublas_dgmm_example.cu](../sample-reports/cuBLAS/Extensions/dgmm/cublas_dgmm_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-b42b88e61c0c) |
| [Extensions/geam/cublas_geam_example.cu](../sample-reports/cuBLAS/Extensions/geam/cublas_geam_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-fd20f8056fbc) |
| [Extensions/tpttr/cublas_tpttr_example.cu](../sample-reports/cuBLAS/Extensions/tpttr/cublas_tpttr_example.cu.md) | PASSED / 4/4 | HIP GPU packed conversion / HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-712f998262d3) |
| [Extensions/trttp/cublas_trttp_example.cu](../sample-reports/cuBLAS/Extensions/trttp/cublas_trttp_example.cu.md) | PASSED / 4/4 | HIP GPU packed conversion / HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-bb358b6e6bba) |
| [Level-1/amax/cublas_amax_example.cu](../sample-reports/cuBLAS/Level-1/amax/cublas_amax_example.cu.md) | PASSED / 3/3 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-e1a0f8f10c70) |
| [Level-1/amin/cublas_amin_example.cu](../sample-reports/cuBLAS/Level-1/amin/cublas_amin_example.cu.md) | PASSED / 3/3 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-f4f602af8e2e) |
| [Level-1/asum/cublas_asum_example.cu](../sample-reports/cuBLAS/Level-1/asum/cublas_asum_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-40073530ff79) |
| [Level-1/axpy/cublas_axpy_example.cu](../sample-reports/cuBLAS/Level-1/axpy/cublas_axpy_example.cu.md) | PASSED / 5/5 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-be500bf3ca71) |
| [Level-1/copy/cublas_copy_example.cu](../sample-reports/cuBLAS/Level-1/copy/cublas_copy_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-4952fdc8000c) |
| [Level-1/dot/cublas_dot_example.cu](../sample-reports/cuBLAS/Level-1/dot/cublas_dot_example.cu.md) | PASSED / 9/9 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-deee37099df4) |
| [Level-1/dot/cublas_dotc_example.cu](../sample-reports/cuBLAS/Level-1/dot/cublas_dotc_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-fd3a625e6126) |
| [Level-1/nrm2/cublas_nrm2_example.cu](../sample-reports/cuBLAS/Level-1/nrm2/cublas_nrm2_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-8fa66ec14863) |
| [Level-1/rot/cublas_rot_example.cu](../sample-reports/cuBLAS/Level-1/rot/cublas_rot_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-e82885a56342) |
| [Level-1/rotg/cublas_rotg_example.cu](../sample-reports/cuBLAS/Level-1/rotg/cublas_rotg_example.cu.md) | PASSED / 3/3 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-92cc650e35c9) |
| [Level-1/rotm/cublas_rotm_example.cu](../sample-reports/cuBLAS/Level-1/rotm/cublas_rotm_example.cu.md) | PASSED / 4/4 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-dbadb2da2824) |
| [Level-1/rotmg/cublas_rotmg_example.cu](../sample-reports/cuBLAS/Level-1/rotmg/cublas_rotmg_example.cu.md) | PASSED / 6/6 | hipBLAS + HIP scale fix / rocBLAS；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-39becb746c7a) |
| [Level-1/scal/cublas_scal_example.cu](../sample-reports/cuBLAS/Level-1/scal/cublas_scal_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-0f181517de79) |
| [Level-1/swap/cublas_swap_example.cu](../sample-reports/cuBLAS/Level-1/swap/cublas_swap_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-cb81fefc3a04) |
| [Level-2/gbmv/cublas_gbmv_example.cu](../sample-reports/cuBLAS/Level-2/gbmv/cublas_gbmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-2f1dee74701d) |
| [Level-2/gemv/cublas_gemv_example.cu](../sample-reports/cuBLAS/Level-2/gemv/cublas_gemv_example.cu.md) | PASSED / 5/5 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-8fcc74fd88d4) |
| [Level-2/ger/cublas_ger_example.cu](../sample-reports/cuBLAS/Level-2/ger/cublas_ger_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-dafc912f10b3) |
| [Level-2/hbmv/cublas_hbmv_example.cu](../sample-reports/cuBLAS/Level-2/hbmv/cublas_hbmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-830249e93314) |
| [Level-2/hemv/cublas_hemv_example.cu](../sample-reports/cuBLAS/Level-2/hemv/cublas_hemv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-49d1e1072823) |
| [Level-2/her/cublas_her_example.cu](../sample-reports/cuBLAS/Level-2/her/cublas_her_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-216c3aeb1892) |
| [Level-2/her2/cublas_her2_example.cu](../sample-reports/cuBLAS/Level-2/her2/cublas_her2_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-466f04f076d3) |
| [Level-2/hpmv/cublas_hpmv_example.cu](../sample-reports/cuBLAS/Level-2/hpmv/cublas_hpmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-30d7157d0096) |
| [Level-2/hpr/cublas_hpr_example.cu](../sample-reports/cuBLAS/Level-2/hpr/cublas_hpr_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-a3ed0afc5a60) |
| [Level-2/hpr2/cublas_hpr2_example.cu](../sample-reports/cuBLAS/Level-2/hpr2/cublas_hpr2_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-e2b65f1de34c) |
| [Level-2/sbmv/cublas_sbmv_example.cu](../sample-reports/cuBLAS/Level-2/sbmv/cublas_sbmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-c98a92c88dae) |
| [Level-2/spmv/cublas_spmv_example.cu](../sample-reports/cuBLAS/Level-2/spmv/cublas_spmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-ddf1050f104d) |
| [Level-2/spr/cublas_spr_example.cu](../sample-reports/cuBLAS/Level-2/spr/cublas_spr_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-8394563bfd41) |
| [Level-2/spr2/cublas_spr2_example.cu](../sample-reports/cuBLAS/Level-2/spr2/cublas_spr2_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-129fb6c7002e) |
| [Level-2/symv/cublas_symv_example.cu](../sample-reports/cuBLAS/Level-2/symv/cublas_symv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-bb2ecba82cf5) |
| [Level-2/syr/cublas_syr_example.cu](../sample-reports/cuBLAS/Level-2/syr/cublas_syr_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-344bf118676a) |
| [Level-2/syr2/cublas_syr2_example.cu](../sample-reports/cuBLAS/Level-2/syr2/cublas_syr2_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-546197ad6c36) |
| [Level-2/tbmv/cublas_tbmv_example.cu](../sample-reports/cuBLAS/Level-2/tbmv/cublas_tbmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-d40b71730384) |
| [Level-2/tbsv/cublas_tbsv_example.cu](../sample-reports/cuBLAS/Level-2/tbsv/cublas_tbsv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-f655a54b7c0a) |
| [Level-2/tpmv/cublas_tpmv_example.cu](../sample-reports/cuBLAS/Level-2/tpmv/cublas_tpmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-9e915bbc36ad) |
| [Level-2/tpsv/cublas_tpsv_example.cu](../sample-reports/cuBLAS/Level-2/tpsv/cublas_tpsv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-e4acdf470897) |
| [Level-2/trmv/cublas_trmv_example.cu](../sample-reports/cuBLAS/Level-2/trmv/cublas_trmv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-653922be39c5) |
| [Level-2/trsv/cublas_trsv_example.cu](../sample-reports/cuBLAS/Level-2/trsv/cublas_trsv_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-c67025a57be4) |
| [Level-3/gemm/cublas_gemm_example.cu](../sample-reports/cuBLAS/Level-3/gemm/cublas_gemm_example.cu.md) | PASSED / 5/5 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-55ff879af86a) |
| [Level-3/gemm3m/cublas_gemm3m_example.cu](../sample-reports/cuBLAS/Level-3/gemm3m/cublas_gemm3m_example.cu.md) | PASSED / 7/7 | hipBLAS/rocBLAS three real SGEMMs + HIP complex split/merge / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-9d6bd29de04f) |
| [Level-3/gemmBatched/cublas_gemmBatched_example.cu](../sample-reports/cuBLAS/Level-3/gemmBatched/cublas_gemmBatched_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-3d0fd757ddec) |
| [Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu](../sample-reports/cuBLAS/Level-3/gemmGroupedBatched/cublas_gemmGroupedBatched_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-3ee59c86042f) |
| [Level-3/gemmStridedBatched/cublas_gemmStridedBatched_example.cu](../sample-reports/cuBLAS/Level-3/gemmStridedBatched/cublas_gemmStridedBatched_example.cu.md) | PASSED / 5/5 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-2f3dd6e98cd3) |
| [Level-3/hemm/cublas_hemm_example.cu](../sample-reports/cuBLAS/Level-3/hemm/cublas_hemm_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-b032a712f6bd) |
| [Level-3/her2k/cublas_her2k_example.cu](../sample-reports/cuBLAS/Level-3/her2k/cublas_her2k_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-f029950a4e1e) |
| [Level-3/herk/cublas_herk_example.cu](../sample-reports/cuBLAS/Level-3/herk/cublas_herk_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-39096c0cca5d) |
| [Level-3/herkx/cublas_herkx_example.cu](../sample-reports/cuBLAS/Level-3/herkx/cublas_herkx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-cee6ade714c6) |
| [Level-3/symm/cublas_symm_example.cu](../sample-reports/cuBLAS/Level-3/symm/cublas_symm_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-2f7215ab6c6c) |
| [Level-3/syr2k/cublas_syr2k_example.cu](../sample-reports/cuBLAS/Level-3/syr2k/cublas_syr2k_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-edc39fd82289) |
| [Level-3/syrk/cublas_syrk_example.cu](../sample-reports/cuBLAS/Level-3/syrk/cublas_syrk_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-3c67d5834988) |
| [Level-3/syrkx/cublas_syrkx_example.cu](../sample-reports/cuBLAS/Level-3/syrkx/cublas_syrkx_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-b7e6d5368799) |
| [Level-3/trmm/cublas_trmm_example.cu](../sample-reports/cuBLAS/Level-3/trmm/cublas_trmm_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-08e75d17293d) |
| [Level-3/trsm/cublas_trsm_example.cu](../sample-reports/cuBLAS/Level-3/trsm/cublas_trsm_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-142b97a4f162) |
| [Level-3/trsmBatched/cublas_trsmBatched_example.cu](../sample-reports/cuBLAS/Level-3/trsmBatched/cublas_trsmBatched_example.cu.md) | PASSED / 2/2 | hipBLAS / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-929b06bbd1fe) |
| [Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu](../sample-reports/cuBLAS/Emulation/bf16x9_gemmEx/cublas_GemmEx_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-b448795e7b8e) |
| [Emulation/bf16x9_sgemm/cublas_sgemm_example.cu](../sample-reports/cuBLAS/Emulation/bf16x9_sgemm/cublas_sgemm_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-6c798f997208) |
| [Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu](../sample-reports/cuBLAS/Emulation/dgemm_dynamic/cublas_dgemm_dynamic_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-94fe19f2ccd6) |
| [Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu](../sample-reports/cuBLAS/Emulation/dgemm_fixed/cublas_dgemm_fixed_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-86222f4276b9) |
| [Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu](../sample-reports/cuBLAS/Emulation/gemmEx_dynamic/cublas_gemmEx_dynamic_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-14a86eab858f) |
| [Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu](../sample-reports/cuBLAS/Emulation/gemmEx_fixed/cublas_gemmEx_fixed_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-0e2c3e7fa377) |
| [Emulation/gemm_grading/grade_blas3.cpp](../sample-reports/cuBLAS/Emulation/gemm_grading/grade_blas3.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-7ce08e76ccc2) |
| [Emulation/gemm_grading/test_blas3.cpp](../sample-reports/cuBLAS/Emulation/gemm_grading/test_blas3.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-cc5f5cc2ba19) |
| [Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu](../sample-reports/cuBLAS/Emulation/zgemm_dynamic/cublas_zgemm_dynamic_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-cb5dc49cb639) |
| [Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu](../sample-reports/cuBLAS/Emulation/zgemm_fixed/cublas_zgemm_fixed_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLAS.md#sample-5508de03d501) |

<a id="module-1"></a>

## cuBLASLt

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [LtHSHgemmGroupedSimple/main.cpp](../sample-reports/cuBLASLt/LtHSHgemmGroupedSimple/main.cpp.md) | PASSED / 3/3 | hipBLASLt + project search/group dispatch / hipBLASLt/rocBLAS；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-c56a0a21cf0b) |
| [LtHSHgemmPointerArrayBatchSimple/main.cpp](../sample-reports/cuBLASLt/LtHSHgemmPointerArrayBatchSimple/main.cpp.md) | PASSED / 1/1 | hipBLASLt / hipBLASLt；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-b7bf7c30e86f) |
| [LtHSHgemmStridedBatchSimple/main.cpp](../sample-reports/cuBLASLt/LtHSHgemmStridedBatchSimple/main.cpp.md) | PASSED / 1/1 | hipBLASLt / hipBLASLt；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-59de0585937d) |
| [LtIgemmTensor/main.cpp](../sample-reports/cuBLASLt/LtIgemmTensor/main.cpp.md) | PASSED / 7/7 | HIP COL32/COL4 packing/unpacking + native hipBLAS GemmEx INT8/INT32 / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-df70f98d9333) |
| [LtPlanarComplex/main.cpp](../sample-reports/cuBLASLt/LtPlanarComplex/main.cpp.md) | PASSED / 8/8 | HIP negative-offset FP16 planar conversion + hipBLAS/rocBLAS FP32 3M + HIP FP16 output / rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-3d1b270b1c38) |
| [LtSgemm/main.cpp](../sample-reports/cuBLASLt/LtSgemm/main.cpp.md) | PASSED / 5/5 | hipBLASLt / hipBLASLt native；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-7f13f06a75d4) |
| [LtSgemmCustomFind/main.cu](../sample-reports/cuBLASLt/LtSgemmCustomFind/main.cu.md) | PASSED / 3/3 | hipBLASLt + project search/group dispatch / hipBLASLt/rocBLAS；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-4d096dd02472) |
| [LtSgemmSimpleAutoTuning/main.cpp](../sample-reports/cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp.md) | PASSED / 3/3 | hipBLASLt + project search/group dispatch / hipBLASLt/rocBLAS；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-1b5db0b7b489) |
| [LtBlk128x128Fp8Matmul/main.cpp](../sample-reports/cuBLASLt/LtBlk128x128Fp8Matmul/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-66eca58406f4) |
| [LtBlk128x128Fp8gemmGroupedSimple/main.cpp](../sample-reports/cuBLASLt/LtBlk128x128Fp8gemmGroupedSimple/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-5c1dee352ace) |
| [LtDgemmEmulated/main.cpp](../sample-reports/cuBLASLt/LtDgemmEmulated/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-bf8a48586072) |
| [LtDgemmPresetAlgo/main.cpp](../sample-reports/cuBLASLt/LtDgemmPresetAlgo/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-a7161a5bf35a) |
| [LtFp8CustomFind/main.cu](../sample-reports/cuBLASLt/LtFp8CustomFind/main.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-42123a52890f) |
| [LtFp8Matmul/main.cpp](../sample-reports/cuBLASLt/LtFp8Matmul/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-3c33cf579f76) |
| [LtFp8gemmGroupedSimple/main.cpp](../sample-reports/cuBLASLt/LtFp8gemmGroupedSimple/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-f98a85ed9cac) |
| [LtMxfp8Matmul/main.cpp](../sample-reports/cuBLASLt/LtMxfp8Matmul/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-27e76a257947) |
| [LtMxfp8gemmGroupedSimple/main.cpp](../sample-reports/cuBLASLt/LtMxfp8gemmGroupedSimple/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-f9186b694a88) |
| [LtNvfp4Matmul/main.cpp](../sample-reports/cuBLASLt/LtNvfp4Matmul/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-47296035378c) |
| [LtNvfp4gemmGroupedSimple/main.cpp](../sample-reports/cuBLASLt/LtNvfp4gemmGroupedSimple/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-15ab2ec6d8ca) |
| [LtSgemmGreenContext/main.cpp](../sample-reports/cuBLASLt/LtSgemmGreenContext/main.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASLt.md#sample-acbea43003b8) |

<a id="module-2"></a>

## cuBLASMp

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [geadd.cu](../sample-reports/cuBLASMp/geadd.cu.md) | PASSED / 6/6 | MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD / MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-f716d108f6e8) |
| [gemr2d.cu](../sample-reports/cuBLASMp/gemr2d.cu.md) | PASSED / 6/6 | MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip / MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-5fecb0dc9913) |
| [gemm.cu](../sample-reports/cuBLASMp/gemm.cu.md) | PARTIAL / 6/7 | MPI + RCCL distribution + hipBLAS FP32 local GEMM / MPI + RCCL distribution + hipBLAS FP32 local GEMM；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-617eb8884d08) |
| [matmul_ag.cu](../sample-reports/cuBLASMp/matmul_ag.cu.md) | PARTIAL / 6/7 | MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization / MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-250830c05814) |
| [matmul_ar.cu](../sample-reports/cuBLASMp/matmul_ar.cu.md) | PARTIAL / 6/7 | MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization / MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-5acd6c625cbe) |
| [matmul_rs.cu](../sample-reports/cuBLASMp/matmul_rs.cu.md) | PARTIAL / 6/7 | MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization / MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-7dce0307d2f3) |
| [symm.cu](../sample-reports/cuBLASMp/symm.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-9114e43283a3) |
| [syr2k.cu](../sample-reports/cuBLASMp/syr2k.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-2af77476003c) |
| [syrk.cu](../sample-reports/cuBLASMp/syrk.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-9f63af00cccc) |
| [syrkx.cu](../sample-reports/cuBLASMp/syrkx.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-7e4be1f7245f) |
| [tp_matmul.cu](../sample-reports/cuBLASMp/tp_matmul.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-7603b4fae1b7) |
| [tradd.cu](../sample-reports/cuBLASMp/tradd.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-d5641e0ded06) |
| [trmm.cu](../sample-reports/cuBLASMp/trmm.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-2074e486dc8c) |
| [trsm.cu](../sample-reports/cuBLASMp/trsm.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuBLASMp.md#sample-a1535ed108da) |

<a id="module-3"></a>

## cuDSS

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [fortran/batch/batch.f90](../sample-reports/cuDSS/fortran/batch/batch.f90.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-ed8e99db11a7) |
| [fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90](../sample-reports/cuDSS/fortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.f90.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-c1497026978d) |
| [fortran/dense_matrix_helpers/dense_matrix_helpers.f90](../sample-reports/cuDSS/fortran/dense_matrix_helpers/dense_matrix_helpers.f90.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-fbaecb35f9cf) |
| [fortran/reordering_phase/reordering_phase.f90](../sample-reports/cuDSS/fortran/reordering_phase/reordering_phase.f90.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-5cd3099a7877) |
| [fortran/residual/residual.f90](../sample-reports/cuDSS/fortran/residual/residual.f90.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-da3a318cdcfe) |
| [fortran/simple/simple.f90](../sample-reports/cuDSS/fortran/simple/simple.f90.md) | PASSED / 2/2 | rocSOLVER + rocBLAS via ISO_C_BINDING/C ABI / GPU CSRRF sparse Cholesky; CPU sparse symbolic graph；改用 AMD 库重写算法流程 | [日志、范围、源码](support-log-index/cuDSS.md#sample-59fa745f5910) |
| [fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90](../sample-reports/cuDSS/fortran/sparse_matrix_helpers/sparse_matrix_helpers.f90.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-3cf3c65f6040) |
| [fortran/uniform_batch/uniform_batch.f90](../sample-reports/cuDSS/fortran/uniform_batch/uniform_batch.f90.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-c4fef2833c5e) |
| [nvfortran/batch/batch.cuf](../sample-reports/cuDSS/nvfortran/batch/batch.cuf.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-2f7dbb46d786) |
| [nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf](../sample-reports/cuDSS/nvfortran/batch_sparse_matrix_helpers/batch_sparse_matrix_helpers.cuf.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-783da9a9437d) |
| [nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf](../sample-reports/cuDSS/nvfortran/dense_matrix_helpers/dense_matrix_helpers.cuf.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-f997bfe4c747) |
| [nvfortran/reordering_phase/reordering_phase.cuf](../sample-reports/cuDSS/nvfortran/reordering_phase/reordering_phase.cuf.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-41fa55f0835f) |
| [nvfortran/residual/residual.cuf](../sample-reports/cuDSS/nvfortran/residual/residual.cuf.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-2867130b869e) |
| [nvfortran/simple/simple.cuf](../sample-reports/cuDSS/nvfortran/simple/simple.cuf.md) | PASSED / 2/2 | rocSOLVER + rocBLAS via ISO_C_BINDING/C ABI / GPU CSRRF sparse Cholesky; CPU sparse symbolic graph；改用 AMD 库重写算法流程 | [日志、范围、源码](support-log-index/cuDSS.md#sample-8d0ee8da6664) |
| [nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf](../sample-reports/cuDSS/nvfortran/sparse_matrix_helpers/sparse_matrix_helpers.cuf.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-110c494de4cb) |
| [nvfortran/uniform_batch/uniform_batch.cuf](../sample-reports/cuDSS/nvfortran/uniform_batch/uniform_batch.cuf.md) | PASSED / 12/12 | standard Fortran ISO_C_BINDING + project HIP CSR pivot LU/solve; CPU symbolic min-degree only；标准 Fortran 入口 + 项目 C ABI / HIP 算法 | [日志、范围、源码](support-log-index/cuDSS.md#sample-1ecfa60d4a88) |
| [simple/simple.cpp](../sample-reports/cuDSS/simple/simple.cpp.md) | PASSED / 3/3 | rocSOLVER CSRRF + rocBLAS / GPU sparse Cholesky; CPU sparse symbolic analysis；改用 AMD 库重写算法流程 | [日志、范围、源码](support-log-index/cuDSS.md#sample-f495b401e674) |
| [simple_batch/simple_batch.cpp](../sample-reports/cuDSS/simple_batch/simple_batch.cpp.md) | PASSED / 8/8 | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter / rocSOLVER/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-84cae1939da0) |
| [simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp](../sample-reports/cuDSS/simple_batch_sparse_matrix_helpers/simple_batch_sparse_matrix_helpers.cpp.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-7d78c16b5bd9) |
| [simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp](../sample-reports/cuDSS/simple_dense_matrix_helpers/simple_dense_matrix_helpers.cpp.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-a0b16fa26f6c) |
| [simple_residual/simple_residual.cpp](../sample-reports/cuDSS/simple_residual/simple_residual.cpp.md) | PASSED / 8/8 | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter / rocSOLVER/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-a2698a05926c) |
| [simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp](../sample-reports/cuDSS/simple_sparse_matrix_helpers/simple_sparse_matrix_helpers.cpp.md) | PASSED / 8/8 | ProjectMatrixHelpers + HIP (host descriptors; real device storage/pointer tables) / project host descriptor C ABI / real HIP buffers；项目 host 描述符 ABI + HIP GPU 存储 | [日志、范围、源码](support-log-index/cuDSS.md#sample-d58b5f8ba98a) |
| [simple_uniform_batch/simple_uniform_batch.cpp](../sample-reports/cuDSS/simple_uniform_batch/simple_uniform_batch.cpp.md) | PASSED / 8/8 | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter / rocSOLVER/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-c683e166ec18) |
| [simple_get_set/simple_get_set.cpp](../sample-reports/cuDSS/simple_get_set/simple_get_set.cpp.md) | PARTIAL / 8/9 | CPU sparse symbolic/matching + rocSOLVER CSRRF LU / HIP CSR pivot LU and GPU query adapter / rocSOLVER/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-c93d8086c25d) |
| [simple_reordering_phase/simple_reordering_phase.cpp](../sample-reports/cuDSS/simple_reordering_phase/simple_reordering_phase.cpp.md) | PARTIAL / 1/2 | CPU symbolic min-degree + project HIP CSR pivot LU/solve via shared C ABI / CPU analysis + HIP preparation；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-97a634ce0b2f) |
| [fortran/get_set/get_set.f90](../sample-reports/cuDSS/fortran/get_set/get_set.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-f1a95499cab8) |
| [fortran/high_precision/high_precision.f90](../sample-reports/cuDSS/fortran/high_precision/high_precision.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-d096ce6ee954) |
| [fortran/hybrid_execute_mode/hybrid_execute_mode.f90](../sample-reports/cuDSS/fortran/hybrid_execute_mode/hybrid_execute_mode.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-d2ee1ebb0f1c) |
| [fortran/hybrid_memory_mode/hybrid_memory_mode.f90](../sample-reports/cuDSS/fortran/hybrid_memory_mode/hybrid_memory_mode.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-e19c0aabc7da) |
| [fortran/memory_handler/memory_handler.f90](../sample-reports/cuDSS/fortran/memory_handler/memory_handler.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-70075b3a7bf1) |
| [fortran/mg_mode/mg_mode.f90](../sample-reports/cuDSS/fortran/mg_mode/mg_mode.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-4131d30736a9) |
| [fortran/mgmn_mode/mgmn_mode.f90](../sample-reports/cuDSS/fortran/mgmn_mode/mgmn_mode.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-30e36a904630) |
| [fortran/multithreaded_mode/multithreaded_mode.f90](../sample-reports/cuDSS/fortran/multithreaded_mode/multithreaded_mode.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-e821d31bc655) |
| [fortran/schur_complement/schur_complement.f90](../sample-reports/cuDSS/fortran/schur_complement/schur_complement.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-41a036aac0ae) |
| [fortran/simple_complex/simple_complex.f90](../sample-reports/cuDSS/fortran/simple_complex/simple_complex.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-716ca56bb3e1) |
| [nvfortran/get_set/get_set.cuf](../sample-reports/cuDSS/nvfortran/get_set/get_set.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-134869ab39d7) |
| [nvfortran/high_precision/high_precision.cuf](../sample-reports/cuDSS/nvfortran/high_precision/high_precision.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-575d5dffd4a6) |
| [nvfortran/hybrid_execute_mode/hybrid_execute_mode.cuf](../sample-reports/cuDSS/nvfortran/hybrid_execute_mode/hybrid_execute_mode.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-35dcd5dff322) |
| [nvfortran/hybrid_memory_mode/hybrid_memory_mode.cuf](../sample-reports/cuDSS/nvfortran/hybrid_memory_mode/hybrid_memory_mode.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-c555ee916225) |
| [nvfortran/memory_handler/memory_handler.cuf](../sample-reports/cuDSS/nvfortran/memory_handler/memory_handler.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-f3959e9646f4) |
| [nvfortran/mg_mode/mg_mode.cuf](../sample-reports/cuDSS/nvfortran/mg_mode/mg_mode.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-ebd8aa767e60) |
| [nvfortran/mgmn_mode/mgmn_mode.cuf](../sample-reports/cuDSS/nvfortran/mgmn_mode/mgmn_mode.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-fb011b00c273) |
| [nvfortran/multithreaded_mode/multithreaded_mode.cuf](../sample-reports/cuDSS/nvfortran/multithreaded_mode/multithreaded_mode.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-e2b90fc41344) |
| [nvfortran/schur_complement/schur_complement.cuf](../sample-reports/cuDSS/nvfortran/schur_complement/schur_complement.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-be34c43b8eac) |
| [nvfortran/simple_complex/simple_complex.cuf](../sample-reports/cuDSS/nvfortran/simple_complex/simple_complex.cuf.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuDSS.md#sample-8103d003119d) |
| [simple_complex/simple_complex.cpp](../sample-reports/cuDSS/simple_complex/simple_complex.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-dcab38ce4193) |
| [simple_high_precision/simple_high_precision.cpp](../sample-reports/cuDSS/simple_high_precision/simple_high_precision.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-2c6713ca7eba) |
| [simple_hybrid_execute_mode/simple_hybrid_execute_mode.cpp](../sample-reports/cuDSS/simple_hybrid_execute_mode/simple_hybrid_execute_mode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-f994102ee9ca) |
| [simple_hybrid_memory_mode/simple_hybrid_memory_mode.cpp](../sample-reports/cuDSS/simple_hybrid_memory_mode/simple_hybrid_memory_mode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-d2cfc3a0766b) |
| [simple_matrix_market/simple_matrix_market.cpp](../sample-reports/cuDSS/simple_matrix_market/simple_matrix_market.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-ee613b397ebb) |
| [simple_memory_handler/simple_memory_handler.cpp](../sample-reports/cuDSS/simple_memory_handler/simple_memory_handler.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-9969308235f4) |
| [simple_mg_mode/simple_mg_mode.cpp](../sample-reports/cuDSS/simple_mg_mode/simple_mg_mode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-38c6b20ee85e) |
| [simple_mgmn_distributed_matrix/simple_mgmn_distributed_matrix.cpp](../sample-reports/cuDSS/simple_mgmn_distributed_matrix/simple_mgmn_distributed_matrix.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-955c8c7857a3) |
| [simple_mgmn_mode/simple_mgmn_mode.cpp](../sample-reports/cuDSS/simple_mgmn_mode/simple_mgmn_mode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-7fd921fe840a) |
| [simple_multithreaded_mode/simple_multithreaded_mode.cpp](../sample-reports/cuDSS/simple_multithreaded_mode/simple_multithreaded_mode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-7b70b60b8a13) |
| [simple_pinned_memory_handler/simple_pinned_memory_handler.cpp](../sample-reports/cuDSS/simple_pinned_memory_handler/simple_pinned_memory_handler.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-2762bcab426e) |
| [simple_schur_complement/simple_schur_complement.cpp](../sample-reports/cuDSS/simple_schur_complement/simple_schur_complement.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-f446ddb35cd0) |
| [test_communication_layer/test_communication_layer.cu](../sample-reports/cuDSS/test_communication_layer/test_communication_layer.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-e5bd84a18efb) |
| [test_threading_layer/test_threading_layer.cu](../sample-reports/cuDSS/test_threading_layer/test_threading_layer.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuDSS.md#sample-710b413588c4) |

<a id="module-4"></a>

## cuEST

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [c_examples/examples/0_context/basic_multigpu_usage/main.c](../sample-reports/cuEST/c_examples/examples/0_context/basic_multigpu_usage/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-26cf1eee1c4c) |
| [c_examples/examples/0_context/basic_multistream_usage/main.c](../sample-reports/cuEST/c_examples/examples/0_context/basic_multistream_usage/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-ec832dd57c85) |
| [c_examples/examples/0_context/basic_usage/main.c](../sample-reports/cuEST/c_examples/examples/0_context/basic_usage/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-e56e8fd4c13e) |
| [c_examples/examples/0_context/user_owned_resources/main.c](../sample-reports/cuEST/c_examples/examples/0_context/user_owned_resources/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-0aea5f1954b7) |
| [c_examples/examples/1_basic_data_structures/ao_basis/main.c](../sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ao_basis/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-9ede6c48937c) |
| [c_examples/examples/1_basic_data_structures/ao_basis_general/main.c](../sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ao_basis_general/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-0173b54c5262) |
| [c_examples/examples/1_basic_data_structures/ao_shells/main.c](../sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ao_shells/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-46c2e1a7076e) |
| [c_examples/examples/1_basic_data_structures/ecp_atom/main.c](../sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ecp_atom/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-b136ae3f4981) |
| [c_examples/examples/1_basic_data_structures/ecp_shells/main.c](../sample-reports/cuEST/c_examples/examples/1_basic_data_structures/ecp_shells/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-d7056ed2cff7) |
| [c_examples/examples/1_basic_data_structures/xc_grid/main.c](../sample-reports/cuEST/c_examples/examples/1_basic_data_structures/xc_grid/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-8e54d119c5a5) |
| [c_examples/examples/1_basic_data_structures/xc_grid_general/main.c](../sample-reports/cuEST/c_examples/examples/1_basic_data_structures/xc_grid_general/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-808a145e5f84) |
| [c_examples/examples/2_one_electron_integrals/one_electron_gradients/main.c](../sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/one_electron_gradients/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-08393e36e1ec) |
| [c_examples/examples/2_one_electron_integrals/one_electron_integrals/main.c](../sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/one_electron_integrals/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-8d597e3b8e82) |
| [c_examples/examples/2_one_electron_integrals/property_gradients/main.c](../sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/property_gradients/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-6812e1a3eb5a) |
| [c_examples/examples/2_one_electron_integrals/property_integrals/main.c](../sample-reports/cuEST/c_examples/examples/2_one_electron_integrals/property_integrals/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-638e6ddb9558) |
| [c_examples/examples/3_density_fitting/core_df_jk/main.c](../sample-reports/cuEST/c_examples/examples/3_density_fitting/core_df_jk/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-d9d4a4142d28) |
| [c_examples/examples/3_density_fitting/core_df_jk_gradients/main.c](../sample-reports/cuEST/c_examples/examples/3_density_fitting/core_df_jk_gradients/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-727bbd4617b9) |
| [c_examples/examples/3_density_fitting/df_mo_integrals/main.c](../sample-reports/cuEST/c_examples/examples/3_density_fitting/df_mo_integrals/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-435931f8baf8) |
| [c_examples/examples/3_density_fitting/nonsymmetric_core_df_k/main.c](../sample-reports/cuEST/c_examples/examples/3_density_fitting/nonsymmetric_core_df_k/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-382cd8f9eddf) |
| [c_examples/examples/4_exchange_correlation/advanced_local_xc_gradient/main.c](../sample-reports/cuEST/c_examples/examples/4_exchange_correlation/advanced_local_xc_gradient/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-79a01035729c) |
| [c_examples/examples/4_exchange_correlation/advanced_local_xc_potential/main.c](../sample-reports/cuEST/c_examples/examples/4_exchange_correlation/advanced_local_xc_potential/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-cd3fa744c065) |
| [c_examples/examples/4_exchange_correlation/local_xc_gradient/main.c](../sample-reports/cuEST/c_examples/examples/4_exchange_correlation/local_xc_gradient/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-9698e443af22) |
| [c_examples/examples/4_exchange_correlation/local_xc_potential/main.c](../sample-reports/cuEST/c_examples/examples/4_exchange_correlation/local_xc_potential/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-76d797d50b01) |
| [c_examples/examples/4_exchange_correlation/nonlocal_xc_gradient/main.c](../sample-reports/cuEST/c_examples/examples/4_exchange_correlation/nonlocal_xc_gradient/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-7183d59f594b) |
| [c_examples/examples/4_exchange_correlation/nonlocal_xc_potential/main.c](../sample-reports/cuEST/c_examples/examples/4_exchange_correlation/nonlocal_xc_potential/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-0cfa7f38ecf8) |
| [c_examples/examples/5_effective_core_potentials/ecp_gradients/main.c](../sample-reports/cuEST/c_examples/examples/5_effective_core_potentials/ecp_gradients/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-943539c94cfb) |
| [c_examples/examples/5_effective_core_potentials/ecp_integrals/main.c](../sample-reports/cuEST/c_examples/examples/5_effective_core_potentials/ecp_integrals/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-508f54167861) |
| [c_examples/examples/6_pcm/pcm_gradients/main.c](../sample-reports/cuEST/c_examples/examples/6_pcm/pcm_gradients/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-4c85b0595edd) |
| [c_examples/examples/6_pcm/pcm_potential/main.c](../sample-reports/cuEST/c_examples/examples/6_pcm/pcm_potential/main.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuEST.md#sample-133abfd9b5bf) |
| [python_examples/0_context/basic_multistream_usage/run.py](../sample-reports/cuEST/python_examples/0_context/basic_multistream_usage/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-ef9d044c3d47) |
| [python_examples/0_context/basic_usage/run.py](../sample-reports/cuEST/python_examples/0_context/basic_usage/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-071107188364) |
| [python_examples/0_context/user_owned_resources/run.py](../sample-reports/cuEST/python_examples/0_context/user_owned_resources/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-ea50f6981fbe) |
| [python_examples/1_basic_data_structures/ao_basis/run.py](../sample-reports/cuEST/python_examples/1_basic_data_structures/ao_basis/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-3ef508dea3c8) |
| [python_examples/1_basic_data_structures/ao_shells/run.py](../sample-reports/cuEST/python_examples/1_basic_data_structures/ao_shells/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-3f82ab7c88a1) |
| [python_examples/2_one_electron_integrals/one_electron_gradients/run.py](../sample-reports/cuEST/python_examples/2_one_electron_integrals/one_electron_gradients/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-33c54f9b8051) |
| [python_examples/2_one_electron_integrals/one_electron_integrals/run.py](../sample-reports/cuEST/python_examples/2_one_electron_integrals/one_electron_integrals/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-f4e97dd0459a) |
| [python_examples/2_one_electron_integrals/property_gradients/run.py](../sample-reports/cuEST/python_examples/2_one_electron_integrals/property_gradients/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-fb5f009485a7) |
| [python_examples/2_one_electron_integrals/property_integrals/run.py](../sample-reports/cuEST/python_examples/2_one_electron_integrals/property_integrals/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-f72d929ba46d) |
| [python_examples/3_density_fitting/core_df_jk/run.py](../sample-reports/cuEST/python_examples/3_density_fitting/core_df_jk/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-b6fbaa4da5a9) |
| [python_examples/3_density_fitting/core_df_jk_gradient_rhf/run.py](../sample-reports/cuEST/python_examples/3_density_fitting/core_df_jk_gradient_rhf/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-f1e00df591c8) |
| [python_examples/3_density_fitting/core_df_jk_gradient_uhf/run.py](../sample-reports/cuEST/python_examples/3_density_fitting/core_df_jk_gradient_uhf/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-a2d414efc28c) |
| [python_examples/3_density_fitting/df_mo_integrals/run.py](../sample-reports/cuEST/python_examples/3_density_fitting/df_mo_integrals/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-6b9610aef38c) |
| [python_examples/3_density_fitting/nonsymmetric_core_df_k/run.py](../sample-reports/cuEST/python_examples/3_density_fitting/nonsymmetric_core_df_k/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-be079cc05688) |
| [python_examples/4_exchange_correlation/local_xc_gradient/run.py](../sample-reports/cuEST/python_examples/4_exchange_correlation/local_xc_gradient/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-83ad3c6d025b) |
| [python_examples/4_exchange_correlation/local_xc_potential/run.py](../sample-reports/cuEST/python_examples/4_exchange_correlation/local_xc_potential/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-ea2331b357b5) |
| [python_examples/4_exchange_correlation/nonlocal_xc_gradient/run.py](../sample-reports/cuEST/python_examples/4_exchange_correlation/nonlocal_xc_gradient/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-ecec95cb0a74) |
| [python_examples/4_exchange_correlation/nonlocal_xc_potential/run.py](../sample-reports/cuEST/python_examples/4_exchange_correlation/nonlocal_xc_potential/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-a1080b0cb8ba) |
| [python_examples/5_effective_core_potentials/ecp_gradients/run.py](../sample-reports/cuEST/python_examples/5_effective_core_potentials/ecp_gradients/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-29cef0400376) |
| [python_examples/5_effective_core_potentials/ecp_integrals/run.py](../sample-reports/cuEST/python_examples/5_effective_core_potentials/ecp_integrals/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-852eff58f533) |
| [python_examples/6_pcm/pcm_gradients/run.py](../sample-reports/cuEST/python_examples/6_pcm/pcm_gradients/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-ddc652be7b7f) |
| [python_examples/6_pcm/pcm_potential/run.py](../sample-reports/cuEST/python_examples/6_pcm/pcm_potential/run.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuEST.md#sample-ec3f5eaefc8b) |

<a id="module-5"></a>

## cuFFT

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [1d_c2c/1d_c2c_example.cpp](../sample-reports/cuFFT/1d_c2c/1d_c2c_example.cpp.md) | PASSED / 6/6 | hipFFT / rocFFT；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-ec57e822e0cc) |
| [1d_mgpu_c2c/1d_mgpu_c2c_example.cpp](../sample-reports/cuFFT/1d_mgpu_c2c/1d_mgpu_c2c_example.cpp.md) | PASSED / 1/1 | hipFFT + RCCL + HIP / Two GPU radix decomposition and GPU merge；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuFFT.md#sample-45f960a47aff) |
| [1d_r2c_c2r/1d_r2c_c2r_example.cpp](../sample-reports/cuFFT/1d_r2c_c2r/1d_r2c_c2r_example.cpp.md) | PASSED / 6/6 | hipFFT / rocFFT；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-2c603110bdd8) |
| [2d_c2r_r2c/2d_c2r_r2c_example.cpp](../sample-reports/cuFFT/2d_c2r_r2c/2d_c2r_r2c_example.cpp.md) | PASSED / 2/2 | hipFFT / rocFFT；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-eedadfd5bbd0) |
| [3d_c2c/3d_c2c_example.cpp](../sample-reports/cuFFT/3d_c2c/3d_c2c_example.cpp.md) | PASSED / 2/2 | hipFFT / rocFFT；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-15934d52a8eb) |
| [3d_mgpu_c2c/3d_mgpu_c2c_example.cpp](../sample-reports/cuFFT/3d_mgpu_c2c/3d_mgpu_c2c_example.cpp.md) | PASSED / 2/2 | hipFFT / rocFFT；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-4ac6ef49c1c7) |
| [3d_mgpu_r2c_c2r/3d_mgpu_r2c_c2r_example.cpp](../sample-reports/cuFFT/3d_mgpu_r2c_c2r/3d_mgpu_r2c_c2r_example.cpp.md) | PASSED / 2/2 | hipFFT / rocFFT；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-c69020cad5ce) |
| [lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu](../sample-reports/cuFFT/lto_callback_window_1d/src/r2c_c2r_legacy_callback_example.cu.md) | PASSED / 2/2 | hipFFT / rocFFT；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-d23422784597) |
| [lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp](../sample-reports/cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_callback_example.cpp.md) | PASSED / 2/2 | hipFFT/rocFFT JIT callbacks + HIP compiler SPIR-V / rocFFT SPIR-V JIT integration；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-fec423468d23) |
| [lto_callback_window_1d/src/r2c_c2r_lto_nvrtc_callback_example.cpp](../sample-reports/cuFFT/lto_callback_window_1d/src/r2c_c2r_lto_nvrtc_callback_example.cpp.md) | PASSED / 2/2 | hipFFT/rocFFT JIT callbacks + HIPRTC / rocFFT SPIR-V JIT integration；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFT.md#sample-091736f02b63) |

<a id="module-6"></a>

## cuFFTMp

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [samples/c2c/cufftmp_c2c.cu](../sample-reports/cuFFTMp/samples/c2c/cufftmp_c2c.cu.md) | PASSED / 6/6 | MPI + hipFFT local YZ/X FFT + RCCL Send/Recv + HIP slab transpose/scale / MPI + hipFFT local YZ/X FFT + RCCL Send/Recv + HIP slab transpose/scale；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-a55d8e4231ee) |
| [Fortran_samples/c2c/cufftmp_c2c.f90](../sample-reports/cuFFTMp/Fortran_samples/c2c/cufftmp_c2c.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-cbc2a469a53d) |
| [Fortran_samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.f90](../sample-reports/cuFFTMp/Fortran_samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-16624924b798) |
| [Fortran_samples/c2c_pencils/cufftmp_c2c_pencils.f90](../sample-reports/cuFFTMp/Fortran_samples/c2c_pencils/cufftmp_c2c_pencils.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-75cd2963b7f2) |
| [Fortran_samples/r2c_c2r/cufftmp_r2c.f90](../sample-reports/cuFFTMp/Fortran_samples/r2c_c2r/cufftmp_r2c.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-277fc9a92a5d) |
| [Fortran_samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.f90](../sample-reports/cuFFTMp/Fortran_samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-b729e363a3ee) |
| [Fortran_samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.f90](../sample-reports/cuFFTMp/Fortran_samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-0c5db45aa6a0) |
| [Fortran_samples/r2c_c2r_shared_scratch/cufftmp_r2c_workarea.f90](../sample-reports/cuFFTMp/Fortran_samples/r2c_c2r_shared_scratch/cufftmp_r2c_workarea.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-71f5fec6bdfd) |
| [Fortran_samples/reshape/cufftmp_reshape.f90](../sample-reports/cuFFTMp/Fortran_samples/reshape/cufftmp_reshape.f90.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-5fd6a55b1315) |
| [JAX_FFT/tests/fft_test.py](../sample-reports/cuFFTMp/JAX_FFT/tests/fft_test.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-4bb57c79c646) |
| [samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.cu](../sample-reports/cuFFTMp/samples/c2c_no_descriptors/cufftmp_c2c_no_descriptors.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-fc90f40c8b00) |
| [samples/c2c_no_descriptors_cufftMpMakePlan/cufftmp_c2c_no_descriptors_cufftMpMakePlan.cu](../sample-reports/cuFFTMp/samples/c2c_no_descriptors_cufftMpMakePlan/cufftmp_c2c_no_descriptors_cufftMpMakePlan.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-a3642dfe720f) |
| [samples/c2c_pencils/cufftmp_c2c_pencils.cu](../sample-reports/cuFFTMp/samples/c2c_pencils/cufftmp_c2c_pencils.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-ebbdcbecdbc5) |
| [samples/r2c_c2r/cufftmp_r2c_c2r.cu](../sample-reports/cuFFTMp/samples/r2c_c2r/cufftmp_r2c_c2r.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-6b2c340c3e20) |
| [samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.cu](../sample-reports/cuFFTMp/samples/r2c_c2r_no_descriptors/cufftmp_r2c_c2r_no_descriptors.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-f8a777ab6adf) |
| [samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.cu](../sample-reports/cuFFTMp/samples/r2c_c2r_pencils/cufftmp_r2c_c2r_pencils.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-2993770cd13a) |
| [samples/r2c_c2r_pencils_cufftMpMakePlan/cufftmp_r2c_c2r_pencils_cufftMpMakePlan.cu](../sample-reports/cuFFTMp/samples/r2c_c2r_pencils_cufftMpMakePlan/cufftmp_r2c_c2r_pencils_cufftMpMakePlan.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-85d136d17142) |
| [samples/r2c_c2r_shared_scratch/cufftmp_r2c_c2r_shared_scratch.cu](../sample-reports/cuFFTMp/samples/r2c_c2r_shared_scratch/cufftmp_r2c_c2r_shared_scratch.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-3b90c24b145d) |
| [samples/r2c_c2r_slabs_GROMACS/cufftmp_r2c_c2r_slabs_GROMACS.cu](../sample-reports/cuFFTMp/samples/r2c_c2r_slabs_GROMACS/cufftmp_r2c_c2r_slabs_GROMACS.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-57c3827b72ec) |
| [samples/reshape/cufftmp_reshape.cu](../sample-reports/cuFFTMp/samples/reshape/cufftmp_reshape.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuFFTMp.md#sample-c016993c7fba) |

<a id="module-7"></a>

## cuPQC

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [example_sha2.cu](../sample-reports/cuPQC/example_sha2.cu.md) | PASSED / 14/14 | HIP runtime + custom device SHA implementation / HIP/gfx1201；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuPQC.md#sample-78960eaab346) |
| [example_sha3.cu](../sample-reports/cuPQC/example_sha3.cu.md) | PASSED / 14/14 | HIP runtime + custom device SHA implementation / HIP/gfx1201；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuPQC.md#sample-2582977be7ea) |
| [example_merkle.cu](../sample-reports/cuPQC/example_merkle.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuPQC.md#sample-ab51618fdaa2) |
| [example_ml_dsa.cu](../sample-reports/cuPQC/example_ml_dsa.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuPQC.md#sample-66a8f2c39e9c) |
| [example_ml_kem.cu](../sample-reports/cuPQC/example_ml_kem.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuPQC.md#sample-7d3bdf198a02) |
| [example_poseidon2.cu](../sample-reports/cuPQC/example_poseidon2.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuPQC.md#sample-3a46e9acabd1) |

<a id="module-8"></a>

## cuRAND

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [Host/mrg32k3a/curand_mrg32k3a_lognormal_example.cpp](../sample-reports/cuRAND/Host/mrg32k3a/curand_mrg32k3a_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-991b29b74ab5) |
| [Host/mrg32k3a/curand_mrg32k3a_normal_example.cpp](../sample-reports/cuRAND/Host/mrg32k3a/curand_mrg32k3a_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-d8acb2b78fec) |
| [Host/mrg32k3a/curand_mrg32k3a_poisson_example.cpp](../sample-reports/cuRAND/Host/mrg32k3a/curand_mrg32k3a_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-ba2e8fb6bca3) |
| [Host/mrg32k3a/curand_mrg32k3a_uniform_example.cpp](../sample-reports/cuRAND/Host/mrg32k3a/curand_mrg32k3a_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-bb56db4a15c9) |
| [Host/mt19937/curand_mt19937_lognormal_example.cpp](../sample-reports/cuRAND/Host/mt19937/curand_mt19937_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-6fa961f9d93c) |
| [Host/mt19937/curand_mt19937_normal_example.cpp](../sample-reports/cuRAND/Host/mt19937/curand_mt19937_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-c033e348f771) |
| [Host/mt19937/curand_mt19937_poisson_example.cpp](../sample-reports/cuRAND/Host/mt19937/curand_mt19937_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-032e4935f5c0) |
| [Host/mt19937/curand_mt19937_uniform_example.cpp](../sample-reports/cuRAND/Host/mt19937/curand_mt19937_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-5b65b6fe565c) |
| [Host/mtgp32/curand_mtgp32_lognormal_example.cpp](../sample-reports/cuRAND/Host/mtgp32/curand_mtgp32_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-f47aca159717) |
| [Host/mtgp32/curand_mtgp32_normal_example.cpp](../sample-reports/cuRAND/Host/mtgp32/curand_mtgp32_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-f868161f2175) |
| [Host/mtgp32/curand_mtgp32_poisson_example.cpp](../sample-reports/cuRAND/Host/mtgp32/curand_mtgp32_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-1aae9720c4eb) |
| [Host/mtgp32/curand_mtgp32_uniform_example.cpp](../sample-reports/cuRAND/Host/mtgp32/curand_mtgp32_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-49d09f9ea171) |
| [Host/philox/curand_philox_lognormal_example.cpp](../sample-reports/cuRAND/Host/philox/curand_philox_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-a41d05f75e64) |
| [Host/philox/curand_philox_normal_example.cpp](../sample-reports/cuRAND/Host/philox/curand_philox_normal_example.cpp.md) | PASSED / 5/5 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-5163388a4fb8) |
| [Host/philox/curand_philox_poisson_example.cpp](../sample-reports/cuRAND/Host/philox/curand_philox_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-e61f72f465d0) |
| [Host/philox/curand_philox_uniform_example.cpp](../sample-reports/cuRAND/Host/philox/curand_philox_uniform_example.cpp.md) | PASSED / 5/5 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-d49c209e2086) |
| [Host/scrambled_sobol32/curand_scrambled_sobol32_lognormal_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol32/curand_scrambled_sobol32_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-6fbe54addf0d) |
| [Host/scrambled_sobol32/curand_scrambled_sobol32_normal_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol32/curand_scrambled_sobol32_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-e70ae20270f0) |
| [Host/scrambled_sobol32/curand_scrambled_sobol32_poisson_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol32/curand_scrambled_sobol32_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-94105aac2379) |
| [Host/scrambled_sobol32/curand_scrambled_sobol32_uniform_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol32/curand_scrambled_sobol32_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-ca82553a5040) |
| [Host/scrambled_sobol64/curand_scrambled_sobol64_lognormal_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol64/curand_scrambled_sobol64_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-7666637992a9) |
| [Host/scrambled_sobol64/curand_scrambled_sobol64_normal_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol64/curand_scrambled_sobol64_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-5346c4c868bb) |
| [Host/scrambled_sobol64/curand_scrambled_sobol64_poisson_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol64/curand_scrambled_sobol64_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-88e0fe9ff0e3) |
| [Host/scrambled_sobol64/curand_scrambled_sobol64_uniform_example.cpp](../sample-reports/cuRAND/Host/scrambled_sobol64/curand_scrambled_sobol64_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-12c10679caa0) |
| [Host/sobol32/curand_sobol32_lognormal_example.cpp](../sample-reports/cuRAND/Host/sobol32/curand_sobol32_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-1aecd529fb5d) |
| [Host/sobol32/curand_sobol32_normal_example.cpp](../sample-reports/cuRAND/Host/sobol32/curand_sobol32_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-d61f0bb6b2bc) |
| [Host/sobol32/curand_sobol32_poisson_example.cpp](../sample-reports/cuRAND/Host/sobol32/curand_sobol32_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-d139fefa58fa) |
| [Host/sobol32/curand_sobol32_uniform_example.cpp](../sample-reports/cuRAND/Host/sobol32/curand_sobol32_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-f1c5af8e17ad) |
| [Host/sobol64/curand_sobol64_lognormal_example.cpp](../sample-reports/cuRAND/Host/sobol64/curand_sobol64_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-39850dcaf018) |
| [Host/sobol64/curand_sobol64_normal_example.cpp](../sample-reports/cuRAND/Host/sobol64/curand_sobol64_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-c496f57a8327) |
| [Host/sobol64/curand_sobol64_poisson_example.cpp](../sample-reports/cuRAND/Host/sobol64/curand_sobol64_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-9ce823f89314) |
| [Host/sobol64/curand_sobol64_uniform_example.cpp](../sample-reports/cuRAND/Host/sobol64/curand_sobol64_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-cbd76e107feb) |
| [Host/xorwow/curand_xorwow_lognormal_example.cpp](../sample-reports/cuRAND/Host/xorwow/curand_xorwow_lognormal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-7e224e81a879) |
| [Host/xorwow/curand_xorwow_normal_example.cpp](../sample-reports/cuRAND/Host/xorwow/curand_xorwow_normal_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-5a46974a3c06) |
| [Host/xorwow/curand_xorwow_poisson_example.cpp](../sample-reports/cuRAND/Host/xorwow/curand_xorwow_poisson_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-f5528f17aa9e) |
| [Host/xorwow/curand_xorwow_uniform_example.cpp](../sample-reports/cuRAND/Host/xorwow/curand_xorwow_uniform_example.cpp.md) | PASSED / 6/6 | hipRAND / rocRAND；库 API 迁移 | [日志、范围、源码](support-log-index/cuRAND.md#sample-871a0a4bb4cf) |

<a id="module-9"></a>

## cuSOLVER

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [MgGetrf/cusolver_MgGetrf_example.cu](../sample-reports/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu.md) | PASSED / 6/6 | HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads / HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-59479cba1451) |
| [Xgeqrf/cusolver_Xgeqrf_example.cu](../sample-reports/cuSOLVER/Xgeqrf/cusolver_Xgeqrf_example.cu.md) | PASSED / 1/1 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-68f8ec5cd2db) |
| [Xgesvd/cusolver_Xgesvd_example.cu](../sample-reports/cuSOLVER/Xgesvd/cusolver_Xgesvd_example.cu.md) | PASSED / 3/3 | rocSOLVER dgesvd + checked dimension bridge / rocSOLVER；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-a8cf7c4caf76) |
| [Xgetrf/cusolver_Xgetrf_example.cu](../sample-reports/cuSOLVER/Xgetrf/cusolver_Xgetrf_example.cu.md) | PASSED / 4/4 | rocSOLVER ILP64 / rocSOLVER；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-f21f3e2bc8c3) |
| [Xpotrf/cusolver_Xpotrf_example.cu](../sample-reports/cuSOLVER/Xpotrf/cusolver_Xpotrf_example.cu.md) | PASSED / 1/1 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-3203924ffcbe) |
| [Xsyevd/cusolver_Xsyevd_example.cu](../sample-reports/cuSOLVER/Xsyevd/cusolver_Xsyevd_example.cu.md) | PASSED / 3/3 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-471f4310f5f2) |
| [Xsyevdx/cusolver_Xsyevdx_example.cu](../sample-reports/cuSOLVER/Xsyevdx/cusolver_Xsyevdx_example.cu.md) | PASSED / 4/4 | rocSOLVER dsyevx + checked dimension bridge / rocSOLVER；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-bce1d24c988d) |
| [Xtrtri/cusolver_Xtrtri_example.cu](../sample-reports/cuSOLVER/Xtrtri/cusolver_Xtrtri_example.cu.md) | PASSED / 4/4 | hipBLAS Dtrsm_64 + HIP diagonal/info adapter / rocBLAS/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-880b188590cd) |
| [gesvd/cusolver_gesvd_example.cu](../sample-reports/cuSOLVER/gesvd/cusolver_gesvd_example.cu.md) | PASSED / 4/4 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-e0724c648c23) |
| [gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu](../sample-reports/cuSOLVER/gesvdaStridedBatched/cusolver_gesvdaStridedBatched_example.cu.md) | PASSED / 8/8 | hipSOLVER/rocSOLVER native full GPU SVD + HIP rank projection and FP64 residual / rocSOLVER + project HIP；改用 AMD 库重写算法流程 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-c717ad5ad665) |
| [gesvdj/cusolver_gesvdj_example.cu](../sample-reports/cuSOLVER/gesvdj/cusolver_gesvdj_example.cu.md) | PASSED / 4/4 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-454eff5e40e2) |
| [gesvdjBatched/cusolver_gesvdjBatched_example.cu](../sample-reports/cuSOLVER/gesvdjBatched/cusolver_gesvdjBatched_example.cu.md) | PASSED / 3/3 | hipSOLVER / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-ed60e960de23) |
| [getrf/cusolver_getrf_example.cu](../sample-reports/cuSOLVER/getrf/cusolver_getrf_example.cu.md) | PASSED / 6/6 | hipSOLVER / rocSOLVER；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-d5d8e56391e4) |
| [orgqr/cusolver_orgqr_example.cu](../sample-reports/cuSOLVER/orgqr/cusolver_orgqr_example.cu.md) | PASSED / 3/3 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-b2081047c80f) |
| [ormqr/cusolver_ormqr_example.cu](../sample-reports/cuSOLVER/ormqr/cusolver_ormqr_example.cu.md) | PASSED / 4/4 | hipSOLVER / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-ac5f69fabde6) |
| [potrfBatched/cusolver_potrfBatched_example.cu](../sample-reports/cuSOLVER/potrfBatched/cusolver_potrfBatched_example.cu.md) | PASSED / 7/7 | hipSOLVER / rocSOLVER；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-d81ce7fc5991) |
| [syevd/cusolver_syevd_example.cu](../sample-reports/cuSOLVER/syevd/cusolver_syevd_example.cu.md) | PASSED / 3/3 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-6cea8cd78840) |
| [syevdx/cusolver_syevdx_example.cu](../sample-reports/cuSOLVER/syevdx/cusolver_syevdx_example.cu.md) | PASSED / 4/4 | hipSOLVER / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-38756ddf697a) |
| [syevj/cusolver_syevj_example.cu](../sample-reports/cuSOLVER/syevj/cusolver_syevj_example.cu.md) | PASSED / 3/3 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-c792dc9a31b9) |
| [syevjBatched/cusolver_syevjBatched_example.cu](../sample-reports/cuSOLVER/syevjBatched/cusolver_syevjBatched_example.cu.md) | PASSED / 3/3 | hipSOLVER / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-12f8505cd79f) |
| [sygvd/cusolver_sygvd_example.cu](../sample-reports/cuSOLVER/sygvd/cusolver_sygvd_example.cu.md) | PASSED / 3/3 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-6fdf8f2795d6) |
| [sygvdx/cusolver_sygvdx_example.cu](../sample-reports/cuSOLVER/sygvdx/cusolver_sygvdx_example.cu.md) | PASSED / 4/4 | hipSOLVER / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-4fe2b2bfcf2b) |
| [sygvj/cusolver_sygvj_example.cu](../sample-reports/cuSOLVER/sygvj/cusolver_sygvj_example.cu.md) | PASSED / 3/3 | hipSOLVER + hipBLAS / rocSOLVER/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-4e30a6c5a93d) |
| [MgPotrf/cusolver_MgPotrf_example1.cu](../sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu.md) | PARTIAL / 6/7 | HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads / HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-f1d624cfda5f) |
| [Xgeev/cusolver_Xgeev_example1.cu](../sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example1.cu.md) | PARTIAL / 1/3 | hipsolver / rocSOLVER；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-695c063397de) |
| [Xgeev/cusolver_Xgeev_example2.cu](../sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example2.cu.md) | PARTIAL / 1/3 | hipsolver / rocSOLVER；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-1fe56daf1bd7) |
| [Xgeev/cusolver_Xgeev_example3.cu](../sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example3.cu.md) | PARTIAL / 1/3 | hipsolver / rocSOLVER；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-9602fa21ffdb) |
| [MgPotrf/cusolver_MgPotrf_example2.cu](../sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example2.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-59f2f1325b54) |
| [MgSyevd/cusolver_MgSyevd_example1.cu](../sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example1.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-e6fe5059759e) |
| [MgSyevd/cusolver_MgSyevd_example2.cu](../sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example2.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-0ebd46d9a63d) |
| [MgSyevd/cusolver_MgSyevd_example3.cu](../sample-reports/cuSOLVER/MgSyevd/cusolver_MgSyevd_example3.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-12d6e49561ca) |
| [Xgeev/cusolver_Xgeev_example4.cu](../sample-reports/cuSOLVER/Xgeev/cusolver_Xgeev_example4.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-2c016a39c7d2) |
| [Xgesvdp/cusolver_Xgesvdp_example.cu](../sample-reports/cuSOLVER/Xgesvdp/cusolver_Xgesvdp_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-0225ea9f8929) |
| [Xgesvdr/cusolver_Xgesvdr_example.cu](../sample-reports/cuSOLVER/Xgesvdr/cusolver_Xgesvdr_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-1e9f47ab6de5) |
| [csrqr/cusolver_csrqr_example1.cu](../sample-reports/cuSOLVER/csrqr/cusolver_csrqr_example1.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-d7258f19dfd5) |
| [csrqr/cusolver_csrqr_example2.cu](../sample-reports/cuSOLVER/csrqr/cusolver_csrqr_example2.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-112ffa8e629b) |
| [gesv/cusolver_irs_expert_cuda-10.2.cu](../sample-reports/cuSOLVER/gesv/cusolver_irs_expert_cuda-10.2.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-d80ea212fe82) |
| [gesv/cusolver_irs_expert_cuda-11.cu](../sample-reports/cuSOLVER/gesv/cusolver_irs_expert_cuda-11.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-75c8502bfb75) |
| [gesv/cusolver_irs_lapack.cu](../sample-reports/cuSOLVER/gesv/cusolver_irs_lapack.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVER.md#sample-397f05bd50ec) |

<a id="module-10"></a>

## cuSOLVERMp

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [mp_getrf_getrs.c](../sample-reports/cuSOLVERMp/mp_getrf_getrs.c.md) | PARTIAL / 6/7 | MPI + RCCL + HIP column-distributed partial-row-pivot LU/solve / MPI + RCCL + HIP column-distributed partial-row-pivot LU/solve；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-eb7f57261b5a) |
| [mp_potrf_potrs.c](../sample-reports/cuSOLVERMp/mp_potrf_potrs.c.md) | PARTIAL / 6/7 | MPI + RCCL + HIP distributed column Cholesky/solve / MPI + RCCL + HIP distributed column Cholesky/solve；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-a678fa558997) |
| [mp_gels.c](../sample-reports/cuSOLVERMp/mp_gels.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-bf9374632fcb) |
| [mp_geqrf.c](../sample-reports/cuSOLVERMp/mp_geqrf.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-a1f07106cb41) |
| [mp_geqrf_orgqr.c](../sample-reports/cuSOLVERMp/mp_geqrf_orgqr.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-dc01537ee369) |
| [mp_gesvd.c](../sample-reports/cuSOLVERMp/mp_gesvd.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-0c5f1a6e102d) |
| [mp_laset.c](../sample-reports/cuSOLVERMp/mp_laset.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-c476e0541dfe) |
| [mp_newton_schulz.cpp](../sample-reports/cuSOLVERMp/mp_newton_schulz.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-c5757bec6a74) |
| [mp_ormqr.c](../sample-reports/cuSOLVERMp/mp_ormqr.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-dbdeaf677ce7) |
| [mp_polar.c](../sample-reports/cuSOLVERMp/mp_polar.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-c4b80b4030ec) |
| [mp_potrf_potrs_fp32.c](../sample-reports/cuSOLVERMp/mp_potrf_potrs_fp32.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-fc6b698ecd98) |
| [mp_potrf_potrs_fp32emulation.c](../sample-reports/cuSOLVERMp/mp_potrf_potrs_fp32emulation.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-42c3786130c5) |
| [mp_syevd.c](../sample-reports/cuSOLVERMp/mp_syevd.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-4b6281b3308b) |
| [mp_sygst.c](../sample-reports/cuSOLVERMp/mp_sygst.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-d191335a554b) |
| [mp_sygvd.c](../sample-reports/cuSOLVERMp/mp_sygvd.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-f12c099adfeb) |
| [mp_sytrd_stedc_ormtr.c](../sample-reports/cuSOLVERMp/mp_sytrd_stedc_ormtr.c.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERMp.md#sample-d04a92fa65d3) |

<a id="module-11"></a>

## cuSOLVERSp2cuDSS

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [csreigs2cuDSS_dcomplex.cpp](../sample-reports/cuSOLVERSp2cuDSS/csreigs2cuDSS_dcomplex.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERSp2cuDSS.md#sample-00e1131c5640) |
| [csreigvsi2cuDSS_double.cpp](../sample-reports/cuSOLVERSp2cuDSS/csreigvsi2cuDSS_double.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERSp2cuDSS.md#sample-5631c84206cc) |
| [cuSolverRf2cuDSS_double.cpp](../sample-reports/cuSOLVERSp2cuDSS/cuSolverRf2cuDSS_double.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERSp2cuDSS.md#sample-1a2693b0dcfb) |
| [cuSolverSp2cuDSS_dcomplex.cpp](../sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_dcomplex.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERSp2cuDSS.md#sample-0ef6c8c7d154) |
| [cuSolverSp2cuDSS_double.cpp](../sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_double.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERSp2cuDSS.md#sample-1309470d706a) |
| [cuSolverSp2cuDSS_float.cpp](../sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_float.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERSp2cuDSS.md#sample-57ac47c76ea2) |
| [cuSolverSp2cuDSS_scomplex.cpp](../sample-reports/cuSOLVERSp2cuDSS/cuSolverSp2cuDSS_scomplex.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSOLVERSp2cuDSS.md#sample-f318ba431d16) |

<a id="module-12"></a>

## cuSPARSE

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [axpby/axpby_example.c](../sample-reports/cuSPARSE/axpby/axpby_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-aaae34a8f576) |
| [bicgstab/bicgstab_example.c](../sample-reports/cuSPARSE/bicgstab/bicgstab_example.c.md) | PASSED / 3/3 | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-7b672be3c57d) |
| [cg/cg_example.c](../sample-reports/cuSPARSE/cg/cg_example.c.md) | PASSED / 3/3 | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-d4519f7f9d73) |
| [coosort/coosort_example.c](../sample-reports/cuSPARSE/coosort/coosort_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-111ec11edd77) |
| [dense2sparse_blockedell/dense2sparse_blockedell_example.c](../sample-reports/cuSPARSE/dense2sparse_blockedell/dense2sparse_blockedell_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-66ee5cea534a) |
| [dense2sparse_csr/dense2sparse_csr_example.c](../sample-reports/cuSPARSE/dense2sparse_csr/dense2sparse_csr_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-d7a333603c96) |
| [gather/gather_example.c](../sample-reports/cuSPARSE/gather/gather_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-d86c56252323) |
| [gpsvInterleavedBatch/gpsvInterleavedBatch_example.c](../sample-reports/cuSPARSE/gpsvInterleavedBatch/gpsvInterleavedBatch_example.c.md) | PASSED / 3/3 | hipSPARSE + hipBLAS / rocSPARSE/rocBLAS；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-91af0c4de917) |
| [graph_capture/graph_capture_example.c](../sample-reports/cuSPARSE/graph_capture/graph_capture_example.c.md) | PASSED / 3/3 | hipSPARSE + HIP Graph / rocSPARSE + HIP runtime；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-25cd87bbbe79) |
| [rot/rot_example.c](../sample-reports/cuSPARSE/rot/rot_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-a17f1bb6df23) |
| [scatter/scatter_example.c](../sample-reports/cuSPARSE/scatter/scatter_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-32e22dc23032) |
| [sddmm_bsr/sddmm_bsr_example.c](../sample-reports/cuSPARSE/sddmm_bsr/sddmm_bsr_example.c.md) | PASSED / 4/4 | hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-bd853bbb07c1) |
| [sddmm_csr/sddmm_csr_example.c](../sample-reports/cuSPARSE/sddmm_csr/sddmm_csr_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-648145fffe3a) |
| [sddmm_csr_batched/sddmm_csr_batched_example.c](../sample-reports/cuSPARSE/sddmm_csr_batched/sddmm_csr_batched_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-7a94387b081a) |
| [sparse2dense_csr/sparse2dense_csr_example.c](../sample-reports/cuSPARSE/sparse2dense_csr/sparse2dense_csr_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-4ad927df8a25) |
| [spgemm/spgemm_example.c](../sample-reports/cuSPARSE/spgemm/spgemm_example.c.md) | PASSED / 2/2 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-37a63823ba10) |
| [spgemm_mem/spgemm_mem_example.c](../sample-reports/cuSPARSE/spgemm_mem/spgemm_mem_example.c.md) | PASSED / 4/4 | HIP GPU budgeted CSR SpGEMM adapter / HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-ba84027eab2d) |
| [spgemm_reuse/spgemm_reuse_example.c](../sample-reports/cuSPARSE/spgemm_reuse/spgemm_reuse_example.c.md) | PASSED / 2/2 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-1f39a4c61231) |
| [spmat_convert/spmat_convert_example.c](../sample-reports/cuSPARSE/spmat_convert/spmat_convert_example.c.md) | PASSED / 4/4 | hipSPARSE Csr2cscEx2 / rocSPARSE/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-03317474d15f) |
| [spmm_blockedell/spmm_blockedell_example.cpp](../sample-reports/cuSPARSE/spmm_blockedell/spmm_blockedell_example.cpp.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-2cd6846f476f) |
| [spmm_coo/spmm_coo_example.c](../sample-reports/cuSPARSE/spmm_coo/spmm_coo_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-2b0dcb6e0069) |
| [spmm_coo_batched/spmm_coo_batched_example.c](../sample-reports/cuSPARSE/spmm_coo_batched/spmm_coo_batched_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-ad3329b1a9d7) |
| [spmm_csr/spmm_csr_example.c](../sample-reports/cuSPARSE/spmm_csr/spmm_csr_example.c.md) | PASSED / 9/9 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-09a6689aea34) |
| [spmm_csr_batched/spmm_csr_batched_example.c](../sample-reports/cuSPARSE/spmm_csr_batched/spmm_csr_batched_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-3aa2e36375d1) |
| [spmm_csr_op/spmm_csr_op_example.c](../sample-reports/cuSPARSE/spmm_csr_op/spmm_csr_op_example.c.md) | PASSED / 3/3 | HIP GPU fused custom SpMM add/mul/epilogue / HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-69dc782d21ed) |
| [spmv_coo/spmv_coo_example.c](../sample-reports/cuSPARSE/spmv_coo/spmv_coo_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-059ef54f2823) |
| [spmv_csr/spmv_csr_example.c](../sample-reports/cuSPARSE/spmv_csr/spmv_csr_example.c.md) | PASSED / 9/9 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-14403cfc55da) |
| [spmv_sell/spmv_sell_example.c](../sample-reports/cuSPARSE/spmv_sell/spmv_sell_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-798b44f56d0d) |
| [spmv_symmetric_csr/spmv_symmetric_example.c](../sample-reports/cuSPARSE/spmv_symmetric_csr/spmv_symmetric_example.c.md) | PASSED / 4/4 | HIP symmetric expansion + rocSPARSE v2 / rocSPARSE/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-fee230e7d2e2) |
| [spmvop_csr/spmv_csr_op_example.c](../sample-reports/cuSPARSE/spmvop_csr/spmv_csr_op_example.c.md) | PASSED / 3/3 | HIP GPU fused custom SpMV epilogue / HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-26a7009f4ab7) |
| [spsm_coo/spsm_coo_example.c](../sample-reports/cuSPARSE/spsm_coo/spsm_coo_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-472ec0c9c7c0) |
| [spsm_csr/spsm_csr_example.c](../sample-reports/cuSPARSE/spsm_csr/spsm_csr_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-e26d84c661ba) |
| [spsv_coo/spsv_coo_example.c](../sample-reports/cuSPARSE/spsv_coo/spsv_coo_example.c.md) | PASSED / 1/1 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-f9bb847786a4) |
| [spsv_csr/spsv_csr_example.c](../sample-reports/cuSPARSE/spsv_csr/spsv_csr_example.c.md) | PASSED / 3/3 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-2e808c70d76e) |
| [spsv_sell/spsv_sell_example.c](../sample-reports/cuSPARSE/spsv_sell/spsv_sell_example.c.md) | PASSED / 4/4 | hipSPARSE + HIP format adapter / rocSPARSE + HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-3b0117f6bcb6) |
| [spvv/spvv_example.c](../sample-reports/cuSPARSE/spvv/spvv_example.c.md) | PASSED / 2/2 | hipSPARSE / rocSPARSE；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-7ec0df125247) |
| [compression/compression_example.cpp](../sample-reports/cuSPARSE/compression/compression_example.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuSPARSE.md#sample-cd94bd1ea4cf) |

<a id="module-13"></a>

## cuSPARSELt

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [matmul/matmul_example.cpp](../sample-reports/cuSPARSELt/matmul/matmul_example.cpp.md) | PASSED / 14/14 | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul / HIP GPU; CPU descriptor/constant-mask setup only；项目 HIP 算法重写 | [日志、范围、源码](support-log-index/cuSPARSELt.md#sample-67e033d8a0a9) |
| [matmul_advanced/matmul_advanced_example.cpp](../sample-reports/cuSPARSELt/matmul_advanced/matmul_advanced_example.cpp.md) | PASSED / 14/14 | project HIP GPU TILE prune + packed 2:4 values/metadata + sparse-only matmul / HIP GPU; CPU descriptor/constant-mask setup only；项目 HIP 算法重写 | [日志、范围、源码](support-log-index/cuSPARSELt.md#sample-9068bb7b1039) |

<a id="module-14"></a>

## cuTENSOR

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [contraction.cu](../sample-reports/cuTENSOR/contraction.cu.md) | PASSED / 3/3 | rocBLAS + HIP / FP32 GEMM and GPU tensor permutations；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-657745510e9b) |
| [contraction_plan_cache.cu](../sample-reports/cuTENSOR/contraction_plan_cache.cu.md) | PASSED / 3/3 | rocBLAS + HIP tiled-plan/cache adapter / rocBLAS/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-94613aa24114) |
| [contraction_trinary.cu](../sample-reports/cuTENSOR/contraction_trinary.cu.md) | PASSED / 3/3 | rocBLAS + HIP tensor adapter / rocBLAS/HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-c3bcffa783e2) |
| [einsum.cu](../sample-reports/cuTENSOR/einsum.cu.md) | PASSED / 3/3 | hipTensor + rocBLAS + HIP / hipTensor/rocBLAS；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-2412685f034d) |
| [elementwise_binary.cu](../sample-reports/cuTENSOR/elementwise_binary.cu.md) | PASSED / 3/3 | hipTensor / hipTensor；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-9692de10a185) |
| [elementwise_permute.cu](../sample-reports/cuTENSOR/elementwise_permute.cu.md) | PASSED / 3/3 | hipTensor / hipTensor；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-a5ef5fdfd94d) |
| [elementwise_permute_padding.cu](../sample-reports/cuTENSOR/elementwise_permute_padding.cu.md) | PASSED / 3/3 | HIP GPU permutation/padding / HIP runtime；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-0d07ff9b05d6) |
| [elementwise_trinary.cu](../sample-reports/cuTENSOR/elementwise_trinary.cu.md) | PASSED / 3/3 | hipTensor / hipTensor；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-b6d62faa53b9) |
| [reduction.cu](../sample-reports/cuTENSOR/reduction.cu.md) | PASSED / 3/3 | hipTensor / hipTensor；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-2d9f2dfd5dee) |
| [blocksparse.cu](../sample-reports/cuTENSOR/blocksparse.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-b1882103d624) |
| [contraction_jit.cu](../sample-reports/cuTENSOR/contraction_jit.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-17bb06d9f674) |
| [python/cutensor/tensorflow/einsum_test.py](../sample-reports/cuTENSOR/python/cutensor/tensorflow/einsum_test.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-2b920a8db2ed) |
| [python/cutensor/torch/einsum_test.py](../sample-reports/cuTENSOR/python/cutensor/torch/einsum_test.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/cuTENSOR.md#sample-904a122a4770) |

<a id="module-15"></a>

## cuTENSORMg

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [contraction_multi_gpu.cu](../sample-reports/cuTENSORMg/contraction_multi_gpu.cu.md) | PASSED / 6/6 | hipBLAS FP32 partitioned contraction + RCCL AllGather; single process with two GPU threads / hipBLAS FP32 partitioned contraction + RCCL AllGather; single process with two GPU threads；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/cuTENSORMg.md#sample-a4fc3e244077) |
| [blog_post.cu](../sample-reports/cuTENSORMg/blog_post.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSORMg.md#sample-b2e8a353479c) |

<a id="module-16"></a>

## cuTENSORMp

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [cutensorMp_contraction.cu](../sample-reports/cuTENSORMp/cutensorMp_contraction.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSORMp.md#sample-f9ce6b5bf2b0) |
| [cutensorMp_redistribute.cu](../sample-reports/cuTENSORMp/cutensorMp_redistribute.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSORMp.md#sample-9dc8b7cf06b8) |
| [cutensorMp_unfold_fold.cu](../sample-reports/cuTENSORMp/cutensorMp_unfold_fold.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/cuTENSORMp.md#sample-4a1d134bc3e2) |

<a id="module-17"></a>

## MathDx/cuBLASDx

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [01_gemm_introduction/introduction_example.cu](../sample-reports/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu.md) | PASSED / 6/6 | HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases) / HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases)；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-855cf663094c) |
| [01_gemm_introduction/introduction_pipeline.cu](../sample-reports/MathDx/cuBLASDx/01_gemm_introduction/introduction_pipeline.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-bc0a6e8de235) |
| [02_gemm_precisions/simple_gemm_fp32.cu](../sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_fp32.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-b400177c3885) |
| [02_gemm_precisions/simple_gemm_fp8.cu](../sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_fp8.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-154a06bbba2b) |
| [02_gemm_precisions/simple_gemm_int8_int8_int32.cu](../sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_int8_int8_int32.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-fa3b35a83c06) |
| [02_gemm_precisions/simple_gemm_mixed_precision.cu](../sample-reports/MathDx/cuBLASDx/02_gemm_precisions/simple_gemm_mixed_precision.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-bbd141ab168b) |
| [03_gemm_complex/simple_gemm_cfp16.cu](../sample-reports/MathDx/cuBLASDx/03_gemm_complex/simple_gemm_cfp16.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-24bb88a4e144) |
| [03_gemm_complex/simple_gemm_std_complex_fp32.cu](../sample-reports/MathDx/cuBLASDx/03_gemm_complex/simple_gemm_std_complex_fp32.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-cb761d3e39f8) |
| [04_gemm_blockdim/blockdim_gemm_fp16.cu](../sample-reports/MathDx/cuBLASDx/04_gemm_blockdim/blockdim_gemm_fp16.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-bf9ad68a5c14) |
| [05_gemm_batched/batched_gemm_fp64.cu](../sample-reports/MathDx/cuBLASDx/05_gemm_batched/batched_gemm_fp64.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-7832547a280b) |
| [06_gemm_leading_dimension/simple_gemm_leading_dimensions.cu](../sample-reports/MathDx/cuBLASDx/06_gemm_leading_dimension/simple_gemm_leading_dimensions.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-68d0de02dcb1) |
| [07_gemm_transform/simple_gemm_transform.cu](../sample-reports/MathDx/cuBLASDx/07_gemm_transform/simple_gemm_transform.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-b33db5bb25cf) |
| [08_gemm_decoupled_io_and_compute/simple_gemm_fp32_decoupled.cu](../sample-reports/MathDx/cuBLASDx/08_gemm_decoupled_io_and_compute/simple_gemm_fp32_decoupled.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-3c30b1e352d5) |
| [09_gemm_custom_layout/simple_gemm_aat.cu](../sample-reports/MathDx/cuBLASDx/09_gemm_custom_layout/simple_gemm_aat.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-27ffbb2fe926) |
| [09_gemm_custom_layout/simple_gemm_custom_layout.cu](../sample-reports/MathDx/cuBLASDx/09_gemm_custom_layout/simple_gemm_custom_layout.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-369ebd6f2093) |
| [10_gemm_block_performance/single_gemm_performance.cu](../sample-reports/MathDx/cuBLASDx/10_gemm_block_performance/single_gemm_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-41f6b4237abb) |
| [11_gemm_device_performance/device_gemm_performance.cu](../sample-reports/MathDx/cuBLASDx/11_gemm_device_performance/device_gemm_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-0a934b9a209b) |
| [12_gemm_device_partial_sums/gemm_device_partial_sums.cu](../sample-reports/MathDx/cuBLASDx/12_gemm_device_partial_sums/gemm_device_partial_sums.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-8a6052cd115d) |
| [13_gemm_fft/gemm_fft.cu](../sample-reports/MathDx/cuBLASDx/13_gemm_fft/gemm_fft.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-2cd09ec3ea30) |
| [13_gemm_fft/gemm_fft_fp16.cu](../sample-reports/MathDx/cuBLASDx/13_gemm_fft/gemm_fft_fp16.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-4323bc0b1903) |
| [13_gemm_fft/gemm_fft_performance.cu](../sample-reports/MathDx/cuBLASDx/13_gemm_fft/gemm_fft_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-83aa91843cc4) |
| [14_gemm_fused/fused_gemm_performance.cu](../sample-reports/MathDx/cuBLASDx/14_gemm_fused/fused_gemm_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-6c8e181be9ac) |
| [14_gemm_fused/gemm_fusion.cu](../sample-reports/MathDx/cuBLASDx/14_gemm_fused/gemm_fusion.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-023e8d556998) |
| [15_nvrtc/nvrtc_gemm.cpp](../sample-reports/MathDx/cuBLASDx/15_nvrtc/nvrtc_gemm.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-a83bb9061fde) |
| [15_nvrtc/nvrtc_trsm.cpp](../sample-reports/MathDx/cuBLASDx/15_nvrtc/nvrtc_trsm.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-091146f1608c) |
| [16_dgemm_emulation/dgemm_emulation.cu](../sample-reports/MathDx/cuBLASDx/16_dgemm_emulation/dgemm_emulation.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-3a9a0d71d1fc) |
| [17_trsm/trsm_block.cu](../sample-reports/MathDx/cuBLASDx/17_trsm/trsm_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-d0ebc4003657) |
| [17_trsm/trsm_thread.cu](../sample-reports/MathDx/cuBLASDx/17_trsm/trsm_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-039e16e8afef) |
| [18_tensor_transform/gemm_conj_transpose.cu](../sample-reports/MathDx/cuBLASDx/18_tensor_transform/gemm_conj_transpose.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-7c63c7424d58) |
| [18_tensor_transform/trsm_conj_transpose.cu](../sample-reports/MathDx/cuBLASDx/18_tensor_transform/trsm_conj_transpose.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-210bba192633) |
| [19_gemm_batched/batched_gemm.cu](../sample-reports/MathDx/cuBLASDx/19_gemm_batched/batched_gemm.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-c63fa2df71f7) |
| [19_gemm_batched/batched_gemm_pipeline.cu](../sample-reports/MathDx/cuBLASDx/19_gemm_batched/batched_gemm_pipeline.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-09da5faa0830) |
| [20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu](../sample-reports/MathDx/cuBLASDx/20_dgemm_emulation_pipeline/dgemm_emulation_pipeline.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-984003cda864) |
| [21_sgemm_emulation_pipeline/sgemm_emulation_pipeline.cu](../sample-reports/MathDx/cuBLASDx/21_sgemm_emulation_pipeline/sgemm_emulation_pipeline.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuBLASDx.md#sample-0056822eaa8a) |

<a id="module-18"></a>

## MathDx/cuFFTDx

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [02_simple_fft_block/simple_fft_block.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block.cu.md) | PASSED / 6/6 | HIP cooperative device radix-2 C2C FFT / HIP cooperative device radix-2 C2C FFT；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-d2fdfd837938) |
| [00_introduction_example/introduction_example.cu](../sample-reports/MathDx/cuFFTDx/00_introduction_example/introduction_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-93fd8975fa89) |
| [01_simple_fft_thread/simple_fft_thread.cu](../sample-reports/MathDx/cuFFTDx/01_simple_fft_thread/simple_fft_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-e5576766561c) |
| [01_simple_fft_thread/simple_fft_thread_fp16.cu](../sample-reports/MathDx/cuFFTDx/01_simple_fft_thread/simple_fft_thread_fp16.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-da5f878a62fa) |
| [01_simple_fft_thread/simple_fft_thread_lto.cu](../sample-reports/MathDx/cuFFTDx/01_simple_fft_thread/simple_fft_thread_lto.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-a2810159e029) |
| [02_simple_fft_block/simple_fft_block_block_dim.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_block_dim.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-ab9e7825f44c) |
| [02_simple_fft_block/simple_fft_block_c2r.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_c2r.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-875113afd329) |
| [02_simple_fft_block/simple_fft_block_c2r_fp16.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_c2r_fp16.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-31150cc1cc08) |
| [02_simple_fft_block/simple_fft_block_c2r_lto.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_c2r_lto.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-7aa85c0788b5) |
| [02_simple_fft_block/simple_fft_block_cub_io.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_cub_io.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-9d1a23b48cd9) |
| [02_simple_fft_block/simple_fft_block_fp16.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_fp16.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-f047e6038bcb) |
| [02_simple_fft_block/simple_fft_block_half2.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_half2.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-a1611cca575b) |
| [02_simple_fft_block/simple_fft_block_r2c.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_r2c.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-30e51b8d3fd6) |
| [02_simple_fft_block/simple_fft_block_r2c_fp16.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_r2c_fp16.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-e422807c5f28) |
| [02_simple_fft_block/simple_fft_block_shared.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_shared.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-4a145373394c) |
| [02_simple_fft_block/simple_fft_block_std_complex.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block_std_complex.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-8def706505e1) |
| [03_block_fft_performance/block_fft_lto_ptx_performance.cu](../sample-reports/MathDx/cuFFTDx/03_block_fft_performance/block_fft_lto_ptx_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-50a0979bfb3c) |
| [03_block_fft_performance/block_fft_performance.cu](../sample-reports/MathDx/cuFFTDx/03_block_fft_performance/block_fft_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-65b219b9a1e8) |
| [03_block_fft_performance/block_fft_performance_many.cu](../sample-reports/MathDx/cuFFTDx/03_block_fft_performance/block_fft_performance_many.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-28533b4d52f7) |
| [04_nvrtc_fft/nvrtc_fft_block.cu](../sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-1647782e18e0) |
| [04_nvrtc_fft/nvrtc_fft_block_lto.cu](../sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_block_lto.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-98ee227a90f5) |
| [04_nvrtc_fft/nvrtc_fft_thread.cu](../sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-0edc6159d6a5) |
| [04_nvrtc_fft/nvrtc_fft_thread_lto.cu](../sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_fft_thread_lto.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-d4280d71bb18) |
| [04_nvrtc_fft/nvrtc_query_autotune_lto.cu](../sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_query_autotune_lto.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-a3590dd96d52) |
| [04_nvrtc_fft/nvrtc_query_database_fft_block.cu](../sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_query_database_fft_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-c0865e112a31) |
| [04_nvrtc_fft/nvrtc_query_database_fft_block_lto.cu](../sample-reports/MathDx/cuFFTDx/04_nvrtc_fft/nvrtc_query_database_fft_block_lto.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-9bf1943fff2d) |
| [05_fft_Xd/fft_2d.cu](../sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-143781f79e0d) |
| [05_fft_Xd/fft_2d_r2c_c2r.cu](../sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d_r2c_c2r.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-b3e4a061577d) |
| [05_fft_Xd/fft_2d_single_kernel.cu](../sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d_single_kernel.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-e228a5922093) |
| [05_fft_Xd/fft_2d_single_kernel_block_dim.cu](../sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_2d_single_kernel_block_dim.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-1f82ecca2d16) |
| [05_fft_Xd/fft_3d.cu](../sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_3d.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-b7f9bd4b5963) |
| [05_fft_Xd/fft_3d_box_single_block.cu](../sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_3d_box_single_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-1c4792bd93e1) |
| [05_fft_Xd/fft_3d_cube_single_block.cu](../sample-reports/MathDx/cuFFTDx/05_fft_Xd/fft_3d_cube_single_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-d0cc8498871a) |
| [06_convolution/convolution.cu](../sample-reports/MathDx/cuFFTDx/06_convolution/convolution.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-9da06195a73e) |
| [06_convolution/convolution_padded.cu](../sample-reports/MathDx/cuFFTDx/06_convolution/convolution_padded.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-a90d4148a3c5) |
| [06_convolution/convolution_performance.cu](../sample-reports/MathDx/cuFFTDx/06_convolution/convolution_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-576c07210947) |
| [06_convolution/convolution_r2c_c2r.cu](../sample-reports/MathDx/cuFFTDx/06_convolution/convolution_r2c_c2r.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-252813cbfd54) |
| [07_convolution_3d/convolution_3d.cu](../sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-5db60c688928) |
| [07_convolution_3d/convolution_3d_c2r.cu](../sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_c2r.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-008b8376198a) |
| [07_convolution_3d/convolution_3d_padded.cu](../sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_padded.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-fb401ce3a95f) |
| [07_convolution_3d/convolution_3d_padded_r2c.cu](../sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_padded_r2c.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-d1ab39c88419) |
| [07_convolution_3d/convolution_3d_r2c.cu](../sample-reports/MathDx/cuFFTDx/07_convolution_3d/convolution_3d_r2c.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-337109322651) |
| [08_mixed_precision/mixed_precision_fft_1d.cu](../sample-reports/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_1d.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-421b9fecce0a) |
| [08_mixed_precision/mixed_precision_fft_2d.cu](../sample-reports/MathDx/cuFFTDx/08_mixed_precision/mixed_precision_fft_2d.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-443982087e58) |
| [09_introduction_lto_example/introduction_lto_example.cu](../sample-reports/MathDx/cuFFTDx/09_introduction_lto_example/introduction_lto_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-17c6597bc5d1) |
| [09_introduction_lto_example/lto_query_database_example.cu](../sample-reports/MathDx/cuFFTDx/09_introduction_lto_example/lto_query_database_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-9e3b59a8f0b8) |
| [10_cufft_device_api_example/cufft_device_api_example.cu](../sample-reports/MathDx/cuFFTDx/10_cufft_device_api_example/cufft_device_api_example.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-aa1fc93f46fc) |
| [10_cufft_device_api_example/cufft_device_api_lto_helper/cufft_device_api_lto_helper.cpp](../sample-reports/MathDx/cuFFTDx/10_cufft_device_api_example/cufft_device_api_lto_helper/cufft_device_api_lto_helper.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-79ee72494ec4) |
| [lto_helper/cufftdx_cufft_lto_helper.cpp](../sample-reports/MathDx/cuFFTDx/lto_helper/cufftdx_cufft_lto_helper.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuFFTDx.md#sample-9110ae453e0c) |

<a id="module-19"></a>

## MathDx/cuRANDDx

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [01_introduction/philox_thread_api.cu](../sample-reports/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu.md) | PARTIAL / 6/7 | rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal / rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/MathDx__cuRANDDx.md#sample-fc4bf2c80a2c) |
| [02_thread_api/mrg_two_distributions_thread_api.cu](../sample-reports/MathDx/cuRANDDx/02_thread_api/mrg_two_distributions_thread_api.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuRANDDx.md#sample-19025ba95aec) |
| [02_thread_api/pcg_thread_api.cu](../sample-reports/MathDx/cuRANDDx/02_thread_api/pcg_thread_api.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuRANDDx.md#sample-dfe2406dc8df) |
| [02_thread_api/philox_random_bits_thread_api.cu](../sample-reports/MathDx/cuRANDDx/02_thread_api/philox_random_bits_thread_api.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuRANDDx.md#sample-b517ef92c787) |
| [02_thread_api/sobol_thread_api.cu](../sample-reports/MathDx/cuRANDDx/02_thread_api/sobol_thread_api.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuRANDDx.md#sample-46c3ef555ad7) |
| [02_thread_api/xorwow_init_and_generate_thread_api.cu](../sample-reports/MathDx/cuRANDDx/02_thread_api/xorwow_init_and_generate_thread_api.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuRANDDx.md#sample-e41d04c13954) |
| [03_nvrtc/nvrtc_pcg_thread_api.cpp](../sample-reports/MathDx/cuRANDDx/03_nvrtc/nvrtc_pcg_thread_api.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuRANDDx.md#sample-24d71f636117) |

<a id="module-20"></a>

## MathDx/cuSolverDx

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [00_Introduction/posv_batched_block.cu](../sample-reports/MathDx/cuSolverDx/00_Introduction/posv_batched_block.cu.md) | PASSED / 10/10 | HIP caller-kernel cooperative complex FP64 Cholesky and solve / project HIP device algorithm；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-83c8ed9c775f) |
| [01_Linear_Solve/getrf_partial_pivot_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/getrf_partial_pivot_block.cu.md) | PASSED / 10/10 | HIP caller-kernel cooperative complex FP32 partial-pivot LU / project HIP device algorithm；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-0664c6319873) |
| [01_Linear_Solve/potrf_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_block.cu.md) | PASSED / 6/6 | HIP cooperative device complex FP64 upper Cholesky, shared LDA33 / HIP cooperative device complex FP64 upper Cholesky, shared LDA33；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-0865ab8c293e) |
| [07_BLAS/trsm_batched_block.cu](../sample-reports/MathDx/cuSolverDx/07_BLAS/trsm_batched_block.cu.md) | PASSED / 9/9 | HIP caller-kernel cooperative real FP64 right/lower triangular solve / project HIP device algorithm；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-efb59a683d6c) |
| [01_Linear_Solve/gesv_batched_partial_pivot_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_partial_pivot_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-00dcb1e022dd) |
| [01_Linear_Solve/gesv_batched_partial_pivot_thread.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_partial_pivot_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-6815bc824613) |
| [01_Linear_Solve/gesv_batched_wo_pivot_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_wo_pivot_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-bcfbf44fd3d1) |
| [01_Linear_Solve/gesv_batched_wo_pivot_thread.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gesv_batched_wo_pivot_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-98876e038a17) |
| [01_Linear_Solve/getrf_wo_pivot_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/getrf_wo_pivot_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-1201bd6c560b) |
| [01_Linear_Solve/gtsv_batched_wo_pivot_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gtsv_batched_wo_pivot_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-4f0bc3636659) |
| [01_Linear_Solve/gtsv_batched_wo_pivot_thread.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/gtsv_batched_wo_pivot_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-9525cc0be866) |
| [01_Linear_Solve/posv_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/posv_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-c1cc5b3edd0d) |
| [01_Linear_Solve/potrf_batched_cluster.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_batched_cluster.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-ea8c5a8bf9c1) |
| [01_Linear_Solve/potrf_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-51d4e1537dff) |
| [01_Linear_Solve/potrf_runtime_ld_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_runtime_ld_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-3395e40d5343) |
| [02_Least_Squares/gels_batched_block.cu](../sample-reports/MathDx/cuSolverDx/02_Least_Squares/gels_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-f30d33a26137) |
| [02_Least_Squares/gels_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/02_Least_Squares/gels_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-b79b60983556) |
| [03_Orthogonal_Factors/geqrf_batched_block.cu](../sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/geqrf_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-5bc91fe699f1) |
| [03_Orthogonal_Factors/geqrf_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/geqrf_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-154957cfddcb) |
| [03_Orthogonal_Factors/ungqr_batched_block.cu](../sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/ungqr_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-101ed28831d4) |
| [03_Orthogonal_Factors/ungqr_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/ungqr_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-8d731db9690a) |
| [03_Orthogonal_Factors/unmqr_batched_block.cu](../sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/unmqr_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-395c32ac74a0) |
| [03_Orthogonal_Factors/unmqr_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/03_Orthogonal_Factors/unmqr_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-745c1799dfbb) |
| [04_Symmetric_Eigenvalues/heev_batched_block.cu](../sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/heev_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-f6016e493fe4) |
| [04_Symmetric_Eigenvalues/heev_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/heev_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-eda5e3360fe6) |
| [04_Symmetric_Eigenvalues/hegst_batched_block.cu](../sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/hegst_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-8d67f0b10d14) |
| [04_Symmetric_Eigenvalues/hegst_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/hegst_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-7e91edfae866) |
| [04_Symmetric_Eigenvalues/hegv_batched_block.cu](../sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/hegv_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-b740abbe6e17) |
| [04_Symmetric_Eigenvalues/htev_batched_block.cu](../sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/htev_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-7de1aa533c98) |
| [04_Symmetric_Eigenvalues/htev_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/04_Symmetric_Eigenvalues/htev_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-fe313f796cd9) |
| [05_Singular_Value_Decomposition/bdsvd_batched_block.cu](../sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/bdsvd_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-c502d8214f4f) |
| [05_Singular_Value_Decomposition/bdsvd_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/bdsvd_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-c2f301c6d1d3) |
| [05_Singular_Value_Decomposition/gesvd_batched_block.cu](../sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/gesvd_batched_block.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-5e3eb37db107) |
| [05_Singular_Value_Decomposition/gesvd_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/05_Singular_Value_Decomposition/gesvd_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-7705822e4669) |
| [07_BLAS/trsm_batched_thread.cu](../sample-reports/MathDx/cuSolverDx/07_BLAS/trsm_batched_thread.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-db47304fb83d) |
| [07_BLAS/trsm_batched_thread_advanced.cu](../sample-reports/MathDx/cuSolverDx/07_BLAS/trsm_batched_thread_advanced.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-7e5b59ac6e77) |
| [08_NVRTC/nvrtc_potrs.cpp](../sample-reports/MathDx/cuSolverDx/08_NVRTC/nvrtc_potrs.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-4b3229f57517) |
| [09_Performance/geqrf_batched_performance.cu](../sample-reports/MathDx/cuSolverDx/09_Performance/geqrf_batched_performance.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-3c1ae0d64366) |
| [10_Advanced/blocked_potrf.cu](../sample-reports/MathDx/cuSolverDx/10_Advanced/blocked_potrf.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-92588fd3a90a) |
| [10_Advanced/cga_blocked_potrf_right_looking.cu](../sample-reports/MathDx/cuSolverDx/10_Advanced/cga_blocked_potrf_right_looking.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-62b7c932b394) |
| [10_Advanced/cga_tsqrhr.cu](../sample-reports/MathDx/cuSolverDx/10_Advanced/cga_tsqrhr.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-7c6b80426285) |
| [10_Advanced/reg_least_squares.cu](../sample-reports/MathDx/cuSolverDx/10_Advanced/reg_least_squares.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__cuSolverDx.md#sample-319c9eadbb57) |

<a id="module-21"></a>

## MathDx/libmathdx

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [cublasdx.cpp](../sample-reports/MathDx/libmathdx/cublasdx.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-ce215d0f6734) |
| [cublasdx_pipeline.cpp](../sample-reports/MathDx/libmathdx/cublasdx_pipeline.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-0ad67f358341) |
| [cublasdx_pipelining_callback.cpp](../sample-reports/MathDx/libmathdx/cublasdx_pipelining_callback.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-e3a1fba72d07) |
| [cublasdx_tensor.cpp](../sample-reports/MathDx/libmathdx/cublasdx_tensor.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-f720194c607c) |
| [cufftdx.cpp](../sample-reports/MathDx/libmathdx/cufftdx.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-40dfe9e6d7eb) |
| [cufftdx_heuristics.cpp](../sample-reports/MathDx/libmathdx/cufftdx_heuristics.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-cb6cfb884060) |
| [curanddx.cpp](../sample-reports/MathDx/libmathdx/curanddx.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-44810480321f) |
| [cusolverdx_potrf.cpp](../sample-reports/MathDx/libmathdx/cusolverdx_potrf.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-3401a8be4fee) |
| [cusolverdx_potrs.cpp](../sample-reports/MathDx/libmathdx/cusolverdx_potrs.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-1b625f95224d) |
| [cusolverdx_trsm.cpp](../sample-reports/MathDx/libmathdx/cusolverdx_trsm.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-78dbe9e54a88) |
| [nvcompdx.cpp](../sample-reports/MathDx/libmathdx/nvcompdx.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-de91473ad71f) |
| [nvcompdx_batch.cpp](../sample-reports/MathDx/libmathdx/nvcompdx_batch.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__libmathdx.md#sample-b3338e111c71) |

<a id="module-22"></a>

## MathDx/nvCOMPDx

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [01_introduction/lz4_gpu_compression_introduction.cu](../sample-reports/MathDx/nvCOMPDx/01_introduction/lz4_gpu_compression_introduction.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__nvCOMPDx.md#sample-a21ecd9ea50f) |
| [02_lz4_gpu/lz4_gpu_compression_decompression.cu](../sample-reports/MathDx/nvCOMPDx/02_lz4_gpu/lz4_gpu_compression_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__nvCOMPDx.md#sample-ee2422228ee4) |
| [03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu](../sample-reports/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_cpu_compression_gpu_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__nvCOMPDx.md#sample-e45b82a92729) |
| [03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu](../sample-reports/MathDx/nvCOMPDx/03_lz4_gpu_and_cpu/lz4_gpu_compression_cpu_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__nvCOMPDx.md#sample-74807902a05a) |
| [04_ans_gpu/ans_gpu_compression_decompression.cu](../sample-reports/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_compression_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__nvCOMPDx.md#sample-b6720eca76c0) |
| [04_ans_gpu/ans_gpu_decompression_reduction.cu](../sample-reports/MathDx/nvCOMPDx/04_ans_gpu/ans_gpu_decompression_reduction.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__nvCOMPDx.md#sample-78c90f8d7bfb) |
| [05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu](../sample-reports/MathDx/nvCOMPDx/05_lz4_cpu_and_nvrtc/lz4_cpu_compression_nvrtc_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/MathDx__nvCOMPDx.md#sample-e5affc36677a) |

<a id="module-23"></a>

## NPP

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp](../sample-reports/NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp.md) | PASSED / 37/37 | Project HIP equal-value 8-connected union/find + hierarchical GPU prefix-scan compression / project HIP CCL；EXACT_CPU_PARTITION_ARBITRARY_VENDOR_IDS | [日志、范围、源码](support-log-index/NPP.md#sample-234b64d6ff2e) |
| [distanceTransform/distanceTransform.cpp](../sample-reports/NPP/distanceTransform/distanceTransform.cpp.md) | PASSED / 6/6 | HIP exact separable Euclidean distance/Voronoi/integer truncation kernels / HIP exact separable Euclidean distance/Voronoi/integer truncation kernels；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/NPP.md#sample-d91dd1bb00e8) |
| [findContour/findContour.cpp](../sample-reports/NPP/findContour/findContour.cpp.md) | PASSED / 31/31 | Project HIP equal-value 8-connected CCL + directed cell-edge loops + GPU ordering and geometry rasterization / project HIP contour geometry；ALGORITHM_VARIANT_EXACT_PROJECT_GEOMETRY | [日志、范围、源码](support-log-index/NPP.md#sample-6e9875bedc70) |
| [nppCanny/npp_canny_simple.cpp](../sample-reports/NPP/nppCanny/npp_canny_simple.cpp.md) | PASSED / 30/30 | HIP C3 Sobel/NMS/GPU union-find hysteresis + OpenCV file IO/CPU comparisons / project HIP classical C3 Canny；ALGORITHM_VARIANT_C3_CLASSICAL_HYSTERESIS | [日志、范围、源码](support-log-index/NPP.md#sample-3348e80044c5) |
| [nppCanny/npp_canny_simple.py](../sample-reports/NPP/nppCanny/npp_canny_simple.py.md) | PASSED / 30/30 | HIP C3 Sobel/NMS/GPU union-find hysteresis + OpenCV file IO/CPU comparisons + ROCm Torch / project HIP classical C3 Canny；ALGORITHM_VARIANT_C3_CLASSICAL_HYSTERESIS | [日志、范围、源码](support-log-index/NPP.md#sample-46f944149acb) |
| [templateMatching/templateMatching.cpp](../sample-reports/NPP/templateMatching/templateMatching.cpp.md) | PASSED / 9/9 | HIP NCC/full original CLI/RAW input/PGM annotation/HIP-event timing / project HIP kernels；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/NPP.md#sample-7ecae8272f98) |
| [houghLines/houghLines.cpp](../sample-reports/NPP/houghLines/houghLines.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/NPP.md#sample-2fad73bf731b) |
| [opencvBenchmark/opencvBenchmark.cpp](../sample-reports/NPP/opencvBenchmark/opencvBenchmark.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/NPP.md#sample-d17ea2c018b5) |
| [watershedSegmentation/watershedSegmentation.cpp](../sample-reports/NPP/watershedSegmentation/watershedSegmentation.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/NPP.md#sample-eb94340a73f3) |

<a id="module-24"></a>

## NPP+

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp](../sample-reports/NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp.md) | PASSED / 37/37 | Project HIP equal-value 8-connected union/find + hierarchical GPU prefix-scan compression / project HIP CCL；EXACT_CPU_PARTITION_ARBITRARY_VENDOR_IDS | [日志、范围、源码](support-log-index/NPP+.md#sample-bfdab826030c) |
| [cannyEdgeDetectorPython/cannyEdgeDetector.py](../sample-reports/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py.md) | PASSED / 36/36 | Project HIP Canny + ROCm Torch (C1 Sobel3/L2/local threshold) / project HIP image C ABI；ALGORITHM_VARIANT | [日志、范围、源码](support-log-index/NPP+.md#sample-bcaff07a3997) |
| [distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp](../sample-reports/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp.md) | PASSED / 40/40 | Project HIP exact unsigned EDT + compact threshold-crossing signed site set + GPU FP64 search, deterministic Voronoi and visualization / project HIP distance transform；ALGORITHM_VARIANT_EXACT_PROJECT_TYPED_SDF | [日志、范围、源码](support-log-index/NPP+.md#sample-3305e6d9970b) |
| [findContour/findContourNPPPlus.cpp](../sample-reports/NPP+/findContour/findContourNPPPlus.cpp.md) | PASSED / 31/31 | Project HIP equal-value 8-connected CCL + directed cell-edge loops + GPU ordering and geometry rasterization / project HIP contour geometry；ALGORITHM_VARIANT_EXACT_PROJECT_GEOMETRY | [日志、范围、源码](support-log-index/NPP+.md#sample-dbe80853dcbe) |
| [floodFill/floodFillVariousRegionTypesNPPPlus.cpp](../sample-reports/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp.md) | PARTIAL / 6/7 | HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata / HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata；库 API 迁移 + 执行语义适配 | [日志、范围、源码](support-log-index/NPP+.md#sample-8ababedf979d) |
| [watershedSegmentation/watershedSegmentationNPPPlus.cpp](../sample-reports/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/NPP+.md#sample-cd89abdb2c1f) |

<a id="module-25"></a>

## nvJPEG

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [Image-Resize-WaterMark/imageResizeWatermark.cpp](../sample-reports/nvJPEG/Image-Resize-WaterMark/imageResizeWatermark.cpp.md) | PARTIAL / 7/8 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo；GPU 实现 + 明确标注的 CPU 阶段 | [日志、范围、源码](support-log-index/nvJPEG.md#sample-9e68524b388a) |
| [Image-Resize/imageResize.cpp](../sample-reports/nvJPEG/Image-Resize/imageResize.cpp.md) | PARTIAL / 7/8 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo；GPU 实现 + 明确标注的 CPU 阶段 | [日志、范围、源码](support-log-index/nvJPEG.md#sample-ba8320f54095) |
| [nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp](../sample-reports/nvJPEG/nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp.md) | PARTIAL / 7/9 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo；GPU 实现 + 明确标注的 CPU 阶段 | [日志、范围、源码](support-log-index/nvJPEG.md#sample-c19023c1e1d4) |
| [nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp](../sample-reports/nvJPEG/nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp.md) | PARTIAL / 7/9 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo；GPU 实现 + 明确标注的 CPU 阶段 | [日志、范围、源码](support-log-index/nvJPEG.md#sample-f846e59c86c3) |
| [nvJPEG-Decoder/nvjpegDecoder.cpp](../sample-reports/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp.md) | PARTIAL / 7/8 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo；GPU 实现 + 明确标注的 CPU 阶段 | [日志、范围、源码](support-log-index/nvJPEG.md#sample-340e3057571d) |
| [nvJPEG-Decoder/tests/test_decoder.py](../sample-reports/nvJPEG/nvJPEG-Decoder/tests/test_decoder.py.md) | PARTIAL / 7/8 | rocJPEG + HIP layout/ROI/Lanczos/watermark + explicit libjpeg CPU fallback/encode / rocJPEG/HIP runtime + libjpeg-turbo；GPU 实现 + 明确标注的 CPU 阶段 | [日志、范围、源码](support-log-index/nvJPEG.md#sample-682072b0c8fa) |
| [nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp](../sample-reports/nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvJPEG.md#sample-1745f35191ec) |

<a id="module-26"></a>

## nvJPEG2000

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp](../sample-reports/nvJPEG2000/nvJPEG2000-Decoder-Pipelined/nvjpeg2k_dec_pipelined.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvJPEG2000.md#sample-dba24802126c) |
| [nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp](../sample-reports/nvJPEG2000/nvJPEG2000-Decoder-Tile-Partial/nvjpeg2k_decode_tile_partial.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvJPEG2000.md#sample-13363bd1435d) |
| [nvJPEG2000-Decoder/nvjpeg2k_decode.cpp](../sample-reports/nvJPEG2000/nvJPEG2000-Decoder/nvjpeg2k_decode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvJPEG2000.md#sample-f4ce4e945dd0) |
| [nvJPEG2000-Encoder/nvjpeg2k_encode.cpp](../sample-reports/nvJPEG2000/nvJPEG2000-Encoder/nvjpeg2k_encode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvJPEG2000.md#sample-d41aa295cf16) |

<a id="module-27"></a>

## nvTIFF

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp](../sample-reports/nvTIFF/nvTIFF-Batched-Region-Decode/nvtiff_batched_region_decode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvTIFF.md#sample-d43dce65abbb) |
| [nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp](../sample-reports/nvTIFF/nvTIFF-Decode-Encode/nvtiff_decode_encode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvTIFF.md#sample-f34554c3d741) |
| [nvTIFF-Decode/nvtiff_decode.cpp](../sample-reports/nvTIFF/nvTIFF-Decode/nvtiff_decode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvTIFF.md#sample-789f9d84b850) |
| [nvTIFF-Encode-Options/nvtiff_encode_options.cpp](../sample-reports/nvTIFF/nvTIFF-Encode-Options/nvtiff_encode_options.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvTIFF.md#sample-4969ed168132) |
| [nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp](../sample-reports/nvTIFF/nvTIFF-GeoTIFF-Decode-Encode/nvtiff_geotiff_decode_encode.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvTIFF.md#sample-218b162f3ac4) |
| [nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp](../sample-reports/nvTIFF/nvTIFF-Image-Info-Multi-Image/nvtiff_image_info.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvTIFF.md#sample-4f237c7e5524) |

<a id="module-28"></a>

## nvCOMP

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [benchmarks/benchmark_crc32.cpp](../sample-reports/nvCOMP/benchmarks/benchmark_crc32.cpp.md) | PASSED / 8/8 | HIP + hipRAND + project segmented IEEE CRC32/GPU GF2 search / project HIP segmented CRC/GF2 backend；原始 benchmark 框架 + 项目 HIP CRC 算法 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-8415662e606e) |
| [examples/high_level_quickstart_example.cpp](../sample-reports/nvCOMP/examples/high_level_quickstart_example.cpp.md) | PASSED / 8/8 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-eb626e77bd0e) |
| [examples/low_level_quickstart_example.cpp](../sample-reports/nvCOMP/examples/low_level_quickstart_example.cpp.md) | PASSED / 8/8 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-ca0296bde2fe) |
| [examples/lz4_cpu_compression.cu](../sample-reports/nvCOMP/examples/lz4_cpu_compression.cu.md) | PASSED / 8/8 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-9b0a4172fece) |
| [examples/lz4_cpu_decompression.cu](../sample-reports/nvCOMP/examples/lz4_cpu_decompression.cu.md) | PASSED / 8/8 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-226ac6261a50) |
| [examples/nvcomp_crc32.cu](../sample-reports/nvCOMP/examples/nvcomp_crc32.cu.md) | PASSED / 11/11 | project HIP IEEE/PKZIP CRC32; CPU file I/O and reference / HIP GPU CRC32 kernel；改用 AMD 库重写算法流程 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-1dbba0759725) |
| [examples/snappy_cpu_compression.cu](../sample-reports/nvCOMP/examples/snappy_cpu_compression.cu.md) | PASSED / 8/8 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-26bca052ac7c) |
| [examples/snappy_cpu_decompression.cu](../sample-reports/nvCOMP/examples/snappy_cpu_decompression.cu.md) | PASSED / 8/8 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-2701f65abaac) |
| [benchmarks/benchmark_lz4_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_lz4_chunked.cu.md) | PARTIAL / 8/9 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-92d2430eb6bf) |
| [benchmarks/benchmark_snappy_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_snappy_chunked.cu.md) | PARTIAL / 8/9 | hipCOMP LZ4/Snappy + CPU liblz4/Snappy + HIP checked stream/CRC manager adapter / hipCOMP/HIP runtime + independent CPU codecs；生态库 + 项目 HIP 实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-702c69271dba) |
| [benchmarks/benchmark_ans_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_ans_chunked.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-af9cbb05aa19) |
| [benchmarks/benchmark_bitcomp_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_bitcomp_chunked.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-7ae591d8f16f) |
| [benchmarks/benchmark_bitcomp_cpu.cu](../sample-reports/nvCOMP/benchmarks/benchmark_bitcomp_cpu.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-46ab73461b73) |
| [benchmarks/benchmark_cascaded_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_cascaded_chunked.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-e4429a97bfd6) |
| [benchmarks/benchmark_deflate_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_deflate_chunked.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-69ac6cb00761) |
| [benchmarks/benchmark_gdeflate_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_gdeflate_chunked.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-1b505f24a1e1) |
| [benchmarks/benchmark_gdeflate_cpu.cpp](../sample-reports/nvCOMP/benchmarks/benchmark_gdeflate_cpu.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-545f82fca028) |
| [benchmarks/benchmark_gzip_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_gzip_chunked.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-493118e8aafe) |
| [benchmarks/benchmark_gzip_streaming.cpp](../sample-reports/nvCOMP/benchmarks/benchmark_gzip_streaming.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-a2dc2173aaa9) |
| [benchmarks/benchmark_python.py](../sample-reports/nvCOMP/benchmarks/benchmark_python.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-55c95f36fe4e) |
| [benchmarks/benchmark_zstd_chunked.cu](../sample-reports/nvCOMP/benchmarks/benchmark_zstd_chunked.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-aa18045b6d63) |
| [examples/bitcomp_native_lossy.cu](../sample-reports/nvCOMP/examples/bitcomp_native_lossy.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-fef17aae178b) |
| [examples/deflate_cpu_compression.cu](../sample-reports/nvCOMP/examples/deflate_cpu_compression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-6ac99d07d634) |
| [examples/deflate_cpu_decompression.cu](../sample-reports/nvCOMP/examples/deflate_cpu_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-ec8fea4603e7) |
| [examples/gdeflate_cpu_compression.cu](../sample-reports/nvCOMP/examples/gdeflate_cpu_compression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-5df6b0280f28) |
| [examples/gdeflate_cpu_decompression.cu](../sample-reports/nvCOMP/examples/gdeflate_cpu_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-200fefb61fbc) |
| [examples/gzip_gpu_compression.cu](../sample-reports/nvCOMP/examples/gzip_gpu_compression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-a92b60029444) |
| [examples/gzip_gpu_decompression.cu](../sample-reports/nvCOMP/examples/gzip_gpu_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-6c531650299a) |
| [examples/lz4_cpu_compression_high_level.cpp](../sample-reports/nvCOMP/examples/lz4_cpu_compression_high_level.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-d1108ee6ec78) |
| [examples/nvcomp_gds.cu](../sample-reports/nvCOMP/examples/nvcomp_gds.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-7ff325d427c4) |
| [examples/zstd_cpu_compression.cu](../sample-reports/nvCOMP/examples/zstd_cpu_compression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-8622e37d2998) |
| [examples/zstd_cpu_decompression.cu](../sample-reports/nvCOMP/examples/zstd_cpu_decompression.cu.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvCOMP.md#sample-7373ea9b50c3) |

<a id="module-29"></a>

## nvMatmulHeuristics

| 样例 / 详情 | 状态 / 用例 | 实际库与实现方式 | 详细日志与范围 |
| --- | --- | --- | --- |
| [1_gemm_heuristics.cpp](../sample-reports/nvMatmulHeuristics/1_gemm_heuristics.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvMatmulHeuristics.md#sample-f5f08745ba56) |
| [2_discovery.cpp](../sample-reports/nvMatmulHeuristics/2_discovery.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvMatmulHeuristics.md#sample-9585c24af291) |
| [3_energy_discovery.cpp](../sample-reports/nvMatmulHeuristics/3_energy_discovery.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvMatmulHeuristics.md#sample-fc516d1ec48d) |
| [4_runtime_estimation.cpp](../sample-reports/nvMatmulHeuristics/4_runtime_estimation.cpp.md) | FAILED / 0/2 | 尚无已验证使用库；库 API 迁移 | [日志、范围、源码](support-log-index/nvMatmulHeuristics.md#sample-fb5849f1038a) |
| [5_get_configs.py](../sample-reports/nvMatmulHeuristics/5_get_configs.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/nvMatmulHeuristics.md#sample-95c23f8d3a0a) |
| [6_get_configs_ex.py](../sample-reports/nvMatmulHeuristics/6_get_configs_ex.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/nvMatmulHeuristics.md#sample-0bf631378227) |
| [7_smem_carveout.py](../sample-reports/nvMatmulHeuristics/7_smem_carveout.py.md) | FAILED / 0/2 | 尚无已验证使用库；语言绑定尚未实现 | [日志、范围、源码](support-log-index/nvMatmulHeuristics.md#sample-8d119ba9fc57) |

## 原始记录与复现

[构建与复现](../usage.md) · [源码与输入身份](../source-tree.json) · [开发与实验历史归档](../history/README.md)

重新生成：`python3 tools/migration/render.py`（同时更新首页、总表和 JSON）。支持结论来自原始清单及验收证据。
