#!/usr/bin/env python3
"""Reconstruct all distance fixtures and replay complete fresh HIP callers and runtime states."""
import json,os,shutil,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from image_distance_build import dependencies
from image_progress import record

GROUPS=['contracts','original-contracts','state-contracts','build','all','frontend-build','originals','arguments','states']
def main():
 commit=git('rev-parse','HEAD').strip();sources=[__file__,*dependencies(),ROOT/'tools/migration/bootstrap_sdk.py',*sorted((ROOT/'tools/moat').glob('image_distance_*.py')),*sorted((ROOT/'migration/rewrite').glob('image-distance-*.json'))];e=Experiment('I2','Distance-clean-checkout-complete-original-and-runtime','host-cold-replay',sources=sources);clone=Path(tempfile.mkdtemp(prefix='image-distance-cold-',dir=ROOT.parent))/'src';children=[];checks=[];rc=e.command(['git','clone','--shared','--quiet',str(ROOT),str(clone)],'fresh-clone',timeout=180)
 try:
  if not rc:rc=e.command(['git','checkout','--quiet',commit],'fixed-source-commit',cwd=clone)
  checks.append(dict(check='no-preexisting-build-or-library-cache',passed=not(clone/'build').exists()))
  for name in ['contracts','original_contracts','state_contracts']:
   if rc:break
   rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),str(clone/('tools/moat/image_distance_'+name+'.py'))],'reconstruct-'+name,cwd=clone,timeout=300)
  checks.append(dict(check='same-all-three-frozen-input-and-workflow-profiles',passed=not rc and all(digest(clone/n)==digest(ROOT/n) for n in ['migration/rewrite/image-distance-profile.json','migration/rewrite/image-distance-original-contract.json','migration/rewrite/image-distance-state-contract.json'])))
  jobs=['tools/migration/bootstrap_sdk.py','tools/moat/image_distance_build.py','tools/moat/image_distance_run.py','tools/moat/image_distance_frontend_build.py','tools/moat/image_distance_originals.py','tools/moat/image_distance_arguments.py','tools/moat/image_distance_states.py']
  for name in jobs:
   if rc:break
   multi=name.endswith('image_distance_states.py');env=dict(os.environ,HIP_VISIBLE_DEVICES='0,2' if multi else '2');mask=['ROCR_VISIBLE_DEVICES=2,3','HIP_VISIBLE_DEVICES=0,1'] if multi else ['ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0'];rc=e.command(['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh','env',*mask,'python3',str(clone/name)],'cold-'+Path(name).stem,cwd=clone,env=env,timeout=900)
  checks.append(dict(check='fresh-bootstrap-build-thirty-inputs-four-originals-and-runtime',passed=rc==0))
  if not rc:
   code=r'''import json,pathlib,sys
clone=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(clone/'tools/moat'))
import image_distance_reference as core
import image_distance_original_reference as originals
import image_distance_arguments_reference as arguments
import image_distance_states_reference as states
for name,fn in [('all',core.validate),('originals',originals.validate),('arguments',arguments.validate),('states',states.validate)]:
 r=json.loads((clone/f'migration/reports/image-distance-{name}.json').read_text());v=fn(r);(out/(name+'-CPU.json')).write_text(json.dumps(v,indent=2)+'\n');assert all(x['status']=='PASSED' for x in v) if isinstance(v,list) else v['status']=='PASSED';print(name,len(v) if isinstance(v,list) else v['case_count'],'PASSED',flush=True)
'''
   rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),'-c',code,str(clone),str(e.path)],'independent-complete-cold-pixels-files-descriptors-and-state-transitions',cwd=clone,timeout=600);checks.append(dict(check='independent-thirty-inputs-48-RAW-69-arguments-27-states',passed=rc==0))
  for name in GROUPS:
   path=clone/f'migration/reports/image-distance-{name}.json'
   if not path.exists():continue
   rows=json.loads(path.read_text());rows=rows if isinstance(rows,list) else [rows]
   for i,r in enumerate(rows):
    meta=json.loads((clone/r['evidence']/'manifest.json').read_text());raw=clone/meta['raw_artifact_dir']
    if not raw.is_dir() or not(raw/'sealed.json').is_file():continue
    target=e.path/'child-evidence'/name/str(i);shutil.copytree(raw,target);(target/'sealed.json').rename(target/'child-seal.json');source=json.loads((target/'source.json').read_text())
    for object_name in source['source_objects'].values():
     src=clone/object_name;dst=ROOT/object_name
     if dst.exists():
      if digest(src)!=digest(dst):raise ValueError('source object collision')
     else:shutil.copyfile(src,dst)
    children.append(dict(name=name,index=i,relative=str(target.relative_to(e.path)),report=r))
  checks.append(dict(check='all-twelve-complete-sealed-child-records',passed=len(children)==12));builds=[c['report'] for c in children if c['name']=='build'];checks.append(dict(check='same-current-compiled-backend-dependencies',passed=len(builds)==1 and builds[0]['abi_version']==1 and builds[0]['dependencies']=={str(p.relative_to(ROOT)):digest(p) for p in dependencies()}))
 except Exception as error:checks.append(dict(check='cold-replay-finished-with-complete-evidence',passed=False,error=repr(error)));rc=rc or 1
 checks.append(dict(check='final-return-code',passed=rc==0));status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';v=dict(status=status,return_code=rc,source_commit=commit,clone=str(clone),checks=checks,children=children);write(e.path/'cold.json',v);v['evidence']=e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-distance-cold.json',v);record('I2','EDT干净检出/三类输入重建/全新HIP编译/30输入/4完整原流程48RAW/69参数/27状态及极值、12子记录冷重放：'+status,[v['evidence']]);print(status,v['evidence']);return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
