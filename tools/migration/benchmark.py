#!/usr/bin/env python3
"""Run explicitly scoped GEMM performance profiles after sampled CPU checks."""
import argparse,datetime,json,os,pathlib,subprocess
from catalog import ROOT
from run import command,digest
p=argparse.ArgumentParser();p.add_argument('--backend',choices=['rocm','cuda'],default='rocm');a=p.parse_args();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('performance-'+a.backend);out.mkdir(parents=True)
env=os.environ.copy();source=ROOT/'rocm/bench/gemm.cpp';common=ROOT/'rocm/common'
if a.backend=='rocm':
 from device_guard import allowed_devices
 devices=allowed_devices(require_idle=True);core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');libs=core.parent/'_rocm_sdk_libraries';cmd=['amdclang++','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(core/'include'),'-I/opt/rocm/core-10.1/include',str(next((libs/'lib').glob('libhipblas.so*'))),str(next((core/'lib').glob('libamdhip64.so*'))),'-Wl,-rpath,'+str(libs/'lib'),'-Wl,-rpath,'+str(core/'lib')]
else:
 devices=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,uuid,driver_version','--format=csv,noheader'],text=True);source=ROOT/'build/cuda-validation/bench/gemm.cpp';common=ROOT/'build/cuda-validation/common';cmd=['g++','-std=c++17','-O2','-I/usr/local/cuda-13.4/include','-L/usr/local/cuda-13.4/lib64','-Wl,-rpath,/usr/local/cuda-13.4/lib64','-lcublas','-lcudart']
binary=out/'gemm';cmd[1:1]=[str(source),'-I'+str(common),'-o',str(binary)]
(out/'commands.json').write_text(json.dumps({'build':cmd,'run':[str(binary)]},indent=2)+'\n');identity={'devices':devices,'rocm_release':env.get('DEEPINFER_ROCM_RELEASE'),'image_id':env.get('DEEPINFER_IMAGE_ID'),'source_sha256':digest(source),'common_header_sha256':digest(common/'check.hpp'),'visible_devices':env.get('HIP_VISIBLE_DEVICES',env.get('CUDA_VISIBLE_DEVICES')),'precision':'AMD rocBLAS default FP32/FP64; CUDA pedantic FP32/FP64','timing_scope':'GPU event around GEMM; allocation, transfers and initialization excluded; default library workspace','power_frequency':'not controlled; device metric snapshots retained separately'};(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n')
rc=command(cmd,ROOT,out/'build.log',env,180)
if rc==0:rc=command([str(binary)],ROOT,out/'run.log',env,600)
results=[]
if rc==0:results=[json.loads(line) for line in (out/'run.log').read_text().splitlines() if line.startswith('{')]
report={'status':'PASSED' if rc==0 and len(results)==6 else 'FAILED','return_code':rc,'evidence':str(out.relative_to(ROOT)),'environment':identity,'profiles':results};(ROOT/f'migration/reports/benchmark-{a.backend}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(rc)
