"""B12--B15 registered scope. Missing original contracts are never silently qualified."""
import json,pathlib
from catalog import ROOT
PLAN=json.loads((ROOT/'migration/roadmap.json').read_text())
GROUPS={b['id'].lower():{} for b in PLAN['batches'] if b['id'] in ['B12','B13','B14','B15']}
for b in PLAN['batches']:
 if b['id'].lower() in GROUPS:
  for s in b['sources']:
   GROUPS[b['id'].lower()][s]=['original','irregular','changed-values','boundary','repeat','singular-or-empty']
ALL={s:c for g in GROUPS.values() for s,c in g.items()}
def kind(s):
 if s.startswith('MathDx/'):return pathlib.PurePosixPath(s).stem
 if s.startswith('cuBLASMp/'):return pathlib.PurePosixPath(s).stem
 if s.startswith('cuSOLVER/'):return 'mg_lu' if 'MgGetrf' in s else 'mg_chol'
 if s.startswith('cuSOLVERMp/'):return 'mp_lu' if 'getrf' in s else 'mp_chol'
 if s.startswith('cuFFTMp/'):return 'mp_fft'
 if s.startswith('cuTENSORMg/'):return 'mg_tensor'
 return {'NPP/nppCanny/npp_canny_simple.cpp':'canny','NPP/templateMatching/templateMatching.cpp':'ncc','NPP/distanceTransform/distanceTransform.cpp':'distance','NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp':'flood'}[s]
def model(s):return 'mpi' if s.startswith(('cuBLASMp/','cuSOLVERMp/','cuFFTMp/')) else 'threads' if s.startswith(('cuSOLVER/Mg','cuTENSORMg/')) else 'single'

ROUTES={
 'b12':'MPI + RCCL + hipBLAS/GemmEx + HIP block-cyclic distribution/redistribution',
 'b13':'RCCL + HIP distributed pivot LU/Cholesky; hipFFT slab transpose FFT; hipBLAS distributed contraction',
 'b14':'HIP cooperative device GEMM/FFT/complex Cholesky; rocRAND device Philox + explicit 53-bit Box-Muller',
 'b15':'HIP Sobel/NMS/hysteresis, exact separable Euclidean distance/Voronoi, NCC/argmax and connected-region kernels',
}
LIMITS={
 'gemm':('original-B-submatrix-offset-and-full-transpose-controls','本轮GEMM保持FP32/尺寸与A/C分布；原例B的IB=3子矩阵描述符及完整transpose/CLI控制未逐项等价，保留部分支持。'),
 'matmul_ag':('original-half-collective-and-quantized-scale-modes','FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。'),
 'matmul_ar':('original-half-collective-and-quantized-scale-modes','FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。'),
 'matmul_rs':('original-half-collective-and-quantized-scale-modes','FP16输入用native GemmEx计算，项目FP32通信/累加后GPU量化FP16；原始FP16 collective舍入、FP8/FP4/scale模式与完整CLI尚未等价。'),
 'mg_chol':('original-Mg-input-distribution-descriptor','8阶/2RHS与单进程多GPU数值通过；项目按列重分配让两卡计算，未实现原始tile256输入/输出描述符的完整转换契约。'),
 'mp_lu':('original-Mp-2D-grid-and-submatrix-offsets','保留MPI双rank/10阶LU+solve和真实分布数值；原例二维block-cyclic网格及IA/JA=3等子矩阵描述符尚未等价，当前为项目列分布。'),
 'mp_chol':('original-Mp-2D-grid-offsets-and-random-SPD-profile','保留MPI双rank/Cholesky+solve和真实分布数值；原例二维网格/子矩阵offset及随机对角占优生成profile尚未等价，当前为已登记Laplacian列分布。'),
 'philox_thread_api':('NVIDIA-LEGACY-bitwise-host-device-lognormal-contract','使用真实rocRAND Philox设备引擎，CPU整数oracle逐word验证counter/subsequence；分布使用显式53-bit Box-Muller。ROCm normal头与当前overlay不兼容，且不声称原例NVIDIA LEGACY host/device逐位相等。'),
 'canny':('native-NPP-C3-gradient-tie-and-file-CLI-equivalence','GPU三通道最大梯度/Sobel/NMS/滞后连接已全像素验收；原生NPP C3梯度与NMS tie策略及原例OpenCV文件CLI未完成逐像素等价。'),
 'ncc':('original-annotation-file-CLI-and-timing-harness','原始2048x1024/96x64、seed1234退化模板、完整score与GPU argmax均验收；原例注释图文件、全部CLI和计时harness尚未移植。'),
 'flood':('native-NPPPlus-five-mode-metadata-and-paint-contract','五种GPU连接/gradient/range/boundary路径及区域统计已验收；原生NPP+ SDK缺失，原例完整paint值/metadata结构和边界策略未逐项等价。'),
}

def route(source):
 k=kind(source)
 return {
  'geadd':'MPI + RCCL AllReduce + HIP FP64 block-cyclic GEADD',
  'gemr2d':'MPI + RCCL AllReduce + HIP block-cyclic redistribution/roundtrip',
  'gemm':'MPI + RCCL distribution + hipBLAS FP32 local GEMM',
  'matmul_ag':'MPI + RCCL AllGather + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization',
  'matmul_ar':'MPI + RCCL AllReduce + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization',
  'matmul_rs':'MPI + RCCL ReduceScatter + hipBLAS GemmEx FP16 inputs/FP32 accumulation + HIP FP16 quantization',
  'mg_lu':'HIP multi-device pivot LU/solve + RCCL broadcast/AllReduce; single process with two GPU threads',
  'mg_chol':'HIP multi-device Cholesky/solve + RCCL broadcast/AllReduce; single process with two GPU threads',
  'mp_lu':'MPI + RCCL + HIP column-distributed partial-row-pivot LU/solve',
  'mp_chol':'MPI + RCCL + HIP distributed column Cholesky/solve',
  'mp_fft':'MPI + hipFFT local YZ/X FFT + RCCL Send/Recv + HIP slab transpose/scale',
  'mg_tensor':'hipBLAS FP32 partitioned contraction + RCCL AllGather; single process with two GPU threads',
  'introduction_example':'HIP cooperative device FP64 GEMM (shared, register-accumulate, register-store phases)',
  'simple_fft_block':'HIP cooperative device radix-2 C2C FFT',
  'potrf_block':'HIP cooperative device complex FP64 upper Cholesky, shared LDA33',
  'philox_thread_api':'rocRAND device Philox4x32-10 + HIP/OCML explicit 53-bit Box-Muller lognormal',
  'canny':'HIP three-channel Sobel/NMS/connected hysteresis kernels',
  'ncc':'HIP zero-mean normalized correlation + GPU argmax kernels',
  'distance':'HIP exact separable Euclidean distance/Voronoi/integer truncation kernels',
  'flood':'HIP connected-region equal/gradient/range/boundary kernels + GPU area/bbox metadata',
 }[k]
