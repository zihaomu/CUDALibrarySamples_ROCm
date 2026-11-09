#!/usr/bin/env python3
"""Compile and validate each implemented sample, retaining per-attempt evidence.
No performance claims are made by this correctness runner.
"""
import argparse, datetime, fcntl, hashlib, json, os, pathlib, platform, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evidence_directory(value):
 """Prefer local full outputs when a report points to the small archived evidence."""
 path=pathlib.Path(value);prefix='migration/reports/evidence/'
 if str(path).startswith(prefix):
  local=ROOT/'artifacts'/str(path)[len(prefix):]
  if local.exists():return local
 return ROOT/path
def command(args,cwd,log,env=None,timeout=180):
 if env is None:env=os.environ.copy()
 if env.get('DEEPINFER_ROCM_RELEASE')=='10.1.0':
  cache=ROOT/'build/cache/rocm10.1-gfx1201';cache.mkdir(parents=True,exist_ok=True)
  for key,sub in [('TRITON_CACHE_DIR','triton'),('TORCH_EXTENSIONS_DIR','torch'),('AMD_COMGR_CACHE_DIR','comgr')]:
   path=cache/sub;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
  env['ROCFFT_RTC_CACHE_PATH']=str(cache/'rocfft.sqlite')
 elif env.get('CUDA_VISIBLE_DEVICES'):
  path=ROOT/'build/cache/cuda13.4-sm120';path.mkdir(parents=True,exist_ok=True);env['CUDA_CACHE_PATH']=str(path)
 log.with_suffix('.environment.json').write_text(json.dumps({k:env[k] for k in ['DEEPINFER_IMAGE_ID','DEEPINFER_ROCM_RELEASE','HIP_VISIBLE_DEVICES','CUDA_VISIBLE_DEVICES','MIGRATION_FIXTURE','MIGRATION_CASE','MIGRATION_INPUT_FIXTURE','MIGRATION_INPUT_FIXTURE_DIR','MIGRATION_OUTPUT_DIR','AMD_COMGR_CACHE_DIR','ROCFFT_RTC_CACHE_PATH','CUDA_CACHE_PATH'] if k in env},indent=2)+'\n')
 try:
  r=subprocess.run(args,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);log.write_text(r.stdout);return r.returncode
 except subprocess.TimeoutExpired as e:
  log.write_text((e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else (e.stdout or '')+'\nTIMEOUT');return 124

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['rocm','cuda'],default='rocm');ap.add_argument('--filter',default='');args=ap.parse_args()
 catalog=json.loads((ROOT/'migration/samples.yaml').read_text());specs=json.loads((ROOT/'migration/m1.json').read_text())
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/args.backend;out.mkdir(parents=True)
 env=os.environ.copy();env['MIGRATION_FIXTURE']=str(ROOT/'tests/fixtures/m1-input.f64');environment={'backend':args.backend,'timestamp':stamp,'platform':platform.platform(),'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE'),'visible_devices':env.get('HIP_VISIBLE_DEVICES',env.get('CUDA_VISIBLE_DEVICES')),'upstream_commit':catalog['upstream_commit'],'fixture_sha256':digest(pathlib.Path(env['MIGRATION_FIXTURE']))}
 if args.backend=='rocm':
  sdk=pathlib.Path('/opt/venv/lib/python3.13/site-packages');core=sdk/'_rocm_sdk_core';libs=sdk/'_rocm_sdk_libraries';compiler=shutil.which('amdclang++');include=[core/'include',libs/'include',pathlib.Path('/opt/rocm/core-10.1/include')];libdir=libs/'lib';runtime='amdhip64';common=ROOT/'rocm/common';srcroot=ROOT/'rocm'
  if environment['rocm_release']!='10.1.0':raise RuntimeError('ROCm 10.1.0 foundation is required')
 else:
  core=pathlib.Path('/usr/local/cuda-13.4');libs=core;compiler='/usr/bin/g++';include=[core/'include'];libdir=core/'lib64';runtime='cudart';common=ROOT/'build/cuda-validation/common';srcroot=ROOT/'build/cuda-validation'
 if not compiler:raise RuntimeError('compiler missing')
 if args.backend=='rocm':
  from device_guard import allowed_devices
  environment['devices']=allowed_devices()
 environment['headers']={str(p):digest(p) for directory in include for p in directory.glob('*/*version*.h')}
 environment['linked_libraries']={}
 for spec in specs:
  if args.backend=='rocm':
   for name in spec['libraries']:
    paths=sorted(libdir.glob('lib'+name+'.so*'))
    if paths: environment['linked_libraries'][str(paths[0])]=digest(paths[0])
 environment['compiler']=compiler;environment['compiler_version']=subprocess.check_output([compiler,'--version'],text=True)
 q=subprocess.run(['nvidia-smi','--query-gpu=index,name,uuid,driver_version','--format=csv,noheader'],capture_output=True,text=True) if args.backend=='cuda' else subprocess.run(['cat','/sys/module/amdgpu/version'],capture_output=True,text=True)
 environment['driver_identity']=q.stdout or q.stderr
 (out/'environment.json').write_text(json.dumps(environment,indent=2)+'\n');results=[]
 for spec in specs:
  if args.filter and args.filter not in spec['path']:continue
  sample=next(s for s in catalog['samples'] if s['source']==spec['upstream_source']);d=out/spec['name'];d.mkdir()
  source=srcroot/spec['path']/'sample.cpp';binary=d/spec['name'];links=spec['libraries'] if args.backend=='rocm' else spec['cuda_libraries']
  build=[compiler,'-std=c++17','-O2',str(source),'-o',str(binary),'-I'+str(common)]+['-I'+str(p) for p in include]+['-L'+str(libdir),'-Wl,-rpath,'+str(libdir)]+['-l'+s for s in links]+['-l'+runtime]
  if args.backend=='rocm':
   build=[a for a in build if not a.startswith('-l')]
   for name in links+[runtime]:
    folder=core/'lib' if name==runtime else libdir
    matches=sorted(folder.glob('lib'+name+'.so*'))
    if not matches:raise RuntimeError('missing shared object '+name)
    build.append(str(matches[0]))
   build+=['-D__HIP_PLATFORM_AMD__','-Wl,-rpath,'+str(core/'lib')]
  if spec.get('gpu_scaling'):
   obj=d/'scaling.o'
   if args.backend=='rocm':
    overlay=ROOT/'build/rocm-sdk-overlay'
    scale_cmd=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-c',str(ROOT/'rocm/common/scaling.hip'),'-o',str(obj)]
   else:
    scale_cmd=[str(core/'bin/nvcc'),'-arch=sm_120','-c',str(ROOT/'build/cuda-validation/common/scaling.cu'),'-o',str(obj)]
   scale_rc=command(scale_cmd,ROOT,d/'scaling-build.log',env)
   (d/'scaling-commands.json').write_text(json.dumps(scale_cmd,indent=2)+'\n')
   if scale_rc:raise RuntimeError('GPU scaling module compile failed: '+str(d/'scaling-build.log'))
   build.append(str(obj))
  commands={'cwd':str(ROOT),'build':build,'run':[str(binary)],'MIGRATION_FIXTURE':env['MIGRATION_FIXTURE']};(d/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
  ids=[];reason=None;status='FAILED';level='L1'
  rc=command(build,ROOT,d/'build.log',env)
  if rc:reason='BUILD_ERROR'
  else:
   level='L2';rc=command([str(binary)],ROOT,d/'run.log',env)
   if rc:reason='TIMEOUT' if rc==124 else 'RUNTIME_OR_NUMERICAL_ERROR'
   else:
    level='L3'
    try:
     rows=[json.loads(line) for line in (d/'run.log').read_text().splitlines() if line.startswith('{')];ids=[r['case'] for r in rows if r.get('passed') is True]
     if len(ids)!=len(set(ids)) or set(ids)!=set(spec['required_cases']):raise ValueError('required case set mismatch')
     status='PASSED';level='L4'
    except (ValueError,KeyError) as e:reason='VALIDATION_RECORD_ERROR'
  evidence=str(d.relative_to(ROOT));summary={'sample_id':sample['id'],'status':status,'level':level,'reason_code':reason,'return_code':rc,'passed_cases':ids,'required_cases':spec['required_cases'],'implementation_sha256':digest(source),'common_sha256':digest(common/'check.hpp'),'environment':str(out.relative_to(ROOT)/'environment.json'),'fixture_sha256':environment['fixture_sha256'],'scope':'M1 extended validation driver; original CUDA executable recorded separately','evidence':evidence}
  (d/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');results.append(summary)
  # Only AMD results determine migration status. Original sample parity remains explicit.
  if args.backend=='rocm':
   sample['selection_reason']=spec.get('selection_reason','采用 AMD 兼容接口保留原库调用语义；已在当前环境验证所列 case，尚未比较性能')
   sample.update(actual_library=spec['display_library'],backend_library=spec['backend_library'],implementation=str(source.relative_to(ROOT)),level=level,status=('PASSED' if spec.get('original_profile_covered') else 'PARTIAL') if status=='PASSED' else 'FAILED',reason_code=(None if spec.get('original_profile_covered') else 'ORIGINAL_PROFILE_PENDING') if status=='PASSED' else reason,reason=(f'使用 {spec["display_library"]}（{spec["backend_library"]}）成功实现 {spec["upstream_source"]} 的原始 profile 及 {len(ids)} 个数值用例' if spec.get('original_profile_covered') else '扩展验证用例通过；原始教学输入/全部行为对齐仍待完成') if status=='PASSED' else '详见 build.log/run.log；尚未将错误归因于库能力',required_cases=spec['required_cases'],passed_cases=ids)
   with (ROOT/'migration/.state.lock').open('w') as state_lock:
    fcntl.flock(state_lock,fcntl.LOCK_EX);live=json.loads((ROOT/'migration/samples.yaml').read_text());current=next(v for v in live['samples'] if v['id']==sample['id'])
    for key in ['actual_library','backend_library','implementation','level','status','reason_code','reason','required_cases','passed_cases','selection_reason']:current[key]=sample[key]
    current['attempts'].append(summary);current['evidence'].append(evidence);(ROOT/'migration/samples.yaml').write_text(json.dumps(live,indent=2,ensure_ascii=False)+'\n')
  print(spec['name'],status,level,reason or '',flush=True)
 (out/'summary.json').write_text(json.dumps(results,indent=2)+'\n')

 report=ROOT/'migration/reports'/('m1-'+args.backend+'-latest.json');report.parent.mkdir(parents=True,exist_ok=True)
 prior=json.loads(report.read_text()).get('results',[]) if report.exists() else []
 combined={v['sample_id']:v for v in prior};combined.update({v['sample_id']:v for v in results})
 report.write_text(json.dumps({'run_id':stamp,'environment':environment,'results':list(combined.values()),'executed_sample_ids':[v['sample_id'] for v in results]},indent=2)+'\n')
 print('Evidence:',out,flush=True)
 return int(not results or any(r['status']!='PASSED' for r in results))
if __name__=='__main__':sys.exit(main())
