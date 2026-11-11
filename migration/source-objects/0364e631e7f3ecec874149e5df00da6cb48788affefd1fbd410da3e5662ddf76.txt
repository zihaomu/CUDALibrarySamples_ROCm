#!/usr/bin/env python3
"""Exercise the actual validators with accepted variations and targeted corruptions."""
import copy,collections,json,shutil,tempfile
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_ccl_reference import reference,validate_output,validate_masks,validate_runtime,validate_native
from image_ccl_original_reference import validate as original_validate
from image_progress import record

def bfs(a):
 h,w=a.shape;raw=np.zeros((h,w),np.uint32);component=0;compact=np.zeros_like(raw)
 for y in range(h):
  for x in range(w):
   if raw[y,x]:continue
   component+=1;label=y*w+x+1;raw[y,x]=label;compact[y,x]=component;q=collections.deque([(y,x)])
   while q:
    yy,xx=q.popleft()
    for dy in [-1,0,1]:
     for dx in [-1,0,1]:
      ny,nx=yy+dy,xx+dx
      if 0<=ny<h and 0<=nx<w and not raw[ny,nx] and a[ny,nx]==a[y,x]:raw[ny,nx]=label;compact[ny,nx]=component;q.append((ny,nx))
 return raw,compact,component

def run_checks():
 spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());gpu=json.loads((ROOT/'migration/reports/image-ccl-masks.json').read_text());runtime=json.loads((ROOT/'migration/reports/image-ccl-runtime.json').read_text());native=json.loads((ROOT/'migration/reports/image-ccl-native.json').read_text());out=ROOT/gpu['outputs'];rows=json.loads((out/'runs.json').read_text());case=next(c for c in spec['cases'] if c['case']=='three-by-three-stale-root');row=next(r for r in rows if r['case']==case['case']);checks=[]
 def check(name,fn,expected=True):
  try:actual=bool(fn())
  except (ValueError,KeyError,IndexError,OSError,TypeError):actual=False
  checks.append(dict(check=name,passed=actual==expected))
 check('all-actual-GPU-cases-pass',lambda:all(r['status']=='PASSED' for r in validate_masks(gpu)))
 def oracles():
  for c in spec['cases']:
   if c['width']*c['height']>5000:continue
   a=np.fromfile(ROOT/c['fixture']/'input.bin',np.uint8).reshape(c['height'],c['pitch'])[:,:c['width']];x=reference(a);y=bfs(a)
   if any(not np.array_equal(i,j) for i,j in zip(x,y)):return False
  return reference(np.array([[0,2,0],[0,2,0],[1,0,1]],np.uint8))[2]==4
 check('independent-BFS-agrees-with-OpenCV-and-four-region-case',oracles)
 with tempfile.TemporaryDirectory(prefix='ccl-validator-') as tmp:
  d=Path(tmp)
  def output_case(name,change=None,file_change=None):
   target=d/name;shutil.copytree(out/case['case'],target);r=copy.deepcopy(row)
   if change:change(r)
   if file_change:
    filename,mutate=file_change;p=target/filename;mutate(p);r['files'][filename]=dict(bytes=p.stat().st_size,sha256=digest(p))
   return validate_output(case,r,target)['status']=='PASSED'
  check('actual-padded-output-passes',lambda:output_case('positive'))
  def flip(p,offset):
   b=bytearray(p.read_bytes());b[offset]^=1;p.write_bytes(b)
  for name,filename,offset in [('raw-wrong-component','labels.bin',4),('compact-wrong-component','compact.bin',4),('raw-padding','labels.bin',case['width']*4),('compact-padding','compact.bin',case['width']*4),('input-or-padding-changed','input-after.bin',case['width'])]:check(name,lambda n=name,f=filename,i=offset:output_case(n,file_change=(f,lambda p:flip(p,i))),False)
  check('truncated-label-file',lambda:output_case('short',file_change=('labels.bin',lambda p:p.write_bytes(p.read_bytes()[:-1]))),False)
  check('wrong-component-count',lambda:output_case('count',lambda r:r.update(reported_count=r['reported_count']+1)),False)
  check('wrong-geometry',lambda:output_case('geometry',lambda r:r.update(width=r['width']+1)),False)
  check('wrong-input-hash-receipt',lambda:output_case('inputhash',lambda r:r.update(input_before_sha256='0'*64)),False)
  check('missing-output-manifest-entry',lambda:output_case('missing',lambda r:r['files'].pop('compact.bin')),False)
  def masks_mutation(name,mutate,rc=0):
   target=d/name;target.mkdir();rs=copy.deepcopy(rows);mutate(rs);(target/'runs.json').write_text(json.dumps(rs))
   for c in spec['cases']:(target/c['case']).symlink_to(out/c['case'],target_is_directory=True)
   return all(r['status']=='PASSED' for r in validate_masks(dict(gpu,outputs=str(target),return_code=rc)))
  check('missing-case',lambda:masks_mutation('drop',lambda r:r.pop()),False)
  check('duplicate-case',lambda:masks_mutation('duplicate',lambda r:r.append(copy.deepcopy(r[0]))),False)
  check('producer-nonzero',lambda:masks_mutation('rc',lambda r:None,1),False)
  check('case-nonzero',lambda:masks_mutation('case-rc',lambda r:r[0].update(return_code=1)),False)
  def runtime_mutation(name,mutate):
   target=d/name;target.mkdir();rs=json.loads((ROOT/runtime['outputs']/'runs.json').read_text());mutate(rs);(target/'runs.json').write_text(json.dumps(rs))
   for p in (ROOT/runtime['outputs']).iterdir():
    if p.is_dir():(target/p.name).symlink_to(p,target_is_directory=True)
   return all(r['status']=='PASSED' for r in validate_runtime(dict(runtime,outputs=str(target))))
  check('runtime-actual-errors-pass',lambda:all(r['status']=='PASSED' for r in validate_runtime(runtime)))
  check('runtime-error-is-success',lambda:runtime_mutation('error-success',lambda r:r[0].update(return_code=0)),False)
  check('runtime-error-storage-changed',lambda:runtime_mutation('error-storage',lambda r:r[0]['after'].__setitem__(0,'0'*64)),False)
  check('runtime-query-wrong-bytes',lambda:runtime_mutation('query-bytes',lambda r:next(x for x in r if x['kind']=='workspace-query').update(bytes=0)),False)
  check('runtime-missing-branch',lambda:runtime_mutation('runtime-drop',lambda r:r.pop()),False)
  def replace_pixel_role(rs):
   positive=next(r for r in rs if r['case']=='after-errors');negative=rs[0];positive.update(kind='expected-error',return_code=1,expected_return_code=1,before=negative['before'],after=negative['after'])
  check('runtime-pixel-replaced-with-error-rejected',lambda:runtime_mutation('pixel-role',replace_pixel_role),False)
  check('runtime-query-redefined-as-invalid-rejected',lambda:runtime_mutation('query-role',lambda rs:next(r for r in rs if r['case']=='workspace-recursive').update(valid=False,width=0,height=0,return_code=1,bytes=0)),False)
  check('runtime-error-replaced-with-query-rejected',lambda:runtime_mutation('error-role',lambda rs:rs[0].update(kind='workspace-query',valid=True,width=1,height=1,return_code=0,bytes=12)),False)
  check('runtime-frozen-source-removed-rejected',lambda:runtime_mutation('source-role',lambda rs:next(r for r in rs if r['case']=='after-errors').update(source_case=None)),False)
  check('native-all-actual-cases-recorded',lambda:len(validate_native(native))==54)
  target=next(r for r in native if r.get('case')=='constant-0' and r['family']=='NPP');where=d/'native-remap';shutil.copytree(ROOT/target['outputs'],where)
  for name in ['labels.bin','compact.bin']:
   p=where/name;a=np.fromfile(p,'<u4');a[:]=937;a.tofile(p)
  changed=copy.deepcopy(native);r=next(r for r in changed if r.get('case')=='constant-0' and r['family']=='NPP');r['outputs']=str(where);r['files']={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in where.iterdir()}
  check('arbitrary-native-label-ID-remap-accepted',lambda:all(v['conformance']=='PASSED' for x in validate_native(changed) if x['family']=='NPP' and x['case']=='constant-0' for v in x['variants'].values()))
  (where/'labels.bin').write_bytes(b'bad');r['files']['labels.bin']=dict(bytes=3,sha256=digest(where/'labels.bin'));check('native-file-structure-rejected',lambda:bool(validate_native(changed)),False)
  original=json.loads((ROOT/'migration/reports/image-ccl-originals.json').read_text())[0];check('actual-C++-files-pass',lambda:original_validate(original)['status']=='PASSED');check('C++-nonzero-rejected',lambda:original_validate(dict(original,return_code=1))['status']=='PASSED',False)
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=len(checks),checks=checks)
def main():
 e=Experiment('I2','CCL-independent-validator-mutations','CPU-validator-test',sources=[__file__,ROOT/'tools/moat/image_ccl_reference.py',ROOT/'tools/moat/image_ccl_original_reference.py',ROOT/'migration/rewrite/image-ccl-profile.json',ROOT/'migration/rewrite/image-ccl-runtime-contract.json']);v=run_checks();write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',dict(v));write(ROOT/'migration/reports/image-ccl-checks.json',v);record('I2','CCL独立BFS/OpenCV交叉、任意native编号正例和像素/压缩/padding/输入/缺例/ABI/文件等验收器正反向检查：'+v['status'],[v['evidence']]);print(v['status'],v['case_count'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
