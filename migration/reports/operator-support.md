# 算子支持与统计口径

## 已验收算子与验证范围

**9 个模块已有整例通过，覆盖 99 个按模块去重的算子/功能族，对应 192 个通过的样例入口。**

计数按数学算子或原例核心功能归并；同模块的精度、尺寸、语言、batch、存储格式和算法变体不重复增加算子数。例如 cuRAND 是 4 种分布、36 个 generator/distribution profile；cuDSS simple 的 3 种语言入口算 1 个功能族。跨模块总数保留不同库接口的实现，GEMM 可分别出现在 cuBLAS 与 cuBLASLt。每个族至少有一个通过独立验收的样例，支持范围限于下表和逐例 required cases。

| 模块 | 已验收算子/功能族数 | 已验收算子/功能 | 通过样例 | 验证范围 |
| --- | ---: | --- | ---: | --- |
| [cuBLAS](../../cuBLAS/README.md) | 52 | `amax`、`amin`、`asum`、`axpy`、`copy`、`dgmm`、`dot`、`dotc`、`gbmv`、`geam`、`gemm`、`gemv`、`ger`、`hbmv`、`hemm`、`hemv`、`her`、`her2`、`her2k`、`herk`、`herkx`、`hpmv`、`hpr`、`hpr2`、`nrm2`、`rot`、`rotg`、`rotm`、`rotmg`、`sbmv`、`scal`、`spmv`、`spr`、`spr2`、`swap`、`symm`、`symv`、`syr`、`syr2`、`syr2k`、`syrk`、`syrkx`、`tbmv`、`tbsv`、`tpmv`、`tpsv`、`tpttr`、`trmm`、`trmv`、`trsm`、`trsv`、`trttp` | 69 | 固定教学profile与所列扩展cases；含复杂rank-k类型化适配、HIP GPU packed转换、FP32分组batched及FP64项目策略调优。rotmg极端缩放使用HIP修正；调优/批量变体按同一数学族去重。 |
| [cuBLASLt](../../cuBLASLt/README.md) | 1 | `GEMM` | 6 | 6个profile：原FP32 SGEMM、HSH pointer-array/strided batch，以及B7 HSH grouped分发与SGEMM custom-find/autotune。FP16输入/输出、FP32累加、bias、候选全输出、workspace=0及所选方案重放通过；分发适配不等于原生device-grouped API。 |
| [cuDSS](../../cuDSS/README.md) | 1 | `稀疏 SPD 直接求解` | 3 | 原始 FP64 5×5 SPD/CSR：C++、Fortran、CUDA Fortran 改写共 3 入口；CPU 稀疏符号分析 + GPU CSRRF 数值分解/求解。 |
| [cuFFT](../../cuFFT/README.md) | 3 | `C2C 复数 FFT`、`FFT 窗口过滤 callback`、`R2C/C2R 实数 FFT` | 10 | 10 个 profile：原始单卡/双卡 C2C、实数正逆变换和 legacy/离线 SPIR-V/HIPRTC callback。1D 多卡使用 hipFFT + RCCL + HIP。 |
| [cuPQC](../../cuPQC/README.md) | 2 | `SHA-256`、`SHA3-256` | 2 | SHA-256 单线程与 SHA3-256 的 32-lane 协作 GPU kernel；各 14 输入与 hashlib 精确一致，PQC 其它算法未实现。 |
| [cuRAND](../../cuRAND/README.md) | 4 | `lognormal`、`normal`、`poisson`、`uniform` | 36 | 4 种分布 × 9 个 generator = 36 个 profile；原始参数、库内重复性和解析分布矩通过，跨库不要求逐位同序列。 |
| [cuSOLVER](../../cuSOLVER/README.md) | 9 | `Cholesky 分解`、`LU 分解/求解`、`QR 分解`、`QR 的 Q 应用`、`QR 的 Q 生成`、`SVD`、`三角矩阵求逆`、`对称特征分解`、`广义对称特征分解` | 21 | 原始FP64教学矩阵；status/info、全量分解/重构、残差、正交性、未排序配对及实际meig检查。B6增加64位LU/三角求逆；SVD/eigen typed接口显式INT_MAX限制。 |
| [cuSPARSE](../../cuSPARSE/README.md) | 20 | `SpVV Graph Capture/Replay`、`axpby`、`bicgstab`、`cg`、`coosort`、`dense2sparse`、`gather`、`gpsvinterleavedbatch`、`rot`、`scatter`、`sddmm`、`sparse2dense`、`spgemm`、`spmat`、`spmm`、`spmv`、`spmvop`、`spsm`、`spsv`、`spvv` | 36 | 已登记CSR/COO/SELL/BSR等格式、CG/BiCG残差/收敛、gpsv布局和真实Graph replay。B8补CSR→CSC、对称展开、HIP GPU预算分块SpGEMM和融合custom op；3项CUDA新API缺失，使用明确标注的兼容数学基线。 |
| [cuTENSOR](../../cuTENSOR/README.md) | 7 | `三元逐元素运算`、`二元逐元素运算`、`张量 contraction`、`张量 einsum`、`张量 permutation`、`张量 plan cache`、`张量 reduction` | 9 | FP32：hipTensor逐元素/排列/规约；rocBLAS+HIP contraction；B5补HIP padding、einsum路由、三输入收缩和真实GPU分块搜索/持久化缓存。B2/B5全部原始规模输出均有全量FP64 CPU检查；早期M3 contraction仅抽样的历史证据另保留。 |

以下仅有子集/能力探针，**不计入上述整例支持数**：

| 模块 | 已验证子集 | 原始样例尚缺什么 |
| --- | --- | --- |
| nvCOMP | hipCOMP LZ4 单 chunk，128/32768/65536 字节 GPU byte-exact 往返 | 现代 status/options、完整 batch/manager 与其它 codec；1 PARTIAL、0 PASSED |
| nvJPEG | rocJPEG hardware backend：64×64 baseline JPEG → RGB，CPU libjpeg 最大像素差 2 | 全部原始输入/格式、CLI、batch、多实例、ROI、编码；1 PARTIAL、0 PASSED |
| NPP | RPP HIP U8 c1/c3、32×24 identity resize 探针 | 原始 Canny、distance transform、label/watershed 等算子未实现；0 PASSED |

逐个算子族与样例的可追溯映射见 [operator-support.json](../../migration/reports/operator-support.json)；失败仍按具体入口和原因保留。
