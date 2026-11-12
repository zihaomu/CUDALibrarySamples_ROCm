#!/usr/bin/env python3
"""Exercise three new benchmark kernels with real device buffers and streams."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
from image_benchmark_build import dependencies
from image_benchmark_identity import inspect

def main():
    build=json.loads((ROOT/'migration/reports/image-benchmark-build.json').read_text())
    e=Experiment('I3','OpenCV-benchmark-three-kernel-device-and-stream-contracts','rocm-runtime',
       sources=[__file__,ROOT/'tools/moat/image_benchmark_runtime.cpp',
                ROOT/'tools/moat/image_benchmark_identity.py',*dependencies()],parent=build['experiment_id'])
    write(e.path/'backend.observed.json',capture())
    identity=inspect(e,build)
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';binary=e.path/'runtime'
    flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
       '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201',
       '-std=c++17','-O2','-D__HIP_PLATFORM_AMD__']
    rc=e.command([*flags,'-x','hip',str(ROOT/'tools/moat/image_benchmark_runtime.cpp'),
       '-L'+str((ROOT/build['library']).parent),'-limage_benchmark',
       '-Wl,-rpath,'+str((ROOT/build['library']).parent),'-L'+str(core/'lib'),
       '-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],'compile-runtime-contracts',timeout=300) if identity['status']=='PASSED' else 1
    rows=[]
    if rc==0:
        rc=e.command([str(binary)],'run-actual-device-contracts',timeout=120)
        commands=json.loads((e.path/'commands.json').read_text())
        logfile=next(c['stdout'] for c in commands if c['phase']=='run-actual-device-contracts')
        rows=[line.split('|') for line in (e.path/logfile).read_text().splitlines()]
    names=['normal','changed-to-zero','restored','default-stream',
           'invalid-rejected-and-output-preserved','destroyed-stream-rejected']
    checks=[dict(check='process-success',passed=rc==0),
       dict(check='actual-loaded-library-identity',passed=identity['status']=='PASSED'),
       dict(check='all-18-frozen-runtime-contracts',passed=rows==[[op,name,'1'] for op in ('gauss','resize','color') for name in names]),
       dict(check='current-library-build',passed=all(digest(ROOT/n)==h for n,h in build['dependencies'].items())),
       dict(check='real-GPU1-backend',passed={d['physical_id'] for d in json.loads((e.path/'backend.observed.json').read_text())['devices']}=={1})]
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,return_code=rc,rows=rows,checks=checks,build_evidence=build['evidence'])
    write(e.path/'runtime.json',result)
    result['evidence']=e.finish(status if status=='PASSED' else 'RUNTIME_ERROR',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-benchmark-runtime.json',result)
    record('I3','benchmark三新增GPU核18项实际设备/流/输入变化/物理长度/别名与拒绝保持检查：'+status+'。',[result['evidence']])
    print(status,[(c['check'],c['passed']) for c in checks]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
