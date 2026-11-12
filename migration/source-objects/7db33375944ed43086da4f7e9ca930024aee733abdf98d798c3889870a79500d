#!/usr/bin/env python3
"""Build tiled JPEG prefix probe on the pinned ROCm container."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE=ROOT/'migration/rewrite/image-jpeg-prefix-profile.json'
REPORT=ROOT/'migration/reports/image-jpeg-prefix-build.json'

def main():
    if json.loads(PROFILE.read_text())['status']!='FROZEN':
        raise ValueError('prefix contract required')
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay=ROOT/'build/rocm-sdk-overlay'
    src=ROOT/'rocm/probes/image/jpeg_parallel_prefix.hip'
    header=ROOT/'rocm/common/image/jpeg_parallel_prefix.hpp'
    e=Experiment('I5','parallel-JPEG-prefix-HIP-build','rocm-build',
                 sources=[__file__,src,header,PROFILE],
                 parent=json.loads(PROFILE.read_text())['evidence'].split('/')[-1])
    write(e.path/'backend.observed.json',capture())
    binary=e.path/'probe'
    rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
                  '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
                  '--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',
                  '-I'+str(header.parent),'-x','hip',str(src),'-o',str(binary),
                  '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'],
                 'compile-parallel-JPEG-prefix',timeout=300)
    result=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)) if rc==0 else None,
                binary_sha256=digest(binary) if rc==0 else None,return_code=rc,
                dependencies={str(p.relative_to(ROOT)):digest(p) for p in (src,header,PROFILE)},experiment_id=e.id)
    write(e.path/'build.json',result)
    result['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR',dict(status=result['status'],checks=[dict(check='hipcc-build',passed=rc==0)]))
    write(REPORT,result)
    record('I5','并行 JPEG prefix 3-kernel HIP 原型构建：'+result['status']+'；尚未进入原入口。',[result['evidence']])
    print(result['status'],result['evidence'])
    return int(rc!=0)

if __name__=='__main__':raise SystemExit(main())
