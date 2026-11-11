#!/usr/bin/env python3
"""Check every distance/site/index/visualization byte against independent spatial search."""
import json
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_distance_model import model
from image_progress import record
from image_distance_inputs import load_case

FORMATS={'distance':('<f8',1,167,40),'visualization':('<u2',1,185,18),'indices':('<i2',2,171,20),'relative':('<i2',2,173,28),'site_ids':('<u8',1,205,24),'sites_xy':('<f8',2,221,32)}
def exact_file(path,n,sha=None):
 if not path.is_file() or path.stat().st_size!=n or sha is not None and digest(path)!=sha:raise ValueError('full file identity '+str(path))
 return path.read_bytes()

def validate(run,raw_override=None):
 spec=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());out=ROOT/run['outputs'];rows=json.loads((out/'runs.json').read_text());cases={c['case']:c for c in spec['cases']};meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());raw=Path(raw_override) if raw_override is not None else ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text())
 if len(commands)!=1 or commands[0]['return_code']!=0 or out.resolve()!=(raw/'outputs').resolve():raise ValueError('actual producer/output binding')
 argv=commands[0]['argv']
 if any(argv.count(option)!=1 for option in ['--output','--library','--sha']):raise ValueError('one actual producer argument per artifact')
 stored=Path(argv[argv.index('--output')+1]);origin=stored.parent
 for part in Path(meta['raw_artifact_dir']).parts:origin=origin.parent
 if origin/meta['raw_artifact_dir']/'outputs'!=stored or str(origin/'tools/moat/image_distance_worker.py') not in argv or argv[argv.index('--library')+1]!=str(origin/run['build']['library']) or argv[argv.index('--sha')+1]!=run['build']['library_sha256']:raise ValueError('actual current producer/library/hash identity')
 if spec['status']!='FROZEN' or spec['case_count']!=30 or run['return_code'] or len(rows)!=30 or {r['case'] for r in rows}!=set(cases) or {p.name for p in out.iterdir()}!=set(cases)|{'runs.json'}:raise ValueError('all thirty frozen successful complete input cases')
 results=[]
 for r in rows:
  c=cases[r['case']];w,h=c['width'],c['height'];item=np.dtype(c['dtype']).itemsize;folder=out/c['case'];expected_names={k+'.bin' for k in FORMATS}|{'input-after.bin'}
  if r['return_code'] or set(r['files'])!=expected_names or {p.name for p in folder.iterdir()}!=expected_names:raise ValueError('complete actual GPU output storage')
  payload=load_case(c);image=np.frombuffer(payload,np.uint8).reshape(h,c['pitch'])[:,:w*item].copy().view(c['dtype']).reshape(h,w);expected=model(image,c['mode'],c['cutoff'],c['remap_circle']);checks=[dict(check='frozen-geometry-and-workspace',passed=[r['width'],r['height'],r['input_pitch'],r['workspace_bytes'],r['descriptor_bytes']]==[w,h,c['pitch'],80*w*h+8,160]),dict(check='full-input-and-padding-unchanged',passed=exact_file(folder/'input-after.bin',len(payload),r['files']['input-after.bin']['sha256'])==payload and r['input_before_sha256']==__import__('hashlib').sha256(payload).hexdigest())];actual_distance=None
  for key,(dtype,components,pad,extra) in FORMATS.items():
   dt=np.dtype(dtype);pitch=w*dt.itemsize*components+extra;v=r['files'][key+'.bin'];raw=np.frombuffer(exact_file(folder/(key+'.bin'),h*pitch,v['sha256']),np.uint8).reshape(h,pitch);logical=raw[:,:w*dt.itemsize*components].copy().view(dt).reshape((h,w) if components==1 else(h,w,components));target=expected[key];ok=np.array_equal(logical,target);metrics={}
   if key=='distance':
    actual_distance=logical;finite=np.isfinite(target);both=np.isfinite(logical);delta=np.abs(logical[finite]-target[finite]) if np.all(both==finite) else np.array([np.inf]);budget=2e-11+1e-12*np.abs(target[finite]);ok=np.array_equal(finite,both) and np.array_equal(np.isposinf(logical),np.isposinf(target)) and np.array_equal(np.isneginf(logical),np.isneginf(target)) and not np.any(np.isnan(logical)) and np.array_equal(np.signbit(logical),np.signbit(target)) and np.array_equal(logical==0,target==0) and np.all(delta<=budget);metrics=dict(max_abs_error=float(delta.max(initial=0)),finite_values=int(finite.sum()),infinite_values=int((~finite).sum()))
   checks.extend([dict(check=key+'/complete-values',passed=bool(ok),**metrics),dict(check=key+'/byte-pitch-and-padding',passed=r['pitches'][key]==pitch and r['pads'][key]==pad and bool(np.all(raw[:,w*dt.itemsize*components:]==pad))),dict(check=key+'/exact-byte-manifest',passed=v['bytes']==h*pitch)])
  for axis in [0,1]:
   near=np.isfinite(actual_distance[:-1,:])&np.isfinite(actual_distance[1:,:]) if axis==0 else np.isfinite(actual_distance[:,:-1])&np.isfinite(actual_distance[:,1:]);a=actual_distance[1:,:] if axis==0 else actual_distance[:,1:];b=actual_distance[:-1,:] if axis==0 else actual_distance[:,:-1];difference=np.abs(a[near]-b[near]);checks.append(dict(check='grid-distance-Lipschitz-axis-'+str(axis),passed=bool(np.all(difference<=1+1e-9)),max_neighbor_difference=float(difference.max(initial=0))))
  result=dict(case=c['case'],status='PASSED' if all(x['passed'] for x in checks) else 'FAILED',site_count=expected['site_count'],checks=checks);results.append(result);print(c['case'],result['status'],flush=True)
 return results

def main():
 e=Experiment('I2','Distance-full-independent-spatial-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_distance_model.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'migration/rewrite/image-distance-profile.json',ROOT/'migration/reports/image-distance-CPU-dependency.json']);run=json.loads((ROOT/'migration/reports/image-distance-all.json').read_text())
 try:results=validate(run);v=dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(results),results=results)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all-thirty-independent-complete-distance-site-and-storage-contracts',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-distance-all-validation.json',v);record('I2','Signed/unsigned EDT30全量输入/子像素sites/确定性Voronoi/可视化/符号/距离结构/padding独立CPU：'+v['status']+'；完整原入口/运行/负测/trace/冷检出/复审另列。',[v['evidence']]);print(v['status'],v.get('error'),[(r['case'],[x for x in r['checks'] if not x['passed']]) for r in v['results'] if r['status']=='FAILED'][:4]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
