#!/usr/bin/env python3
"""Mutate actual full RGB artifacts and frozen inputs, including paired hash forgeries."""
import argparse,copy,hashlib,json,shutil,tempfile
from pathlib import Path
from unittest.mock import patch
from experiment import ROOT,Experiment,write,digest
import image_flood_reference as reader
from image_flood_inputs import load_case
from image_progress import record
NAMES=['actual29-pass','rebased-complete-raw-pass','unbound-output-redirect','missing-case','duplicate-case','producer-nonzero','case-nonzero','descriptor-size','width','parameter-redefinition','workspace-capacity','missing-buffer','extra-buffer','trailing-region-byte','wrong-RGB','wrong-mask','wrong-bbox','wrong-count','wrong-original-seed','output-padding','mask-padding','input-readback','input-padding','paired-input-and-receipt-forgery','wrong-library-sha','duplicate-producer-option','frozen-input-change','frozen-config-change','frozen-manifest-change','exact-frozen-fixture-rebase-pass']
def run_checks():
 run=json.loads((ROOT/'migration/reports/image-flood-all.json').read_text());source=ROOT/run['outputs'];records=json.loads((source/'runs.json').read_text());spec=json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text());cases={c['case']:c for c in spec['cases']};meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());original_raw=ROOT/meta['raw_artifact_dir'];checks=[];cache={};model=reader.model
 def cached(a,c):
  key=(a.shape,hashlib.sha256(a.tobytes()).hexdigest(),json.dumps({k:c[k] for k in ['mode','seed','lower','upper','fill','boundary']},sort_keys=True))
  if key not in cache:cache[key]=model(a,c)
  return cache[key]
 def check(name,fn,wanted=True):
  try:actual=bool(fn())
  except (ValueError,TypeError,KeyError,IndexError,OSError):actual=False
  checks.append(dict(check=name,passed=actual==wanted))
 def accepted(r,raw=None):
  rows=reader.validate(r,raw_override=raw);return len(rows)==29 and all(v['status']=='PASSED' for v in rows)
 with tempfile.TemporaryDirectory(prefix='flood-core-readers-') as temporary,patch.object(reader,'model',cached):
  base=Path(temporary);check('actual29-pass',lambda:accepted(run))
  def mutant(name,case=None,file=None,change=None,rows_change=None,run_change=None,command_change=None,extra=False,bind=True):
   raw=base/name;out=raw/'outputs';out.mkdir(parents=True);rows=copy.deepcopy(records);commands=json.loads((original_raw/'commands.json').read_text())
   if command_change:command_change(commands)
   write(raw/'commands.json',commands)
   for row in rows:
    p=out/row['case']
    if row['case']==case:shutil.copytree(source/row['case'],p)
    else:p.symlink_to(source/row['case'],target_is_directory=True)
   if file:
    p=out/case/file;change(p);row=next(r for r in rows if r['case']==case)
    if p.exists():row['files'][file]=dict(bytes=p.stat().st_size,sha256=digest(p))
   if extra:(out/case/'unexpected.bin').write_bytes(b'extra')
   if rows_change:rows_change(rows,out)
   write(out/'runs.json',rows);r=copy.deepcopy(run);r['outputs']=str(out)
   if run_change:run_change(r)
   return accepted(r,raw if bind else None)
  check('rebased-complete-raw-pass',lambda:mutant('rebase'));check('unbound-output-redirect',lambda:mutant('unbound',bind=False),False)
  check('missing-case',lambda:mutant('missing',rows_change=lambda rows,out:rows.pop()),False);check('duplicate-case',lambda:mutant('duplicate',rows_change=lambda rows,out:rows.append(copy.deepcopy(rows[0]))),False);check('producer-nonzero',lambda:mutant('producer-rc',run_change=lambda r:r.update(return_code=1)),False);check('case-nonzero',lambda:mutant('case-rc',rows_change=lambda rows,out:rows[0].update(return_code=1)),False)
  for name,field,value in [('descriptor-size','descriptor_bytes',159),('width','width',1),('workspace-capacity','workspace_bytes',1)]:check(name,lambda name=name,field=field,value=value:mutant(name,rows_change=lambda rows,out:rows[0].update({field:value})),False)
  check('parameter-redefinition',lambda:mutant('param',rows_change=lambda rows,out:rows[0]['parameters'].update(lower=[1,1,1])),False);small='constant-all-region'
  def flip(path,offset=0):data=bytearray(path.read_bytes());data[offset]^=1;path.write_bytes(data)
  check('missing-buffer',lambda:mutant('missing-buffer',small,'region.bin',lambda p:p.unlink()),False);check('extra-buffer',lambda:mutant('extra-buffer',small,extra=True),False);check('trailing-region-byte',lambda:mutant('partial',small,'region.bin',lambda p:p.write_bytes(p.read_bytes()+b'\0')),False)
  for name,file,offset in [('wrong-RGB','output.bin',0),('wrong-mask','mask.bin',0),('wrong-bbox','region.bin',0),('wrong-count','region.bin',16),('wrong-original-seed','region.bin',20),('output-padding','output.bin',3*cases[small]['width']),('mask-padding','mask.bin',cases[small]['width']),('input-readback','input-after.bin',0),('input-padding','input-after.bin',3*cases[small]['width'])]:check(name,lambda name=name,file=file,offset=offset:mutant(name,small,file,lambda p:flip(p,offset)),False)
  def paired(rows,out):next(r for r in rows if r['case']==small)['input_before_sha256']=digest(out/small/'input-after.bin')
  check('paired-input-and-receipt-forgery',lambda:mutant('paired-input',small,'input-after.bin',lambda p:flip(p,3*cases[small]['width']),rows_change=paired),False);check('wrong-library-sha',lambda:mutant('library',run_change=lambda r:r['build'].update(library_sha256='0'*64)),False);check('duplicate-producer-option',lambda:mutant('duplicate-argv',command_change=lambda cs:cs[0]['argv'].extend(['--library',str(ROOT/run['build']['library'])])),False)
  for name,file in [('frozen-input-change','input.bin'),('frozen-config-change','config.json'),('frozen-manifest-change','manifest.json')]:
   folder=base/name;shutil.copytree(ROOT/cases[small]['fixture'],folder);flip(folder/file);c=dict(cases[small],fixture=str(folder));check(name,lambda c=c:bool(load_case(c)),False)
  folder=base/'frozen-rebase';shutil.copytree(ROOT/cases[small]['fixture'],folder);check('exact-frozen-fixture-rebase-pass',lambda:load_case(dict(cases[small],fixture=str(folder)))==load_case(cases[small]))
 if len(checks)!=len(NAMES) or {c['check'] for c in checks}!=set(NAMES):raise ValueError('all fixed core reader mutation obligations')
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=len(checks),checks=checks)
def main():
 p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');a=p.parse_args();path=ROOT/'migration/rewrite/image-flood-validator-cases.json'
 if a.freeze:
  e=Experiment('I3','FloodFill-core-validator-mutation-contract','CPU-contract',sources=[__file__,ROOT/'migration/rewrite/image-flood-profile.json']);write(path,NAMES);write(e.path/'cases.json',NAMES);r=dict(status='FROZEN',case_count=len(NAMES));write(e.path/'contracts.json',r);r['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-flood-check-contracts.json',r);record('I3','flood核心验收器'+str(len(NAMES))+'项正向/rebase/实际全RGB-mask-metadata-padding/paired输入receipt/冻结文件反例固定。',[r['evidence']]);print(r['status']);return 0
 if json.loads(path.read_text())!=NAMES:raise ValueError('frozen core reader inventory')
 e=Experiment('I3','FloodFill-real-core-validator-mutations','CPU-validator-test',sources=[__file__,path,ROOT/'tools/moat/image_flood_reference.py',ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-profile.json'])
 try:v=run_checks()
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='all-real-core-reader-mutations-execute',passed=False,error=repr(error))])
 write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-flood-checks.json',v);record('I3','flood30真实核心验收器正反例/允许完整raw重定位而拒绝未绑定重定向、全RGB-mask-info-padding与paired-hash伪造：'+v['status'],[v['evidence']]);print(v['status'],v.get('case_count'),[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
