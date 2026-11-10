#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from experiment import Experiment,ROOT,write,digest
from snapshot import capture

p=argparse.ArgumentParser();p.add_argument('--only',nargs='*',default=[]);a=p.parse_args()
core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=Path('/opt/rocm/core-10.1')
includes=[ROOT/'rocm/common',ROOT/'rocm/backends/blas',ROOT/'rocm/device/solver',core/'include',native/'include']
libraries=[native/'lib',core.parent/'_rocm_sdk_libraries/lib',core/'lib']
profiles=json.loads((ROOT/'migration/rewrite/first-eight.json').read_text())['profiles']
results=json.loads((ROOT/'migration/reports/rewrite-first-builds.json').read_text()) if (ROOT/'migration/reports/rewrite-first-builds.json').exists() else {}
observed=capture()
for profile in profiles:
 if a.only and profile['kind'] not in a.only:continue
 source=ROOT/'rocm/ported'/profile['source'];dependencies=[source,Path(__file__),ROOT/'tools/moat/experiment.py']
 dependencies+=list((ROOT/'rocm/common').glob('rewrite*.hpp'))+list((ROOT/'rocm/backends/blas').glob('*.hpp'))+list((ROOT/'rocm/device/solver').glob('*.hpp'))
 e=Experiment(profile['batch'],profile['sample_id'],'rocm-build',sources=dependencies)
 write(e.path/'backend.observed.json',observed)
 binary=e.path/'sample'
 cmd=['hipcc','--rocm-path='+str(ROOT/'build/rocm-sdk-overlay'),'--hip-path='+str(ROOT/'build/rocm-sdk-overlay'),
      '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201',
      '-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-x','hip',str(source),'-o',str(binary)]
 cmd+=['-I'+str(x) for x in includes]+['-L'+str(x) for x in libraries]+['-Wl,-rpath,'+str(x) for x in libraries]+['-lhipblas','-lamdhip64']
 rc=e.command(cmd,'build',timeout=240)
 if rc==0:e.command(['ldd',str(binary)],'runtime-links',timeout=30)
 record=dict(source=profile['source'],implementation=str(source.relative_to(ROOT)),implementation_sha256=digest(source),
             dependencies={str(x.relative_to(ROOT)):digest(x) for x in dependencies},
             status='BUILT' if rc==0 else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)) if rc==0 else None,
             binary_sha256=digest(binary) if rc==0 else None,experiment_id=e.id)
 record['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR',reason=None if rc==0 else f'build exit {rc}')
 results[profile['kind']]=record;write(ROOT/'migration/reports/rewrite-first-builds.json',results)
 print(profile['kind'],record['status'],record['evidence'],flush=True)
