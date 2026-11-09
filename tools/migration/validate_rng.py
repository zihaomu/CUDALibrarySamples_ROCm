#!/usr/bin/env python3
"""Original RNG parameters, host/device reproducibility and analytic moments."""
import argparse,datetime,fcntl,json,os,pathlib,re
from catalog import ROOT
from device_guard import allowed_devices
from run import command,digest
from progress import checkpoint
parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['rocm','cuda'],default='rocm');parser.add_argument('--filter',default='');parser.add_argument('--include-mt',action='store_true');parser.add_argument('--timeout',type=int,default=60);args=parser.parse_args()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'artifacts'/stamp/('rng-validation' if args.backend=='rocm' else 'rng-cuda-validation');out.mkdir(parents=True);env=os.environ.copy();identity={'backend':args.backend,'devices':allowed_devices() if args.backend=='rocm' else env.get('CUDA_VISIBLE_DEVICES'),'image_id':env.get('DEEPINFER_IMAGE_ID'),'rocm_release':env.get('DEEPINFER_ROCM_RELEASE')};(out/'environment.json').write_text(json.dumps(identity,indent=2)+'\n');cat=json.loads((ROOT/'migration/samples.yaml').read_text());core=pathlib.Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');libs=core.parent/'_rocm_sdk_libraries';results=[]
for s in cat['samples']:
 if s['family']!='cuRAND' or args.filter not in s['source'] or ('mt19937/' in s['source'] and not args.include_mt):continue
 src=ROOT/'rocm/ported'/s['source'];d=out/s['source'].replace('/','_');d.mkdir();text=src.read_text();original_n=int(re.search(r'const int n = (\d+);',text)[1]);text='#include "rng_observe.hpp"\n'+re.sub(r'const int n = \d+;',f'const int n = argc>1?std::atoi(argv[1]):{original_n};',text);text=text.replace('print_vector(h_data);','rng_observer::emit(h_data);');port=d/'sample.cpp';
 if args.backend=='cuda':
  from prepare_cuda import convert
  text=convert(text)
 port.write_text(text);binary=d/'sample';cmd=(['amdclang++','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',str(port),'-I'+str(ROOT/'rocm/common'),'-I'+str(ROOT/'rocm/ported/cuRAND/utils'),'-I'+str(core/'include'),'-I/opt/rocm/core-10.1/include',str(next((libs/'lib').glob('libhiprand.so*'))),str(next((core/'lib').glob('libamdhip64.so*'))),'-Wl,-rpath,'+str(libs/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-o',str(binary)] if args.backend=='rocm' else []);
 if args.backend=='cuda':cmd=['g++','-std=c++17','-O2',str(port),'-I'+str(ROOT/'rocm/common'),'-I'+str(ROOT/'build/cuda-rng-utils'),'-I/usr/local/cuda-13.4/include','-L/usr/local/cuda-13.4/lib64','-Wl,-rpath,/usr/local/cuda-13.4/lib64','-lcurand','-lcudart','-o',str(binary)]
 (d/'commands.json').write_text(json.dumps({'build':cmd,'runs':[[str(binary),str(n)] for n in [original_n,original_n,98304]]},indent=2)+'\n');rc=command(cmd,ROOT,d/'build.log',env,180);cases=[];observations=[]
 if rc==0:
  for i,n in enumerate([original_n,original_n,98304]):
   log=d/f'run-{i}.log';code=command([str(binary),str(n)],ROOT,log,env,args.timeout);values=[json.loads(l) for l in log.read_text().splitlines() if l.startswith('{"rng_observation"')];observations.append(values);cases.append({'case':f'host-and-device-n{n}-run{i}','passed':code==0 and len(values)==2 and all(v['finite'] and v['n']==n for v in values),'return_code':code})
  cases.append({'case':'same-seed-or-offset-repeat-host-and-device','passed':len(observations[0])==2 and len(observations[1])==2 and all(a['hash']==b['hash'] for a,b in zip(observations[0],observations[1]))})
  distribution=s['source'].rsplit('_',2)[-2];params={k:float(v.rstrip('fF')) for k,v in re.findall(r'const (?:data_type|float|double) (mean|stddev|lambda)\s*=\s*([\d.]+[fF]?);',text)}
  for i,v in enumerate(observations[2]):
   if distribution=='uniform':good=v['min']>0 and v['max']<=1 and abs(v['mean']-.5)<.02 and abs(v['variance']-1/12)<.01
   elif distribution in {'normal','lognormal'}:
    mu=params['mean'];sigma=params['stddev'];m=v['log_mean'] if distribution=='lognormal' else v['mean'];var=v['log_variance'] if distribution=='lognormal' else v['variance'];good=(v['positive'] if distribution=='lognormal' else True) and abs(m-mu)<.04*sigma and abs(var-sigma*sigma)<.08*sigma*sigma
   else:
    lam=params['lambda'];good=v['integer'] and v['min']>=0 and abs(v['mean']-lam)<.04*max(1,lam**.5) and abs(v['variance']-lam)<.1*max(1,lam)
   cases.append({'case':f'analytic-{distribution}-moments-'+('host' if i==0 else 'device'),'passed':good,'observed':v,'parameters':params})
 r={'sample_id':s['id'],'status':'PASSED' if rc==0 and len(cases)==6 and all(c['passed'] for c in cases) else 'FAILED','build_return_code':rc,'cases':cases,'evidence':str(d.relative_to(ROOT)),'source_sha256':s['source_sha256'],'original_port_sha256':digest(src),'validation_source_sha256':digest(port),'environment':identity,'oracle':'Analytic distribution moments; same seed/offset repeat separately for host and GPU, original per-source n and n=98304. Sequences are library-specific.'};(d/'summary.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r);print(s['source'],r['status'],flush=True)
 if args.backend!='rocm':continue
 with (ROOT/'migration/.state.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';current=json.loads(p.read_text());row=next(v for v in current['samples'] if v['id']==s['id']);row['rng_validation']=r;row['evidence'].append(r['evidence'])
  if r['status']=='PASSED' and not row.get('passed_cases'):row.update(status='PASSED',level='L4',actual_library='hipRAND',backend_library='rocRAND',reason_code='VALIDATED_ORIGINAL_PROFILE',reason='hipRAND/rocRAND 原始源码 n 的 host/device 路径、同 seed/offset 可复现性与 n=98304 的解析分布矩验证通过；不要求 cuRAND/rocRAND 序列逐值相同。',required_cases=[v['case'] for v in cases],passed_cases=[v['case'] for v in cases])
  p.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n')
report=ROOT/'migration/reports'/('rng-original-validation.json' if args.backend=='rocm' else 'rng-cuda-validation.json');old=json.loads(report.read_text()) if report.exists() else [];merged={v['sample_id']:v for v in old};merged.update({v['sample_id']:v for v in results});report.write_text(json.dumps(list(merged.values()),indent=2)+'\n');checkpoint('S27 RNG 原始 profile 解析分布验收',f'{len(results)} 项中 {sum(r["status"]=="PASSED" for r in results)} 通过；初始化超时及本轮结果均保留，未跳换 generator。','处理数值差异与 CUDA 统计对照')
