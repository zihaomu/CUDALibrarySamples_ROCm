#!/usr/bin/env python3
"""Refresh measured progress in the master README, operator tables and roadmap."""
import collections,datetime,json
from catalog import ROOT
from batches4_8_spec import GROUPS
cat=json.loads((ROOT/'migration/samples.yaml').read_text());samples={s['source']:s for s in cat['samples']}
p=ROOT/'migration/reports/batches4_8-validation.json';proof={r['source']:r for r in json.loads(p.read_text())} if p.exists() else {}
totals=collections.Counter(s['status'] for s in cat['samples']);text='# B4–B8 实时实施与验收\n\n'
text+='更新时间：'+datetime.datetime.now(datetime.timezone.utc).isoformat()+'。26 个目标；当前全项目 '+str(totals['PASSED'])+' PASSED，'+str(totals['PARTIAL'])+' PARTIAL，'+str(totals['FAILED'])+' FAILED。每项只有预登记全部 case 的 AMD/CPU/CUDA 数值与语义检查通过后才提升。\n\n'
text+='| 批次 | 样例 / 详细日志 | 实际 AMD 路线 | 本批进度 | CPU / CUDA |\n| --- | --- | --- | --- | --- |\n'
summary=[]
for group,rows in GROUPS.items():
 passed=cases=0
 for source,required in rows.items():
  s=samples[source];r=proof.get(source);yes=bool(r and r['status']==r['cuda_comparison']=='PASSED');passed+=yes;cases+=len(required) if yes else 0
  progress=('已验收 '+str(len(required))+'/'+str(len(required))+' cases') if yes else ('已尝试，见日志' if r else '待实施；保留既有 '+s['status'])
  text+='| '+group.upper()+' | ['+source+'](../sample-reports/'+source+'.md) | '+str(s.get('actual_library') or '待验证')+' | '+progress+' | '+(r['status']+' / '+r['cuda_comparison'] if r else '未验收')+' |\n'
 summary.append({'batch':group.upper(),'samples_passed':passed,'samples_required':len(rows),'cases_passed':cases,'cases_required':sum(len(v) for v in rows.values())})
text+='\n原生 Ex 包装的运行失败和精确失败源码另存 [b4-native-ex-failure.json](b4-native-ex-failure.json)。固定 complex32 的 HERK/SYRK 使用类型化 hipBLAS；packed 使用项目 HIP GPU kernel；SELL/BSR 在 GPU 上转换后调用 hipSPARSE，再恢复原始存储格式。\n\n'
text+='本批源码与输入草案见 `tools/migration/batches4_8_spec.py`；数值证据见 [validation](batches4_8-validation.json)、[AMD](batches4_8-rocm.json)、[CUDA](batches4_8-cuda.json)。大二进制输出留本地、记录 SHA256/生成方式。性能资格单列，不将正确性运行的计时宣称为合格加速。\n'
(ROOT/'migration/reports/batches4-8.md').write_text(text);(ROOT/'migration/reports/batches4-8-progress.json').write_text(json.dumps({'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'batches':summary,'project_counts':dict(totals)},indent=2)+'\n')
marker='<!-- B4B8_PROGRESS:START -->';end='<!-- B4B8_PROGRESS:END -->'
canonical=ROOT.parent/'doc/cuda_samples_on_rocm_roadmap.md'
if canonical.exists():
 body=canonical.read_text();banner=marker+'\n\n**B4–B8 实施更新：** '+'；'.join(r['batch']+' '+str(r['samples_passed'])+'/'+str(r['samples_required']) for r in summary)+'。当前主表 '+str(totals['PASSED'])+' 个样例通过。[实时验收表](https://github.com/zihaomu/CUDALibrarySamples_ROCm/blob/main/migration/reports/batches4-8.md)。以下 166/473 等数字为原始计划基线；本更新不改写历史计划。\n\n'+end+'\n\n'
 if marker in body:body=body.split(marker)[0]+banner+body.split(end,1)[1].lstrip('\n')
 else:body=body.replace('## 1. 当前基线与计划目标',banner+'## 1. 当前基线与计划目标',1)
 body=body.replace('**计划已制定，B4–B15 尚未执行；不构成新增支持声明**','**B4–B8 正在按实时表实施；B9–B15 尚未启动。以下正文保留原始计划基线**')
 canonical.write_text(body);(ROOT/'migration/roadmap.md').write_text(body)
print('Updated live B4--B8 table',[(r['batch'],r['samples_passed']) for r in summary])
