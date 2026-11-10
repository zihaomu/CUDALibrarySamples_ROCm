# AMD 生态库选择与范围结论

各结论限定在项目环境锁和已记录源码版本。没有完成转换不等于硬件或整个 ROCm 不支持。逐例命令、错误和数值检查保存在 samples.yaml / sample-reports。

| 子项目 | 已执行结果与失败边界 | 恢复条件 |
| --- | --- | --- |
| cuBLAS | 常规运算与第二批索引/旋转/batch 已验收；rotmg 原生重复缩放错误由项目 HIP GPU 修正。Emulation、3m、部分 Ex/packed 转换仍有接口/算法改写缺口。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuBLASLt | FP32 与两种 HSH FP16 batch 路径验证通过；高级 scale/quantization、grouped/autotune 接口及 FP8 格式不能按名字强行等同。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuSPARSE | CSR/COO/blocked ELL、SpVV/SpGEMM/reuse、CG/BiCGSTAB、gpsvInterleavedBatch 与真实 SpVV Graph Capture/Replay 已通过独立 CPU 和 CUDA 验收。BSR SDDMM、部分新转换/custom operator 与其它原始入口仍失败，不能推及整个库。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuSOLVER | 基础分解、Xgeqrf/Xpotrf、gesvdjBatched、syevjBatched、syevdx/sygvdx 已验收；后四项检查逐batch重构/配对、meig与选区。Xgeev三例仍需排除CPU兼容路径，gesvdaStridedBatched仍需确认近似算法与残差语义，保留PARTIAL；Mg、IRS等其它入口缺AMD改写或oracle。 B13另完成611阶MgGetrf双GPU/tile256列分布与GPU pivot/solve；MgPotrf输入descriptor仍PARTIAL。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuFFT | 原始单卡、双卡、legacy/JIT callback 分别实现；1D Xt 不支持的单 batch 路径改用 hipFFT + RCCL + GPU 合并，JIT 使用 SPIR-V。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuRAND | 36 个 generator/distribution 的原始参数、重复性与解析分布矩均验证；MT19937 初始化需较长时限，跨库序列不要求相同。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuDSS | simple三语言及B11的异构/均匀batch、重排序analysis-only、1000阶GENERAL双RHS已验收：CPU sparse symbolic/matching + rocSOLVER CSRRF或HIP CSR pivot LU。get_set保留完整cuDSS超级面板/16字段内存/原顺序DIAG语义缺口；小例性能和大规模动态pivot、Schur/分布式/allocator等未资格化。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuSOLVERSp2cuDSS | 原例对比两个 NVIDIA 稀疏直接求解 API；没有完成保持两条路线及对应配置语义的 AMD 改写。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuSPARSELt | hipSPARSELt 已编译并真实运行，gfx1201 kernel 数据缺失；锁定源码的支持架构列表也不接受 gfx1201，不能用 dense GEMM 代替结构化稀疏。 | 使用有匹配 kernel bundle 的受支持 GPU，或新的 gfx1201 hipSPARSELt 实现/包；重新跑 prune/compress/matmul 与 CPU 参考。 |
| cuTENSOR | hipTensor 的 binary/trinary、permutation、reduction 原始 extents 与小尺寸全部输出通过 CPU/CUDA；FP32 contraction 架构 gate 缺口由 rocBLAS + HIP 排列补足；其它高级/绑定场景仍失败。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuTENSORMg | B13保留4096 extents/2048 block、i,k / k,j / i,j及单进程双GPU，hipBLAS + RCCL输入分布/完整输出通过FP64 CPU；其它类型/分区及性能不外推。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuTENSORMp | 原始 MPI tensor 描述与分布式算法尚未改写；RCCL 基础可行性不等同原始 Mp profile。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuBLASMp | B12原始FP64 GEADD与block-cyclic重分布/往返通过；MPI双rank使用不同GPU及真实RCCL。GEMM原始B子矩阵offset、FP16 collective舍入/FP8/FP4 scale和完整CLI保持PARTIAL；没有多节点资格。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuSOLVERMp | MPI + RCCL + HIP真实分布列LU/Cholesky与求解、残差已验收；原始二维process-grid、子矩阵offset与随机SPD profile未完整等价，两例PARTIAL。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuFFTMp | B13 MPI双rank/不同GPU：原始16³和不均匀17×13×9经native hipFFT + GPU slab转换 + RCCL Send/Recv，频域和逆变换全量通过；其它分布/多节点未覆盖。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| NPP | 精确Euclidean距离/Voronoi位移/整数截断通过，原始两图浮点/整数结果与native NPP逐像素一致。Canny原始图仍有1995/921600像素差异，NCC原始注释图/CLI/计时框架未移植，保留PARTIAL；RPP检查未提供这些对应API，改用HIP。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| NPP+ | HIP等值/gradient/range/boundary五种连接区域试点及GPU面积/bbox/边界统计通过；缺原生NPP+ SDK，完整paint/metadata/边界语义未等价，PARTIAL；其它入口未实现。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| nvJPEG | B10 六个入口的baseline硬件解码、9布局/缩放/RGB ROI/native batch/多实例、HIP Lanczos/水印与真实CLI/Python测试已验收。原始12张图中2张progressive明确CPU libjpeg fallback，锁定rocJPEG HYBRID返回-12；GPU progressive、部分原例调度/decoupled/backend控制未等价，6项仍PARTIAL；JPEG编码为CPU。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| nvJPEG2000 | rocJPEG 的 JPEG decode 不能替代 JPEG2000；原始 GPU codec/多阶段/metadata 接口没有 AMD 实现，CPU OpenJPEG 不计成功。 | 提供可在锁定 AMD 环境工作的 GPU JPEG2000 codec/实现，保留原例 bit depth、batch、输出与质量要求。 |
| nvTIFF | 原始 TIFF GPU codec 与多页/GeoTIFF/options 等接口未改写；CPU TIFF 容器处理不能冒充 GPU codec。 | 补 GPU TIFF codec 及容器/元数据桥接；分别验收 encode/decode/multi-image/GeoTIFF/options。 |
| nvCOMP | B9 LZ4/Snappy 6个原始例子通过：hipCOMP native batch/manager，CPU liblz4/Snappy阶段、跨厂商RAW block GPU互解及损坏流检查。2个benchmark仅codec/基础文件CLI通过，完整NVBENCH框架未移植；其它codec/高级API仍缺。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| nvMatmulHeuristics | hipBLASLt heuristic 已在 M1 验证；原始配置格式/模型与搜索接口未完整迁移，Origami 仅为待验收候选。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuPQC | SHA2/SHA3 使用自有 HIP 设备实现且独立摘要完全一致；ML-KEM/ML-DSA/Merkle/Poseidon2 仍需设备算法与 API 改写。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| cuEST | 原始 GPU 电子结构 context、积分/梯度、DF/XC/PCM 等 vendor SDK 尚无本项目 AMD 绑定/算法实现；hipBLAS 本身不提供这些高层算子。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| MathDx/cuBLASDx | HIP调用方kernel内FP64 32³ GEMM，shared/register-accumulate/register-store三阶段及协作/共享内存通过；其余设备融合模板未移植。公开MathDx25.6缺当前上游新API，兼容CUDA数学与vendor失败分开。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| MathDx/cuFFTDx | HIP设备内128点双C2C FFT、原始32线程/每线程8元素和扩展合法线程块/尺寸通过；其它模板仍需实现。原生SDK版本不匹配不冒充vendor基线成功。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| MathDx/cuRANDDx | rocRAND设备Philox4x32-10原生引擎与独立整数oracle逐word通过；显式53bit Box-Muller数学通过。原生normal头/overlay接口差异及NVIDIA LEGACY逐位host/device序列未等价，PARTIAL。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| MathDx/cuSolverDx | HIP设备内32阶complex FP64上三角Cholesky、shared LDA33/256线程与非SPD info通过；其它求解DSL未改写。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| MathDx/libmathdx | HIPRTC 已在 FFT JIT 路线验证，但不自带原始 libmathdx 的各设备算法生成器/描述 DSL，尚未等价改写。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |
| MathDx/nvCOMPDx | hipCOMP 的 host API 不等于 device-callable nvCOMPDx；原始设备融合/CPU互通/ANS 等需要专门重写。 | 实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。 |

证据与选型依据：

- [hipTensor 精度/架构 gate（锁定源码）](https://github.com/ROCm/rocm-libraries/blob/380ea3ec237d03c4a384b4ed4c49fda82d9f81dd/projects/hiptensor/library/src/hip_device.cpp)：gfx1201 支持不代表每一种 compute type 都支持。实际 FP32 contraction 返回 ARCH_MISMATCH；FP16 compute 另有数值失败，未拿它冒充 FP32。
- [hipSPARSELt 支持架构（锁定源码）](https://github.com/ROCm/rocm-libraries/blob/380ea3ec237d03c4a384b4ed4c49fda82d9f81dd/projects/hipsparselt/cmake/hipsparselt_supported_architectures.cmake)：实机库缺少 gfx1201 kernel，项目的独立 CMake 目标检查也报不支持。仅限此版本/硬件/后端。
- [hipFFT 实现（锁定源码）](https://github.com/ROCm/rocm-libraries/blob/380ea3ec237d03c4a384b4ed4c49fda82d9f81dd/projects/hipfft/library/src/amd_detail/hipfft.cpp)：1D 单 batch Xt 与重复 device ID 有限制；本项目保留历史失败，并实现实际两卡的另一条路线。
- [AMD JIT callback 编译说明](https://rocm.docs.amd.com/projects/rocFFT/en/develop/how-to/load-store-callbacks.html)：本项目验证实际 ROCm 10.1 API 与 SPIR-V；文档 develop 分支本身不是运行成功证据。
- [hipCOMP 固定源码](https://github.com/ROCm/hipCOMP-core/tree/03df9f7369211ee15d370817165224c73fdc9a46)：保留项目构建日志和 library hash，范围仅限实际测试 codec。

GPU 资源限制：部分正确性检查与其他任务共用卡，数值结果逐项验收；性能必须通过独占/空闲资格。资格依据各批 evidence 的动态占用和预约记录；第三批启动时用物理GPU0，后因其它任务预约改用物理GPU2，GPU3 始终排除。6 个 GEMM 原始计时保留为竞争条件下观察，不发布合格速度比。
