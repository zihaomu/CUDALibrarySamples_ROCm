#!/usr/bin/env python3
"""Build and replay the complete C1 workflow in a checkout with no build cache."""
import json,os,shutil,sys,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from image_progress import record

def main():
 commit=git('rev-parse','HEAD').strip();sources=[__file__]+[ROOT/'tools/moat'/n for n in ['canny_plus_environment.py','canny_plus_replay_fixtures.py','canny_plus_build.py','canny_plus_run.py','canny_plus_validate.py','canny_plus_worker.py']]
 e=Experiment('I1','CannyPlus-clean-checkout','host-cold-replay',sources=sources);checks=[];child=[];root=Path(tempfile.mkdtemp(prefix='canny-cold-',dir=ROOT.parent));clone=root/'src'
 launcher='/home/zihaomu/zihaomu_workspace/rocm10-launch.sh'
 env=dict(os.environ,HIP_VISIBLE_DEVICES='2');rc=e.command(['git','clone','--shared','--quiet',str(ROOT),str(clone)],'fresh-clone',timeout=180,env=env)
 if not rc:rc=e.command(['git','checkout','--quiet',commit],'fixed-checkout',cwd=clone)
 checks.append(dict(check='no-preexisting-build-cache',passed=not (clone/'build').exists()))
 if not rc:
  for name in ['canny_plus_environment.py','canny_plus_replay_fixtures.py','canny_plus_build.py','canny_plus_run.py','canny_plus_run.py --original']:
   args=name.split();command=[launcher,'env','ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0','PYTHONPATH='+str(clone/'build/image-gpu-site')+':'+str(clone/'rocm/python'),'python3',str(clone/'tools/moat'/args[0]),*args[1:]]
   rc=e.command(command,'cold-'+args[0].removesuffix('.py')+('-original' if len(args)>1 else ''),env=env,cwd=clone,timeout=1800)
   if rc:break
 checks.append(dict(check='cold-bootstrap-fixtures-compile-and-both-GPU-workflows',passed=rc==0))
 if not rc:
  code='''import json,sys,pathlib
sys.path.insert(0,sys.argv[1]+"/tools/moat")
import canny_plus_validate as oracle
clone=pathlib.Path(sys.argv[1]);original=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3]);oracle.ROOT=clone
spec=json.loads((clone/"migration/rewrite/canny-plus-profile.json").read_text());native=json.loads((original/"migration/reports/canny-plus-native.json").read_text())
for row in native:row["outputs"]=str(original/row["outputs"])
rows=[]
for name,is_original in [("rocm",False),("original",True)]:
 run=json.loads((clone/("migration/reports/canny-plus-"+name+".json")).read_text());v=oracle.validate(run,spec,native,is_original);rows.append(v);(out/(name+"-CPU.json")).write_text(json.dumps(v,indent=2));print(name,v["status"],v["case_count"],flush=True)
assert all(v["status"]=="PASSED" for v in rows)
'''
  rc=e.command([str(ROOT/'build/image-cpu-venv/bin/python'),'-c',code,str(clone),str(ROOT),str(e.path)],'independent-full-cold-output-validation',timeout=300)
  checks.append(dict(check='fresh-31-masks-and-eight-original-files-CPU',passed=rc==0))
  for name in ['environment','fixture-replay','build','rocm','original']:
   report=json.loads((clone/('migration/reports/canny-plus-'+name+'.json')).read_text());reference=clone/report['evidence'];meta=json.loads((reference/'manifest.json').read_text());raw=clone/meta['raw_artifact_dir'];dest=e.path/'child-evidence'/name;shutil.copytree(raw,dest);child.append(dict(name=name,relative=str(dest.relative_to(e.path)),report=report))
  build=next(r['report'] for r in child if r['name']=='build');checks.append(dict(check='fresh-compiled-source-closure',passed=all(digest(ROOT/n)==sha for n,sha in build['dependencies'].items())))
 checks.append(dict(check='cold-final-process-success',passed=rc==0))
 status='PASSED' if checks and all(c['passed'] is True for c in checks) else 'FAILED';result=dict(status=status,checks=checks,source_commit=commit,clone=str(clone),children=child,return_code=rc)
 write(e.path/'cold.json',result);result['evidence']=e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/canny-plus-cold.json',result)
 record('I1','全新checkout无build缓存：'+status+'；重新安装私有依赖、重建31输入/共享库、重跑31mask与8尺寸1000循环、独立CPU复核。',[result['evidence']]);print(status,result['evidence']);return int(status!='PASSED')
if __name__=='__main__':raise SystemExit(main())
