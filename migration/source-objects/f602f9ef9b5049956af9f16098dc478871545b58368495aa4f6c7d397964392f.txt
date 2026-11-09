#!/usr/bin/env python3
"""Compile one source, execute all predeclared cases serially on the selected GPU."""
import argparse,datetime,json,os,pathlib,shutil,subprocess
from catalog import ROOT
from batch2_spec import GROUPS
from run import command,digest
p=argparse.ArgumentParser();p.add_argument('groups',nargs='+',choices=list(GROUPS));p.add_argument('--backend',choices=['rocm','cuda'],default='rocm');p.add_argument('--only',nargs='+',default=[]);p.add_argument('--fixture-root');a=p.parse_args();backend=a.backend;env=os.environ.copy();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('batch2-'+backend);out.mkdir(parents=True);cuda=pathlib.Path('/usr/local/cuda-13.4');core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');libs=core.parent/'_rocm_sdk_libraries';native=pathlib.Path('/opt/rocm/core-10.1')
if backend=='rocm':
 from device_guard import allowed_devices
 devices=allowed_devices()
else:devices=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,uuid,driver_version','--format=csv,noheader'],text=True)
identity={'backend':backend,'devices':devices,'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE'),'visible_devices':env.get('HIP_VISIBLE_DEVICES',env.get('CUDA_VISIBLE_DEVICES'))};(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n');results=[]
for group in a.groups:
 for source,cases in GROUPS[group].items():
  if a.only and not any('/'+name+'/' in source or pathlib.Path(source).stem==pathlib.Path(name).stem for name in a.only):continue
  d=out/source.replace('/','_');d.mkdir();root=ROOT/('rocm/ported' if backend=='rocm' else 'build/cuda-observed');src=root/source;family=source.split('/')[0];binary=d/'sample';names={'cuBLAS':['hipblas'],'cuSPARSE':['hipsparse'],'cuSOLVER':['hipsolver','hipblas'],'cuTENSOR':['hiptensor']}[family];includes=[src.parent,root/family/'utils',ROOT/'rocm/common'];library_roots=[ROOT/'build/project-sdk/lib',ROOT/'build/rocm-sdk-overlay/lib',libs/'lib',core/'lib']
  if backend=='rocm':
   cmd=['amdclang++','-std=c++17','-O2','-x','c++','-D__HIP_PLATFORM_AMD__'];includes += [core/'include',native/'include',ROOT/'build/project-sdk/include']+[native/'include'/name for name in ['hipblas','hipsparse','hipsolver']];links=['-L'+str(p) for p in library_roots]+['-Wl,-rpath,'+str(p) for p in library_roots]+['-l'+s for s in names+['amdhip64']]
   if '/rotmg/' in source:
    overlay=ROOT/'build/rocm-sdk-overlay';cmd=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-x','hip'];links.insert(0,str(ROOT/'rocm/common/rotmg_scale_fix.hip'))
  else:
   cmd=[str(cuda/'bin/nvcc'),'-std=c++17','-O2','-x','cu','-arch=sm_120'];includes += [cuda/'include',ROOT/'build/cuda-sdk/include'];links=['-L'+str(cuda/'lib64'),'-Xlinker=-rpath='+str(cuda/'lib64'),'-L'+str(ROOT/'build/cuda-sdk/lib'),'-Xlinker=-rpath='+str(ROOT/'build/cuda-sdk/lib')]+['-l'+name for name in {'cuBLAS':['cublas'],'cuSPARSE':['cusparse'],'cuSOLVER':['cusolver','cublas'],'cuTENSOR':['cutensor']}[family]]
  cmd += [str(src),'-o',str(binary)]+['-I'+str(p) for p in includes]+links;sha=digest(src);(d/'commands.json').write_text(json.dumps({'build':cmd,'cwd':str(ROOT),'cases':cases,'run':[str(binary)]},indent=2)+'\n');rc=command(cmd,ROOT,d/'build.log',env,180);runs=[]
  if digest(src)!=sha:raise RuntimeError('Source changed during build: '+str(src))
  if rc==0:
   for case in cases:
    c=d/case;c.mkdir();runenv=env.copy();runenv.update(MIGRATION_CASE=case,MIGRATION_OUTPUT_DIR=str(c))
    if family=='cuTENSOR':runenv['MIGRATION_FIXTURE_SEED']='20261109'
    if a.fixture_root and family=='cuTENSOR':runenv['MIGRATION_INPUT_FIXTURE_DIR']=str(ROOT/a.fixture_root/source.replace('/','_')/case)
    code=command([str(binary)],ROOT,c/'run.log',runenv,180);runs.append({'case':case,'return_code':code,'evidence':str(c.relative_to(ROOT))});print(source,case,code,flush=True)
  r={'sample_id':str(pathlib.PurePosixPath(source).parent)+'::'+pathlib.PurePosixPath(source).name,'source':source,'implementation':str(src.relative_to(ROOT)),'implementation_sha256':sha,'original_sha256':digest(ROOT/source),'build_return_code':rc,'runs':runs,'evidence':str(d.relative_to(ROOT)),'environment':identity,'libraries':names if backend=='rocm' else None};(d/'summary.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r)
  if rc:print(source,'BUILD FAILED',rc,flush=True)
report=ROOT/'migration/reports'/('batch2-'+backend+'.json');old=json.loads(report.read_text()) if report.exists() else [];merged={r['source']:r for r in old};merged.update({r['source']:r for r in results});report.write_text(json.dumps(list(merged.values()),indent=2)+'\n');print('Report',report,flush=True)
