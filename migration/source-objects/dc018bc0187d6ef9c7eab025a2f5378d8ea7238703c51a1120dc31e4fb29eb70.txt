#!/usr/bin/env python3
"""Deduplicate qualified sample profiles into explicitly scoped operator families."""
import collections,json,pathlib,re
from catalog import ROOT,CANDIDATES

def operator_name(sample):
 family=sample['family'];path=pathlib.PurePosixPath(sample['source']);kind=path.parent.name.lower()
 if family=='cuBLAS':
  if 'dotc' in path.name.lower():return 'dotc'
  if kind.startswith(('cherk','csyrk')):kind=kind[1:]
  while True:
   normalized=re.sub(r'(stridedbatched|groupedbatched|batched|autotuning|3m|ex)$','',kind)
   if normalized==kind:return kind
   kind=normalized
 if family=='cuBLASLt':return 'GEMM'
 if family=='cuDSS':return '稀疏 SPD 直接求解'
 if family=='cuFFT':
  if 'callback' in sample['source']:return 'FFT 窗口过滤 callback'
  return 'R2C/C2R 实数 FFT' if 'r2c' in sample['source'] or 'c2r' in sample['source'] else 'C2C 复数 FFT'
 if family=='cuPQC':return 'SHA3-256' if 'sha3' in path.name else 'SHA-256'
 if family=='cuRAND':return re.search(r'_(lognormal|normal|uniform|poisson)_example',path.name)[1]
 if family=='cuSOLVER':
  if kind in {'syevd','xsyevd','syevj','syevjbatched','syevdx','xsyevdx'}:return '对称特征分解'
  if kind in {'sygvd','sygvj','sygvdx'}:return '广义对称特征分解'
  if kind in {'gesvd','gesvdj','gesvdjbatched','xgesvd'}:return 'SVD'
  return {'getrf':'LU 分解/求解','xgetrf':'LU 分解/求解','ormqr':'QR 的 Q 应用','xtrtri':'三角矩阵求逆','orgqr':'QR 的 Q 生成','xgeqrf':'QR 分解','xpotrf':'Cholesky 分解','potrfbatched':'Cholesky 分解'}[kind]
 if family=='cuSPARSE':
  if kind=='graph_capture':return 'SpVV Graph Capture/Replay'
  if kind.startswith('dense2sparse'):return 'dense2sparse'
  if kind.startswith('sparse2dense'):return 'sparse2dense'
  return kind.split('_')[0]
 if family=='cuTENSOR':return {'contraction':'张量 contraction','contraction_trinary':'张量 contraction','contraction_plan_cache':'张量 plan cache','einsum':'张量 einsum','elementwise_permute_padding':'张量 permutation','elementwise_binary':'二元逐元素运算','elementwise_trinary':'三元逐元素运算','elementwise_permute':'张量 permutation','reduction':'张量 reduction'}[path.stem]
 raise ValueError('Qualified family needs an explicit operator grouping: '+family)

SCOPES={
 'cuBLAS':'固定教学输入与所列扩展 cases；第二批含并列/空索引、旋转 flags、batch/grouped 和正负 alpha；rotmg 极端缩放使用明确登记的 HIP 修正。其它精度/API 仍逐例管理。',
 'cuBLASLt':'3 个 profile：FP32 SGEMM、HSH FP16 input/output + FP32 compute 的 pointer-array 与 strided batch。',
 'cuDSS':'原始 FP64 5×5 SPD/CSR：C++、Fortran、CUDA Fortran 改写共 3 入口；CPU 稀疏符号分析 + GPU CSRRF 数值分解/求解。',
 'cuFFT':'10 个 profile：原始单卡/双卡 C2C、实数正逆变换和 legacy/离线 SPIR-V/HIPRTC callback。1D 多卡使用 hipFFT + RCCL + HIP。',
 'cuPQC':'SHA-256 单线程与 SHA3-256 的 32-lane 协作 GPU kernel；各 14 输入与 hashlib 精确一致，PQC 其它算法未实现。',
 'cuRAND':'4 种分布 × 9 个 generator = 36 个 profile；原始参数、库内重复性和解析分布矩通过，跨库不要求逐位同序列。',
 'cuSOLVER':'原始固定教学矩阵；检查 status/info、特征值/奇异值、重构、求解残差与正交性。第三批覆盖 batched SVD/未排序特征对、索引/值域/全量/空区间与实际 meig。',
 'cuSPARSE':'CSR/COO/SELL/blocked-ELL 等已登记格式与 batched 变体；SpVV/SpGEMM/reuse 数值变化与 CSR 结构；第三批 CG/BiCGSTAB 的独立求解、残差/收敛，gpsv 的逐 batch interleaved 布局，以及真实 GPU 图捕获/输入变化 replay。',
 'cuTENSOR':'FP32：contraction 用 rocBLAS + HIP；其它已通过的逐元素/permutation/reduction 使用 hipTensor。逐例记录原始 extents 与扩展小尺寸、全部输出 CPU 检查；contraction 的原始规模另为抽样验收。'}

SCOPES.update({
 'cuBLAS':'固定教学profile与所列扩展cases；含复杂rank-k类型化适配、HIP GPU packed转换、FP32分组batched及FP64项目策略调优。rotmg极端缩放使用HIP修正；调优/批量变体按同一数学族去重。',
 'cuBLASLt':'6个profile：原FP32 SGEMM、HSH pointer-array/strided batch，以及B7 HSH grouped分发与SGEMM custom-find/autotune。FP16输入/输出、FP32累加、bias、候选全输出、workspace=0及所选方案重放通过；分发适配不等于原生device-grouped API。',
 'cuSOLVER':'原始FP64教学矩阵；status/info、全量分解/重构、残差、正交性、未排序配对及实际meig检查。B6增加64位LU/三角求逆；SVD/eigen typed接口显式INT_MAX限制。',
 'cuSPARSE':'已登记CSR/COO/SELL/BSR等格式、CG/BiCG残差/收敛、gpsv布局和真实Graph replay。B8补CSR→CSC、对称展开、HIP GPU预算分块SpGEMM和融合custom op；3项CUDA新API缺失，使用明确标注的兼容数学基线。',
 'cuTENSOR':'FP32：hipTensor逐元素/排列/规约；rocBLAS+HIP contraction；B5补HIP padding、einsum路由、三输入收缩和真实GPU分块搜索/持久化缓存。B2/B5全部原始规模输出均有全量FP64 CPU检查；早期M3 contraction仅抽样的历史证据另保留。'})

def summarize(cat):
 families={};total_operators=0
 for family in CANDIDATES:
  samples=[s for s in cat['samples'] if s['family']==family];groups=collections.defaultdict(list)
  for s in samples:
   if s['status']=='PASSED':groups[operator_name(s)].append(s)
  operations=[{'name':name,'sample_ids':[s['id'] for s in rows],'sample_reports':['migration/sample-reports/'+s['source']+'.md' for s in rows],'source_profiles':len(rows)} for name,rows in sorted(groups.items())];counts=collections.Counter(s['status'] for s in samples);total_operators+=len(operations)
  families[family]={'verified_operator_family_count':len(operations),'verified_operators':operations,'sample_count':len(samples),'sample_outcomes':dict(counts),'validation_scope':SCOPES.get(family,'尚无通过整例验收的算子族。'),'failure_reason_counts':dict(collections.Counter(s['reason_code'] for s in samples if s['status'] not in {'PASSED','PARTIAL'}))}
 return {'schema_version':1,'counting_rule':'Operator/functional families are deduplicated within each module; dtypes, sizes, language, batch, storage formats and algorithm variants do not create extra operators. At least one explicitly scoped PASSED source profile is required. Cross-module totals may include the same mathematical operation implemented through different library interfaces.','qualification_rule':'A verified family proves only its linked PASSED source profiles/required cases, not every API configuration. PARTIAL examples and capability probes are excluded.','verified_operator_families':total_operators,'modules_with_verified_operators':sum(bool(v['verified_operator_family_count']) for v in families.values()),'passed_source_profiles':sum(s['status']=='PASSED' for s in cat['samples']),'modules':families}

def render_overview(report,prefix=''):
 text='## 已验收算子与验证范围\n\n'
 text+=f'**{report["modules_with_verified_operators"]} 个模块已有整例通过，覆盖 {report["verified_operator_families"]} 个按模块去重的算子/功能族，对应 {report["passed_source_profiles"]} 个通过的样例入口。**\n\n'
 text+='计数按数学算子或原例核心功能归并；同模块的精度、尺寸、语言、batch、存储格式和算法变体不重复增加算子数。例如 cuRAND 是 4 种分布、36 个 generator/distribution profile；cuDSS simple 的 3 种语言入口算 1 个功能族。跨模块总数保留不同库接口的实现，GEMM 可分别出现在 cuBLAS 与 cuBLASLt。每个族至少有一个通过独立验收的样例，支持范围限于下表和逐例 required cases。\n\n'
 text+='| 模块 | 已验收算子/功能族数 | 已验收算子/功能 | 通过样例 | 验证范围 |\n| --- | ---: | --- | ---: | --- |\n'
 for family,row in report['modules'].items():
  if not row['verified_operator_family_count']:continue
  names='、'.join('`'+v['name']+'`' for v in row['verified_operators']);text+=f'| [{family}]({prefix}{family}/README.md) | {row["verified_operator_family_count"]} | {names} | {row["sample_outcomes"].get("PASSED",0)} | {row["validation_scope"]} |\n'
 text+='\n以下仅有子集/能力探针，**不计入上述整例支持数**：\n\n| 模块 | 已验证子集 | 原始样例尚缺什么 |\n| --- | --- | --- |\n'
 text+='| nvCOMP | hipCOMP LZ4 单 chunk，128/32768/65536 字节 GPU byte-exact 往返 | 现代 status/options、完整 batch/manager 与其它 codec；1 PARTIAL、0 PASSED |\n'
 text+='| nvJPEG | rocJPEG hardware backend：64×64 baseline JPEG → RGB，CPU libjpeg 最大像素差 2 | 全部原始输入/格式、CLI、batch、多实例、ROI、编码；1 PARTIAL、0 PASSED |\n'
 text+='| NPP | RPP HIP U8 c1/c3、32×24 identity resize 探针 | 原始 Canny、distance transform、label/watershed 等算子未实现；0 PASSED |\n'
 text+=f'\n逐个算子族与样例的可追溯映射见 [operator-support.json]({prefix}migration/reports/operator-support.json)；失败仍按具体入口和原因保留。\n\n'
 return text

def write_reports(cat):
 report=summarize(cat);p=ROOT/'migration/reports';(p/'operator-support.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');(p/'operator-support.md').write_text(('# 算子支持与统计口径\n\n'+render_overview(report,'../../')).rstrip()+'\n');return report

if __name__=='__main__':
 report=write_reports(json.loads((ROOT/'migration/samples.yaml').read_text()));print(report['verified_operator_families'],'operator families;',report['modules_with_verified_operators'],'modules;',report['passed_source_profiles'],'profiles')
