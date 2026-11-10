#!/usr/bin/env python3
import argparse,json,shlex,tarfile,shutil
from pathlib import Path
from experiment import Experiment,ROOT,write,digest
p=argparse.ArgumentParser();p.add_argument('--only',nargs='*',default=[]);p.add_argument('--cases',nargs='*',default=[]);a=p.parse_args();host='nvidia-5090x2'
sources=[ROOT/'tools/moat/cuda_first_reference.cu',ROOT/'rocm/common/rewrite_runtime.hpp',ROOT/'tools/moat/cuda_remote_run.py']
build=Experiment('R1-R2','first-eight-native-and-compatible','cuda-build',sources=sources)
remote='/tmp/'+build.id;bundle=build.path/'inputs.tar.gz'
shared_inputs=build.path/'inputs';shutil.copytree(ROOT/'tests/fixtures/rewrite-first',shared_inputs)
with tarfile.open(bundle,'w:gz') as f:
 for source in sources:f.add(source,arcname=str(source.relative_to(ROOT)))
 f.add(shared_inputs,arcname='tests/fixtures/rewrite-first')
commands=[(['ssh',host,shlex.join(['mkdir','-p',remote])],'prepare'),
          (['scp',str(bundle),host+':'+remote+'/inputs.tar.gz'],'upload'),
          (['ssh',host,shlex.join(['tar','-xzf',remote+'/inputs.tar.gz','-C',remote])],'unpack'),
          (['ssh',host,shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/tools/moat/cuda_first_reference.cu','-I'+remote+'/rocm/common','-lcublas','-lcublasLt','-lcusolver','-o',remote+'/reference'])],'build'),
          (['ssh',host,'nvidia-smi --query-gpu=index,name,uuid,driver_version --format=csv,noheader'],'device-identity')]
for cmd,phase in commands:
 rc=build.command(cmd,phase,timeout=240)
 if rc:print(build.finish('BUILD_ERROR',reason=f'{phase} exit {rc}'));raise SystemExit(rc)
evidence=build.finish('EXECUTED');print('CUDA build',evidence,flush=True)
spec=json.loads((ROOT/'migration/rewrite/first-eight.json').read_text())['profiles'];report=ROOT/'migration/reports/rewrite-first-cuda.json';records=json.loads(report.read_text()) if report.exists() else {}
for profile in spec:
 kind=profile['kind']
 if a.only and kind not in a.only:continue
 for case in profile['cases']:
  if a.cases and case not in a.cases:continue
  fixture=shared_inputs/kind/case;mh=digest(fixture/'manifest.json')
  e=Experiment(profile['batch'],profile['sample_id'],'cuda',case=case,sources=sources,
      parent=build.id,comparison_id=kind+'/'+case+'/'+mh)
  shutil.copytree(fixture,e.path/'inputs')
  out=e.path/'outputs';out.mkdir();remoteout=remote+'/outputs/'+kind+'/'+case
  cmd=['python3',remote+'/tools/moat/cuda_remote_run.py','--input',remote+'/tests/fixtures/rewrite-first/'+kind+'/'+case,'--output',remoteout,'--binary',remote+'/reference','--kind',kind]
  rc=e.command(['ssh',host,shlex.join(cmd)],'cuda-run',timeout=180)
  copyrc=e.command(['scp','-r',host+':'+remoteout+'/.',str(out)],'collect',timeout=60)
  record=dict(kind=kind,case=case,return_code=rc if rc else copyrc,output=str(out.relative_to(ROOT)),
              experiment_id=e.id,comparison_id=e.meta['comparison_id'],input_manifest_sha256=mh,
              input_snapshot=str((e.path/'inputs').relative_to(ROOT)),
              baseline_scope='native-cuBLAS-3m-or-Lt-planar' if kind in ['gemm3m','herk3m','syrk3m','planar'] else 'compatible-CUDA-mathematics-not-original-MathDx-or-special-IMMA')
  record['evidence']=e.finish('EXECUTED' if not rc and not copyrc else 'RUNTIME_ERROR',reason=None if not rc and not copyrc else f'CUDA exit {rc}, collect {copyrc}')
  records[kind+'/'+case]=record;write(report,records);print(kind,case,rc,flush=True)
