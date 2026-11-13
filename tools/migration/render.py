#!/usr/bin/env python3
"""Generate per-entrypoint, family and root status pages from observed evidence."""
import collections,json,os,pathlib,re,subprocess
from catalog import ROOT,CANDIDATES,BASE
from operator_support import write_reports
from support_log_index import write_index
STATES=['PASSED','PARTIAL','FAILED','BLOCKED','UNSUPPORTED','NOT_STARTED','IN_PROGRESS']
def link(label,target,parent):return '['+str(label).replace('|','/')+']('+os.path.relpath(target,parent).replace(' ','%20')+')'
def safe(text):return str(text or '—').replace('|','/').replace('\n',' ')
def display_library(value):
 names={x.lower():x for x in ['hipBLAS','hipBLASLt','hipSPARSE','hipSPARSELt','hipSOLVER','hipFFT','hipRAND','hipTensor','hipCOMP','rocBLAS','rocSPARSE','rocSOLVER','rocFFT','rocRAND','rocJPEG']}
 return re.sub(r'\b(?:'+ '|'.join(names)+r')\b',lambda m:names[m[0].lower()],value,flags=re.I)
def detail_path(s):return ROOT/'migration/sample-reports'/(s['source']+'.md')
def render():
 cat=json.loads((ROOT/'migration/samples.yaml').read_text());decisions=json.loads((ROOT/'migration/ecosystem-decisions.json').read_text());operators=write_reports(cat);write_index(cat);groups=collections.defaultdict(list)
 for s in cat['samples']:groups[s['family']].append(s)
 counts=collections.Counter(s['status'] for s in cat['samples']);totals='；'.join(f'{k}: {counts[k]}' for k in STATES)
 for s in cat['samples']:
  q=detail_path(s);q.parent.mkdir(parents=True,exist_ok=True);lines=['# '+s['id'],'',f'**{s["status"]} / {s["level"]}**','',s['reason'],'', '| 字段 | 当前记录 |','| --- | --- |',f'| 原始入口 | {link(s["source"],ROOT/s["source"],q.parent)} |',f'| 实际库 / 后端 | {safe(s.get("actual_library"))} / {safe(s.get("backend_library"))} |',f'| 候选路线 | {safe(", ".join(s["candidate_libraries"]))} |',f'| 代码 | {link(s["implementation"],ROOT/s["implementation"],q.parent) if s.get("implementation") else "无实现"} |',f'| required cases | {len(s["passed_cases"])}/{len(s["required_cases"])} |',f'| CUDA baseline / comparison | {s["cuda_baseline"]} / {s["cuda_comparison"]} |',f'| 性能 | {s["benchmark"]} |',f'| 原始源码 SHA256 | `{s["source_sha256"]}` |','', '编译/运行返回 0 仅对应 L3；通过独立参考检查后才记 L4。失败的候选库不列为已使用库。','']
  if s['required_cases']:lines+=['必需用例：'+', '.join('`'+x+'`' for x in s['required_cases'])+'。','']
  lines+=['实现方式：`'+s.get('equivalence','未登记')+'`。','', '恢复/扩展条件：'+s.get('retry_condition','见当前失败原因')+'','']
  if s.get('cuda_comparison_reason'):lines+=['CUDA 对照限制：'+s['cuda_comparison_reason'],'']
  if s.get('cuda_vendor_comparison')=='BLOCKED':lines+=['CUDA SHA 检查使用同一自有实现；NVIDIA cuPQC vendor SDK 基线不可用，两者范围分别记录。','']
  if s.get('original_port'):
   a=s['original_port'];lines+=['## 原始 API 自动移植稿最近一次尝试','', '该记录与上表选定的手写/替代实现分别保留。','',safe(a.get('reason')),'', '尝试库：'+safe(', '.join(a.get('attempted_libraries',[])))+'；实现 hash：`'+a.get('implementation_sha256','')+'`。','']
  lines+=['## 复现与证据','', '从仓库根目录，先核对物理 GPU 占用。HIP ordinal 与物理编号不同；项目 guard 根据 PCI 地址拒绝 GPU3 和被预约的卡。','']
  if s.get('reproduce'):lines+=[('在仓库根目录运行：GPU 构建/执行由 launcher 进入锁定容器，CPU 验收在宿主 Python3.12；先按对应批次报告同步 CUDA 证据。' if s.get('reason_code') in {'VALIDATED_BATCH2','VALIDATED_BATCH3','VALIDATED_B4_B8','VALIDATED_B9_B11','VALIDATED_B9_B11_SUBSET','VALIDATED_B12_B15','VALIDATED_B12_B15_SUBSET'} else '在已锁定并通过 guard 的 ROCm 10.1.0 容器中（多 GPU 用例须暴露两个允许的设备）：'),'', '```bash',s['reproduce'],'```','']
  elif s.get('implementation','') and not s['implementation'].startswith('rocm/ported/') and s['implementation'].endswith('sample.cpp') and s['family']!='cuDSS':
   f=str(pathlib.Path(s['implementation']).parent.relative_to('rocm'));lines+=['```bash','HIP_VISIBLE_DEVICES=2 tools/migration/run_rocm.sh --filter '+f,'```','']
  else:lines+=['具体命令见该入口证据目录中的 `commands.json`，运行环境见同批 `environment.json`。批量入口：`tools/migration/bulk_run.py --families <family>`；特殊驱动见专项报告。','']
  lines += ['- '+link(e,ROOT/e,q.parent) for e in dict.fromkeys(s['evidence'])]
  q.write_text('\n'.join(line.rstrip() for line in lines).rstrip()+'\n')
  # Keep the established M1 implementation README entry points.
  if (s.get('implementation') or '').endswith('/sample.cpp') and not s['implementation'].startswith('rocm/ported/'):
   r=(ROOT/s['implementation']).parent/'README.md';r.write_text('# '+s['id']+' 的 ROCm 实现\n\n'+s['reason']+'\n\n'+link('逐例状态、命令与证据',q,r.parent)+'\n')
 for family in CANDIDATES:
  p=ROOT/family/'README.md';samples=groups[family];c=collections.Counter(s['status'] for s in samples);a='<!-- ROCM-MIGRATION:START -->';b='<!-- ROCM-MIGRATION:END -->'
  rows=[a,'## ROCm 支持情况','',f'{len(samples)} 个独立源入口；'+ '，'.join(f'{state} {c[state]}' for state in STATES)+ '。','', '候选库：'+', '.join(CANDIDATES[family])+'。候选不等于已使用；基础探针成功也不等于整库迁移成功。','',decisions[family]['reason'],'','| 原始样例 / 逐例详情 | 实际库 / 后端 | 程度 / 状态 | 已覆盖 / 缺失功能与成功或失败原因 | CUDA baseline / 对照 | 证据 |','| --- | --- | --- | --- | --- | --- |']
  for s in samples:
   libs=(s.get('actual_library') or '未验证使用库')+(' / '+s['backend_library'] if s.get('actual_library') and s.get('backend_library') else '');ev='；'.join(link('记录',ROOT/e,p.parent) for e in s['evidence'][-2:]) or '—';label=str(pathlib.Path(s['source']).relative_to(family));rows.append('| '+link(label,ROOT/s['source'],p.parent)+' · '+link('详情',detail_path(s),p.parent)+' | '+safe(libs)+' | '+s['level']+' / '+s['status']+' | '+safe(s['reason'])+' | '+s['cuda_baseline']+' / '+s['cuda_comparison']+' | '+ev+' |')
  rows+=['','生成来源：'+link('migration/samples.yaml',ROOT/'migration/samples.yaml',p.parent)+'；执行 `python3 tools/migration/render.py` 更新。',b]
  content=p.read_text() if p.exists() else '# '+family+'\n'
  if a in content:content=content.split(a)[0]+content.split(b,1)[1].lstrip('\n')
  prefix=content.rstrip();original=subprocess.run(['git','show',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT,capture_output=True)
  if original.returncode==0 and original.stdout.decode().replace('\r\n','\n').rstrip()==prefix:prefix=original.stdout.decode().rstrip('\r\n')
  p.write_bytes((prefix+'\n\n'+'\n'.join(rows)+'\n').encode())
 p=ROOT/'README.md'
 routes={
  'nvJPEG':'项目 HIP JPEG 编码；CPU marker/DHT 编排',
  'cuBLAS':'hipBLAS / rocBLAS + HIP',
  'cuBLASLt':'hipBLASLt、hipBLAS / rocBLAS + HIP 布局转换',
  'cuBLASMp':'MPI + RCCL + HIP',
  'cuDSS':'rocSOLVER / rocBLAS + HIP、CPU 符号分析、项目描述符 ABI',
  'cuFFT':'hipFFT / rocFFT + HIP / HIPRTC；多卡使用 RCCL',
  'cuFFTMp':'MPI + hipFFT + RCCL + HIP',
  'cuPQC':'项目 HIP SHA 实现',
  'cuRAND':'hipRAND / rocRAND',
  'cuSOLVER':'hipSOLVER / rocSOLVER + HIP；多卡使用 RCCL',
  'cuSPARSE':'hipSPARSE / rocSPARSE + hipBLAS + HIP / HIP Graph',
  'cuSPARSELt':'项目 HIP 2:4 裁剪、压缩和稀疏乘法',
  'cuTENSOR':'hipTensor、rocBLAS + HIP',
  'cuTENSORMg':'hipBLAS + RCCL + HIP',
  'MathDx/cuBLASDx':'调用方 HIP kernel 内的协作计算',
  'MathDx/cuFFTDx':'调用方 HIP kernel 内的 FFT',
  'MathDx/cuSolverDx':'调用方 HIP kernel 内的分解和求解',
  'NPP':'项目 HIP 图像处理实现',
  'NPP+':'项目 HIP 图像处理 + ROCm Torch',
  'nvCOMP':'hipCOMP + 项目 HIP CRC 实现',
 }
 intro='''[![License](https://img.shields.io/badge/License-Apache_2.0-yellowgreen.svg)](LICENSE.md)

# CUDA Library Samples on ROCm

将 NVIDIA CUDA Library Samples 逐例实现为 ROCm 版本，按原例功能选择 AMD 生态库、HIP 算法或明确标注的 CPU/GPU 混合实现。原始 CUDA 样例保留作参考。

[算子支持方式与完整验证记录](migration/reports/support-log-index.md) · [已验收算子清单](migration/reports/operator-support.md) · [构建与复现](migration/usage.md) · [项目文档](migration/README.md)

## 整体支持情况

'''
 intro+=f'覆盖 **{len(CANDIDATES)} 个模块、{len(cat["samples"])} 个独立样例入口**；其中 **{operators["modules_with_verified_operators"]} 个模块已有整例通过**，共 **{operators["verified_operator_families"]} 个按模块去重的算子/功能族**。\n\n'
 intro+='| 当前结论 | 入口数 |\n| --- | ---: |\n'
 for status,label in [('PASSED','已通过'),('PARTIAL','部分支持'),('FAILED','尚未通过'),('UNSUPPORTED','确认不支持'),('BLOCKED','前置条件阻塞')]:
  if counts[status] or status in {'PASSED','PARTIAL','FAILED'}:intro+=f'| {label}（{status}） | {counts[status]} |\n'
 pending=len(cat['samples'])-counts['PASSED']
 intro+=f'\n尚未整例通过 **{pending} 个入口**。通过结论限于该入口登记的原始功能和必需用例；精度、规模、语言、batch 和存储变体不重复增加算子数。未通过原因、部分实现范围和重现日志统一列在[详细记录](migration/reports/support-log-index.md)。\n\n'
 intro+='## 模块支持矩阵\n\n路线列对应已通过样例的实际实现。部分支持与失败入口的实现、限制和证据见各模块详情。\n\n'
 intro+='| 模块 / 详细记录 | 已验收实现路线 | 算子/功能族 | 通过/总入口 | 部分 | 失败 |\n| --- | --- | ---: | ---: | ---: | ---: |\n'
 for family in CANDIDATES:
  items=groups[family];c=collections.Counter(s['status'] for s in items)
  route=routes[family] if c['PASSED'] else '尚无整例通过'
  target=ROOT/'migration/reports/support-log-index'/(family.replace('/','__')+'.md')
  intro+='| '+link(family,target,ROOT)+' | '+route+' | '+str(operators['modules'][family]['verified_operator_family_count'])+' | '+str(c['PASSED'])+'/'+str(len(items))+' | '+str(c['PARTIAL'])+' | '+str(c['FAILED'])+' |\n'
 intro+='''
## 验证范围

- AMD 验证环境为 ROCm 10.1.0 / Radeon AI PRO R9700（gfx1201），CUDA 对照使用双 RTX 5090。版本、设备和逐例执行条件见[环境锁](migration/environments/project.lock.json)与详细记录。
- 每个通过入口均有对应正确性验收。独立 CPU 参考、原生 CUDA 基线与兼容 CUDA 数学对照分别登记；原始工具链缺失时明确保留限制。
- 描述符管理等功能按原例语义统计；CPU 阶段、项目 HIP 重写和生态库调用均在详细记录中标明。
- 性能独立验收，目前没有可发布的合格跨设备速度比。其它设备架构、Windows 与多节点范围尚未验证。

[支持方式、覆盖用例与完整日志](migration/reports/support-log-index.md) · [机器可读清单](migration/samples.yaml) · [性能验证](migration/reports/performance-comparison.md) · [上游项目说明](migration/upstream.md) · [许可证](LICENSE.md)
'''
 p.write_text(intro);print(totals)
if __name__=='__main__':render()
