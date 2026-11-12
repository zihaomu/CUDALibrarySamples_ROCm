#!/usr/bin/env python3
"""Build the complete Hough C++ sample against shared HIP Canny and Hough."""
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

SOURCE=ROOT/'rocm/ported/NPP/houghLines/houghLines.cpp'
def dependencies():
    base=ROOT/'rocm/common/image'
    return [SOURCE,ROOT/'migration/rewrite/image-hough-profile.json',
            *[base/n for n in ['canny.h','canny.hip','canny_stages.h','canny_stages.hip','hough.h','hough.hip','hough_trig.h']]]

def main():
    e=Experiment('I3','Hough-Canny-GPU-and-complete-C++-build','rocm-build',sources=[__file__,*dependencies()])
    write(e.path/'backend.observed.json',capture())
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay=ROOT/'build/rocm-sdk-overlay'
    common=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
            '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
            '--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__']
    lib=e.path/'libimage_hough.so';binary=e.path/'houghLines'
    rc=e.command([*common,'-fPIC','-x','hip','-shared',
            *[str(ROOT/'rocm/common/image'/n) for n in ['canny_stages.hip','canny.hip','hough.hip']],
            '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(lib)],
            'compile-shared-Canny-Hough-GPU-library',timeout=300)
    if not rc:
        rc=e.command([*common,'-x','hip',str(SOURCE),'-L'+str(lib.parent),'-limage_hough',
                      '-Wl,-rpath,'+str(lib.parent),'-L'+str(core/'lib'),
                      '-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],
                      'compile-complete-Hough-C++-entry',timeout=300)
    result=dict(status='BUILT' if not rc else 'BUILD_ERROR',return_code=rc,experiment_id=e.id,
                library=str(lib.relative_to(ROOT)) if lib.exists() else None,
                library_sha256=digest(lib) if lib.exists() else None,
                binary=str(binary.relative_to(ROOT)) if binary.exists() else None,
                binary_sha256=digest(binary) if binary.exists() else None,
                dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},
                build_recipe_sha256=digest(__file__))
    write(e.path/'build.json',result);result['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR')
    write(ROOT/'migration/reports/image-hough-build.json',result)
    record('I3','Hough共享HIP Canny/180角×1px GPU累加与峰提取、完整C++入口构建：'+result['status']+'；数值/运行语义待独立验收。',[result['evidence']])
    print(result['status'],result['evidence'])
    return rc

if __name__=='__main__':raise SystemExit(main())
