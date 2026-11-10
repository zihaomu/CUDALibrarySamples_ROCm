#!/usr/bin/env python3
"""Live measured support and limitations for every B12--B15 target."""
import json,collections,datetime
from catalog import ROOT
from batches12_15_spec import GROUPS,ROUTES,LIMITS,kind,route
cat=json.loads((ROOT/'migration/samples.yaml').read_text());samples={s['source']:s for s in cat['samples']}
def read(name):
 p=ROOT/'migration/reports'/name;return {r['source']:r for r in json.loads(p.read_text())} if p.exists() else {}
proof=read('batches12_15-validation.json');amd=read('batches12_15-rocm.json');rows=[];totals=collections.Counter(s['status'] for s in cat['samples']);body='# B12–B15 实施、支持方式与逐例日志\n\n更新时间：'+datetime.datetime.now(datetime.timezone.utc).isoformat()+'。20个目标；原始vendor基线、兼容CUDA数学对照、CPU参考与未完成原例合同分开记录。\n\n'
for group,sources in GROUPS.items():
 full=partial=cases=0;body+='| '+group.upper()+' 原始入口 / 详细日志 | 实际AMD路线 | 当前结果 | 原例合同缺口 / 原因 |\n| --- | --- | --- | --- |\n'
 for source,required in sources.items():
  r=proof.get(source);attempt=amd.get(source);state=r['contract_status'] if r else 'AMD已运行/待验收' if attempt and not attempt['build_return_code'] else '构建/实施中';full+=state=='PASSED';partial+=state=='PARTIAL';cases+=len(r['cases']) if r and r['status']==r['cuda_comparison']=='PASSED' else 0;missing=LIMITS.get(kind(source),(None,'登记profile；扩展其它精度/规模/执行模型需要新验收。'))[1];body+='| ['+source+'](../sample-reports/'+source+'.md) | '+route(source)+' | '+state+' | '+missing+' |\n'
 body+='\n';rows.append(dict(batch=group.upper(),samples_required=len(sources),samples_passed=full,samples_partial=partial,cases_verified=cases,cases_required=sum(map(len,sources.values()))))
intro='**本轮：'+str(sum(r['samples_passed'] for r in rows))+'整例支持、'+str(sum(r['samples_partial'] for r in rows))+'部分支持；'+str(sum(r['cases_verified'] for r in rows))+'/120 case完成AMD／独立CPU／同输入兼容CUDA验收。** 全项目'+str(totals['PASSED'])+' PASSED、'+str(totals['PARTIAL'])+' PARTIAL、'+str(totals['FAILED'])+' FAILED。\n\n';body=body.replace('| B12 原始入口',intro+'| B12 原始入口',1)
body+='''B12 使用两个MPI进程，按PCI确认不同GPU；block-cyclic输入/本地输出、gemr2d重分布往返和真实RCCL AllGather/AllReduce/ReduceScatter独立检查。geadd保持原例FP64，collective试点为FP16输入native GemmEx + FP32通信/累加 + GPU FP16量化，舍入/量化高级模式没有被算作完整支持。CPU只做布局编排，数值运算/collective在GPU。

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
'''
(ROOT/'migration/reports/batches12-15.md').write_text(body);progress=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),batches=rows,project_counts=dict(totals));(ROOT/'migration/reports/batches12-15-progress.json').write_text(json.dumps(progress,indent=2)+'\n');print(rows)
canonical=ROOT.parent/'doc/cuda_samples_on_rocm_roadmap.md'
if canonical.exists():
 text=canonical.read_text();start='<!-- B12B15_PROGRESS:START -->';end='<!-- B12B15_PROGRESS:END -->';banner=start+'\n\n**B12–B15实施：** '+'；'.join(r['batch']+' '+str(r['samples_passed'])+'整例/'+str(r['samples_partial'])+'部分，'+str(r['cases_verified'])+'/'+str(r['cases_required'])+'case' for r in rows)+'。详见[实施与缺口表](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/rocm/migration/reports/batches12-15.md)。\n\n'+end+'\n\n'
 if start in text:text=text.split(start)[0]+banner+text.split(end,1)[1].lstrip('\n')
 else:text=text.replace('## 1. 当前基线与计划目标',banner+'## 1. 当前基线与计划目标',1)
 text=text.replace('B12–B15尚未启动','B12–B15实施结果见实时表');canonical.write_text(text);(ROOT/'migration/roadmap.md').write_text(text)
