#!/usr/bin/env python3
"""Recompute all runtime masks and independently check actual error payloads."""
import argparse,csv,json
from collections import Counter
import numpy as np
from experiment import ROOT,Experiment,write,digest
from canny_color_runtime import contract
from canny_color_reference import model
from image_validation import coverage,array_check,file_set
from image_progress import record

def validate(run,trace=False):
 spec=contract();rows=json.loads((ROOT/run['outputs']/'results.json').read_text());out=ROOT/run['outputs'];names=['trace-first','trace-changed'] if trace else spec['outputs']+['python/'+n for n in spec['python_errors']]+['ABI/'+n for n in spec['ABI_errors']]+['query/'+n for n in spec['query_errors']]+['rejected-input-preserved','rejected-output-preserved'];checks=[dict(check='actual-process-success',passed=run['return_code']==0),coverage(rows,[dict(case=n) for n in names])];profile=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());case=next(c for c in profile['cases'] if c['case']==spec['fixture']);fixture=ROOT/case['fixture'];c=json.loads((fixture/'config.json').read_text());h,w=c['height'],c['width'];base=np.fromfile(fixture/'input.bin',np.uint8).reshape(h,c['pitch'])[:,:3*w].reshape(h,w,3).copy()
 for r in rows:
  name=r['case'];checks.append(dict(check=name+'/worker-status',passed=r['passed'] is True))
  if name.startswith(('ABI/','query/')):
   checks.append(dict(check=name+'/actual-status',passed=type(r.get('status')) is int and r['status']==spec['expected_ABI_status']))
   if name.startswith('query/'):checks.append(dict(check=name+'/query-storage-unchanged',passed=type(r.get('size_after')) is int and r['size_after']==999))
   continue
  if name.startswith('python/'):
   checks.append(dict(check=name+'/actual-exception',passed=r.get('exception_type')==spec['python_exception_types'].get(name.removeprefix('python/')) and isinstance(r.get('diagnostic'),str) and bool(r['diagnostic'])));continue
  storage=name.startswith('rejected-');required=spec['storage_file_set'] if storage else spec['output_file_set'];complete=isinstance(r.get('files'),dict) and set(r['files'])==set(required);checks.append(dict(check=name+'/complete-payload',passed=complete))
  if not complete:continue
  d=out/name;checks.append(file_set(d,required))
  for n,v in r['files'].items():checks.append(dict(check=name+'/'+n+'/identity',passed=(d/n).is_file() and (d/n).stat().st_size==v['bytes'] and digest(d/n)==v['sha256']))
  if storage:
   expected=base if name=='rejected-input-preserved' else np.full((h,w),173,np.uint8);checks.append(array_check(d/'buffer.bin',expected,r['files']['buffer.bin']['sha256']));continue
  config=json.loads((d/'config.json').read_text());expected_input=base[:,::-1].copy() if name in {'changed','stream-b','concurrent-b','trace-changed'} else base
  checks.append(dict(check=name+'/complete-input-layout-and-thresholds',passed=config==dict(width=w,height=h,pitch=w*3,channels=3,low=50,high=100)));checks.append(array_check(d/'input.bin',expected_input,r['files']['input.bin']['sha256']));expected,_=model(d);checks.append(array_check(d/'output.bin',expected,r['files']['output.bin']['sha256']))
 if trace:
  dispatches=[]
  for p in (ROOT/run['trace']).rglob('*kernel_trace.csv'):dispatches+=list(csv.DictReader(p.open()))
  counts=Counter()
  for r in dispatches:
   for n in ['sobel','suppress','init','hook','compress','seeds','result']:
    if '::'+n+'(' in r['Kernel_Name']:counts[n]+=1
  checks.append(dict(check='two-real-complete-C3-pipelines',passed=all(counts[n]==2 for n in ['sobel','suppress','init','seeds','result']) and counts['hook']==counts['compress']>=2 and all(int(r['End_Timestamp'])>int(r['Start_Timestamp']) for r in dispatches),dispatch_counts=dict(counts)))
  checks.append(dict(check='trace-changed-mask-effective',passed=(out/'trace-first/output.bin').read_bytes()!=(out/'trace-changed/output.bin').read_bytes()))
 else:
  checks.append(dict(check='repeat-stable-and-changed-input-effective',passed=(out/'repeat-a/output.bin').read_bytes()==(out/'repeat-b/output.bin').read_bytes() and (out/'repeat-a/output.bin').read_bytes()!=(out/'changed/output.bin').read_bytes()));streams={r['case']:r.get('stream') for r in rows};checks.append(dict(check='two-distinct-nondefault-streams',passed=bool(streams['stream-a']) and bool(streams['stream-b']) and streams['stream-a']!=streams['stream-b']))
 return dict(status='PASSED' if checks and all(c['passed'] is True for c in checks) else 'FAILED',checks=checks,case_count=len(rows))

def main():
 p=argparse.ArgumentParser();p.add_argument('--trace',action='store_true');a=p.parse_args();name='trace' if a.trace else 'runtime';run=json.loads((ROOT/('migration/reports/canny-color-'+name+'.json')).read_text());e=Experiment('I1','C3-Canny-'+name+'-CPU-check','CPU-reference',sources=[__file__,ROOT/'tools/moat/canny_color_runtime.py',ROOT/'tools/moat/canny_color_reference.py',ROOT/'tools/moat/image_canny_stages_reference.py',ROOT/'tools/moat/image_validation.py',ROOT/'migration/rewrite/canny-color-runtime.json'],parent=run['experiment_id'])
 try:v=validate(run,a.trace)
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='complete-runtime-data',passed=False,error=repr(error))])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',v);v['parent']=run['evidence'];write(ROOT/('migration/reports/canny-color-'+name+'-validation.json'),v);record('I1','C3 '+name+'独立CPU/实际返回码/完整GPU执行检查：'+v['status']+'。',[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
