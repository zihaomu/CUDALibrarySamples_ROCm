#!/usr/bin/env python3
"""Rebuild the C++/Python C3 workflows from a checkout with no private SDK/cache."""
import json,os,shutil,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from canny_color_build import dependencies
from image_progress import record

def main():
 commit=git('rev-parse','HEAD').strip();sources=[__file__,*dependencies()]+[ROOT/'tools/moat'/n for n in ['image_opencv_setup.py','canny_plus_environment.py','canny_color_replay_fixtures.py','canny_color_build.py','canny_color_run.py','canny_color_worker.py','canny_color_reference.py','image_canny_stages_reference.py','image_validation.py','image_progress.py']];e=Experiment('I1','C3-Canny-clean-checkout','host-cold-replay',sources=sources);root=Path(tempfile.mkdtemp(prefix='canny-color-cold-',dir=ROOT.parent));clone=root/'src';checks=[];children=[];env=dict(os.environ,HIP_VISIBLE_DEVICES='2');launcher='/home/zihaomu/zihaomu_workspace/rocm10-launch.sh';rc=e.command(['git','clone','--shared','--quiet',str(ROOT),str(clone)],'fresh-clone',timeout=180)
 if not rc:rc=e.command(['git','checkout','--quiet',commit],'fixed-checkout',cwd=clone)
 checks.append(dict(check='no-preexisting-build-or-SDK',passed=not (clone/'build').exists()))
 if not rc:rc=e.command(['python3',str(clone/'tools/moat/image_opencv_setup.py')],'cold-private-host-OpenCV-SDK',cwd=clone,timeout=300)
 if not rc:
  for name in ['canny_plus_environment.py','canny_color_replay_fixtures.py','canny_color_build.py','canny_color_run.py','canny_color_run.py --originals']:
   args=name.split();cmd=[launcher,'env','ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0','PYTHONPATH='+str(clone/'build/image-gpu-site')+':'+str(clone/'rocm/python'),'python3',str(clone/'tools/moat'/args[0]),*args[1:]];rc=e.command(cmd,'cold-'+args[0].removesuffix('.py')+('-originals' if len(args)>1 else ''),env=env,cwd=clone,timeout=1800)
   if rc:break
 checks.append(dict(check='fresh-SDK-bootstrap-fixtures-build-and-both-languages',passed=rc==0))
 if not rc:
  code='''import json,sys,pathlib
sys.path.insert(0,sys.argv[1]+"/tools/moat")
import canny_color_reference as oracle
clone=pathlib.Path(sys.argv[1]);original=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3]);oracle.ROOT=clone
spec=json.loads((clone/"migration/rewrite/canny-color-profile.json").read_text());native=json.loads((original/"migration/reports/canny-color-native.json").read_text())
for row in native:row["outputs"]=str(original/row["outputs"]);row["evidence"]=str(original/row["evidence"])
runs=json.loads((clone/"migration/reports/canny-color-rocm.json").read_text());masks=oracle.validate_masks(runs[0],spec,native);runs=json.loads((clone/"migration/reports/canny-color-originals.json").read_text());originals=oracle.validate_originals(runs,spec)
for name,v in [("masks",masks),("originals",originals)]:
 (out/(name+"-CPU.json")).write_text(json.dumps(v,indent=2));print(name,v["status"],v["case_count"],flush=True)
assert masks["status"]==originals["status"]=="PASSED"
'''
  rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),'-c',code,str(clone),str(ROOT),str(e.path)],'independent-22-masks-and-ten-original-files',timeout=300)
  checks.append(dict(check='all-fresh-22-masks-and-ten-language-workflows-CPU',passed=rc==0))
 reports={'SDK':'image-opencv-sdk','environment':'canny-plus-environment','fixtures':'canny-color-fixture-replay','build':'canny-color-build','masks':'canny-color-rocm','originals':'canny-color-originals'}
 for name,filename in reports.items():
  path=clone/('migration/reports/'+filename+'.json')
  if not path.is_file():continue
  value=json.loads(path.read_text());entries=value if isinstance(value,list) else [value]
  for index,report in enumerate(entries):
   reference=clone/report['evidence']
   if not (reference/'manifest.json').is_file():continue
   meta=json.loads((reference/'manifest.json').read_text());raw=clone/meta['raw_artifact_dir'];dest=e.path/'child-evidence'/name/str(index);shutil.copytree(raw,dest);(dest/'sealed.json').rename(dest/'child-seal.json');src=json.loads((dest/'source.json').read_text())
   for object_name in src['source_objects'].values():
    original=clone/object_name;target=ROOT/object_name
    if target.exists():
     if digest(target)!=digest(original):raise RuntimeError('Source object collision')
    else:shutil.copyfile(original,target)
   children.append(dict(name=name,index=index,relative=str(dest.relative_to(e.path)),report=report))
 if not rc:
  b=next(r['report'] for r in children if r['name']=='build');checks.append(dict(check='fresh-current-compiled-source-closure',passed=b['dependencies']=={str(p.relative_to(ROOT)):digest(p) for p in dependencies()}));checks.append(dict(check='all-fifteen-fresh-child-records',passed=len(children)==15))
 checks.append(dict(check='cold-final-process-success',passed=rc==0));status='PASSED' if checks and all(c['passed'] is True for c in checks) else 'FAILED';result=dict(status=status,checks=checks,source_commit=commit,clone=str(clone),children=children,return_code=rc);write(e.path/'cold.json',result);result['evidence']=e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/canny-color-cold.json',result);record('I1','C3干净clone私有SDK/依赖/输入/编译/22mask及两语言10完整入口重放：'+status+'；全部子raw与source objects由父seal保留。',[result['evidence']]);print(status,result['evidence']);return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
