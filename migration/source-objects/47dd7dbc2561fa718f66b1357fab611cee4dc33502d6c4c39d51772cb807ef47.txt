#!/usr/bin/env python3
"""Actual output mutations of the full frozen distance acceptance readers."""
import copy,hashlib,json,shutil,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from experiment import ROOT,Experiment,write,digest
import image_distance_reference as reader
import image_distance_original_reference as originals
from image_distance_inputs import load_case
from image_progress import record

NAMES=['actual-full-thirty-passes','relocated-complete-raw-passes','unbound-output-redirect-rejected','missing-case','duplicate-case','producer-nonzero','case-nonzero','wrong-descriptor-size','wrong-width','changed-input-bytes','changed-input-padding','wrong-declared-padding','missing-buffer','extra-buffer','trailing-partial-element','within-fixed-distance-budget','outside-fixed-distance-budget','positive-infinity-cannot-be-positive-NaN','negative-infinity-cannot-be-negative-NaN','unsigned-infinity-cannot-be-NaN','wrong-infinity-sign','wrong-site-ID','wrong-site-coordinate','wrong-absolute-index','wrong-relative-index','wrong-visualization','wrong-output-padding','frozen-input-bytes-change','frozen-config-change','frozen-manifest-change','original-floating-helper-rejects-positive-NaN','original-floating-helper-rejects-negative-NaN','relocated-frozen-fixture-bytes-pass','coupled-semantics-preserving-fixture-and-receipt-forgery-rejected']

def run_checks():
 run=json.loads((ROOT/'migration/reports/image-distance-all.json').read_text());actual=ROOT/run['outputs'];records=json.loads((actual/'runs.json').read_text());spec=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());cases={c['case']:c for c in spec['cases']};meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());source_raw=ROOT/meta['raw_artifact_dir'];cache={};original_model=reader.model;checks=[]
 def cached(a,mode,cutoff,remap):
  key=(a.shape,a.dtype.str,hashlib.sha256(a.tobytes()).hexdigest(),mode,cutoff,remap)
  if key not in cache:cache[key]=original_model(a,mode,cutoff,remap)
  return cache[key]
 def check(name,fn,wanted=True):
  try:observed=bool(fn())
  except (ValueError,TypeError,KeyError,IndexError,OSError):observed=False
  checks.append(dict(check=name,passed=observed==wanted))
 with tempfile.TemporaryDirectory(prefix='distance-validator-') as temporary,patch.object(reader,'model',cached):
  base=Path(temporary)
  check(NAMES[0],lambda:all(r['status']=='PASSED' for r in reader.validate(run)))
  def mutant(name,case=None,change=None,rows_change=None,run_change=None,extra=False,bind=True):
   raw=base/name;out=raw/'outputs';out.mkdir(parents=True);shutil.copyfile(source_raw/'commands.json',raw/'commands.json');rows=copy.deepcopy(records)
   for row in rows:
    target=out/row['case']
    if row['case']==case:shutil.copytree(actual/row['case'],target)
    else:target.symlink_to(actual/row['case'],target_is_directory=True)
   if change:
    filename,fn=change;p=out/case/filename;fn(p);row=next(r for r in rows if r['case']==case)
    if p.exists():row['files'][filename]=dict(bytes=p.stat().st_size,sha256=digest(p))
   if extra:(out/case/'unexpected.bin').write_bytes(b'bad')
   if rows_change:rows_change(rows)
   write(out/'runs.json',rows);r=dict(run,outputs=str(out))
   if run_change:r.update(run_change)
   return all(v['status']=='PASSED' for v in reader.validate(r,raw_override=raw if bind else None))
  check(NAMES[1],lambda:mutant('relocated'))
  check(NAMES[2],lambda:mutant('unbound',bind=False),False)
  check('missing-case',lambda:mutant('missing',rows_change=lambda rs:rs.pop()),False)
  check('duplicate-case',lambda:mutant('duplicate',rows_change=lambda rs:rs.append(copy.deepcopy(rs[0]))),False)
  check('producer-nonzero',lambda:mutant('producer',run_change=dict(return_code=1)),False)
  check('case-nonzero',lambda:mutant('case-status',rows_change=lambda rs:rs[0].update(return_code=1)),False)
  check('wrong-descriptor-size',lambda:mutant('ABI',rows_change=lambda rs:rs[0].update(descriptor_bytes=159)),False)
  check('wrong-width',lambda:mutant('width',rows_change=lambda rs:rs[0].update(width=1)),False)
  small='unsigned-no-site'
  def flip(path,at=0):b=bytearray(path.read_bytes());b[at]^=1;path.write_bytes(b)
  check('changed-input-bytes',lambda:mutant('input',small,('input-after.bin',flip)),False)
  check('changed-input-padding',lambda:mutant('input-pad',small,('input-after.bin',lambda p:flip(p,cases[small]['width']))),False)
  check('wrong-declared-padding',lambda:mutant('declared-pad',rows_change=lambda rs:rs[0]['pads'].update(distance=0)),False)
  check('missing-buffer',lambda:mutant('missing-buffer',small,('site_ids.bin',lambda p:p.unlink())),False)
  check('extra-buffer',lambda:mutant('extra',small,extra=True),False)
  check('trailing-partial-element',lambda:mutant('partial',small,('distance.bin',lambda p:p.write_bytes(p.read_bytes()+b'\x00'))),False)
  def floating(path,value,offset=0):b=bytearray(path.read_bytes());b[offset:offset+8]=np.array([value],'<f8').tobytes();path.write_bytes(b)
  case='unsigned-one-site';profile=cases[case];width=profile['width'];point=(7*(width*8+40)+(11+1)*8)
  check('within-fixed-distance-budget',lambda:mutant('within',case,('distance.bin',lambda p:floating(p,1.+1e-12,point))))
  check('outside-fixed-distance-budget',lambda:mutant('outside',case,('distance.bin',lambda p:floating(p,1.+1e-5,point))),False)
  for name,case,value in [('positive-infinity-cannot-be-positive-NaN','signed-constant-positive',np.nan),('negative-infinity-cannot-be-negative-NaN','signed-constant-negative',np.copysign(np.nan,-1.)),('unsigned-infinity-cannot-be-NaN','unsigned-no-site',np.nan),('wrong-infinity-sign','unsigned-no-site',-np.inf)]:check(name,lambda name=name,case=case,value=value:mutant(name,case,('distance.bin',lambda p:floating(p,value))),False)
  for name,filename in [('wrong-site-ID','site_ids.bin'),('wrong-site-coordinate','sites_xy.bin'),('wrong-absolute-index','indices.bin'),('wrong-relative-index','relative.bin'),('wrong-visualization','visualization.bin')]:check(name,lambda name=name,filename=filename:mutant(name,small,(filename,flip)),False)
  check('wrong-output-padding',lambda:mutant('output-pad',small,('distance.bin',lambda p:flip(p,cases[small]['width']*8))),False)
  for name,file in [('frozen-input-bytes-change','input.bin'),('frozen-config-change','config.json'),('frozen-manifest-change','manifest.json')]:
   folder=base/name;shutil.copytree(ROOT/cases[small]['fixture'],folder);p=folder/file
   if file=='input.bin':b=bytearray(p.read_bytes());b[0]=2;p.write_bytes(b)
   else:flip(p)
   case=dict(cases[small],fixture=str(folder));check(name,lambda case=case:bool(load_case(case)),False)
  fresh=base/'relocated-fixture';shutil.copytree(ROOT/cases[small]['fixture'],fresh);check('relocated-frozen-fixture-bytes-pass',lambda:load_case(dict(cases[small],fixture=str(fresh)))==(ROOT/cases[small]['fixture']/'input.bin').read_bytes())
  forged=base/'coupled-fixture';shutil.copytree(ROOT/cases[small]['fixture'],forged);blob=bytearray((forged/'input.bin').read_bytes());blob[0]=2;(forged/'input.bin').write_bytes(blob);forged_profile=copy.deepcopy(spec);next(c for c in forged_profile['cases'] if c['case']==small)['fixture']=str(forged);profile_text=(ROOT/'migration/rewrite/image-distance-profile.json').read_text();original_loads=json.loads
  def replaced_profile(text,*args,**kwargs):return copy.deepcopy(forged_profile) if text==profile_text else original_loads(text,*args,**kwargs)
  def forge_receipt(rows):next(r for r in rows if r['case']==small)['input_before_sha256']=hashlib.sha256(blob).hexdigest()
  def forged_after(path):path.write_bytes(blob)
  with patch.object(reader.json,'loads',replaced_profile):check('coupled-semantics-preserving-fixture-and-receipt-forgery-rejected',lambda:mutant('coupled-receipt',small,('input-after.bin',forged_after),rows_change=forge_receipt),False)
  for name,value,expected in [('original-floating-helper-rejects-positive-NaN',np.nan,np.inf),('original-floating-helper-rejects-negative-NaN',np.copysign(np.nan,-1.),-np.inf)]:
   p=base/(name+'.bin');np.array([value],'<f8').tofile(p);check(name,lambda p=p,expected=expected:originals.values(p,np.array([expected],'<f8'),True),False)
 if len(checks)!=len(NAMES) or {c['check'] for c in checks}!=set(NAMES):raise ValueError('all fixed validator mutation obligations')
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=len(checks),checks=checks)

def main():
 names=ROOT/'migration/rewrite/image-distance-validator-cases.json'
 if json.loads(names.read_text())!=NAMES:raise ValueError('frozen validator inventory')
 e=Experiment('I2','Distance-real-validator-mutations','CPU-validator-test',sources=[__file__,names,*[ROOT/'tools/moat'/n for n in ['image_distance_reference.py','image_distance_original_reference.py','image_distance_model.py','image_distance_inputs.py']],ROOT/'migration/rewrite/image-distance-profile.json'])
 try:v=run_checks()
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='all-actual-mutations-execute',passed=False,error=repr(error))])
 write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-distance-checks.json',v);record('I2','EDT固定34项实际完整输出/预算内外/±Inf对NaN/身份/字节/ABI/冻结输入/原例helper验收器反例：'+v['status'],[v['evidence']]);print(v['status'],v.get('case_count'),[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
