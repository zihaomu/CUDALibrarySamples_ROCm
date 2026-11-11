#!/usr/bin/env python3
"""Rebuild contour code and replay full numerical and runtime contracts in a clone."""
import json,os,shutil,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from image_contour_build import dependencies
from image_progress import record

GROUPS=['contracts','build','all','frontends-build','originals','data-errors','arguments','states']
def main():
 commit=git('rev-parse','HEAD').strip();sources=[__file__,*dependencies(),ROOT/'tools/migration/bootstrap_sdk.py',*sorted((ROOT/'tools/moat').glob('image_contour_*.py')),*sorted((ROOT/'migration/rewrite').glob('image-contour-*.json'))];e=Experiment('I2','Contour-clean-checkout','host-cold-replay',sources=sources);where=Path(tempfile.mkdtemp(prefix='image-contour-cold-',dir=ROOT.parent));clone=where/'src';checks=[];children=[];rc=e.command(['git','clone','--shared','--quiet',str(ROOT),str(clone)],'fresh-clone',timeout=180)
 if not rc:rc=e.command(['git','checkout','--quiet',commit],'fixed-source-commit',cwd=clone)
 checks.append(dict(check='no-preexisting-build',passed=not(clone/'build').exists()))
 if not rc:rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),str(clone/'tools/moat/image_contour_contracts.py')],'reconstruct-all-22-frozen-inputs',cwd=clone,timeout=300)
 checks.append(dict(check='same-frozen-profile',passed=not rc and digest(clone/'migration/rewrite/image-contour-profile.json')==digest(ROOT/'migration/rewrite/image-contour-profile.json')))
 launcher='/home/zihaomu/zihaomu_workspace/rocm10-launch.sh'
 jobs=['tools/migration/bootstrap_sdk.py','tools/moat/image_contour_build.py','tools/moat/image_contour_run.py','tools/moat/image_contour_frontends_build.py','tools/moat/image_contour_originals.py','tools/moat/image_contour_data_errors.py','tools/moat/image_contour_arguments.py','tools/moat/image_contour_states.py']
 if not rc:
  for name in jobs:
   multi=name.endswith('image_contour_states.py');env=dict(os.environ,HIP_VISIBLE_DEVICES='0,2' if multi else '2');mask=['ROCR_VISIBLE_DEVICES=2,3','HIP_VISIBLE_DEVICES=0,1'] if multi else ['ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0'];rc=e.command([launcher,'env',*mask,'python3',str(clone/name)],'cold-'+Path(name).stem,env=env,cwd=clone,timeout=900)
   if rc:break
 checks.append(dict(check='cold-bootstrap-build-full-inputs-originals-and-runtime',passed=rc==0))
 if not rc:
  code=r'''import json,pathlib,sys
clone=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);sys.path.insert(0,str(clone/'tools/moat'))
import image_contour_reference as masks
import image_contour_original_reference as originals
import image_contour_data_reference as data
import image_contour_arguments_reference as arguments
import image_contour_states_reference as states
for name,fn in [('all',masks.validate),('originals',originals.validate),('data-errors',data.validate),('arguments',arguments.validate),('states',states.validate)]:
 r=json.loads((clone/f'migration/reports/image-contour-{name}.json').read_text());v=fn(r);(out/(name+'-CPU.json')).write_text(json.dumps(v,indent=2)+'\n');assert all(x['status']=='PASSED' for x in v) if isinstance(v,list) else v['status']=='PASSED';print(name,len(v) if isinstance(v,list) else v['case_count'],'PASSED',flush=True)
'''
  rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),'-c',code,str(clone),str(e.path)],'independent-all-cold-pixels-geometry-files-and-runtime',cwd=clone,timeout=600);checks.append(dict(check='independent-22-inputs-15-workflows-26-data-61-argument-11-state-contracts',passed=rc==0))
 for name in GROUPS:
  path=clone/f'migration/reports/image-contour-{name}.json'
  if not path.exists():continue
  rs=json.loads(path.read_text());rs=rs if isinstance(rs,list) else [rs]
  for i,r in enumerate(rs):
   meta=json.loads((clone/r['evidence']/'manifest.json').read_text());raw=clone/meta['raw_artifact_dir']
   if not raw.is_dir() or not(raw/'sealed.json').is_file():continue
   dest=e.path/'child-evidence'/name/str(i);shutil.copytree(raw,dest);(dest/'sealed.json').rename(dest/'child-seal.json');src=json.loads((dest/'source.json').read_text())
   for object_name in src['source_objects'].values():
    source=clone/object_name;target=ROOT/object_name
    if target.exists():
     if digest(target)!=digest(source):raise RuntimeError('source object collision')
    else:shutil.copyfile(source,target)
   children.append(dict(name=name,index=i,relative=str(dest.relative_to(e.path)),report=r))
 checks.append(dict(check='all-22-sealed-child-records',passed=len(children)==22));builds=[c['report'] for c in children if c['name']=='build'];checks.append(dict(check='same-current-compiled-dependencies',passed=len(builds)==1 and builds[0]['abi_version']==2 and builds[0]['dependencies']=={str(p.relative_to(ROOT)):digest(p) for p in dependencies()}));checks.append(dict(check='final-return-code',passed=rc==0));status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';v=dict(status=status,source_commit=commit,clone=str(clone),return_code=rc,checks=checks,children=children);write(e.path/'cold.json',v);v['evidence']=e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-contour-cold.json',v);record('I2','Contour干净检出/22输入重建/ABI2新HIP编译/15实际原流程及26设备数据、61参数、11状态合同冷重放：'+status+'；22子记录原始bytes和source objects封存。',[v['evidence']]);print(status,v['evidence']);return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
