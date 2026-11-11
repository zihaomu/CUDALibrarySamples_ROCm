#!/usr/bin/env python3
"""Independent CPU masks and raw dispatch checks for the actual runtime jobs."""
import argparse,csv,json
from collections import Counter
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_validation import coverage,array_check,file_set
from image_canny_stages_reference import reference
from image_canny_local_research import local_mask
from canny_plus_runtime import contract
from image_progress import record

def validate(run,trace=False):
 spec=contract();out=ROOT/run['outputs'];rows=json.loads((out/'results.json').read_text());expected=(['trace-first','trace-changed'] if trace else spec['outputs']+['python/'+v for v in spec['python_errors']]+['ABI/'+v for v in spec['ABI_errors']]+['rejected-call-output-preserved','rejected-call-input-preserved'])
 checks=[dict(check='actual-process-success',passed=run['return_code']==0),coverage(rows,[dict(case=c) for c in expected])]
 for row in rows:
  name=row['case'];checks.append(dict(check=name+'/runtime-status',passed=row['passed'] is True))
  if 'files' not in row:continue
  d=out/name;checks.append(file_set(d,['input.bin','config.json','output.bin']))
  for n,v in row['files'].items():checks.append(dict(check=name+'/'+n+'/identity',passed=(d/n).is_file() and (d/n).stat().st_size==v['bytes'] and digest(d/n)==v['sha256']))
  if all(c['passed'] for c in checks):
   mask=local_mask(reference(d),72,256);checks.append(array_check(d/'output.bin',mask,row['files']['output.bin']['sha256']))
 if trace:
  paths=list((ROOT/run['trace']).rglob('*kernel_trace.csv'));dispatches=[]
  for path in paths:dispatches+=list(csv.DictReader(path.open()))
  names=Counter()
  for row in dispatches:
   for name in ['::sobel(','::suppress(','::local_threshold(']:
    if name in row['Kernel_Name']:names[name]+=1
  checks.append(dict(check='two-real-complete-three-stage-GPU-dispatches',passed=names==Counter({'::sobel(':2,'::suppress(':2,'::local_threshold(':2}) and all(int(r['End_Timestamp'])>int(r['Start_Timestamp']) for r in dispatches),counts=dict(names)))
  checks.append(dict(check='changed-input-changes-traced-mask',passed=(out/'trace-first/output.bin').read_bytes()!=(out/'trace-changed/output.bin').read_bytes()))
 else:
  masks={r['case']:(out/r['case']/'output.bin').read_bytes() for r in rows if 'files' in r}
  checks.append(dict(check='repeat-stable-and-changed-input-effective',passed=masks['repeat-first']==masks['repeat-second'] and masks['repeat-first']!=masks['changed-input']))
  streams={r['case']:r.get('stream') for r in rows};checks.append(dict(check='distinct-nondefault-caller-streams',passed=bool(streams['stream-a']) and bool(streams['stream-b']) and streams['stream-a']!=streams['stream-b']))
 return dict(status='PASSED' if checks and all(c['passed'] is True for c in checks) else 'FAILED',checks=checks,case_count=len(rows))

def main():
 p=argparse.ArgumentParser();p.add_argument('--trace',action='store_true');a=p.parse_args();name='trace' if a.trace else 'runtime';run=json.loads((ROOT/('migration/reports/canny-plus-'+name+'.json')).read_text())
 e=Experiment('I1','CannyPlus-'+name+'-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/canny_plus_runtime.py',ROOT/'tools/moat/image_validation.py',ROOT/'tools/moat/image_canny_stages_reference.py',ROOT/'tools/moat/image_canny_local_research.py',ROOT/'migration/rewrite/canny-plus-runtime.json'],parent=run['experiment_id'])
 try:v=validate(run,a.trace)
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='complete-runtime-data',passed=False,error=repr(error))])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',v);v['parent']=run['evidence'];write(ROOT/('migration/reports/canny-plus-'+name+'-validation.json'),v)
 record('I1','Canny '+name+'独立核对：'+v['status']+'；所有返回码/输入输出字节与原始GPU dispatch记录已检查。',[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
