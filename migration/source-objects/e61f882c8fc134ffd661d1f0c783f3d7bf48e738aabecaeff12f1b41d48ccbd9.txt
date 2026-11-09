#!/usr/bin/env python3
"""Build both AMD SPIR-V callback variants and retain binary observations."""
import datetime,json,os,pathlib
from catalog import ROOT
from run import command,digest
from device_guard import allowed_devices
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/'jit-fft';out.mkdir(parents=True);env=os.environ.copy();identity={'devices':allowed_devices(),'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE')};(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n');core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');libs=core.parent/'_rocm_sdk_libraries';overlay=ROOT/'build/rocm-sdk-overlay';source=ROOT/'rocm/cuFFT/lto_callback_window_1d/sample_jit.cpp';callback=source.parent/'window_callback.hip';binary=out/'sample';bc=out/'callback.spv';host=['amdclang++','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',str(source),'-I'+str(ROOT/'rocm/common'),'-I'+str(core/'include'),'-I/opt/rocm/core-10.1/include','-L/opt/rocm/core-10.1/lib','-L'+str(overlay/'lib'),'-lhipfft','-lhiprtc','-lamdhip64','-Wl,-rpath,'+str(libs/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-o',str(binary)];device=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=amdgcnspirv','--offload-device-only','-c',str(callback),'-I/opt/rocm/core-10.1/include','-o',str(bc)];(out/'commands.json').write_text(json.dumps({'host':host,'aot_bitcode':device},indent=2)+'\n');source_before=digest(source);callback_before=digest(callback);host_rc=command(host,ROOT,out/'host-build.log',env,180);bc_rc=command(device,ROOT,out/'bitcode-build.log',env,180);results=[]
if digest(source)!=source_before or digest(callback)!=callback_before:raise RuntimeError('source changed during callback build')
for mode in ['bitcode','runtime']:
 d=out/mode;d.mkdir();run=[str(binary),mode,str(bc if mode=='bitcode' else callback)];(d/'commands.json').write_text(json.dumps(run)+'\n');e=env.copy();e['MIGRATION_OUTPUT_DIR']=str(d);rc=host_rc or (bc_rc if mode=='bitcode' else 0)
 if rc==0:rc=command(run,ROOT,d/'run.log',e,180)
 r={'mode':mode,'return_code':rc,'status':'EXECUTED' if rc==0 else 'FAILED','source_sha256':digest(source),'callback_sha256':digest(callback),'evidence':str(d.relative_to(ROOT)),'environment':identity};(d/'summary.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r);print(r,flush=True)
(ROOT/'migration/reports/jit-fft.json').write_text(json.dumps(results,indent=2)+'\n')
