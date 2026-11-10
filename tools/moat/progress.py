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
 text='数值复核中；尚未签发整例资格'
 total=len(keys);lines.append(f'| {p["batch"]} / `{k}` | {ar}/{total} / {ap}/{total} | {cr}/{total} / {cp}/{total} | '+(f'[{text}]({latest.removeprefix("migration/reports/")}/summary.md)' if latest else text)+' |')
 rows.append(dict(kind=k,required=total,amd_executed=ar,cpu_verified=ap,cuda_executed=cr,cuda_cpu_verified=cp))
lines+=['',f'反向检查：{sum(bool(x["passed"]) for x in negative.get("checks",[]))}/{len(negative.get("checks",[]))}；原生与兼容 CUDA 数学对照分别登记。',
        '', '当前全项目状态：'+ '、'.join(f'{v} {k}' for k,v in counts.items())+'。',
        '', '日志：[实验事件索引](rewrite-experiments.jsonl)；[AMD运行](rewrite-first-rocm.json)；[独立CPU验收](rewrite-first-rocm-validation.json)；[CUDA运行](rewrite-first-cuda.json)。',
        '', '待完成：提交固定源码后的独立审查、必要原生 SDK 合同复核、反向检查与支持资格签发。']
(ROOT/'migration/reports/rewrite-progress.md').write_text('\n'.join(lines)+'\n')
write(ROOT/'migration/reports/rewrite-progress.json',dict(updated_at=now(),rows=rows,baseline_counts=dict(counts)))
doc=ROOT.parent/'doc/cuda_samples_on_rocm_moat_rewrite_plan.md';body=doc.read_text();start='<!-- MOAT_EXEC_PROGRESS:START -->';end='<!-- MOAT_EXEC_PROGRESS:END -->'
total=sum(x['required'] for x in rows)
section='\n'.join([start,'',f'最近更新：{now()}。首批 AMD {sum(x["amd_executed"] for x in rows)}/{total} 已运行，独立 CPU {sum(x["cpu_verified"] for x in rows)}/{total} 通过；CUDA {sum(x["cuda_executed"] for x in rows)}/{total} 已运行，独立 CPU {sum(x["cuda_cpu_verified"] for x in rows)}/{total} 通过。整例资格仍在审查，未提前修改支持计数。','',end])
if start in body:body=re.sub(re.escape(start)+'.*?'+re.escape(end),section,body,flags=re.S)
else:body+='\n'+section+'\n'
doc.write_text(body)
mirror=body.replace('](cuda_samples_on_rocm_design.md)','](design.md)').replace('](cuda_samples_on_rocm_roadmap.md)','](roadmap.md)').replace('](../CUDALibrarySamples_ROCm/','](../').replace('](../../AGENTS.md)','](../AGENTS.md)')
(ROOT/'migration/moat-rewrite-plan.md').write_text(mirror)
readme=ROOT/'README.md';text=readme.read_text();link='[MOAT 重写计划](migration/moat-rewrite-plan.md) · [重写实时进展与实验日志](migration/reports/rewrite-progress.md)'
if link not in text:text=text.replace('# CUDA Library Samples on ROCm\n','# CUDA Library Samples on ROCm\n\n'+link+'\n',1);readme.write_text(text)
print(json.dumps(rows))
