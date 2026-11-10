#!/usr/bin/env python3
"""Publish a planning document without changing any measured sample outcome."""
import collections, hashlib, json, pathlib, subprocess
from catalog import ROOT, CANDIDATES

WEB='https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/'
def link(label,path):return '['+label+']('+WEB+path.replace(' ','%20')+')'
def targets(family,names):return [family+'/'+name for name in names]

BATCHES=[
 dict(id='B4',phase='近期',title='基础 API 修复与两种稀疏格式',risk='低到中',depends='已有 BLAS、QR、CSR 数值验收基础',
      route='hipBLAS/rocBLAS；hipSOLVER；HIP 格式桥接 + hipSPARSE/rocSPARSE',
      gate='先核对 hipBLAS Ex 的 computeType/const 指针签名；修复 ormqr 观测代码中的不存在变量 X。稀疏原生 NOT_IMPLEMENTED 保留为历史失败，再验证 GPU 格式桥接。',
      accept='BLAS 全输出 CPU 参考、HERK 共轭/对角虚部/三角区、packed 布局与 padding；QR 重构/Q 应用/求解残差；SELL 填充槽与三角属性、BSR 块内行列序和 alpha/beta。格式转换与数值计算均留在 GPU。',
      cases='original；nonzero-beta；transpose/conjugate；lower/upper；padded-lda/不规则阶数；稀疏 changed-values、unit-diagonal、block-order、存储的零值。每项只登记适用组合。',
      sources=targets('cuBLAS/Extensions',[
          'GemmBatchedEx/cublas_GemmBatchedEx_example.cu','CherkEx/cublas_CherkEx_example.cu',
          'CsyrkEx/cublas_CsyrkEx_example.cu','trttp/cublas_trttp_example.cu','tpttr/cublas_tpttr_example.cu'])+
          ['cuSOLVER/ormqr/cusolver_ormqr_example.cu','cuSPARSE/spsv_sell/spsv_sell_example.c','cuSPARSE/sddmm_bsr/sddmm_bsr_example.c']),
 dict(id='B5',phase='近期',title='张量布局、einsum 与 contraction 执行语义',risk='中，cache 项需先探针',depends='第二批 tensor 与既有 rocBLAS + HIP contraction 路线',
      route='hipTensor 优先；FP32 路线不满足时使用 rocBLAS + HIP 排列/分块；项目层 cache 适配须明确登记',
      gate='先核验 dtype、host/device 指针、stride/padding 和原始规模内存。cache 必须有真实可复用对象与失效规则；不能删除 cache 调用后称原例通过。',
      accept='原始规模保持，必要时分块流式 CPU 参考；小尺寸全量检查，原始规模的检查覆盖率逐例公开。trinary 检查收缩顺序、alpha/beta 与全部语义输出；einsum 限于原例实现的语法；cache 验证冷启动/命中/进程重启/失效和结果一致。',
      cases='原始 profile；小尺寸非整齐 extents；非零 beta；非零 padding/非连续 stride；cache 文件不存在、有效与损坏、描述变化；原始 einsum 的 5 个表达式。',
      sources=targets('cuTENSOR',['elementwise_permute_padding.cu','einsum.cu','contraction_trinary.cu','contraction_plan_cache.cu'])),
 dict(id='B6',phase='近期',title='64 位求解器接口与三角求逆',risk='中',depends='已有 LU、SVD、选区特征分解参考',
      route='hipSOLVER 能保留契约时使用；否则优先直接 rocSOLVER 的对应 GPU API',
      gate='确认安装包中的真实 64 位函数、pivot/info 类型与 workspace 单位。Xgetrf 的 algo0/algo1 和无 pivot 分支分别核验，不能把两种选项无说明映射成同一路径。',
      accept='PA=LU、Ax=b；三角逆 AA^{-1}=I；SVD 重构与正交性；选区 meig 与特征对残差。不得以小矩阵可用为由静默截断 int64 接口；未保持的选项继续 PARTIAL。',
      cases='original；pivot/no-pivot（原例适用时）；singular-info；padded leading dimension；选区 index/value/all/empty；upper/lower/unit diagonal。',
      sources=targets('cuSOLVER',['Xgetrf/cusolver_Xgetrf_example.cu','Xsyevdx/cusolver_Xsyevdx_example.cu','Xtrtri/cusolver_Xtrtri_example.cu','Xgesvd/cusolver_Xgesvd_example.cu'])),
 dict(id='B7',phase='中期',title='Grouped GEMM 与算法搜索/调优',risk='中到高',depends='B4；已验收 hipBLASLt HSH 与 SGEMM',
      route='hipBLAS Grouped Ex、hipBLASLt/hipBLASLtExt + 项目搜索驱动',
      gate='先检查所需 grouped、compute type、算法枚举/计时入口是否可用；CUDA algorithm ID 不跨库照搬。原例 autotune 必须真实搜索，不能固定一次 GEMM 代替。',
      accept='异构 group/尺寸/alpha/beta、完整输出参考；搜索候选各自正确，workspace 限制生效，所选算法可重放。性能排名只有空闲资格通过后才发布。',
      cases='不同 group 大小；transpose；workspace=0/受限；多候选；无可用候选；重复选型。',
      sources=['cuBLAS/Extensions/GemmGroupedBatchedEx/cublas_GemmGroupedBatchedEx_example.cu','cuBLAS/Extensions/GemmExAutoTuning/cublas_GemmExAutoTuning_example.cu','cuBLASLt/LtHSHgemmGroupedSimple/main.cpp','cuBLASLt/LtSgemmCustomFind/main.cu','cuBLASLt/LtSgemmSimpleAutoTuning/main.cpp']),
 dict(id='B8',phase='中期',title='高级稀疏转换、内存策略与自定义运算',risk='高',depends='B4 的格式桥接；已有 HIPRTC/SPIR-V 经验',
      route='hipSPARSE/rocSPARSE + HIP 格式/对称展开；自定义 op 使用 HIPRTC 或设备 HIP 实现',
      gate='逐项核对格式转换、SpGEMM 内存预算语义、symmetric 存储、自定义乘加行为。函数名缺失不能直接判硬件不支持。',
      accept='CSR/COO 结构和数值、索引基数、对称三角只计一次；SpGEMM 分块/预算不能忽略；custom op 必须真的在 GPU 数值路径生效，保留设备执行模型。',
      cases='empty rows；index-base0/1；非均匀行长；内存预算变化；上下三角；普通运算与自定义乘加产生不同结果。',
      sources=targets('cuSPARSE',['spmat_convert/spmat_convert_example.c','spgemm_mem/spgemm_mem_example.c','spmv_symmetric_csr/spmv_symmetric_example.c','spmvop_csr/spmv_csr_op_example.c','spmm_csr_op/spmm_csr_op_example.c'])),
 dict(id='B9',phase='中期',title='LZ4/Snappy 从单 chunk 探针扩展到原始流程',risk='中到高',depends='现有 hipCOMP LZ4 单 chunk 往返；先建立 codec/包格式互操作探针',
      route='锁定 hipCOMP + 项目 API/metadata 适配；原例明确的 CPU 编解码阶段保留独立 CPU codec',
      gate='检查现代 nvCOMP 的 batch、status/options、manager 和 header/bitstream 语义；先跑两个库间互解，不能只证明同库 round-trip。',
      accept='逐 chunk 真实长度/status、最大输出尺寸、变长 batch、空/重复/随机输入及截断损坏数据；原始 CPU/GPU 阶段分工保留。若 quickstart 暴露其它未支持 codec，只验 LZ4 不得把整例改 PASSED。',
      cases='原始默认配置；batch1/多 chunk/不等长；0/1/边界长度；CPU→GPU、GPU→CPU 互操作；损坏/截断流；重复执行。',
      sources=targets('nvCOMP',[
          'examples/low_level_quickstart_example.cpp','examples/high_level_quickstart_example.cpp',
          'examples/lz4_cpu_compression.cu','examples/lz4_cpu_decompression.cu',
          'examples/snappy_cpu_compression.cu','examples/snappy_cpu_decompression.cu',
          'benchmarks/benchmark_lz4_chunked.cu','benchmarks/benchmark_snappy_chunked.cu'])),
 dict(id='B10',phase='中期',title='JPEG 解码完整输入流程、ROI 和后处理',risk='中到高',depends='现有 rocJPEG baseline + RPP resize 探针；B5 的 stride/padding 检查可复用',
      route='rocJPEG + RPP/HIP；Python 只作为真实 GPU CLI 的测试驱动',
      gate='先遍历原始 JPEG 输入集合和 format/backend 参数，测 hardware/software 路线的实际支持；明确 progressive、subsampling、ROI 的缺口。',
      accept='CPU libjpeg 参考与颜色/布局容差、所有原始输入、batch/多实例/ROI、文件读写与退出码；resize/watermark 检查组合结果；Python imports 通过不代替 GPU 测试。JPEG encoder 不在该批。',
      cases='原始 corpus；各可用输出布局；ROI 边界；batch/多实例重复；无效输入；resize 尺寸与 watermark alpha；CLI 成功/失败。',
      sources=targets('nvJPEG',['nvJPEG-Decoder/nvjpegDecoder.cpp','nvJPEG-Decoder-MultipleInstances/nvJPEGDecMultipleInstances.cpp','nvJPEG-Decoder-Backend-ROI/nvJPEGROIDecode.cpp','Image-Resize/imageResize.cpp','Image-Resize-WaterMark/imageResizeWatermark.cpp','nvJPEG-Decoder/tests/test_decoder.py'])),
 dict(id='B11',phase='中期门槛批',title='稀疏直接求解从 SPD 子集扩展',risk='高；通过能力门槛后再实施',depends='已有 CPU 符号分析 + GPU CSRRF；先建立一般/对称矩阵数值分解能力',
      route='CPU 稀疏符号分析 + rocSOLVER/其它经过锁定验证的 GPU 稀疏数值路线；项目配置适配',
      gate='batch/uniform/reordering 原例有 SPD；residual 默认 GENERAL、get_set 使用 SYMMETRIC 和多项配置。必须逐例保留矩阵类别、pivot、配置与查询，不可全部改成 SPD。',
      accept='不转 dense；符号图/排列正确，逐 batch 残差；配置改变必须对应真实行为；查询返回真实数据；一般/不定矩阵失败行为可解释。仅 SPD 通过不能推广到其它三类。',
      cases='原始矩阵类型；不同 sparsity/batch 大小；结构相同值变化；重排序前后；奇异/不定矩阵；config set/get 与内存/排列信息。',
      sources=targets('cuDSS',['simple_batch/simple_batch.cpp','simple_uniform_batch/simple_uniform_batch.cpp','simple_reordering_phase/simple_reordering_phase.cpp','simple_residual/simple_residual.cpp','simple_get_set/simple_get_set.cpp'])),
 dict(id='B12',phase='条件研究',title='多进程多 GPU BLAS 与数据分布',risk='高',depends='MPI + RCCL 环境与至少两张允许使用的 AMD 卡；先通过通信/分布探针',
      route='MPI + RCCL + hipBLAS/rocBLAS + 分布/重分布实现',
      gate='多 rank 使用不同 GPU；block-cyclic/进程网格与原始 collective 语义先验收。物理 GPU3 排除；多节点 profile 需要实际多节点，不以同机模拟冒充。',
      accept='各 rank 本地分片与全局重构参考；AllGather/AllReduce/ReduceScatter 实际执行；通信顺序与同步正确；不能只把已有双卡 GEMM 探针换名字。',
      cases='2 rank 与不同进程网格；非整齐分片；不同 collective；重分布往返；重复执行；错误 rank/设备参数。',
      sources=targets('cuBLASMp',['geadd.cu','gemr2d.cu','gemm.cu','matmul_ag.cu','matmul_ar.cu','matmul_rs.cu'])),
 dict(id='B13',phase='条件研究',title='多 GPU 分解/FFT/张量算法',risk='很高',depends='B12 的分布和通信基础；对应单卡参考；按 Mg 与 Mp 分别实现执行模型',
      route='rocSOLVER/hipFFT/hipBLAS + MPI/RCCL + 项目分布式算法',
      gate='确认真正的跨 GPU 数值分解、FFT transpose/reshape、张量分区算法；只有分发输入再在一张卡计算不能算原例成功。',
      accept='所有设备实际参与计算；LU/Cholesky 残差、FFT 全局布局与归一化、tensor 全局输出；原始 Mg 单进程和 Mp 多进程语义分别保留。',
      cases='原始 descriptor/进程模型；不均匀分片；不同矩阵/FFT 尺寸；回传布局；重复同步；奇异/非SPD状态。',
      sources=['cuSOLVER/MgGetrf/cusolver_MgGetrf_example.cu','cuSOLVER/MgPotrf/cusolver_MgPotrf_example1.cu','cuSOLVERMp/mp_getrf_getrs.c','cuSOLVERMp/mp_potrf_potrs.c','cuFFTMp/samples/c2c/cufftmp_c2c.cu','cuTENSORMg/contraction_multi_gpu.cu']),
 dict(id='B14',phase='条件研究',title='MathDx 设备内算子四个试点',risk='很高',depends='分别建立 AMD 设备端 ABI、协作粒度与原始 oracle；不能使用 host 库调用替代',
      route='HIP 设备函数；GEMM 候选 rocWMMA/CK；RNG 候选 rocRAND device；FFT/求解设备算法按实际适用性实现',
      gate='明确 warp/thread/block/共享内存与布局；需要证明函数在原始 kernel 内被调用。原 CUDA vendor SDK 基线缺失时单列 BLOCKED，使用自有 CUDA 实现须另标。',
      accept='设备内计算/协作执行和数学结果同时通过；非32线程、共享内存边界、RNG counter/subsequence、求解 info 等按原例检查；host GEMM/FFT/solver 通过不计 Dx 通过。',
      cases='原始模板/线程块配置；不同合法维度；边界/奇异输入；协作粒度变化；RNG 序列属性；共享内存边界。',
      sources=['MathDx/cuBLASDx/01_gemm_introduction/introduction_example.cu','MathDx/cuFFTDx/02_simple_fft_block/simple_fft_block.cu','MathDx/cuRANDDx/01_introduction/philox_thread_api.cu','MathDx/cuSolverDx/01_Linear_Solve/potrf_block.cu']),
 dict(id='B15',phase='条件研究',title='图像基础算法的 GPU 重写试点',risk='高',depends='RPP 格式/stride 探针；先做各算法 GPU 能力探针和 CPU oracle',
      route='RPP 可用 primitives + rocPRIM/HIP；CPU OpenCV 仅作参考',
      gate='逐算子验证可用 primitive；Canny 的梯度/NMS/滞后连接、距离变换度量、flood-fill 连通性都要保持。resize 成功不表示这些算法已有实现。',
      accept='完整像素/掩码对照，边界模式/阈值/连通性、batch/ROI/stride；不能只用 CPU OpenCV 执行再把图复制到 GPU。',
      cases='原始图像；全零/单点/边界/非连续输入；阈值变化；不同模板尺寸；连通性/距离度量；确定性。',
      sources=['NPP/nppCanny/npp_canny_simple.cpp','NPP/templateMatching/templateMatching.cpp','NPP/distanceTransform/distanceTransform.cpp','NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp']),
]

def disposition(sample,assigned):
    source=sample['source'];family=sample['family'];low=source.lower()
    if source in assigned:return assigned[source],'明确候选；先通过对应批次入口门槛，尚未实施。'
    if family=='cuSPARSELt':return 'U1 当前栈原生不可用','锁定 gfx1201 kernel/架构 gate 缺失；只对该版本/路线判定。'
    if '/Xgeev/' in source:return 'U2 GPU 路线缺口','具体执行差异与恢复条件见 U2；保留当前原始尝试结果。'
    if 'gesvdaStridedBatched' in source:return 'U3 近似语义缺口','原契约差异与恢复条件见 U3；保留现有 PARTIAL。'
    if family=='nvCOMP' and any(k in low for k in ['bitcomp','gdeflate','benchmark_ans']):return 'U4 codec 路线不可用','具体 codec 路线边界见 U4；保留当前失败证据。'
    if family=='nvCOMP' and ('compression' in low or 'benchmark_' in low) and any(k in low for k in ['zstd','gzip','deflate']):return 'G-CODEC-DIR 先核方向','按第 4 节核对编码/解码方向与互操作；不能混为整例支持。'
    if family=='cuBLASLt' and 'GreenContext' in source:return 'U5 NVIDIA 执行契约','CUDA SM/Green Context 不是普通 GEMM 数值功能；精确契约不能用默认 stream 替代。'
    if source=='cuSPARSE/compression/compression_example.cpp':return 'G-VMM 先做能力探针','HIP 有 VMM/压缩属性结构；需实测压缩分配是否生效，不能因旧 CUDA 符号未映射就判硬件不支持。'
    if family in ['nvTIFF','nvJPEG2000'] or family=='nvJPEG' and 'Encoder' in source:return 'G-CODEC 新增 GPU codec','rocJPEG 解码路线覆盖不了该 codec/编码方向；需专用实现与互操作参考。'
    if family=='cuBLAS' and ('Emulation/' in source or '3m' in low) or family=='cuBLASLt' and any(k in low for k in ['fp8','fp4','emulat','planar','igemm']):return 'G-PRECISION 低精度/算法探针','保留编码、scale、舍入及算法语义；不能替成普通高精度 GEMM 计通过。'
    if family.startswith('MathDx/'):return 'R-DX 设备算法研究','B14 四个试点通过后再按设备执行模型扩展；不是仅改头文件或调用 host 库。'
    if family=='cuEST':return 'R-SCIENCE 专项研究','高层积分/梯度/DF/XC 等科学算法与 SDK 绑定缺口；BLAS 不能替代，需独立科学参考。'
    if family=='cuPQC':return 'R-PQC 专项研究','需 GPU 密码/哈希算法、KAT/边界与互操作；现有 SHA 通过不能推广。'
    if family in ['cuBLASMp','cuSOLVERMp','cuFFTMp','cuTENSORMg','cuTENSORMp'] or family=='cuSOLVER' and '/Mg' in source or family=='cuDSS' and ('mg_mode' in low or 'mgmn' in low):return 'G-DISTRIBUTED 分布式门槛','B12/B13 基础后再扩展；多节点需实际网络/多节点证据。'
    if family=='cuDSS':return 'R-SPARSE-DIRECT 专项研究','矩阵类型、Schur/内存/线程/配置/语言绑定需逐项实现；SPD 子集不可覆盖全部。'
    if family=='cuSOLVERSp2cuDSS' or family=='cuSOLVER' and '/csrqr/' in source:return 'R-SPARSE-QR 专项研究','需真实 GPU 稀疏 QR/直接求解及原始双路线语义，不能换 dense 求解。'
    if family=='cuSOLVER':return 'R-SOLVER 算法研究','精度迭代改进、极分解/随机SVD等各自需要算法与 oracle；先完成 B6。'
    if family=='cuTENSOR':return 'G-TENSOR 高级功能/绑定','block-sparse、JIT 数值模式和框架绑定需专门适配，不能只做 dense 数学替代。'
    if family=='nvMatmulHeuristics':return 'G-HEURISTICS 模型与硬件门槛','hipBLASLt/Origami 是候选，不等于 NVIDIA 配置、能耗估计、SM carveout 契约。'
    if family=='nvCOMP':return 'G-COMPRESS codec/API 探针','先验收 B9；其余 codec、GDS、CRC、manager/streaming/CPU互操作逐项设计。'
    if family in ['NPP','NPP+']:return 'R-VISION 算法研究','先验收 B15；轮廓、连通域、watershed 等另做 GPU pipeline 与参考。'
    return 'R-API 后续能力调查','保留既有具体错误和恢复条件，完成相关先导批次后再锁定样例与 cases。'

def main():
    cat=json.loads((ROOT/'migration/samples.yaml').read_text());by_source={s['source']:s for s in cat['samples']}
    assigned={}
    for batch in BATCHES:
        for source in batch['sources']:
            assert source in by_source,source
            assert source not in assigned,source
            assigned[source]=batch['id']
    assert len(assigned)==65,len(assigned)
    pending=[s for s in cat['samples'] if s['status']!='PASSED'];counts=collections.Counter(s['status'] for s in cat['samples'])
    expected={'PASSED':166,'PARTIAL':6,'FAILED':464,'UNSUPPORTED':2,'BLOCKED':1}
    if dict(counts)!=expected:raise RuntimeError('实测状态已改变；先审查并更新路线图基线、候选进展和条件上限，再重新生成。')
    inventory=[{'source':s['source'],'family':s['family'],'current_status':s['status'],
                'planning_group':disposition(s,assigned)[0],'planning_reason':disposition(s,assigned)[1],
                'current_reason':s['reason'],'detail':'migration/sample-reports/'+s['source']+'.md'} for s in pending]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    report={'date':'2026-11-10','state':'PLANNED_NOT_EXECUTED','baseline_commit':head,
            'baseline_counts':dict(counts),'entrypoints':len(cat['samples']),'pending_entrypoints':len(pending),
            'planned_candidate_profiles':len(assigned),'batches':BATCHES,'inventory':inventory,
            'rule':'Planning classifications do not change samples.yaml runtime status; library existence and candidate counts do not mean qualified support.'}
    (ROOT/'migration/roadmap.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    text=INTRO.replace('@HEAD@',head)
    text+='\n<a id="batches"></a>\n\n## 2. 十二批候选总览\n\n'
    text+='近期 B4–B6：16 个样例；中期 B7–B11：29 个；条件研究 B12–B15：20 个；合计 **65 个互不重复候选**，其余 **'+str(len(pending)-sum(s['source'] in assigned for s in pending))+' 个未通过入口**归入带原因的门槛/研究队列。候选量不等于保证成功量，批次也不等于新增数学算子族。\n\n'
    text+='| 批次 | 阶段 / 风险 | 主题 | 样例候选 | 首要依赖 |\n| --- | --- | --- | ---: | --- |\n'
    for b in BATCHES:text+='| ['+b['id']+'](#'+b['id'].lower()+') | '+b['phase']+' / '+b['risk']+' | '+b['title']+' | '+str(len(b['sources']))+' | '+b['depends']+' |\n'
    text+='\n**排期顺序：** B4 → B5 → B6；B7/B8/B9 可按设备与 SDK 条件选先后，随后 B10；B11 必须先补一般稀疏数值能力。B12/B13 依赖多 rank 多卡，B14/B15 各自先做一个设备内/图像算子探针。GPU 共享预约和 vendor SDK 会影响工期，当前不承诺日历日期。\n\n'
    text+='每批分为“源码/能力核对 → 最小真实 GPU 探针 → 锁定 case → 实现 → AMD/独立 CPU/CUDA 验收 → 反向检查 → 文档及 fork 发布”。门槛失败时记录失败与恢复条件，继续可独立推进的批次；不把缺能力项强行降精度或改执行模型来凑通过率。\n\n'
    for b in BATCHES:
        text+='<a id="'+b['id'].lower()+'"></a>\n\n### '+b['id']+'：'+b['title']+'（'+str(len(b['sources']))+' 例）\n\n'
        text+='**候选路线：** '+b['route']+'。\n\n**开始门槛：** '+b['gate']+'\n\n**验收：** '+b['accept']+'\n\n**case 草案：** '+b['cases']+'\n\n'
        text+='| 原始样例 / 现有日志与原因 | 当前状态 |\n| --- | --- |\n'
        for source in b['sources']:
            s=by_source[source];text+='| '+link('`'+source+'`','migration/sample-reports/'+source+'.md')+' | '+s['status']+' |\n'
        text+='\n'
        if b['id']=='B4':text+='B4 中 packed↔triangular 两例登记为项目 HIP GPU 实现；其余优先生态库。`ormqr` 两端旧日志的 `X is undefined` 来自项目观测适配，修复该问题不应表述为 AMD 数学库不支持。\n\n'
        if b['id']=='B5':text+='原始 padding 样例重复给 `paddingLeft` 赋值，`paddingRight` 对应项实际默认为 0：保留这个原始 case，再独立添加左右非零 case，不能静默把注释当运行事实。trinary 的 A、D 各约 4 GiB，须另计中间张量/workspace；不据旧超时日志直接判硬件不支持。einsum 只要求原例 5 个表达式，原 parser 的 ellipsis/broadcast TODO 不计作已支持。\n\n'
        if b['id']=='B11':text+='此批是能力扩展研究目标，不能沿用“所有例子均为 SPD”的假设。尤其 `simple_residual` 默认是 GENERAL，`simple_get_set` 是 SYMMETRIC 并查询重排序/匹配/内存信息；先导库不满足时，保持失败/部分完成并给出缺口。\n\n'
    text+=BOUNDARIES
    text+='\n## 5. 全部 30 模块的去向\n\n| 模块 | PASSED / 总入口 | 尚未通过 | 已选批次 / 后续方向 |\n| --- | ---: | ---: | --- |\n'
    for family in CANDIDATES:
        rows=[s for s in cat['samples'] if s['family']==family];left=[s for s in rows if s['status']!='PASSED'];batches=list(dict.fromkeys(assigned[s['source']] for s in left if s['source'] in assigned))
        extra=sorted({disposition(s,assigned)[0] for s in left if s['source'] not in assigned})
        desc='、'.join(batches+extra) if left else '现有登记 profile 已验收；只保留回归与扩展 case，暂不新增批次。'
        text+='| '+link(family,family+'/README.md')+' | '+str(len(rows)-len(left))+'/'+str(len(rows))+' | '+str(len(left))+' | '+desc+' |\n'
    text+=ACCEPTANCE
    text+='\n<a id="inventory"></a>\n\n## 8. 473 个未通过入口的逐项计划索引\n\n以下是 2026-11-10 的计划基线，不是新的执行结果。每项都有批次或门槛/研究队列；链接打开原始详细错误、支持方式和历史 log。`U*` 是“当前指定路线不满足原契约”的计划分类，**不自动把 FAILED/PARTIAL 改成 UNSUPPORTED**。只有清单现有的 2 个 hipSPARSELt 项已具有 UNSUPPORTED 实测证据。\n\n'
    for family in CANDIDATES:
        group=[r for r in inventory if r['family']==family]
        if not group:continue
        text+='### '+family+'\n\n| 样例 / 原始详情与 log | 当前结果 | 计划去向 | 原因 / 条件 |\n| --- | --- | --- | --- |\n'
        for r in group:
            name=str(pathlib.PurePosixPath(r['source']).relative_to(family));text+='| '+link(name,r['detail'])+' | '+r['current_status']+' | '+r['planning_group']+' | '+r['planning_reason']+' |\n'
        text+='\n'
    path=ROOT/'migration/roadmap.md';path.write_text(text.rstrip()+'\n')
    canonical=ROOT.parent/'doc/cuda_samples_on_rocm_roadmap.md';canonical.write_bytes(path.read_bytes())
    print('Wrote',canonical,'and migration/roadmap.md;',len(assigned),'candidates,',len(inventory),'pending dispositions')


INTRO='''# CUDA Samples on ROCm：后续多批支持计划与能力边界

日期：2026-11-10。文档状态：**计划已制定，B4–B15 尚未执行；不构成新增支持声明**。

[12 批总览](#batches) · [当前无法等价支持的项目与原因](#limits) · [验收与日志规则](#acceptance) · [473 项逐例去向](#inventory)

## 1. 当前基线与计划目标

基线提交：`@HEAD@`。639 个入口中，**166 PASSED、6 PARTIAL、464 FAILED、2 UNSUPPORTED、1 BLOCKED**；已有 9 个合格模块、91 个按模块去重的算子/功能族。473 个入口尚未整例通过。第二批 17 例/45 cases、第三批 8 例/26 cases 已完成。M0–M5 “已执行”包含真实失败，不等于全库已支持。

后续按“接口修复与已知数学 → 布局/高级语义 → codec/科学算法 → 多进程/设备内计算”推进。每例优先 AMD 官方库，兼容层不适合时直接使用 roc*，需要项目 HIP/CPU 阶段时公开写明。所有原始 CUDA 源码/构建定义保持不变；新代码与观测适配独立保存。

AMD 固定 ROCm 10.1.0 immutable foundation（镜像 `sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03`）、R9700/gfx1201；HIP 7.16 为正常组件版本。CUDA 对照使用 nvidia-5090x2、CUDA 13.4.92/sm_120。物理 GPU3 禁止计算；每次启动按 PCI 映射及动态预约选卡，不沿用上批空闲假设。多节点和独占性能资源目前没有完成资格验证。

**“不可能支持”的准确边界：** 现有证据能够证明某个锁定版本/硬件/现成 API 路线不可用，或某种 NVIDIA 专属执行/二进制契约不能原样搬到 AMD；不能由此证明一个通用数学、图像或压缩算法在 AMD 上永远无法实现。第 4 节逐项说明“无法保持的是什么、证据是什么、改变什么条件可以恢复”。

本次只制定与发布计划，不启动新 GPU 实验，不改变逐例 status/required cases，不把 65 个候选预先算作通过。支持范围与全部 log 见[统一索引](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/support-log-index.md)，机读计划见[roadmap.json](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/roadmap.json)。
'''

BOUNDARIES='''
## 3. 未进入这 65 个样例的工作

其余队列不是“永远不做”。优先完成相关先导批次、检查实际 API/硬件能力，再选择 4–8 个入口组成新的批次。每个队列的当前失败样例都在第 8 节，不遗漏未通过入口。

| 队列 | 待做内容 | 升级成执行批次的条件 |
| --- | --- | --- |
| 低精度/算法语义 | 其余 3m、BF16x9、动态 mantissa emulation、FP8/MXFP8/NVFP4、planar complex/特殊 int8 布局 | 先核编码、scale 粒度、累加/舍入、合法 dtype 和 gfx1201 kernel；必须区分原生硬件、软件仿真和数学近似。不能用普通 GEMM 宣称已保留这些特性。 |
| solver 高级算法 | Xgesvdp/Xgesvdr、mixed-precision IRS、稀疏 QR、一般/复数/不定稀疏直接求解 | 有可运行 GPU 算法和原始接口/精度策略参考；CSRRF 的适用前提逐项满足。 |
| tensor 高级与 Python | block-sparse、3XTF32/JIT/cache、PyTorch/TensorFlow binding | 原始稀疏结构、计算精度、真实 JIT 和设备执行都被保留；单纯 NumPy/CPU 或 dense 改写不够。 |
| 其它 codec/媒体 | Cascaded/RLE、实验性 Deflate/GZIP/ZSTD 解码、CRC/GDS/manager、JPEG encoder/JPEG2000/TIFF | 先有正确方向的 GPU codec/CRC/I/O 路径及 CPU/CUDA 互操作语料。CPU 编码或容器解析可作为原例已有阶段，但不能代替原例要求的 GPU codec。 |
| NPP/NPP+ 其它算法 | 连通域、轮廓、Hough、watershed、签名距离变换、Python bindings | 先用 B15 建立 GPU 图像 pipeline、边界与 CPU oracle，再逐算子实现。 |
| 稀疏直接求解高级接口 | Schur complement、复杂重排序、allocator、hybrid memory/execute、线程回调、各种语言 | 不能把配置当装饰；数值路径、真实内存/线程/配置行为和错误处理均需独立验证。 |
| nvMatmulHeuristics | 配置生成/发现、runtime/能耗估计、SM carveout | hipBLASLt heuristics/Origami 仅是候选；先确认可用的 AMD 模型、测量与资源控制，不能只返回任意算法替代。 |
| 其余 MathDx/libmathdx/nvCOMPDx | 融合设备算子、JIT 生成器、device compression | B14 设备内试点成功后按算法扩展；不能跨用 host API 算作设备融合。 |
| cuPQC 非 SHA | ML-KEM、ML-DSA、Merkle、Poseidon2 | 独立 GPU 算法、标准已知答案/互操作测试；不能从 SHA-256/SHA3 推及其它算法，也不因样例正确就承诺安全审计/生产资格。 |
| cuEST 51 个入口 | 积分/梯度、DF/XC/PCM 等科学 API 与绑定 | 专项算法实现与独立科学参考；需要单列研发计划，不能用 BLAS 本身替代高层科学算子。 |

<a id="limits"></a>

## 4. 当前不能等价支持的项目、原因与恢复条件

### 4.1 已有明确证据的路线边界

| 编号 | 不能直接支持的内容 | 证据及原因 | 保留/替代方式与恢复条件 |
| --- | --- | --- | --- |
| U1 | 锁定 hipSPARSELt 在 gfx1201 上的原生 prune/compress/matmul 两个样例 | 已实际运行缺 kernel；锁定源码目标检查也拒绝 gfx1201。[实测与架构检查](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/upstream-support/hipsparselt-gfx1201-configure.log)、[归档目标列表](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/upstream-support/hipsparselt_supported_architectures.cmake)。 | 当前保持 2 UNSUPPORTED。换有匹配 kernel 的 GPU/SDK，或实现真实结构化稀疏 GPU 路线后重验；dense GEMM 不能冒充原生结构化稀疏。 |
| U2 | 通过当前 hipSOLVER `Xgeev` 兼容路径获得纯 GPU 一般特征分解 | AMD 官方说明该路线转 CPU LAPACK；AMD 上能运行不是 GPU 算法证据。[hipSOLVER General eigensolvers](https://rocm.docs.amd.com/projects/hipSOLVER/en/latest/reference/intro.html#general-eigensolvers)。 | Xgeev 三例保持 PARTIAL，第四例保留现有构建失败。可以另记“CPU 功能可用”，但不计 GPU；恢复需原生/自有 GPU 一般特征求解并验证左右特征向量等契约。 |
| U3 | 用当前 `gesvdaStridedBatched` 包装实现原始近似 SVD + residual norm 契约 | 官方说明其 partial SVD 为精确算法且不计算残差范数。[hipSOLVER Partial SVD](https://rocm.docs.amd.com/projects/hipSOLVER/en/latest/reference/intro.html#partial-svd-functions)。 | 保持 PARTIAL；另写满足原始算法与残差语义的 GPU 实现，或明确只交付“数学子集”。不能仅补打印一个残差就宣称算法语义等价。 |
| U4 | 用锁定 hipCOMP 直接完成 Bitcomp、ANS、GDeflate 的原 codec/bitstream 互操作 | 固定 commit 支持表把三者标为未支持；Deflate/GZIP/ZSTD 也只有实验性解码，不能推成双向。[固定 hipCOMP 支持表](https://github.com/ROCm/hipCOMP-core/blob/03df9f7369211ee15d370817165224c73fdc9a46/README.md#algorithm-support)。 | 当前是“库路线缺失”，原例仍 FAILED，不扩大为硬件 UNSUPPORTED。通用算法并非永远不可做；需独立兼容 GPU codec、公开格式与 CUDA/CPU 互解证据。 |
| U5 | 在 AMD 上原样复现 CUDA Green Context 的 NVIDIA SM 资源契约/ABI | 原例使用 cudaDevSmResourceSplitByCount、cudaGreenCtxCreate 和专属 stream/context；普通 SGEMM 不包含这些功能。[原始样例](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/cuBLASLt/LtSgemmGreenContext/sample_cublasLt_LtSgemmGreenCtx.cu)。 | 原 NVIDIA 对象/SM 资源语义不能原样成为 AMD 对象；可研究 AMD CU 资源控制的功能替代，但需单列语义适配证据，不能默认 stream 顶替。 |

### 4.2 尚无充分证据判成“不可能”的内容

| 内容 | 当前结论与限制 | 下一步证据门槛 |
| --- | --- | --- |
| cuSPARSE 通用压缩内存分配 | 旧草稿只暴露未适配的 CUDA 符号。HIP 也定义 VMM/分配属性，结构字段存在并不说明压缩真的可用；当前不足以宣称硬件不支持。 | 检查锁定 runtime 的属性/枚举，真实 create/map/query，验证压缩属性被采纳和正确性；不能用普通未压缩 hipMalloc 假装通过。[HIP VMM](https://rocm.docs.amd.com/projects/HIP/en/latest/how-to/hip_runtime_api/memory_management/virtual_memory.html)。 |
| JPEG 编码、JPEG2000、TIFF | 现有 rocJPEG 路线提供 JPEG 解码，不是这三类 GPU codec 的实现；这不是这些编码数学上不可实现的证明。[rocJPEG 定位](https://rocm.docs.amd.com/projects/rocJPEG/en/latest/)。 | 新 GPU codec 或自有实现；分别核验输入精度、码流、质量、metadata/ROI/多页；CPU OpenJPEG/libtiff 只能作为容器/参考阶段。 |
| hipTensor FP32 contraction 与 gfx1201 | 项目原生路线曾报 ARCH_MISMATCH，但 rocBLAS + HIP 的数学替代已验收一个原始 profile。不能把这次原生缺口推广成所有 tensor 不可支持。 | B5 保留 dtype 与布局，检查每个后端实际支持；JIT/cache/稀疏布局功能需另外实现，不能只看数学结果。 |
| FP8/FP4/MX/BF16x9/3XTF32 | 格式、缩放、舍入、硬件指令和算法并不自动跨厂商等价；旧编译失败不构成永久不支持。 | 显式数据格式转换与软件/原生精度证据；需要保留原始精度策略，软件仿真必须标注且不承诺原生性能。 |
| NVIDIA 设备二进制、私有 descriptor/cache、算法 ID | NVIDIA 机器码/驱动对象/不透明缓存不能不经转换直接视作 AMD 可执行对象；算法编号和性能选择不是跨库通用协议。 | 有源代码时做 AMD 重写并记录边界；需要私有算法/格式但没有合法可用实现或参考时保持阻塞。可替代的是功能契约，不是宣称二进制可互换。 |
| 多节点通信、NVSHMEM 特有语义、distributed allocator | 本项目当前没有合格多节点验收环境；RCCL 的存在不等于原始分布式算法与所有网络能力可用。 | 原模型需要的节点数、NIC/驱动、GPU-aware MPI/通信路径与数据分布逐项实测。单机两卡通过不当作多节点通过。 |
| MathDx / NPP / cuEST / cuPQC | 原始前端/SDK/算法大多尚未改写，是研发缺口。不能由缺 NVIDIA 头文件推出 AMD 不能做相同数学功能。 | 按设备执行/科学/图像/密码契约开发与独立验证，先小试点后扩展；见 B14/B15 与研究队列。 |

**范围结论：没有证据支持把其余 471 个未通过入口统统标为硬件“不可能支持”。** 现有清单仅 2 项具有锁定栈 UNSUPPORTED 结论；U2–U5 是具体路线/契约边界，原始状态继续保持。未来升级库也必须新建环境/依赖锁和实测证据，不能覆盖旧失败记录。
'''

ACCEPTANCE='''
<a id="acceptance"></a>

## 6. 每批必须满足的验收与日志要求

1. **启动前锁定契约。** 固定原始样例路径/source hash、dtype/layout/执行模型、必需 case 和误差规则；先写 `batchN` 清单再跑。本文 case 是设计草案，不能根据输出好坏事后删除必需 case。
2. **分开报告能力。** 头文件/链接存在、GPU 实际执行、独立数值通过、原始完整功能、性能资格分别记录。候选库没有运行证据时不写成“已使用成功”。
3. **保留原始规模与语义。** 小尺寸可用于调试与全量 CPU oracle；不能只跑缩小输入就宣称原始 profile 通过。原始大规模如只抽样检查，明确抽样策略/覆盖率，不能称全输出通过。缓存、allocator、设备内调用、多 rank/多 GPU 不能省略。
4. **三方核对。** AMD 与 5090 CUDA 使用共享输入或可重建输入 hash；CPU 独立参考检查全部适用输出、结构与残差。跨库 RNG 不要求同序列，压缩/JPEG/密码分别按码流互操作、像素容差和已知答案验收。CUDA vendor SDK 基线缺失明确记 BLOCKED，同实现 CUDA 另记范围。
5. **反向检查。** 注入有限值错误、NaN、布局/indices 错误、错误 info、空图/假缓存等适用错误，确认 oracle 拒绝；不能使用程序自身 expected 输出作为唯一参考。
6. **数值和性能分开。** 共享卡可做正确性；只有通过空闲/资源资格且重复统计有效才发布速度比。现有 6 个 GEMM 性能结果仍 BLOCKED，本计划不自动解除。
7. **每步更新 MD。** 每个实现步骤后追加设计实施日志；每批更新 sample status、actual/backend library、源码、reason、required/passed cases、CPU/CUDA 证明和恢复条件。失败也要归档，状态不靠口头总结改变。
8. **统一证据。** 每个样例/输入保留 build.log、run.log、commands.json、environment、源码/输入 hash、结构化误差/阈值/info 与实际 GPU/图/通信语义；小型文本入 Git，大二进制记 hash/生成方法。更新支持方式与详细 log 总表，再提交并校验 fork 首页。

每批可交付 PASSED、PARTIAL、FAILED、BLOCKED 或有充分范围证据的 UNSUPPORTED；交付的要求是实现结果、证据和原因完整。不能以“执行完计划”替代“每个目标都成功”。

## 7. 数量预期、资源和发布方式

- **近期条件上限：** B4–B6 的 16 个候选若都保留原始功能并通过验收，样例可从 166 增至 182。它们当前仍为未通过，文档没有预先增加支持数。
- **全部候选条件上限：** 65 例若最终全部合格，样例上限为 231；条件研究批次不提供成功保证。91 个算子/功能族不能简单加 65，batch/dtype/布局/API 变体需按现有规则去重。
- **资源：** B4–B11 主要单 GPU 正确性；B12/B13 至少两卡且部分必须多进程/多节点；B14 需设备编译/JIT 工具链；codec/媒体需语料、CPU 参考库和独立 CUDA SDK。所有依赖使用项目 overlay，不修改共享 foundation。
- **调度：** 每批完成后根据真正失败 gate、GPU 可用性和新库版本调整后续优先级，更新本文版本。没有实测依据时不承诺固定日期或吞吐。
- **文件：** 用户工作区 `doc/cuda_samples_on_rocm_roadmap.md`；fork 可读副本 `migration/roadmap.md`；机器清单 `migration/roadmap.json`；原始设计 `doc/cuda_samples_on_rocm_design.md` / `migration/design.md`。本计划通过 `python3 tools/migration/roadmap.py` 从逐例清单生成；生成不会执行 GPU，也不会修改实测状态。

参考依据：本仓库的逐例/环境锁/原生失败日志优先于浮动文档。hipCOMP 使用固定 commit `03df9f7369211ee15d370817165224c73fdc9a46`，hipTensor 与架构材料来自固定 `380ea3ec237d03c4a384b4ed4c49fda82d9f81dd`；其它 AMD 官方文档于 2026-11-10 核对，latest 内容不能替代锁定镜像中的实际能力。hipBLAS Ex/hipBLASLt/rocSOLVER 的 API 是候选路线依据，不是本批新增成功证据。

- [实际库选择、成功边界与恢复条件](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/ecosystem-decisions.md)
- [完整样例支持方式与日志](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/support-log-index.md)
- [项目环境锁](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/environments/project.lock.json) · [可选库固定版本](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/environments/optional-dependencies.lock.json)
- [hipBLAS Ex API](https://rocm.docs.amd.com/projects/hipBLAS/en/latest/reference/hipblas-api-functions.html#blas-extensions) · [hipBLASLt](https://rocm.docs.amd.com/projects/hipBLASLt/en/latest/index.html) · [rocSOLVER LAPACK](https://rocm.docs.amd.com/projects/rocSOLVER/en/latest/reference/lapack.html)
'''

if __name__=='__main__':main()
