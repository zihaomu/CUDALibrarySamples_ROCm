#!/usr/bin/env python3
"""Reject cumulative-child RSS as an encoder-process measurement."""
import json,sys
from experiment import ROOT,Experiment,write
from image_encoder_performance import TARGET_RUN
from image_completion_progress import record

def main():
    e=Experiment('I5','encoder-process-RSS-isolation','CPU-negative',sources=[__file__,ROOT/'tools/moat/image_encoder_performance.py'])
    code=TARGET_RUN+'''
import json,resource,sys
subprocess.run([sys.executable,'-c','a=bytearray(128*1024*1024);print(len(a))'],check=True,capture_output=True)
small,_,_=target_run(['/bin/true'])
cumulative=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
failed,out,err=target_run([sys.executable,'-c','import sys;print("output");print("error",file=sys.stderr);sys.exit(7)'])
print(json.dumps(dict(small=small,cumulative_RSS_KiB=cumulative,failed=failed,stdout=out,stderr=err)))
'''
    rc=e.command([sys.executable,'-c',code],'large-preparation-small-target')
    value=json.loads((e.path/e.commands[-1]['stdout']).read_text())
    checks=[dict(check='measurement-completed',passed=rc==0),
        dict(check='small-target-excludes-heavy-preparation',passed=value['small']['return_code']==0 and value['small']['encoder_process_max_RSS_KiB']<value['cumulative_RSS_KiB']/2),
        dict(check='nonzero-status-and-streams-preserved',passed=value['failed']['return_code']==7 and value['stdout']=='output\n' and value['stderr']=='error\n')]
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,observed=value)
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-performance-controls.json',row)
    record('IMG-01','CPU RSS采集修正：'+status+'；wait4绑定目标PID，大准备进程不再污染小目标峰值。旧性能表child_max_RSS_KiB仅为wrapper全部子进程累计峰值，保留原记录；新测量另存v2。',[row['evidence']]);print(status,value);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
