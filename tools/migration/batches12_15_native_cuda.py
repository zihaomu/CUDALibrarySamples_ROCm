#!/usr/bin/env python3
"""Attempt original NVIDIA programs separately from compatible CUDA math baselines."""
import argparse,datetime,json,os,pathlib,subprocess,hashlib
from catalog import ROOT
from batches12_15_spec import ALL
p=argparse.ArgumentParser();p.add_argument('--only',nargs='*',default=[]);args=p.parse_args()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/'batches12_15-native-cuda';out.mkdir(parents=True);cuda=pathlib.Path('/usr/local/cuda-13.4');sdk=ROOT/'build/mathdx-sdk/nvidia/mathdx';rows=[]
for source in ALL:
 if args.only and not any(x in source for x in args.only):continue
 d=out/source.replace('/','_');d.mkdir();src=ROOT/source;binary=d/'sample';cmd=[str(cuda/'bin/nvcc'),'-std=c++17','-O2','-x','cu','-arch=sm_120',str(src),'-o',str(binary),'-Xcompiler=-pthread','-I'+str(ROOT/'build/mpi/include'),'-I'+str(ROOT/'cuSOLVER/utils'),'-I'+str(ROOT/'cuSOLVERMp'),'-I'+str(sdk/'include'),'-I'+str(sdk/'external/cutlass/include'),'-L'+str(ROOT/'build/mpi/lib'),'-Xlinker=-rpath='+str(ROOT/'build/mpi/lib'),'-lmpi','-lcublas','-lcufft','-lcusolver','-lcurand','-lnccl'];
 if source.startswith('cuSOLVER/Mg'):cmd+=['-lcusolverMg']
 if source.startswith(('NPP/','NPP+/')):cmd+=['-lnppif','-lnppist','-lnppisu','-lnppc','-lnppig','-lnppidei','-lnpps']
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1');(d/'commands.json').write_text(json.dumps(dict(build=cmd),indent=2)+'\n')
 try:
  r=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);(d/'build.log').write_text(r.stdout);rc=r.returncode
 except subprocess.TimeoutExpired:rc=124;(d/'build.log').write_text('TIMEOUT\n')
 code=None
 if rc==0:
  run=[str(binary)]
  if source.startswith(('cuSOLVERMp/','cuFFTMp/')):run=[str(ROOT/'build/mpi/bin/mpiexec'),'-n','2']+run

  cwd=src.parent
  if source.startswith(('NPP/','NPP+/')):cwd=src.parent/'build';cwd.mkdir(exist_ok=True)
  if 'templateMatching' in source:run+=['-i',str(ROOT/'build/batch15-fixtures/ncc/original/0/input.bin'),'-n','0']
  try:r=subprocess.run(run,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(d/'run.log').write_text(r.stdout);code=r.returncode
  except subprocess.TimeoutExpired:code=124;(d/'run.log').write_text('TIMEOUT\n')
 rows.append(dict(source=source,original_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),build_return_code=rc,run_return_code=code,evidence=str(d.relative_to(ROOT)),scope='Original vendor program; success does not provide shared-input equivalence without additional numerical observations.'));print(source,rc,code,flush=True)
report=ROOT/'migration/reports/batches12_15-native-cuda.json';old=json.loads(report.read_text()) if report.exists() else [];merged={r['source']:r for r in old};merged.update({r['source']:r for r in rows});report.write_text(json.dumps(list(merged.values()),indent=2)+'\n')
