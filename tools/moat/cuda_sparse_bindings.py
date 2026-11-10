#!/usr/bin/env python3
"""Run real native cuDSS for the exact standard-Fortran fixture arrays."""
import json,shlex,shutil,tarfile
from experiment import ROOT,Experiment,write,digest
from qualification_common import fixture
host='nvidia-5090x2';sdk=ROOT/'build/cuda-sdk';sources=['tools/moat/cuda_uniform_binding.hpp','tools/moat/cuda_sparse_binding_reference.cu','rocm/common/rewrite_runtime.hpp',__file__];e=Experiment('R5','sparse-binding-native-cuDSS','cuda-build',sources=[ROOT/n for n in sources]);remote='/tmp/'+e.id;bundle=e.path/'native.tar.gz';headers=list((sdk/'include').glob('cudss*.h'));library=sdk/'lib/libcudss.so.1';write(e.path/'sdk-identity.json',dict(headers={p.name:digest(p) for p in headers},library=dict(name=library.name,sha256=digest(library),bytes=library.stat().st_size)))
with tarfile.open(bundle,'w:gz') as f:
 for name in sources:f.add(ROOT/name,arcname=str(name) if not str(name).startswith('/') else 'tools/moat/cuda_sparse_bindings.py')
 for path in headers:f.add(path,arcname='sdk/include/'+path.name)
 f.add(library,arcname='sdk/lib/libcudss.so.1');f.add(ROOT/'tests/fixtures/rewrite-bindings',arcname='inputs')
steps=[(['ssh',host,shlex.join(['mkdir','-p',remote])],'prepare'),(['scp',str(bundle),host+':'+remote+'/native.tar.gz'],'upload'),(['ssh',host,shlex.join(['tar','-xzf',remote+'/native.tar.gz','-C',remote])],'unpack'),(['ssh',host,shlex.join(['/usr/local/cuda-13.4/bin/nvcc','-std=c++17','-O2','-arch=sm_120',remote+'/tools/moat/cuda_sparse_binding_reference.cu','-I'+remote+'/rocm/common','-I'+remote+'/sdk/include','-L'+remote+'/sdk/lib','-Xlinker','-rpath='+remote+'/sdk/lib','-l:libcudss.so.1','-lcublas','-o',remote+'/reference'])],'native-build'),(['ssh',host,'nvidia-smi --query-gpu=index,name,uuid,driver_version --format=csv,noheader'],'device-identity')]
for cmd,phase in steps:
 rc=e.command(cmd,phase,timeout=240)
 if rc:print(e.finish('NATIVE_BUILD_FAILED'));raise SystemExit(rc)
build=dict(experiment_id=e.id,evidence=e.finish('EXECUTED'),remote=remote,scope='native cuDSS numerical baseline; actual standard-Fortran AMD entry tested separately; no nvfortran compiler on CUDA host');write(ROOT/'migration/reports/rewrite-sparse-binding-native-build.json',build);results={}
for kind in ['batch','uniform_batch','reordering_phase','residual']:
 for case in ['original','changed-values','layout','base0','repeat','irregular','singular-info']:
  src=ROOT/'tests/fixtures/rewrite-bindings'/kind/case;mf=fixture(src);mh=digest(src/'manifest.json');comparison='sparse-binding/'+kind+'/'+case+'/'+mh;sample='cuDSS/fortran/'+kind+'::'+kind+'.f90';r=Experiment('R5',sample,'cuda-native',case=case,sources=[ROOT/n for n in sources],parent=e.id,comparison_id=comparison);shutil.copytree(src,r.path/'inputs');out=r.path/'outputs';out.mkdir();remoteout=remote+'/outputs/'+kind+'/'+case
  # The transport preserves the native status; outputs are collected even on error.
  command='mkdir -p '+shlex.quote(remoteout)+' && REWRITE_INPUT='+shlex.quote(remote+'/inputs/'+kind+'/'+case)+' REWRITE_OUTPUT='+shlex.quote(remoteout)+' '+shlex.quote(remote+'/reference');rc=r.command(['ssh',host,command],'native-cuDSS-solve');copy=r.command(['scp','-r',host+':'+remoteout+'/.',str(out)],'collect');write(out/'manifest.json',dict(files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in out.iterdir()}));row=dict(sample_id=sample,kind='sparse-binding',profile=kind,language='native-C++-cuDSS',case=case,return_code=rc,collection_return_code=copy,output=str(out.relative_to(ROOT)),input_snapshot=str((r.path/'inputs').relative_to(ROOT)),input_manifest_sha256=mh,comparison_id=comparison,experiment_id=r.id,build=build,baseline_scope=build['scope']);row['evidence']=r.finish('EXECUTED' if rc==0 and copy==0 else 'EXPECTED_REJECTION' if rc==2 and mf['expected_exit']==2 and copy==0 else 'NATIVE_MISMATCH');results[kind+'/'+case]=row;write(ROOT/'migration/reports/rewrite-sparse-binding-cuda.json',results);print(kind,case,rc,flush=True)
