#!/usr/bin/env python3
"""Mirror completion work-package progress to both user and repository plans."""
import argparse,fcntl,json,re
from experiment import ROOT,now,write
from image_progress import record as legacy_record

REPORT=ROOT/'migration/reports/image-completion-progress.json'
START='<!-- IMAGE_COMPLETION:START -->'
END='<!-- IMAGE_COMPLETION:END -->'
PHASES={'IMG-00':'I0','IMG-01':'I5','IMG-02':'I3','IMG-03':'I4','IMG-04':'I4',
        'IMG-05':'I5','IMG-06':'I6','IMG-07':'I7','IMG-08':'I8','IMG-09':'I8','IMG-10':'I9'}

def record(stage,message,evidence=(),state='IN_PROGRESS'):
    if stage not in PHASES or state not in {'PLANNED','IN_PROGRESS','COMPLETED'}:
        raise ValueError('invalid completion stage/state')
    with (ROOT/'build/image-completion-progress.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        data=json.loads(REPORT.read_text()) if REPORT.exists() else dict(status='IN_PROGRESS',stages={},events=[])
        data['updated_at']=now();data['stages'][stage]=state
        data['events'].append(dict(time=data['updated_at'],stage=stage,state=state,message=message,evidence=list(evidence)))
        write(REPORT,data)
        path=ROOT.parent/'doc/cuda_samples_on_rocm_image_completion_plan.md'
        if not path.exists():path=ROOT/'migration/image-completion-plan.md'
        body=path.read_text().replace('计划状态：**PLANNED**；本次仅完成现状核对和后续设计，不新增整例资格。',
                                      '计划状态：**IN_PROGRESS**；已按用户指令开始实施，整例资格仍按完整合同签发。')
        for phase,status in data['stages'].items():
            body=re.sub(r'^(\| '+re.escape(phase)+r' \| )(PLANNED|IN_PROGRESS|COMPLETED)( \| )[^\n]+$',
                        lambda m:m[1]+status+m[3]+'最新步骤和证据见下方实时记录 |',body,flags=re.M)
        block=[START,'','### 实时实施记录','',
               '| 时间（UTC） | 阶段 | 状态 | 实施结果 | 证据 |',
               '| --- | --- | --- | --- | --- |']
        for event in data['events']:
            refs='；'.join('`'+p+'`' for p in event['evidence'])
            block.append('| '+' | '.join([event['time'],event['stage'],event['state'],
                         event['message'].replace('|','/').replace('\n','<br>'),refs])+' |')
        block += ['',END]
        rendered='\n'.join(block)
        if START in body:body=body.split(START,1)[0]+rendered+body.split(END,1)[1]
        else:body+='\n'+rendered+'\n'
        path.write_text(body);(ROOT/'migration/image-completion-plan.md').write_text(body)
    legacy_record(PHASES[stage],stage+'：'+message,evidence)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True);p.add_argument('--message',required=True)
    p.add_argument('--evidence',nargs='*',default=[]);p.add_argument('--state',default='IN_PROGRESS')
    a=p.parse_args();record(a.stage,a.message,a.evidence,a.state)
