#!/usr/bin/env python3
"""Build the complete HIP/OpenCV C++ benchmark with four GPU operations."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

SOURCE=ROOT/'rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp'
def dependencies():
    base=ROOT/'rocm/common/image'
    return [SOURCE,ROOT/'NPP/opencvBenchmark/opencvBenchmark.cpp',
            ROOT/'NPP/opencvBenchmark/images/CircuitBoard_2048x1024_8u.raw',
            ROOT/'migration/reports/image-I3-rocm-OpenCV.json',
            ROOT/'migration/reports/image-I3-native-OpenCV.json',
            *[base/n for n in ['benchmark.h','benchmark.hip','canny.h','canny.hip',
                              'canny_stages.h','canny_stages.hip']]]

def main():
    e=Experiment('I3','OpenCV-benchmark-four-HIP-operations-and-original-C++-CLI-build',
                 'rocm-build',sources=[__file__,*dependencies()])
    write(e.path/'backend.observed.json',capture())
    dep=json.loads((ROOT/'migration/reports/image-I3-rocm-OpenCV.json').read_text())
    receipt=json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text())['receipt']
    opencv=ROOT/dep['prefix'];mismatch=[name for name,identity in receipt['files'].items()
                if not (opencv/name).is_file() or (opencv/name).stat().st_size!=identity['bytes']
                or digest(opencv/name)!=identity['sha256']]
    if dep['status']!='READY' or mismatch:
        result=dict(status='DEPENDENCY_FAILED',return_code=None,experiment_id=e.id,
                    dependency_status=dep['status'],opencv_mismatches=mismatch,
                    opencv_files_checked=len(receipt['files']))
        write(e.path/'build.json',result)
        result['evidence']=e.finish('ENV_BLOCKED',dict(status=result['status'],mismatches=mismatch))
        write(ROOT/'migration/reports/image-benchmark-build.json',result)
        record('I3','OpenCV benchmark构建依赖校验失败，200文件回执或READY状态不符；失败已封存。',[result['evidence']])
        print(result['status'],result['evidence']);return 1
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay=ROOT/'build/rocm-sdk-overlay';common=['hipcc','--rocm-path='+str(overlay),
           '--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
           '--offload-arch=gfx1201','-std=c++17','-O2','-ffp-contract=off','-D__HIP_PLATFORM_AMD__']
    lib=e.path/'libimage_benchmark.so';binary=e.path/'opencvBenchmark'
    rc=e.command([*common,'-fPIC','-x','hip','-shared',
                  *[str(ROOT/'rocm/common/image'/n) for n in ['canny_stages.hip','canny.hip','benchmark.hip']],
                  '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(lib)],
                 'compile-four-HIP-operations-and-Canny',timeout=300)
    if not rc:
        rc=e.command([*common,'-x','hip','-I'+str(opencv/'include/opencv4'),str(SOURCE),
                      '-L'+str(lib.parent),'-limage_benchmark','-Wl,-rpath,'+str(lib.parent),
                      '-L'+str(opencv/'lib'),'-Wl,-rpath,'+str(opencv/'lib'),
                      '-lopencv_imgproc','-lopencv_core','-L'+str(core/'lib'),
                      '-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],
                     'compile-complete-OpenCV-benchmark-entry',timeout=300)
    result=dict(status='BUILT' if not rc else 'BUILD_ERROR',return_code=rc,experiment_id=e.id,
                library=str(lib.relative_to(ROOT)) if lib.is_file() else None,
                library_sha256=digest(lib) if lib.is_file() else None,
                binary=str(binary.relative_to(ROOT)) if binary.is_file() else None,
                binary_sha256=digest(binary) if binary.is_file() else None,
                opencv_prefix=dep['prefix'],opencv_files_checked=len(receipt['files']),
                opencv_core_sha256=receipt['files']['lib/libopencv_core.so.4.12.0']['sha256'],
                opencv_imgproc_sha256=receipt['files']['lib/libopencv_imgproc.so.4.12.0']['sha256'],
                dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},
                build_recipe_sha256=digest(__file__))
    write(e.path/'build.json',result)
    result['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR',dict(status=result['status']))
    write(ROOT/'migration/reports/image-benchmark-build.json',result)
    record('I3','原始OpenCV benchmark四GPU算子+同版本CPU OpenCV C++完整入口构建：'+result['status']+'；尚未数值验收，不增资格。',[result['evidence']])
    print(result['status'],result['evidence'])
    return int(rc!=0)

if __name__=='__main__':raise SystemExit(main())
