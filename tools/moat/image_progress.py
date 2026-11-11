#!/usr/bin/env python3
"""Keep image migration events and the canonical plan synchronized."""
import argparse,collections,json,fcntl
from pathlib import Path
from experiment import ROOT,now,write

REPORT=ROOT/'migration/reports/image-libraries-progress.json'
START='<!-- IMAGE_EXECUTION:START -->'
END='<!-- IMAGE_EXECUTION:END -->'

def render(data):
 plan=json.loads((ROOT/'migration/rewrite/image-libraries-plan.json').read_text());catalog=json.loads((ROOT/'migration/samples.yaml').read_text());ids={r['sample_id'] for r in plan['samples']};samples=[s for s in catalog['samples'] if s['id'] in ids];counts=collections.Counter(s['status'] for s in samples)
 lines=['# 图像库实施与实验记录','',f'更新时间：{data["updated_at"]}。执行中；当前支持结论仍以 samples.yaml 和已封存资格为准。','',f'26入口当前：{counts["PASSED"]} PASSED / {counts["PARTIAL"]} PARTIAL / {counts["FAILED"]} FAILED。','', '| 阶段 | 执行状态 |','| --- | --- |']
 lines += [f'| {p["id"]} | {data["phases"].get(p["id"],"NOT_STARTED")} |' for p in plan['phases']]
 lines+=['','## 每步记录','','| 时间 | 阶段 | 事件 / 结果 | 证据 |','| --- | --- | --- | --- |']
 for e in data['events']:
  refs='；'.join('['+Path(p).name+']('+str(Path(p).relative_to('migration/reports'))+')' if p.startswith('migration/reports/') else '`'+p+'`' for p in e['evidence']) or '静态检查/任务接入'
  lines.append('| '+e['time']+' | '+e['phase']+' | '+e['message'].replace('|','/').replace('\n','<br>')+' | '+refs+' |')
 (ROOT/'migration/reports/image-libraries-progress.md').write_text('\n'.join(lines)+'\n')
 canonical=ROOT.parent/'doc/cuda_samples_on_rocm_image_libraries_plan.md';body=canonical.read_text().replace('状态：**PLANNED_NOT_EXECUTED**。本方案仅建立实施队列，不增加通过数。','状态：**IN_PROGRESS**。已开始按计划实施；原设计与基线保留，当前实验和阶段状态见下方执行记录。')
 block='\n'.join([START,'','## 实时执行记录','',f'最近更新：{data["updated_at"]}。26入口当前{counts["PASSED"]}通过/{counts["PARTIAL"]}部分/{counts["FAILED"]}失败；实验运行成功不会直接升级支持数。','','| 时间 | 阶段 | 事件 / 结果 | 证据 |','| --- | --- | --- | --- |']+['| '+e['time']+' | '+e['phase']+' | '+e['message'].replace('|','/').replace('\n','<br>')+' | '+'；'.join('`'+p+'`' for p in e['evidence'])+' |' for e in data['events']]+['',END])
 if START in body:body=body.split(START,1)[0]+block+body.split(END,1)[1]
 else:body+='\n\n'+block+'\n'
 canonical.write_text(body);(ROOT/'migration/image-libraries-plan.md').write_text(body)
 execution=ROOT.parent/'doc/cuda_samples_on_rocm_image_equivalence_execution.md'
 if execution.exists():
  text=execution.read_text().replace('状态：**方案已制定，未据此新增样例资格**。','状态：**IN_PROGRESS**。逐步实施中；仅封存资格会增加支持数。')
  latest=data['events'][-1]
  stage='\n'.join([START,'','## 当前实施检查点','',f'更新时间：{data["updated_at"]}。26入口当前{counts["PASSED"]}通过/{counts["PARTIAL"]}部分/{counts["FAILED"]}失败。','',latest['phase']+'：'+latest['message'],'','证据：'+'；'.join('`'+p+'`' for p in latest['evidence']),'','完整逐步事件见主计划和 `migration/reports/image-libraries-progress.md`。','',END])
  if START in text:text=text.split(START,1)[0]+stage+text.split(END,1)[1]
  else:text+='\n\n'+stage+'\n'
  execution.write_text(text);(ROOT/'migration/image-equivalence-execution.md').write_text(text)

def record(phase,message,evidence=(),state=None):
 lock=ROOT/'build/image-progress.lock';lock.parent.mkdir(exist_ok=True)
 with lock.open('a') as stream:
  fcntl.flock(stream,fcntl.LOCK_EX)
  data=json.loads(REPORT.read_text()) if REPORT.exists() else dict(status='IN_PROGRESS',phases={},events=[])
  if state:data['phases'][phase]=state
  data['updated_at']=now();data['events'].append(dict(time=data['updated_at'],phase=phase,message=message,evidence=list(evidence)));write(REPORT,data);render(data)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',required=True);p.add_argument('--message',required=True);p.add_argument('--evidence',nargs='*',default=[]);p.add_argument('--state');a=p.parse_args();record(a.phase,a.message,a.evidence,a.state)
