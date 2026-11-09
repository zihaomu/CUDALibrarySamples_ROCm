#!/usr/bin/env python3
"""Original SHA2/SHA3 profiles plus independent hashlib known-answer cases."""
import argparse,datetime,fcntl,hashlib,json,os,pathlib,re
from catalog import ROOT
from run import command,digest
p=argparse.ArgumentParser();p.add_argument('--backend',choices=['rocm','cuda'],default='rocm');args=p.parse_args();env=os.environ.copy();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('hash-'+args.backend);out.mkdir(parents=True);identity={'backend':args.backend,'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE')}
if args.backend=='rocm':
 from device_guard import allowed_devices
 identity['devices']=allowed_devices()
(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n');results=[]
for name in ['sha2','sha3']:
 source=ROOT/'rocm/cuPQC'/f'{name}_256.hip';d=out/name;d.mkdir();binary=d/'sample';core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
 if args.backend=='rocm':cmd=['hipcc','-O2','-std=c++17','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201',str(source),'-I'+str(ROOT/'rocm/common'),'-Wl,-rpath,'+str(core/'lib'),'-o',str(binary)]
 else:
  text=source.read_text().replace('hipGetLastError','cudaGetLastError').replace('hipDeviceSynchronize','cudaDeviceSynchronize').replace('__shfl(','__shfl_sync(0xffffffff,');source=d/'sample.cu';source.write_text(text);cmd=['/usr/local/cuda-13.4/bin/nvcc','-O2','-std=c++17','-arch=sm_120',str(source),'-I'+str(ROOT/'build/cuda-validation/common'),'-o',str(binary)]
 (d/'commands.json').write_text(json.dumps({'build':cmd,'run_template':[str(binary),'<input.bin>']},indent=2)+'\n');rc=command(cmd,ROOT,d/'build.log',env,180);cases=[]
 if rc==0:
  inputs=[('original',b'The quick brown fox jumps over the lazy dog')]+[(f'length-{n}',bytes((i*17+3)%256 for i in range(n))) for n in [0,1,55,56,63,64,65,135,136,137,271,272,1000]]
  for cid,data in inputs:
   f=d/(cid+'.bin');f.write_bytes(data);log=d/(cid+'.log');code=command([str(binary),str(f)],ROOT,log,env,30);actual=log.read_text().strip();expected=(hashlib.sha256 if name=='sha2' else hashlib.sha3_256)(data).hexdigest();passed=code==0 and actual==expected;cases.append({'case':cid,'passed':passed,'input_sha256':hashlib.sha256(data).hexdigest(),'actual':actual,'expected':expected,'return_code':code})
 r={'sample_id':f'cuPQC::example_{name}.cu','name':name,'backend':args.backend,'status':'PASSED' if rc==0 and all(c['passed'] for c in cases) else 'FAILED','build_return_code':rc,'cases':cases,'oracle':'Python hashlib/OpenSSL, exact 256-bit digest','implementation':str((ROOT/'rocm/cuPQC'/f'{name}_256.hip').relative_to(ROOT)),'implementation_sha256':digest(ROOT/'rocm/cuPQC'/f'{name}_256.hip'),'evidence':str(d.relative_to(ROOT)),'environment':identity,'scope':'SHA2 one thread; SHA3 cooperative 32-lane wave, one GPU kernel; original input plus padding/rate boundaries'};(d/'summary.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r);print(name,r['status'],sum(c['passed'] for c in cases),'/',len(cases),flush=True)
(ROOT/f'migration/reports/hash-{args.backend}.json').write_text(json.dumps(results,indent=2)+'\n')
if args.backend=='rocm':
 with (ROOT/'migration/.state.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
  for r in results:
   s=next(s for s in cat['samples'] if s['source']==f'cuPQC/example_{r["name"]}.cu');s.update(status=r['status'],level='L4' if r['status']=='PASSED' else 'L1',actual_library='HIP runtime + custom device SHA implementation',backend_library='HIP/gfx1201',implementation=r['implementation'],required_cases=[x['case'] for x in r['cases']],passed_cases=[x['case'] for x in r['cases'] if x['passed']],reason_code='VALIDATED_ORIGINAL_PROFILE' if r['status']=='PASSED' else 'NUMERICAL_OR_BUILD_FAILURE',reason=r['scope']+'；14 个输入与独立 hashlib 精确一致' if r['status']=='PASSED' else '实际编译/数值失败，见 hash report');s['attempts'].append(r);s['evidence'].append(r['evidence'])
  p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
