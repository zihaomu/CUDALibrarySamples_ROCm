#!/usr/bin/env python3
"""Independent per-channel predicates and OpenCV components, full RGB/storage checks."""
import hashlib,json
from pathlib import Path
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_flood_inputs import load_case
from image_progress import record
def model(a,c):
 h,w,_=a.shape;sx,sy=c['seed'];seed=a[sy,sx].astype(np.int32);mode=c['mode'];lo=np.array(c['lower']);hi=np.array(c['upper'])
 if mode==0:lo=hi=seed
 elif mode<3:lo=np.maximum(0,seed-lo);hi=np.minimum(255,seed+hi)
 allowed=np.all((a>=lo)&(a<=hi),axis=2);_,labels=cv2.connectedComponents(allowed.astype(np.uint8),connectivity=8)
 selected=allowed&(labels==labels[sy,sx]) if allowed[sy,sx] else np.zeros((h,w),bool);inner=np.zeros_like(selected)
 if mode in [2,4]:
  pad=np.pad(selected,1,constant_values=False)
  for oy in range(3):
   for ox in range(3):inner|=selected&~pad[oy:oy+h,ox:ox+w]
 out=a.copy();out[selected]=c['fill'];out[inner]=c['boundary'];y,x=np.where(selected);box=[int(x.min()),int(y.min()),int(x.max()),int(y.max())] if len(x) else [0]*4;region=np.array([*box,len(x),*seed],'<u4');return dict(output=out,mask=selected.astype(np.uint8)*255,region=region)
def exact_file(path,size,sha=None):
 if not path.is_file() or path.stat().st_size!=size or sha is not None and digest(path)!=sha:raise ValueError('full flood file identity '+str(path))
 return path.read_bytes()
def validate(run,raw_override=None):
 spec=json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text());cases={c['case']:c for c in spec['cases']};out=ROOT/run['outputs'];meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());raw=Path(raw_override) if raw_override else ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text());rows=json.loads((out/'runs.json').read_text())
 if run['return_code'] or spec['status']!='FROZEN' or len(rows)!=len(cases) or spec['case_count']!=len(cases) or len(cases)!=29 or {r['case'] for r in rows}!=set(cases) or {p.name for p in out.iterdir()}!=set(cases)|{'runs.json'} or len(commands)!=1 or commands[0]['return_code'] or out.resolve()!=(raw/'outputs').resolve():raise ValueError('complete unique frozen flood cases and actual output binding')
 argv=commands[0]['argv']
 if any(argv.count(option)!=1 for option in ['--output','--library','--sha']):raise ValueError('one actual flood producer argument per artifact')
 stored=Path(argv[argv.index('--output')+1]);origin=stored.parent
 for _ in Path(meta['raw_artifact_dir']).parts:origin=origin.parent
 worker=str(origin/'tools/moat/image_flood_worker.py');expected=[worker,'--library',str(origin/run['build']['library']),'--sha',run['build']['library_sha256'],'--output',str(stored)]
 if origin/meta['raw_artifact_dir']/'outputs'!=stored or worker not in argv or argv[argv.index(worker):]!=expected:raise ValueError('actual flood producer library and hash')
 results=[]
 for r in rows:
  c=cases[r['case']];w,h=c['width'],c['height'];n=w*h;payload=load_case(c);a=np.frombuffer(payload,np.uint8).reshape(h,c['pitch'])[:,:w*3].copy().reshape(h,w,3);expected=model(a,c);p=out/c['case'];names={'input-after.bin','output.bin','mask.bin','region.bin'}
  if set(r['files'])!=names or {x.name for x in p.iterdir()}!=names:raise ValueError('full flood output inventory')
  for name,v in r['files'].items():exact_file(p/name,v['bytes'],v['sha256'])
  checks=[dict(check='frozen-geometry-mode-seed-and-all-channel-parameters',passed=r['return_code']==0 and [r['width'],r['height'],r['input_pitch'],r['output_pitch'],r['mask_pitch'],r['workspace_bytes'],r['descriptor_bytes']]==[w,h,c['pitch'],3*w+19,w+23,((3*n+3)//4)*4+4*n+4,160] and r['parameters']=={k:c[k] for k in ['mode','seed','lower','upper','fill','boundary']}),dict(check='full-frozen-input-and-padding-preserved',passed=exact_file(p/'input-after.bin',len(payload))==payload and r['input_before_sha256']==hashlib.sha256(payload).hexdigest())]
  for name,channels,pad,pitch in [('output',3,185,3*w+19),('mask',1,171,w+23)]:
   b=np.frombuffer(exact_file(p/(name+'.bin'),h*pitch),np.uint8).reshape(h,pitch);logical=b[:,:w*channels].reshape(expected[name].shape);checks.extend([dict(check=name+'/all-values',passed=bool(np.array_equal(logical,expected[name])),different_values=int(np.count_nonzero(logical!=expected[name]))),dict(check=name+'/full-row-padding',passed=bool(np.all(b[:,w*channels:]==pad)))])
  region=np.frombuffer(exact_file(p/'region.bin',32),'<u4');checks.append(dict(check='complete-inclusive-box-count-and-original-seed',passed=bool(np.array_equal(region,expected['region'])),actual=region.tolist(),expected=expected['region'].tolist()));v=dict(case=c['case'],status='PASSED' if all(x['passed'] for x in checks) else 'FAILED',checks=checks);results.append(v);print(c['case'],v['status'],flush=True)
 return results
def main():
 e=Experiment('I3','FloodFill-independent-complete-RGB-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-profile.json']);run=json.loads((ROOT/'migration/reports/image-flood-all.json').read_text())
 try:results=validate(run);v=dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(results),results=results)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all-frozen-RGB-masks-metadata-and-padding',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-flood-all-validation.json',v);record('I3','RGB flood29完整输入的全RGB/8连通mask/原seed色/inclusive bbox与count/padding独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'));return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
