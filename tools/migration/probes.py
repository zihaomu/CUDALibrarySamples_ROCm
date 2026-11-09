#!/usr/bin/env python3
"""Qualify specific AMD ecosystem routes. A probe is not a whole sample port."""
import argparse,datetime,json,os,pathlib
from catalog import ROOT
from run import command,digest
from device_guard import allowed_devices
p=argparse.ArgumentParser();p.add_argument('names',nargs='+');a=p.parse_args()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/'native-probes';out.mkdir(parents=True);env=os.environ.copy();devices=allowed_devices();core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');libs=core.parent/'_rocm_sdk_libraries';native=pathlib.Path('/opt/rocm/core-10.1');identity={'devices':devices,'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE')};(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n')
choices={'hipcomp_lz4':['hipcomp'],'rpp_resize':['rpp'],'rocjpeg_decode':['rocjpeg'],'rccl_gemm':['rccl','hipblas'],'hiptensor_contract':['hiptensor'],'hiptensor_contract_fp16_compute':['hiptensor'],'tensor_rocblas':['rocblas'],'distributed_fft':['hipfft','rccl'],'rocsolver_sparse_chol':['rocsolver','rocblas']};results=[]
for name in a.names:
 d=out/name;d.mkdir();src=ROOT/'rocm/cuDSS/simple/sample.cpp' if name=='rocsolver_sparse_chol' else ROOT/'rocm/probes'/(name+('.hip' if name in {'tensor_rocblas','distributed_fft'} else '.cpp'));binary=d/'probe';roots=[ROOT/'build/hipcomp/lib',ROOT/'build/project-sdk/lib',libs/'lib',core/'lib',native/'lib'];cmd=['amdclang++','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',str(src),'-o',str(binary)]+['-I'+str(x) for x in [ROOT/'rocm/common',core/'include',native/'include',ROOT/'build/deps/hipCOMP-core/include',ROOT/'build/project-sdk/include']]+['-L'+str(x) for x in roots]+['-Wl,-rpath,'+str(x) for x in roots]+['-l'+x for x in choices[name]+['amdhip64']];
 if src.suffix=='.hip':
  cmd[0]='hipcc';overlay=ROOT/'build/rocm-sdk-overlay';cmd[1:1]=['--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201']
 run=[str(binary)]+([str(ROOT/'nvJPEG/nvJPEG-Decoder/input_images/cat_baseline.jpg')] if name=='rocjpeg_decode' else []);(d/'commands.json').write_text(json.dumps({'cwd':str(ROOT),'build':cmd,'run':run},indent=2)+'\n');rc=command(cmd,ROOT,d/'build.log',env,180);stage='build'
 if rc==0:
  stage='run';run_env=env.copy();run_env['MIGRATION_OUTPUT_DIR']=str(d);rc=command(run,ROOT,d/'run.log',run_env,120)
 result={'name':name,'status':'PASSED' if rc==0 else 'FAILED','return_code':rc,'stage':stage,'libraries':choices[name],'source_sha256':digest(src),'evidence':str(d.relative_to(ROOT)),'environment':identity};(d/'summary.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(json.dumps(result),flush=True)
p=ROOT/'migration/reports/native-probes.json';old=json.loads(p.read_text()) if p.exists() else {};old.update({r['name']:r for r in results});p.write_text(json.dumps(old,indent=2)+'\n')
