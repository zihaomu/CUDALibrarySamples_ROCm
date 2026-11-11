#!/usr/bin/env python3
"""Replay the CCL build and all full workflows without a preexisting build cache."""
import json,os,shutil,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from image_ccl_build import dependencies
from image_progress import record
def main():
 commit=git('rev-parse','HEAD').strip();names=['image_ccl_contracts.py','image_ccl_build.py','image_ccl_run.py','image_ccl_worker.py','image_ccl_originals.py','image_ccl_reference.py','image_ccl_original_reference.py','image_progress.py','snapshot.py'];sources=[__file__,*dependencies(),*[ROOT/'tools/moat'/n for n in names],ROOT/'tools/migration/bootstrap_sdk.py'];e=Experiment('I2','CCL-clean-checkout','host-cold-replay',sources=sources);where=Path(tempfile.mkdtemp(prefix='image-ccl-cold-',dir=ROOT.parent));clone=where/'src';checks=[];children=[];rc=e.command(['git','clone','--shared','--quiet',str(ROOT),str(clone)],'fresh-clone',timeout=180)
 if not rc:rc=e.command(['git','checkout','--quiet',commit],'fixed-source-commit',cwd=clone)
 checks.append(dict(check='no-preexisting-build',passed=not(clone/'build').exists()))
 if not rc:rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),str(clone/'tools/moat/image_ccl_contracts.py')],'reconstruct-27-frozen-inputs',cwd=clone,timeout=300)
 if not rc:checks.append(dict(check='same-frozen-profile',passed=digest(clone/'migration/rewrite/image-ccl-profile.json')==digest(ROOT/'migration/rewrite/image-ccl-profile.json')))
 env=dict(os.environ,HIP_VISIBLE_DEVICES='2');launcher='/home/zihaomu/zihaomu_workspace/rocm10-launch.sh'
 jobs=[('tools/migration/bootstrap_sdk.py',[]),('tools/moat/image_ccl_build.py',[]),('tools/moat/image_ccl_run.py',[]),('tools/moat/image_ccl_run.py',['--runtime']),('tools/moat/image_ccl_originals.py',[])]
 if not rc:
  for name,args in jobs:
   rc=e.command([launcher,'env','ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0','python3',str(clone/name),*args],'cold-'+Path(name).stem+('-runtime' if args else ''),env=env,cwd=clone,timeout=900)
   if rc:break
 checks.append(dict(check='cold-bootstrap-build-masks-runtime-originals',passed=rc==0))
 if not rc:
  code='''import pathlib,sys,json
clone=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(clone/'tools/moat'))
import image_ccl_reference as oracle
import image_ccl_original_reference as originals
oracle.ROOT=clone;originals.ROOT=clone
for kind in ['masks','runtime','originals']:
 r=json.loads((clone/('migration/reports/image-ccl-'+kind+'.json')).read_text());v=oracle.validate_masks(r) if kind=='masks' else oracle.validate_runtime(r) if kind=='runtime' else [originals.validate(x) for x in r];(out/(kind+'-CPU.json')).write_text(json.dumps(v,indent=2)+'\\n');assert all(x['status']=='PASSED' for x in v);print(kind,len(v),'PASSED',flush=True)
'''
  rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),'-c',code,str(clone),str(e.path)],'independent-all-cold-pixels-files-and-runtime',cwd=clone,timeout=300);checks.append(dict(check='independent-27-masks-44-runtime-15-workflows',passed=rc==0))
 for name in ['contracts','build','masks','runtime','originals']:
  path=clone/f'migration/reports/image-ccl-{name}.json'
  if not path.exists():continue
  rs=json.loads(path.read_text());rs=rs if isinstance(rs,list) else [rs]
  for i,r in enumerate(rs):
   meta=json.loads((clone/r['evidence']/'manifest.json').read_text());raw=clone/meta['raw_artifact_dir']
   if not raw.is_dir() or not (raw/'sealed.json').is_file():continue
   dest=e.path/'child-evidence'/name/str(i);shutil.copytree(raw,dest);(dest/'sealed.json').rename(dest/'child-seal.json');src=json.loads((dest/'source.json').read_text())
   for object_name in src['source_objects'].values():
    source=clone/object_name;target=ROOT/object_name
    if target.exists():
     if digest(target)!=digest(source):raise RuntimeError('source object collision')
    else:shutil.copyfile(source,target)
   children.append(dict(name=name,index=i,relative=str(dest.relative_to(e.path)),report=r))
 checks.append(dict(check='all-19-child-records',passed=len(children)==19))
 builds=[c['report'] for c in children if c['name']=='build'];checks.append(dict(check='same-current-compiled-dependencies',passed=len(builds)==1 and builds[0]['dependencies']=={str(p.relative_to(ROOT)):digest(p) for p in dependencies()}));checks.append(dict(check='final-return-code',passed=rc==0));status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';v=dict(status=status,source_commit=commit,clone=str(clone),return_code=rc,checks=checks,children=children);write(e.path/'cold.json',v);v['evidence']=e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-ccl-cold.json',v);record('I2','CCL干净检出/27输入重建/新HIP编译/两C++全15流程及44运行合同冷重放：'+status+'；全部子raw和source objects封存。',[v['evidence']]);print(status,v['evidence']);return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
