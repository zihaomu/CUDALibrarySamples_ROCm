#!/usr/bin/env python3
"""Check other-device stream rejection without running kernels on that device."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
from image_hough_build import dependencies

def main():
    build=json.loads((ROOT/'migration/reports/image-hough-build.json').read_text())
    e=Experiment('I3','Hough-foreign-device-empty-stream-rejection','rocm-runtime',
                 sources=[__file__,ROOT/'tools/moat/image_hough_foreign_stream.cpp',*dependencies()])
    observed=capture();write(e.path/'backend.observed.json',observed)
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
    lib=ROOT/build['library'];binary=e.path/'foreign-stream'
    flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
           '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
           '--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__']
    rc=e.command([*flags,'-x','hip',str(ROOT/'tools/moat/image_hough_foreign_stream.cpp'),
                  '-L'+str(lib.parent),'-limage_hough','-Wl,-rpath,'+str(lib.parent),
                  '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],
                 'compile-foreign-stream-harness',timeout=300)
    if not rc:rc=e.command([str(binary)],'reject-foreign-stream-without-foreign-kernel',timeout=120)
    output=(e.path/'logs/0002-reject-foreign-stream-without-foreign-kernel.stdout.log').read_text().strip() if not rc else ''
    checks=[dict(check='two-visible-physical-devices-zero-and-one',passed={d['physical_id'] for d in observed['devices']}=={0,1}),
            dict(check='actual-process-exit',passed=rc==0),
            dict(check='foreign-stream-rejected-and-own-device-bytes-unchanged',passed=output.startswith('foreign-device-stream|') and output.endswith('|1') and output.split('|')[1]!='0'),
            dict(check='current-build-source-and-library',passed=all(digest(ROOT/n)==h for n,h in build['dependencies'].items()) and digest(lib)==build['library_sha256'])]
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,checks=checks,return_code=rc,output=output,build_evidence=build['evidence'])
    write(e.path/'results.json',result)
    result['evidence']=e.finish('PASSED' if status=='PASSED' else 'RUNTIME_ERROR',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-hough-foreign-stream.json',result)
    record('I3','Hough物理GPU0仅创建空外设备流，物理GPU1保持实际存储且外流必须拒绝：'+status+'。',[result['evidence']])
    print(status,output)
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
