# 算子支持与统计口径

## 已验收算子与验证范围

**18 个模块已有整例通过，覆盖 117 个按模块去重的算子/功能族，对应 231 个通过的样例入口。**

计数按数学算子或原例核心功能归并；同模块的精度、尺寸、语言、batch、存储格式和算法变体不重复增加算子数。例如 cuRAND 是 4 种分布、36 个 generator/distribution profile；cuDSS simple 的 3 种语言入口算 1 个功能族。跨模块总数保留不同库接口的实现，GEMM 可分别出现在 cuBLAS 与 cuBLASLt。每个族至少有一个通过独立验收的样例，支持范围限于下表和逐例 required cases。

| 模块 | 已验收算子/功能族数 | 已验收算子/功能 | 通过样例 | 验证范围 |
| --- | ---: | --- | ---: | --- |
| [cuBLAS](../../cuBLAS/README.md) | 52 | `amax`、`amin`、`asum`、`axpy`、`copy`、`dgmm`、`dot`、`dotc`、`gbmv`、`geam`、`gemm`、`gemv`、`ger`、`hbmv`、`hemm`、`hemv`、`her`、`her2`、`her2k`、`herk`、`herkx`、`hpmv`、`hpr`、`hpr2`、`nrm2`、`rot`、`rotg`、`rotm`、`rotmg`、`sbmv`、`scal`、`spmv`、`spr`、`spr2`、`swap`、`symm`、`symv`、`syr`、`syr2`、`syr2k`、`syrk`、`syrkx`、`tbmv`、`tbsv`、`tpmv`、`tpsv`、`tpttr`、`trmm`、`trmv`、`trsm`、`trsv`、`trttp` | 72 | 固定教学profile与所列扩展cases；含复杂rank-k类型化适配、HIP GPU packed转换、FP32分组batched及FP64项目策略调优。rotmg极端缩放使用HIP修正；调优/批量变体按同一数学族去重。 |
| [cuBLASLt](../../cuBLASLt/README.md) | 1 | `GEMM` | 8 | 既有6个profile为FP32 SGEMM、HSH pointer-array/strided、grouped分发及custom-find/autotune。MOAT新资格分别登记FP16 planar负偏移转换/FP32 3M/FP16输出，以及真实COL32/COL4 packing + native INT8/INT32 GemmEx；按样例链接与资格状态限定范围。 |
| [cuBLASMp](../../cuBLASMp/README.md) | 2 | `block-cyclic 重分布`、`分布式 GEADD` | 2 | 已登记FP64 GEADD与1024阶block-cyclic重分布/往返；双MPI进程和不同GPU实际通信。GEMM子矩阵与低精度collective/quantized scale模式等缺口保持PARTIAL，未覆盖多节点。 |
| [cuDSS](../../cuDSS/README.md) | 2 | `稀疏直接求解`、`稀疏重排序与求解` | 14 | FP64 CSR：simple、异构/均匀batch、重排后完整求解及GENERAL多RHS残差；CPU符号/matching + rocSOLVER CSRRF或项目HIP CSR pivot LU。MOAT新增8个真实ISO_C_BINDING Fortran入口，uniform保留GPU factor并选择性重算，residual应用实际检查；原CUDA Fortran工具链仍缺。CPP重排严格METIS向量不同及get_set缺项保持PARTIAL，不把历史analysis-only计为完整求解。规模/动态pivot按逐例范围。 |
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
| [NPP](../../NPP/README.md) | 2 | `Euclidean 距离变换/Voronoi`、`零均值 NCC` | 2 | 精确Euclidean距离/Voronoi/整数截断；NCC原始2048×1024 RAW、全部CLI、完整score/GPU argmax、PGM与HIP-event计时已收口，常量模板/图块按原生大图路径实测；Canny原生像素策略与其它未完成入口继续逐例记录。 |
| [nvCOMP](../../nvCOMP/README.md) | 3 | `CRC32`、`LZ4`、`Snappy` | 7 | hipCOMP LZ4/Snappy原生批处理；CPU↔GPU与hipCOMP↔nvCOMP双向互解、逐chunk status/实际长度、空/边界/损坏流；LZ4 native manager/factory +项目CRC32C及100 raw buffers。独立CRC32入口采用项目HIP IEEE/PKZIP算法，与zlib及真实nvCOMP逐chunk比较，空输入按原生语义拒绝；具体资格见逐例状态。完整NVBENCH框架仍单列PARTIAL。 |

以下仅有子集/能力探针，**不计入上述整例支持数**：

| 模块 | 已验证子集 | 原始样例尚缺什么 |
| --- | --- | --- |
| nvJPEG | rocJPEG baseline 解码；B10真实CLI/布局/缩放/ROI/多实例/后处理逐例验收 | progressive缺少原生GPU后端；显式CPU fallback/encode另标注；6 PARTIAL、0 PASSED |
| NPP | 精确Euclidean距离/Voronoi已整例通过；Canny与NCC有数值子集 | 原生Canny像素策略、NCC文件harness及其它尚未完成合同按逐例状态记录 |

逐个算子族与样例的可追溯映射见 [operator-support.json](../../migration/reports/operator-support.json)；失败仍按具体入口和原因保留。
