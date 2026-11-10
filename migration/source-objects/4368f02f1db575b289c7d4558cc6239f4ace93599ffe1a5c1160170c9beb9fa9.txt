#!/usr/bin/env python3
"""Preserve source, device/rank identity and every numerical attempt for B12--B15."""
import argparse,datetime,json,os,pathlib,re,subprocess,signal
from catalog import ROOT
from run import digest
from batches12_15_spec import GROUPS,kind,model

def dependencies(src,includes):
 found={};todo=[src]
 while todo:
  p=todo.pop()
  for n in re.findall(r'^#include\s+"([^"<>]+)"',p.read_text(),re.M):
   q=next((d/n for d in [p.parent]+includes if (d/n).is_file()),None)
   if q and q.is_relative_to(ROOT) and str(q.relative_to(ROOT)) not in found:found[str(q.relative_to(ROOT))]=digest(q);todo.append(q)
 return found

def command(cmd,log,env,timeout):
 log.with_suffix('.environment.json').write_text(json.dumps({k:v for k,v in env.items() if k.startswith(('MIGRATION_','DEEPINFER_')) or k in ['HIP_VISIBLE_DEVICES','CUDA_VISIBLE_DEVICES','FI_PROVIDER','MPIR_CVAR_CH4_NETMOD']},indent=2)+'\n')
 with log.open('w') as f:
  p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:return p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();f.write('\nTIMEOUT\n');return 124
p=argparse.ArgumentParser();p.add_argument('groups',nargs='+',choices=list(GROUPS));p.add_argument('--backend',choices=['rocm','cuda'],default='rocm');p.add_argument('--only',nargs='+',default=[]);p.add_argument('--cases',nargs='+',default=[]);p.add_argument('--timeout',type=int,default=300);a=p.parse_args();env=dict(os.environ,FI_PROVIDER='tcp',MPIR_CVAR_CH4_NETMOD='ofi');backend=a.backend;stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('batches12_15-'+backend);out.mkdir(parents=True)
if backend=='rocm':
 from device_guard import allowed_devices
 devices=allowed_devices()
else:devices=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,uuid,driver_version','--format=csv,noheader'],text=True)
identity=dict(backend=backend,devices=devices,image_id=env.get('DEEPINFER_IMAGE_ID'),rocm_release=env.get('DEEPINFER_ROCM_RELEASE'),visible_devices=env.get('HIP_VISIBLE_DEVICES',env.get('CUDA_VISIBLE_DEVICES')));(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n');results=[]
core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=pathlib.Path('/opt/rocm/core-10.1');overlay=ROOT/'build/rocm-sdk-overlay';cuda=pathlib.Path('/usr/local/cuda-13.4');mpi=ROOT/'build/mpi'
for group,profiles in GROUPS.items():
 if group not in a.groups:continue
 for source,cases in profiles.items():
  if a.only and not any(n in source for n in a.only):continue
  src=ROOT/('rocm/ported' if backend=='rocm' else 'build/cuda-observed')/source;d=out/source.replace('/','_');d.mkdir();binary=d/'sample';includes=[src.parent,ROOT/'rocm/common',mpi/'include'];libs=[mpi/'lib',mpi/'lib/mpich'];links=['mpi']
  if backend=='rocm':
   cmd=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-x','hip'];includes+=[core/'include',native/'include']+[native/'include'/n for n in ['hipblas','hipsolver','hipsparse','rocblas','rocsolver','rocsparse','hipfft','rocrand']];libs += [native/'lib',core.parent/'_rocm_sdk_libraries/lib',core/'lib'];links+=['amdhip64','hipblas','rccl','hipfft','rocrand']
  else:cmd=[str(cuda/'bin/nvcc'),'-std=c++17','-O2','-x','cu','-arch=sm_120'];includes +=[cuda/'include',pathlib.Path('/usr/include')];libs += [cuda/'lib64',pathlib.Path('/usr/lib/x86_64-linux-gnu')];links+=['cublas','nccl','cufft','curand']
  cmd += [('-Wl,' if backend=='rocm' else '-Xlinker=')+str(mpi/'lib/mpich/libfabric.so.1')]
  cmd += [str(src),'-o',str(binary),('-pthread' if backend=='rocm' else '-Xcompiler=-pthread')]+['-I'+str(q) for q in includes]+['-L'+str(q) for q in libs]+['-Wl,-rpath,'+str(q) if backend=='rocm' else '-Xlinker=-rpath='+str(q) for q in libs]+['-l'+n for n in links];sha=digest(src);dep=dependencies(src,includes);(d/'commands.json').write_text(json.dumps(dict(build=cmd,cwd=str(ROOT),cases=cases),indent=2)+'\n');rc=command(cmd,d/'build.log',env,240);runs=[]
  if digest(src)!=sha or any(digest(ROOT/n)!=h for n,h in dep.items()):raise RuntimeError('source changed during build')
  if rc==0:
   for case in cases:
    if a.cases and case not in a.cases:continue
    c=d/case;c.mkdir();runenv=dict(env,MIGRATION_CASE=case,MIGRATION_OUTPUT_DIR=str(c));run=[str(binary)]
    if model(source)=='mpi':run=[str(mpi/'bin/mpiexec'),'-n','2']+run
    (c/'commands.json').write_text(json.dumps(run,indent=2)+'\n');code=command(run,c/'run.log',runenv,a.timeout);runs.append(dict(case=case,return_code=code,evidence=str(c.relative_to(ROOT))));print(source,case,code,flush=True)
  else:print(source,'BUILD FAILED',rc,flush=True)
  r=dict(source=source,batch=group,execution_model=model(source),implementation=str(src.relative_to(ROOT)),implementation_sha256=sha,original_sha256=digest(ROOT/source),build_return_code=rc,runs=runs,evidence=str(d.relative_to(ROOT)),environment=identity,libraries=links,dependencies=dep);(d/'summary.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r)
report=ROOT/'migration/reports'/('batches12_15-'+backend+'.json');old=json.loads(report.read_text()) if report.exists() else [];merged={r['source']:r for r in old};merged.update({r['source']:r for r in results});report.write_text(json.dumps(list(merged.values()),indent=2)+'\n')
