#!/usr/bin/env python3
import argparse,json,shlex,shutil,tarfile
from experiment import ROOT,Experiment,write,digest
p=argparse.ArgumentParser();p.add_argument('--only',nargs='+',required=True);p.add_argument('--native-approx',action='store_true');args=p.parse_args();host='nvidia-5090x2'
sources=[ROOT/'tools/moat/cuda_extension_reference.cu',ROOT/'rocm/common/rewrite_runtime.hpp',ROOT/'tools/moat/cuda_remote_run.py',ROOT/'tools/moat/cuda_extensions.py'];build=Experiment('R3-R7','registered-extensions','cuda-build',sources=sources);remote='/tmp/'+build.id;shared=build.path/'inputs';shutil.copytree(ROOT/'tests/fixtures/rewrite-extensions',shared);bundle=build.path/'inputs.tar.gz'
with tarfile.open(bundle,'w:gz') as f:
 for source in sources:f.add(source,arcname=str(source.relative_to(ROOT)))
 f.add(shared,arcname='tests/fixtures/rewrite-extensions')
steps=[(['ssh',host,shlex.join(['mkdir','-p',remote])],'prepare'),(['scp',str(bundle),host+':'+remote+'/inputs.tar.gz'],'upload'),(['ssh',host,shlex.join(['tar','-xzf',remote+'/inputs.tar.gz','-C',remote])],'unpack'),(['ssh',host,shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/tools/moat/cuda_extension_reference.cu','-I'+remote+'/rocm/common','-lcublas','-lcusolver','-o',remote+'/reference'])],'build'),(['ssh',host,'nvidia-smi --query-gpu=index,name,uuid,driver_version --format=csv,noheader'],'device-identity')]
for cmd,phase in steps:
 rc=build.command(cmd,phase,timeout=240)
 if rc:print(build.finish('BUILD_ERROR'));raise SystemExit(rc)
be=build.finish('EXECUTED');profiles=json.loads((ROOT/'migration/rewrite/extensions.json').read_text())['profiles'];suffix='native-approx' if args.native_approx else 'cuda';report=ROOT/f'migration/reports/rewrite-extension-{suffix}.json';records=json.loads(report.read_text()) if report.exists() else {}
for profile in profiles:
 if profile['kind'] not in args.only:continue
 for case in (['original'] if args.native_approx else profile['cases']):
  src=shared/profile['kind']/case;mh=digest(src/'manifest.json');e=Experiment(profile['batch'],profile['sample_id'],suffix,case=case,sources=sources,parent=build.id,comparison_id=profile['kind']+'/'+case+'/'+mh);shutil.copytree(src,e.path/'inputs');out=e.path/'outputs';out.mkdir();remoteout=remote+'/outputs/'+profile['kind']+'/'+case;kind='svd-native' if args.native_approx else profile['kind']
  command=['python3',remote+'/tools/moat/cuda_remote_run.py','--input',remote+'/tests/fixtures/rewrite-extensions/'+profile['kind']+'/'+case,'--output',remoteout,'--binary',remote+'/reference','--kind',kind]
  rc=e.command(['ssh',host,shlex.join(command)],'cuda-run');copyrc=e.command(['scp','-r',host+':'+remoteout+'/.',str(out)],'collect')
  write(out/'manifest.json',dict(files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in out.iterdir() if p.is_file()}));r=dict(kind=profile['kind'],case=case,return_code=rc or copyrc,output=str(out.relative_to(ROOT)),input_snapshot=str((e.path/'inputs').relative_to(ROOT)),input_manifest_sha256=mh,comparison_id=e.meta['comparison_id'],experiment_id=e.id,baseline_scope='native-cusolver-gesvda' if args.native_approx else 'compatible-CUDA-native-full-SVD-plus-projection',build_evidence=be)
  r['evidence']=e.finish('EXECUTED' if not rc and not copyrc else 'RUNTIME_ERROR');records[profile['kind']+'/'+case]=r;write(report,records);print(kind,case,rc,flush=True)
