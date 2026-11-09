#!/usr/bin/env python3
"""Version-scoped library choices and reasons; per-entry failure logs remain authoritative."""
import json
from catalog import ROOT,CANDIDATES
NOTES={
'cuBLAS':'常规运算与第二批索引/旋转/batch 已验收；rotmg 原生重复缩放错误由项目 HIP GPU 修正。Emulation、3m、部分 Ex/packed 转换仍有接口/算法改写缺口。',
'cuBLASLt':'FP32 与两种 HSH FP16 batch 路径验证通过；高级 scale/quantization、grouped/autotune 接口及 FP8 格式不能按名字强行等同。',
'cuSPARSE':'CSR/COO/blocked ELL 及 SpVV/SpGEMM/reuse 数值变化已验收；CG/BiCGSTAB/graph 等缺独立检查，BSR SDDMM 与部分新转换/custom operator 路线仍失败。',
'cuSOLVER':'基础分解及第二批 Xgeqrf/Xpotrf 重构、残差已验收；Mg、IRS、其余 64-bit/Jacobi/近似 API 或专用 oracle 缺口仍失败/部分完成。',
'cuFFT':'原始单卡、双卡、legacy/JIT callback 分别实现；1D Xt 不支持的单 batch 路径改用 hipFFT + RCCL + GPU 合并，JIT 使用 SPIR-V。',
'cuRAND':'36 个 generator/distribution 的原始参数、重复性与解析分布矩均验证；MT19937 初始化需较长时限，跨库序列不要求相同。',
'cuDSS':'simple 的 C++/Fortran 用 CPU 稀疏符号图 + rocSOLVER CSRRF GPU 数值分解/求解；高级 descriptor、Schur、分布式、allocator 等 API 尚未完整改写。',
'cuSOLVERSp2cuDSS':'原例对比两个 NVIDIA 稀疏直接求解 API；没有完成保持两条路线及对应配置语义的 AMD 改写。',
'cuSPARSELt':'hipSPARSELt 已编译并真实运行，gfx1201 kernel 数据缺失；锁定源码的支持架构列表也不接受 gfx1201，不能用 dense GEMM 代替结构化稀疏。',
'cuTENSOR':'hipTensor 的 binary/trinary、permutation、reduction 原始 extents 与小尺寸全部输出通过 CPU/CUDA；FP32 contraction 架构 gate 缺口由 rocBLAS + HIP 排列补足；其它高级/绑定场景仍失败。',
'cuTENSORMg':'单进程跨卡 tensor 分区/布局/通信 API 尚未实现；单卡 hipTensor 不等同 Mg。',
'cuTENSORMp':'原始 MPI tensor 描述与分布式算法尚未改写；RCCL 基础可行性不等同原始 Mp profile。',
'cuBLASMp':'已验证双卡 hipBLAS/RCCL 基础计算，但原始 MPI 进程网格、block-cyclic 数据分布、各精度和高级 profile 尚未实现。',
'cuSOLVERMp':'分布式 LU/Cholesky/特征值等需要 MPI/通信及算法层改写；不能以单卡 hipSOLVER 作为成功。',
'cuFFTMp':'MPI/Fortran/NVSHMEM 与原始 slab/pencil/reshape 分布接口仍有绑定和实现缺口；双卡 Xt 的成功范围单独报告。',
'NPP':'RPP HIP 小型 resize 能力已探测；原始 Canny、distance transform、label/watershed 等特殊算子未完成等价实现，不能由 resize 推广。',
'NPP+':'原始高级轮廓/距离/分割及 Python 绑定尚未改写；RPP/rocPRIM 只是候选组件。',
'nvJPEG':'rocJPEG 硬件 baseline RGB decode 与 CPU libjpeg 对照通过；原例全部输入/多实例/ROI/编码与 resize-watermark 流程尚未覆盖。',
'nvJPEG2000':'rocJPEG 的 JPEG decode 不能替代 JPEG2000；原始 GPU codec/多阶段/metadata 接口没有 AMD 实现，CPU OpenJPEG 不计成功。',
'nvTIFF':'原始 TIFF GPU codec 与多页/GeoTIFF/options 等接口未改写；CPU TIFF 容器处理不能冒充 GPU codec。',
'nvCOMP':'hipCOMP 已源码构建、LZ4 GPU 往返验证；现代 nvCOMP 状态/选项/manager/API 代际差异及各 codec 仍未覆盖全部原始 profile。',
'nvMatmulHeuristics':'hipBLASLt heuristic 已在 M1 验证；原始配置格式/模型与搜索接口未完整迁移，Origami 仅为待验收候选。',
'cuPQC':'SHA2/SHA3 使用自有 HIP 设备实现且独立摘要完全一致；ML-KEM/ML-DSA/Merkle/Poseidon2 仍需设备算法与 API 改写。',
'cuEST':'原始 GPU 电子结构 context、积分/梯度、DF/XC/PCM 等 vendor SDK 尚无本项目 AMD 绑定/算法实现；hipBLAS 本身不提供这些高层算子。',
'MathDx/cuBLASDx':'需要设备内可调用的 GEMM/TRSM、shared/register/pipeline/fusion 重写；rocWMMA/CK 是候选，host hipBLAS 不算 Dx 等价实现。',
'MathDx/cuFFTDx':'需要设备内 FFT 与融合算法；host hipFFT/rocFFT 的成功不能替代这些 device-callable profile。',
'MathDx/cuRANDDx':'rocRAND device API 是候选；原始 DSL、PCG/Philox rounds、subsequence/ordering 与设备端组合行为尚未逐例实现。',
'MathDx/cuSolverDx':'原始线程/块级设备求解与融合需要自有 HIP/设备算法；host rocSOLVER 不作为成功替代。',
'MathDx/libmathdx':'HIPRTC 已在 FFT JIT 路线验证，但不自带原始 libmathdx 的各设备算法生成器/描述 DSL，尚未等价改写。',
'MathDx/nvCOMPDx':'hipCOMP 的 host API 不等于 device-callable nvCOMPDx；原始设备融合/CPU互通/ANS 等需要专门重写。'}
RETRY={k:'实现并审查上列缺失的 AMD API/算法，保留原始 dtype/layout/execution model；使用原始 profile 与独立参考重新验收。' for k in NOTES}
RETRY['cuSPARSELt']='使用有匹配 kernel bundle 的受支持 GPU，或新的 gfx1201 hipSPARSELt 实现/包；重新跑 prune/compress/matmul 与 CPU 参考。'
RETRY['nvJPEG2000']='提供可在锁定 AMD 环境工作的 GPU JPEG2000 codec/实现，保留原例 bit depth、batch、输出与质量要求。'
RETRY['nvTIFF']='补 GPU TIFF codec 及容器/元数据桥接；分别验收 encode/decode/multi-image/GeoTIFF/options。'
assert set(NOTES)==set(CANDIDATES)
(ROOT/'migration/ecosystem-decisions.json').write_text(json.dumps({k:{'reason':v,'retry_condition':RETRY[k]} for k,v in NOTES.items()},indent=2,ensure_ascii=False)+'\n')
text='# AMD 生态库选择与范围结论\n\n各结论限定在项目环境锁和已记录源码版本。没有完成转换不等于硬件或整个 ROCm 不支持。逐例命令、错误和数值检查保存在 samples.yaml / sample-reports。\n\n| 子项目 | 已执行结果与失败边界 | 恢复条件 |\n| --- | --- | --- |\n'
for k in NOTES:text+='| '+k+' | '+NOTES[k]+' | '+RETRY[k]+' |\n'
text+='''
证据与选型依据：

- [hipTensor 精度/架构 gate（锁定源码）](https://github.com/ROCm/rocm-libraries/blob/380ea3ec237d03c4a384b4ed4c49fda82d9f81dd/projects/hiptensor/library/src/hip_device.cpp)：gfx1201 支持不代表每一种 compute type 都支持。实际 FP32 contraction 返回 ARCH_MISMATCH；FP16 compute 另有数值失败，未拿它冒充 FP32。
- [hipSPARSELt 支持架构（锁定源码）](https://github.com/ROCm/rocm-libraries/blob/380ea3ec237d03c4a384b4ed4c49fda82d9f81dd/projects/hipsparselt/cmake/hipsparselt_supported_architectures.cmake)：实机库缺少 gfx1201 kernel，项目的独立 CMake 目标检查也报不支持。仅限此版本/硬件/后端。
- [hipFFT 实现（锁定源码）](https://github.com/ROCm/rocm-libraries/blob/380ea3ec237d03c4a384b4ed4c49fda82d9f81dd/projects/hipfft/library/src/amd_detail/hipfft.cpp)：1D 单 batch Xt 与重复 device ID 有限制；本项目保留历史失败，并实现实际两卡的另一条路线。
- [AMD JIT callback 编译说明](https://rocm.docs.amd.com/projects/rocFFT/en/develop/how-to/load-store-callbacks.html)：本项目验证实际 ROCm 10.1 API 与 SPIR-V；文档 develop 分支本身不是运行成功证据。
- [hipCOMP 固定源码](https://github.com/ROCm/hipCOMP-core/tree/03df9f7369211ee15d370817165224c73fdc9a46)：保留项目构建日志和 library hash，范围仅限实际测试 codec。

GPU 资源限制：部分正确性检查与其他任务共用卡，数值结果逐项验收；性能必须通过独占/空闲资格。当前 GPU0/1/4/5 有大任务，GPU2/6 被预约，GPU3 排除计算，GPU7 也有任务。6 个 GEMM 原始计时保留为竞争条件下观察，不发布合格速度比。
'''
(ROOT/'migration/reports/ecosystem-decisions.md').write_text(text)
print('Wrote decisions for',len(NOTES),'families')
