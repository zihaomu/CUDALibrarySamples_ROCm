#!/usr/bin/env python3
"""Render measured rewrite progress without promoting unqualified entrypoints."""
import collections,json,re
from pathlib import Path
from experiment import ROOT,write,now,digest

def read(name):
 p=ROOT/'migration/reports'/name;return json.loads(p.read_text()) if p.exists() else {}
spec=json.loads((ROOT/'migration/rewrite/first-eight.json').read_text())['profiles'];runs=read('rewrite-first-rocm.json');cpu=read('rewrite-first-rocm-validation.json');cuda=read('rewrite-first-cuda.json');cv=read('rewrite-first-cuda-validation.json');negative=read('rewrite-first-negative.json')
cat=json.loads((ROOT/'migration/samples.yaml').read_text());counts=collections.Counter(s['status'] for s in cat['samples'])
lines=['# MOAT 重写实时进展','',f'更新时间：{now()}。样例支持结论仍以 samples.yaml 为准。','',
       '| 批次 / 样例 | AMD 已运行 / CPU通过 | CUDA 已运行 / CPU通过 | 当前验收结论 |','| --- | ---: | ---: | --- |']
rows=[]
for p in spec:
 k=p['kind'];keys=[k+'/'+c for c in p['cases']]
 def valid(results,records,x):
  return x in results and x in records and results[x]['status']=='PASSED' and results[x].get('validation_source_sha256')==digest(ROOT/'tools/moat/first_reference.py') and results[x]['run']['experiment_id']==records[x]['experiment_id']
 ar=sum(x in runs and runs[x]['return_code']==0 for x in keys);ap=sum(valid(cpu,runs,x) for x in keys);cr=sum(x in cuda and cuda[x]['return_code']==0 for x in keys);cp=sum(valid(cv,cuda,x) for x in keys)
 latest=next((cpu[x]['evidence'] for x in reversed(keys) if x in cpu),next((runs[x]['evidence'] for x in reversed(keys) if x in runs),None))
 sample=next(s for s in cat['samples'] if s['id']==p['sample_id'])
 text='整例已签发资格：'+sample['status'] if sample.get('reason_code')=='VALIDATED_MOAT_REWRITE' else '数值复核中；尚未签发整例资格'
 total=len(keys);lines.append(f'| {p["batch"]} / `{k}` | {ar}/{total} / {ap}/{total} | {cr}/{total} / {cp}/{total} | '+(f'[{text}]({latest.removeprefix("migration/reports/")}/summary.md)' if latest else text)+' |')
 rows.append(dict(kind=k,required=total,amd_executed=ar,cpu_verified=ap,cuda_executed=cr,cuda_cpu_verified=cp))
lines+=['',f'反向检查：{sum(bool(x["passed"]) for x in negative.get("checks",[]))}/{len(negative.get("checks",[]))}；原生与兼容 CUDA 数学对照分别登记。',
        '', '当前全项目状态：'+ '、'.join(f'{v} {k}' for k,v in counts.items())+'。',
        '', '日志：[实验事件索引](rewrite-experiments.jsonl)；[AMD运行](rewrite-first-rocm.json)；[独立CPU验收](rewrite-first-rocm-validation.json)；[CUDA运行](rewrite-first-cuda.json)。',
        '', 'R1–R2完整记录：[批次验收](rewrite-R1-R2.md)。其它批次见下表；全项目MOAT surface与其它平台仍有owed项。']
tasks=json.loads((ROOT/'migration/moat/tasks.json').read_text())['tasks'];by={t['sample_id']:t for t in tasks}
pending=collections.Counter(by[s['id']]['primary_phase'] for s in cat['samples'] if s['status']!='PASSED')
new_qualified=collections.Counter(by[s['id']]['primary_phase'] for s in cat['samples'] if s['status']=='PASSED' and s.get('reason_code')=='VALIDATED_MOAT_REWRITE')
remaining_frontends=sum(s['status']!='PASSED' and by[s['id']]['primary_phase']=='R5' and by[s['id']]['baseline_status']=='FAILED' for s in cat['samples'])
operators=read('operator-support.json');new_total=sum(new_qualified.values());remaining=sum(v for k,v in counts.items() if k!='PASSED')
phase_rows=[]
descriptions={'R1':'5个 BLAS/Lt 整例','R2':'3个 device solver 整例','R3':'原24项复审，NCC/SVD两例收口','R4':'按资格签发的小批推进；R9含C++ helper及CRC benchmark','R5':f'真实 Fortran 入口；{remaining_frontends}前端与额外CPP项仍待支持','R6':'224项专题研究与最小基础探针；未签发整例','R7':'2个真实GPU packed sparse2:4 整例','R8':'总回归、依赖封存、干净检出与交付'}
states={'R1':'COMPLETED_SCOPED','R2':'COMPLETED_SCOPED','R3':'ASSESSMENT_COMPLETE_22_GAPS','R4':f'SCOPED_BATCHES_{pending["R4"]}_PENDING','R5':f'PARTIALLY_IMPLEMENTED_{remaining_frontends}_FRONTENDS_PENDING','R6':'ASSESSMENT_COMPLETE_PORTS_PENDING','R7':'COMPLETED_SCOPED','R8':'IN_PROGRESS'}
delivery=read('rewrite-R8-review.json');clean=read('rewrite-clean-checkout.json');final=read('final-validation.json')
if delivery.get('verdict')=='APPROVED' and clean.get('status')=='PASSED' and final.get('status')=='PASSED':states['R8']='COMPLETED_SCOPED'
lines+=['','## 全阶段与未完成范围','','| 阶段 | 本轮新整例资格 | 仍未通过 | 当前结果与范围 |','| --- | ---: | ---: | --- |']
for phase in descriptions:
 row=dict(phase=phase,new_qualified=new_qualified[phase],pending=pending[phase],state=states[phase],scope=descriptions[phase]);phase_rows.append(row)
 lines.append(f'| {phase} | {row["new_qualified"]} | {row["pending"]} | {row["state"]}；{row["scope"]} |')
lines+=['',f'累计新增资格{new_total}项，另撤销旧C++排序样例资格1项，支持211→{counts["PASSED"]}，净增{counts["PASSED"]-211}。当前{counts["PASSED"]}/639通过、{remaining}待支持；{operators.get("verified_operator_families")}功能族、{operators.get("modules_with_verified_operators")}模块。','',
 f'[R3](rewrite-R3.md) · [R4](rewrite-R4.md) · [R5](rewrite-R5.md) · [R6](rewrite-R6.md) · [R7](rewrite-R7.md) · [{remaining}项逐例原因与后续实验](rewrite-remaining-assessment.md)。',
 '', f'计划第1.2节区分阶段执行和整例支持；R5剩余{remaining_frontends}个前端及其它待实现项没有被登记为完成。wave64、Windows、多节点与全项目MOAT surface仍未验证。']
if (ROOT/'migration/reports/rewrite-R9.md').exists():lines+=['','[R9：九个helper与CRC32 benchmark实时记录](rewrite-R9.md)。候选实现不预记整例资格。']
(ROOT/'migration/reports/rewrite-progress.md').write_text('\n'.join(lines)+'\n')
write(ROOT/'migration/reports/rewrite-progress.json',dict(updated_at=now(),rows=rows,baseline_counts=dict(counts),phases=phase_rows))
doc=ROOT.parent/'doc/cuda_samples_on_rocm_moat_rewrite_plan.md';body=doc.read_text();start='<!-- MOAT_EXEC_PROGRESS:START -->';end='<!-- MOAT_EXEC_PROGRESS:END -->'
total=sum(x['required'] for x in rows)
first_ids={p['sample_id'] for p in spec}
qualified=sum(s['id'] in first_ids and s.get('reason_code')=='VALIDATED_MOAT_REWRITE' and s['status']=='PASSED' for s in cat['samples'])
section='\n'.join([start,'',f'最近更新：{now()}。首批 AMD/独立CPU/CUDA 51/51；首批资格 {qualified}/8。累计{new_total}项新资格，撤销1项旧资格，当前{counts["PASSED"]} PASSED/{counts["PARTIAL"]} PARTIAL/{counts["FAILED"]} FAILED。剩余{remaining}项全部有路线与重试条件；R5仍有{remaining_frontends}前端和额外CPP项待支持。R8：{states["R8"]}；全项目surface与其它平台仍owed。','',end])
if start in body:body=re.sub(re.escape(start)+'.*?'+re.escape(end),section,body,flags=re.S)
else:body+='\n'+section+'\n'
doc.write_text(body)
mirror=body.replace('](cuda_samples_on_rocm_design.md)','](design.md)').replace('](cuda_samples_on_rocm_roadmap.md)','](roadmap.md)').replace('](../CUDALibrarySamples_ROCm/','](../').replace('](../../AGENTS.md)','](../AGENTS.md)')
(ROOT/'migration/moat-rewrite-plan.md').write_text(mirror)
readme=ROOT/'README.md';text=readme.read_text();link='[MOAT 重写计划](migration/moat-rewrite-plan.md) · [重写实时进展与实验日志](migration/reports/rewrite-progress.md)'
if link not in text:text=text.replace('# CUDA Library Samples on ROCm\n','# CUDA Library Samples on ROCm\n\n'+link+'\n',1);readme.write_text(text)
print(json.dumps(rows))
