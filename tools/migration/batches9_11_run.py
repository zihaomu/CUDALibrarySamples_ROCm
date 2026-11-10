#!/usr/bin/env python3
"""Build and execute registered B9--B11 profiles, preserving immutable environment proof."""
import argparse,datetime,json,os,pathlib,re,subprocess
from catalog import ROOT
from run import command,digest
from batches9_11_spec import GROUPS

def dependencies(src,includes):
 found={};todo=[src]
 while todo:
  p=todo.pop()
  for n in re.findall(r'^#include\s+"([^"<>]+)"',p.read_text(),re.M):
   q=next((d/n for d in [p.parent]+includes if (d/n).is_file()),None)
   if q and q.is_relative_to(ROOT) and str(q.relative_to(ROOT)) not in found:found[str(q.relative_to(ROOT))]=digest(q);todo.append(q)
 return found
p=argparse.ArgumentParser();p.add_argument('groups',nargs='+',choices=list(GROUPS));p.add_argument('--backend',choices=['rocm','cuda'],default='rocm');p.add_argument('--only',nargs='+',default=[]);p.add_argument('--timeout',type=int,default=300);a=p.parse_args();env=os.environ.copy();backend=a.backend;stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('batches9_11-'+backend);out.mkdir(parents=True)
if backend=='rocm':
 from device_guard import allowed_devices
 devices=allowed_devices()
else:devices=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,uuid,driver_version','--format=csv,noheader'],text=True)
identity=dict(backend=backend,devices=devices,image_id=env.get('DEEPINFER_IMAGE_ID'),rocm_release=env.get('DEEPINFER_ROCM_RELEASE'),visible_devices=env.get('HIP_VISIBLE_DEVICES',env.get('CUDA_VISIBLE_DEVICES')));(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n');results=[]
core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=pathlib.Path('/opt/rocm/core-10.1');overlay=ROOT/'build/rocm-sdk-overlay';cpu=ROOT/'build/cpu-codecs';cuda=pathlib.Path('/usr/local/cuda-13.4')
for group,profiles in GROUPS.items():
 if group not in a.groups:continue
 for source,cases in profiles.items():
  if a.only and not any(n in source for n in a.only):continue
  root=ROOT/('rocm/ported' if backend=='rocm' else 'build/cuda-observed');src=root/source;d=out/source.replace('/','_');d.mkdir();binary=d/'sample';includes=[src.parent,ROOT/'rocm/common',cpu/'include'];libs=[cpu/'lib',cpu/'lib64'];links=[]
  if backend=='rocm':
   cmd=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-x','hip'];includes+=[core/'include',native/'include']+[native/'include'/n for n in ['hipblas','hipsolver','hipsparse','rocblas','rocsolver','rocsparse']];libs+=[ROOT/'build/hipcomp/lib',native/'lib',core.parent/'_rocm_sdk_libraries/lib',core/'lib'];includes+=[ROOT/'build/hipcomp/include'];links+=['amdhip64']
  else:cmd=[str(cuda/'bin/nvcc'),'-std=c++17','-O2','-x','cu','-arch=sm_120'];includes+=[cuda/'include',ROOT/'build/cuda-sdk/include'];libs+=[cuda/'lib64',ROOT/'build/cuda-sdk/lib']
  if group=='b9':links+=['hipcomp' if backend=='rocm' else 'nvcomp','lz4','snappy']
  elif group=='b10':links+=['rocjpeg' if backend=='rocm' else 'nvjpeg','jpeg']
  elif group=='b11':links+=['rocsolver','rocblas'] if backend=='rocm' else ['cudss']
  compile_src=src if src.suffix!='.py' else root/'nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp'
  cmd += [str(compile_src),'-o',str(binary)]+['-I'+str(q) for q in includes]+['-L'+str(q) for q in libs]+['-Wl,-rpath,'+str(q) if backend=='rocm' else '-Xlinker=-rpath='+str(q) for q in libs]+['-l'+n for n in links];sha=digest(src);(d/'commands.json').write_text(json.dumps(dict(build=cmd,cwd=str(ROOT),cases=cases,run=[str(binary)]),indent=2)+'\n');rc=command(cmd,ROOT,d/'build.log',env,240);runs=[]
  if digest(src)!=sha:raise RuntimeError('source changed during build')
  if rc==0:
   for case in cases:
    c=d/case;c.mkdir();runenv=dict(env,MIGRATION_CASE=case,MIGRATION_OUTPUT_DIR=str(c));
    if case=='cross-library-interop':runenv['MIGRATION_CODEC_FIXTURE_DIR']=str(ROOT/'build/b9-cross-fixtures'/('cuda' if backend=='rocm' else 'rocm')/source.replace('/','_'))
    code=command(([os.sys.executable,str(ROOT/'tools/migration/batch10_case.py'),'--binary',str(binary),'--source',source,'--case',case,'--output',str(c)] if group=='b10' else [str(binary)]),ROOT,c/'run.log',runenv,a.timeout);(c/'binary-outputs.json').write_text(json.dumps({p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in c.rglob('*.bin')},indent=2)+'\n');runs.append(dict(case=case,return_code=code,evidence=str(c.relative_to(ROOT))));print(source,case,code,flush=True)
  else:print(source,'BUILD FAILED',rc,flush=True)
  r=dict(source=source,batch=group,implementation=str(src.relative_to(ROOT)),implementation_sha256=sha,original_sha256=digest(ROOT/source),build_return_code=rc,runs=runs,evidence=str(d.relative_to(ROOT)),environment=identity,libraries=links,dependencies=dict(dependencies(compile_src,includes),**({str(compile_src.relative_to(ROOT)):digest(compile_src)} if compile_src!=src else {})));(d/'summary.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r)
report=ROOT/'migration/reports'/('batches9_11-'+backend+'.json');old=json.loads(report.read_text()) if report.exists() else [];merged={r['source']:r for r in old};merged.update({r['source']:r for r in results});report.write_text(json.dumps(list(merged.values()),indent=2)+'\n')
