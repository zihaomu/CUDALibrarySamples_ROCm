#!/usr/bin/env python3
"""Verify every original output and actual CLI branch independently on CPU."""
import argparse,json,re
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write
from image_ccl_reference import reference,exact,file
from image_progress import record
SIZES=[('lena','Lena',512,512),('CT_skull','CT_skull',512,512),('PCB_METAL','PCB_METAL',509,335),('PCB2','PCB2',1024,683),('PCB','PCB',1280,720)]
def validate(r,cli=False,raw_override=None):
 checks=[dict(check='actual-process-status',passed=r['return_code']==r['expected_return_code'])];out=ROOT/r['outputs'];m=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=Path(raw_override) if raw_override is not None else ROOT/m['raw_artifact_dir'];stdout=(raw/r['stdout']).read_text();stderr=(raw/r['stderr']).read_text();case=r['case']
 if r['expected_return_code']:
  tokens={'missing-b':'invalid or duplicate -b','zero':'batch count must be 1..5','negative':'batch count must be 1..5','above-five':'batch count must be 1..5','noninteger':'batch count must be 1..5','duplicate':'invalid or duplicate -b','unknown-option':'unknown option: --unknown','missing-input':'missing input:','truncated-input':'invalid raw input length:','unwritable-output':'cannot create output:','no-GPU':'no ROCm-capable device is detected'};checks.append(dict(check='actual-specific-diagnostic',passed='CCL error:' in stderr and tokens[case] in stderr));return dict(case=r['family']+'/'+r['mode']+'/'+case,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
 if case=='help':
  checks.append(dict(check='help-with-range-and-default',passed='Usage:' in stdout and '1..5 [default 5]' in stdout));return dict(case=r['family']+'/'+r['mode']+'/'+case,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
 n=5 if cli else int(case);expected=set();include_batch=r['family']=='NPP' or r['mode']=='batch-compression';counts=[];individual_counts=[];batch_counts=[]
 for stem,prefix,w,h in SIZES[:n]:
  input_path=ROOT/r['family']/'batchedLabelMarkersAndCompression/images'/(stem+f'_{w}x{h}_8u.raw');a=np.fromfile(input_path,np.uint8).reshape(h,w);rawlabels,compact,k=reference(a);individual_counts.extend([k,k]);batch_counts.extend([k]*(2 if include_batch else 1))
  for batch,compressed in [(False,False),(False,True),(True,False)]+([(True,True)] if include_batch else []):
   name=prefix+'_'+('CompressedMarkerLabels' if compressed else 'LabelMarkers')+('UFBatch' if batch else 'UF')+f'_8Way_{w}x{h}_32u.raw';expected.add(name);actual=np.frombuffer(file(out/name,w*h*4),'<u4').reshape(h,w);checks.append(exact(name+'/all-original-pixels',actual,compact if compressed else rawlabels));pass
 allowed=set(expected)
 if cli:allowed|={stem+f'_{w}x{h}_8u.raw' for stem,_,w,h in SIZES}
 actual={p.name for p in out.iterdir()};checks.append(dict(check='exact-original-output-set',passed=actual==allowed));counts=individual_counts+batch_counts;actual_counts=[int(x) for x in re.findall(r'compressed label count is (\d+)',stdout)];checks.append(dict(check='all-reported-counts-and-messages',passed=actual_counts==counts));checks.append(dict(check='no-runtime-error-diagnostic',passed=not stderr.strip()));return dict(case=r['family']+'/'+r['mode']+'/'+case,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,file_count=len(expected))
def main():
 p=argparse.ArgumentParser();p.add_argument('--cli',action='store_true');a=p.parse_args();kind='cli' if a.cli else 'originals';runs=json.loads((ROOT/f'migration/reports/image-ccl-{kind}.json').read_text());e=Experiment('I2','CCL-original-'+kind+'-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_ccl_reference.py',ROOT/'migration/rewrite/image-ccl-profile.json']);expected={(f,m,c) for f,m in [('NPP','default'),('NPP+','default'),('NPP+','batch-compression')] for c in (['default-directory','help','missing-b','zero','negative','above-five','noninteger','duplicate','unknown-option','missing-input','truncated-input','unwritable-output','no-GPU'] if a.cli else [str(n) for n in range(1,6)])}
 try:
  if len(runs)!=len(expected) or {(r['family'],r['mode'],r['case']) for r in runs}!=expected:raise ValueError('all unique original workflows/CLI required')
  results=[validate(r,a.cli) for r in runs];v=dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(results),file_count=sum(r.get('file_count',0) for r in results),results=results)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='independent-original-files-and-contract',passed=v['status']=='PASSED')]));write(ROOT/f'migration/reports/image-ccl-{kind}-validation.json',v);record('I2','CCL完整C++ '+kind+'逐原图/全部文件/计数/实际诊断验收：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[(r['case'],[c for c in r['checks'] if not c['passed']]) for r in v['results'] if r['status']=='FAILED'][:5]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
