# 算子支持与统计口径

## 已验收算子与验证范围

**9 个模块已有整例通过，覆盖 91 个按模块去重的算子/功能族，对应 166 个通过的样例入口。**

计数按数学算子或原例核心功能归并；同模块的精度、尺寸、语言、batch、存储格式和算法变体不重复增加算子数。例如 cuRAND 是 4 种分布、36 个 generator/distribution profile；cuDSS simple 的 3 种语言入口算 1 个功能族。跨模块总数保留不同库接口的实现，GEMM 可分别出现在 cuBLAS 与 cuBLASLt。每个族至少有一个通过独立验收的样例，支持范围限于下表和逐例 required cases。

| 模块 | 已验收算子/功能族数 | 已验收算子/功能 | 通过样例 | 验证范围 |
| --- | ---: | --- | ---: | --- |
| [cuBLAS](../../cuBLAS/README.md) | 50 | `amax`、`amin`、`asum`、`axpy`、`copy`、`dgmm`、`dot`、`dotc`、`gbmv`、`geam`、`gemm`、`gemv`、`ger`、`hbmv`、`hemm`、`hemv`、`her`、`her2`、`her2k`、`herk`、`herkx`、`hpmv`、`hpr`、`hpr2`、`nrm2`、`rot`、`rotg`、`rotm`、`rotmg`、`sbmv`、`scal`、`spmv`、`spr`、`spr2`、`swap`、`symm`、`symv`、`syr`、`syr2`、`syr2k`、`syrk`、`syrkx`、`tbmv`、`tbsv`、`tpmv`、`tpsv`、`trmm`、`trmv`、`trsm`、`trsv` | 62 | 固定教学输入与所列扩展 cases；第二批含并列/空索引、旋转 flags、batch/grouped 和正负 alpha；rotmg 极端缩放使用明确登记的 HIP 修正。其它精度/API 仍逐例管理。 |
| [cuBLASLt](../../cuBLASLt/README.md) | 1 | `GEMM` | 3 | 3 个 profile：FP32 SGEMM、HSH FP16 input/output + FP32 compute 的 pointer-array 与 strided batch。 |
| [cuDSS](../../cuDSS/README.md) | 1 | `稀疏 SPD 直接求解` | 3 | 原始 FP64 5×5 SPD/CSR：C++、Fortran、CUDA Fortran 改写共 3 入口；CPU 稀疏符号分析 + GPU CSRRF 数值分解/求解。 |
| [cuFFT](../../cuFFT/README.md) | 3 | `C2C 复数 FFT`、`FFT 窗口过滤 callback`、`R2C/C2R 实数 FFT` | 10 | 10 个 profile：原始单卡/双卡 C2C、实数正逆变换和 legacy/离线 SPIR-V/HIPRTC callback。1D 多卡使用 hipFFT + RCCL + HIP。 |
| [cuPQC](../../cuPQC/README.md) | 2 | `SHA-256`、`SHA3-256` | 2 | SHA-256 单线程与 SHA3-256 的 32-lane 协作 GPU kernel；各 14 输入与 hashlib 精确一致，PQC 其它算法未实现。 |
| [cuRAND](../../cuRAND/README.md) | 4 | `lognormal`、`normal`、`poisson`、`uniform` | 36 | 4 种分布 × 9 个 generator = 36 个 profile；原始参数、库内重复性和解析分布矩通过，跨库不要求逐位同序列。 |
| [cuSOLVER](../../cuSOLVER/README.md) | 7 | `Cholesky 分解`、`LU 分解/求解`、`QR 分解`、`QR 的 Q 生成`、`SVD`、`对称特征分解`、`广义对称特征分解` | 16 | 原始固定教学矩阵；检查 status/info、特征值/奇异值、重构、求解残差与正交性。第三批覆盖 batched SVD/未排序特征对、索引/值域/全量/空区间与实际 meig。 |
| [cuSPARSE](../../cuSPARSE/README.md) | 18 | `SpVV Graph Capture/Replay`、`axpby`、`bicgstab`、`cg`、`coosort`、`dense2sparse`、`gather`、`gpsvinterleavedbatch`、`rot`、`scatter`、`sddmm`、`sparse2dense`、`spgemm`、`spmm`、`spmv`、`spsm`、`spsv`、`spvv` | 29 | CSR/COO/SELL/blocked-ELL 等已登记格式与 batched 变体；SpVV/SpGEMM/reuse 数值变化与 CSR 结构；第三批 CG/BiCGSTAB 的独立求解、残差/收敛，gpsv 的逐 batch interleaved 布局，以及真实 GPU 图捕获/输入变化 replay。 |
| [cuTENSOR](../../cuTENSOR/README.md) | 5 | `三元逐元素运算`、`二元逐元素运算`、`张量 contraction`、`张量 permutation`、`张量 reduction` | 5 | FP32：contraction 用 rocBLAS + HIP；其它已通过的逐元素/permutation/reduction 使用 hipTensor。逐例记录原始 extents 与扩展小尺寸、全部输出 CPU 检查；contraction 的原始规模另为抽样验收。 |

以下仅有子集/能力探针，**不计入上述整例支持数**：

| 模块 | 已验证子集 | 原始样例尚缺什么 |
| --- | --- | --- |
| nvCOMP | hipCOMP LZ4 单 chunk，128/32768/65536 字节 GPU byte-exact 往返 | 现代 status/options、完整 batch/manager 与其它 codec；1 PARTIAL、0 PASSED |
| nvJPEG | rocJPEG hardware backend：64×64 baseline JPEG → RGB，CPU libjpeg 最大像素差 2 | 全部原始输入/格式、CLI、batch、多实例、ROI、编码；1 PARTIAL、0 PASSED |
| NPP | RPP HIP U8 c1/c3、32×24 identity resize 探针 | 原始 Canny、distance transform、label/watershed 等算子未实现；0 PASSED |

逐个算子族与样例的可追溯映射见 [operator-support.json](../../migration/reports/operator-support.json)；失败仍按具体入口和原因保留。
