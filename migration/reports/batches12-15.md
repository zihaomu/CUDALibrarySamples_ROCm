# B12–B15 实施、支持方式与逐例日志

更新时间：2026-11-10T05:51:26.573715+00:00。20个目标；原始vendor基线、兼容CUDA数学对照、CPU参考与未完成原例合同分开记录。

**本轮：9整例支持、11部分支持；120/120 case完成AMD／独立CPU／同输入兼容CUDA验收。** 全项目211 PASSED、24 PARTIAL、402 FAILED。

| B12 原始入口 / 详细日志 | 实际AMD路线 | 当前结果 | 原例合同缺口 / 原因 |
| --- | --- | --- | --- |
| [cuBLASMp/geadd.cu](../sample-reports/cuBLASMp/geadd.cu.md) | MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |
| [cuBLASMp/gemr2d.cu](../sample-reports/cuBLASMp/gemr2d.cu.md) | MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |
| [cuBLASMp/gemm.cu](../sample-reports/cuBLASMp/gemm.cu.md) | MPI + RCCL distribution + hipBLAS FP32 local GEMM | PARTIAL | 本轮GEMM保持FP32/尺寸与A/C分布；原例B的IB=3子矩阵描述符及完整transpose/CLI控制未逐项等价，保留部分支持。 |
| [cuBLASMp/matmul_ag.cu](../sample-reports/cuBLASMp/matmul_ag.cu.md) | MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization | PARTIAL | FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。 |
| [cuBLASMp/matmul_ar.cu](../sample-reports/cuBLASMp/matmul_ar.cu.md) | MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization | PARTIAL | FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。 |
| [cuBLASMp/matmul_rs.cu](../sample-reports/cuBLASMp/matmul_rs.cu.md) | MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization | PARTIAL | FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。 |

| B13 原始入口 / 详细日志 | 实际AMD路线 | 当前结果 | 原例合同缺口 / 原因 |
| --- | --- | --- | --- |
| [cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu](../sample-reports/cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu.md) | HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |
| [cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu](../sample-reports/cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu.md) | HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads | PARTIAL | 8阶/2RHS与单进程多GPU数值通过；项目按列重分配让两卡计算，未实现原始tile256输入/输出描述符的完整转换契约。 |
| [cuSOLVERMp/mp_getrf_getrs.c](../sample-reports/cuSOLVERMp/mp_getrf_getrs.c.md) | MPI + RCCL + HIP column-distributed partial-row-pivot LU/solve | PARTIAL | 保留MPI双rank/10阶LU+solve和真实分布数值；原例二维block-cyclic网格及IA/JA=3等子矩阵描述符尚未等价，当前为项目列分布。 |
| [cuSOLVERMp/mp_potrf_potrs.c](../sample-reports/cuSOLVERMp/mp_potrf_potrs.c.md) | MPI + RCCL + HIP distributed column Cholesky/solve | PARTIAL | 保留MPI双rank/Cholesky+solve和真实分布数值；原例二维网格/子矩阵offset及随机对角占优生成profile尚未等价，当前为已登记Laplacian列分布。 |
| [cuFFTMp/samples/c2c/cufftmp_c2c.cu](../sample-reports/cuFFTMp/samples/c2c/cufftmp_c2c.cu.md) | MPI + hipFFT local YZ/X FFT + RCCL Send/Recv + HIP slab transpose/scale | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |
| [cuTENSORMg/contraction_multi_gpu.cu](../sample-reports/cuTENSORMg/contraction_multi_gpu.cu.md) | hipBLAS FP32 partitioned contraction + RCCL AllGather; single process with two GPU threads | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |

| B14 原始入口 / 详细日志 | 实际AMD路线 | 当前结果 | 原例合同缺口 / 原因 |
| --- | --- | --- | --- |
| [MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu](../sample-reports/MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu.md) | HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases) | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |
| [MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block.cu](../sample-reports/MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block.cu.md) | HIP cooperative device radix-2 C2C FFT | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |
| [MathDx/cuRANDDx/01_introduction/philox_thread_api.cu](../sample-reports/MathDx/cuRANDDx/01_introduction/philox_thread_api.cu.md) | rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal | PARTIAL | 使用真实rocRAND Philox设备引擎，CPU整数oracle逐word验证counter/subsequence；分布使用显式53-bit Box-Muller。ROCm normal头与当前overlay不兼容，且不声称原例NVIDIA LEGACY host/device逐位相等。 |
| [MathDx/cuSolverDx/01_Linear_Solve/potrf_block.cu](../sample-reports/MathDx/cuSolverDx/01_Linear_Solve/potrf_block.cu.md) | HIP cooperative device complex FP64 upper Cholesky, shared LDA33 | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |

| B15 原始入口 / 详细日志 | 实际AMD路线 | 当前结果 | 原例合同缺口 / 原因 |
| --- | --- | --- | --- |
| [NPP/nppCanny/npp_canny_simple.cpp](../sample-reports/NPP/nppCanny/npp_canny_simple.cpp.md) | HIP three-channel Sobel/NMS/connected hysteresis kernels | PARTIAL | GPU三通道最大梯度/Sobel/NMS/滞后连接已全像素验收；原生NPP C3梯度与NMS tie策略及原例OpenCV文件CLI未完成逐像素等价。 |
| [NPP/templateMatching/templateMatching.cpp](../sample-reports/NPP/templateMatching/templateMatching.cpp.md) | HIP zero-mean normalized correlation + GPU argmax kernels | PARTIAL | 原始2048x1024/96x64、seed1234退化模板、完整score与GPU argmax均验收；原例注释图文件、全部CLI和计时harness尚未移植。 |
| [NPP/distanceTransform/distanceTransform.cpp](../sample-reports/NPP/distanceTransform/distanceTransform.cpp.md) | HIP exact separable Euclidean distance/Voronoi/integer truncation kernels | PASSED | 登记profile；扩展其它精度/规模/执行模型需要新验收。 |
| [NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp](../sample-reports/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp.md) | HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata | PARTIAL | 五种GPU连接/gradient/range/boundary路径及区域统计已验收；原生NPP+ SDK缺失，原例完整paint值/metadata结构和边界策略未逐项等价。 |

B12 使用两个MPI进程，按PCI确认不同GPU；block-cyclic输入/本地输出、gemr2d重分布往返和真实RCCL AllGather/AllReduce/ReduceScatter独立检查。geadd保持原例FP64，collective试点为FP16输入native GemmEx + FP32通信/累加 + GPU FP16量化，舍入/量化高级模式没有被算作完整支持。CPU只做布局编排，数值运算/collective在GPU。

B13 保持Mg单进程双GPU与Mp双进程模型。611阶LU按256列tile分布、GPU pivot/broadcast/分解；Cholesky试点GPU分布列更新，LU/POTRF后在设备重构factor并复制求解。FFT原始16³与不均匀17×13×9经native hipFFT本地YZ/X变换、实际GPU pack/unpack与RCCL Send/Recv从X-slab转Y-slab，频域/缩放/逆变换全量验收。contraction保留4096/2048、模式i,k / k,j / i,j、二维逻辑block映射到两张物理GPU，输入显式初始化，完整FP64 CPU参考检查全部输出。MgPotrf/Mp descriptor缺口仍PARTIAL；未验证多节点和任意网格/规模/性能。

B14 的GEMM/FFT/complex上三角Cholesky在调用方kernel内部执行HIP设备函数，检查所有阶段、真实线程形状、shared LDA33 padding和非SPD info，使用host BLAS/FFT冒充Dx的路径不计通过。RNG使用真实rocRAND Philox设备引擎，CPU整数Philox10逐word验证counter/subsequence，再以独立53bit Box-Muller核对全部lognormal输出。rocRAND normal头与当前overlay接口冲突已保留失败日志；该RNG适配不等价于NVIDIA LEGACY逐位host/device序列，仍PARTIAL。公开MathDx25.6与当前上游新API版本差异另留原生CUDA编译证据。

B15 在GPU实现Sobel/NMS/连接传播、精确separable Euclidean距离/Voronoi位移/整数截断、零均值NCC/GPU argmax、五种连接区域试点与GPU面积/bbox/边界查询。使用原仓库PNG/RAW图像、非连续行stride/ROI、空输入类、阈值和重复case；CPU只作输入文件解码/fixture与独立SciPy参考。原生NPP/NPP+语义、文件CLI及注释图缺口逐例保留；RPP可用API检查单独归档，不用resize探针替代这些算法支持。

验证加固：20个独立oracle各2次错误输出，共40次；另13次PCI/PID/collective/slab通信/设备函数/shared padding/Philox/stride/Voronoi/argmax/空工作语义错误全部拒绝；10项真实MPI rank数、GPU数与图像descriptor错误均停止。[故障注入](batches12_15-negative.json) · [运行边界](batches12_15-runtime-checks.json)。原始NPP两图float距离/uint16截断逐像素一致，Voronoi按位移解释并允许合法nearest-site ties；小尺寸/空site的native API限制另记。[原生NPP对照](batch15-native-comparison.json) · [Voronoi失败与修正证据](batch15-native-voronoi-failure.json) · [项目依赖锁](../environments/batches12_15-dependencies.json)。

[数值/语义验收](batches12_15-validation.json) · [AMD逐例构建运行](batches12_15-rocm.json) · [兼容CUDA数学基线](batches12_15-cuda.json) · [原始vendor程序尝试](batches12_15-native-cuda.json)。原始vendor程序退出成功只说明它自身运行成功，不冒充同输入逐输出对照。每case的outputs-manifest.json记录所有bin/log/JSON的SHA256；大二进制留本地按固定源码/输入重建。

复现（先按环境锁准备项目MPICH、MathDx CUDA SDK和image fixtures）：

```bash
python3 tools/migration/setup_batches12_15.py
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batch15_fixtures.py
HIP_VISIBLE_DEVICES=2,1 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh python tools/migration/batches12_15_run.py b12 b13 b14 b15
python3 tools/migration/package_batches12_15_cuda.py
# 将tar解到CUDA机项目根目录，再执行：
# CUDA_VISIBLE_DEVICES=0,1 python3 tools/migration/batches12_15_run.py b12 b13 b14 b15 --backend cuda
python3 tools/migration/collect_batches12_15_cuda.py
OPENBLAS_NUM_THREADS=2 python3 tools/migration/batches12_15_validate.py b12 b13 b14 b15 --qualify
```

HIP ordinal 2,1在本次机器映射到物理GPU0/2；启动前每次重新guard和检查预约，不把物理卡号直接当HIP ordinal。动态资源不同应换允许的可见卡并重新验收。无多节点证据，不宣称多节点支持。
