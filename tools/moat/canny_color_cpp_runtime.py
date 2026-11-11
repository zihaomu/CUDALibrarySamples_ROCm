#!/usr/bin/env python3
"""Build/run the actual C++ class on a host ROI and real invalid calls."""
import json,os
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from canny_color_build import dependencies
from image_progress import record

def main():
 spec=ROOT/'migration/rewrite/canny-color-cpp-runtime.json';contract=dict(cases=['noncontiguous','dimension-mismatch','type-mismatch','invalid-low','invalid-order','invalid-high','constructor-zero','constructor-negative','constructor-limit','after-errors','concurrent-a','concurrent-b'],fixture='independent-noise-128374')
 if not spec.exists():write(spec,contract)
 if json.loads(spec.read_text())!=contract:raise RuntimeError('C++ runtime contract changed')
 profile=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());fixture=ROOT/next(c for c in profile['cases'] if c['case']==contract['fixture'])['fixture'];build=json.loads((ROOT/'migration/reports/canny-color-build.json').read_text());source=ROOT/'rocm/probes/image/canny_color_cpp_contract.cpp'
 if any(digest(ROOT/n)!=sha for n,sha in build['dependencies'].items()) or digest(ROOT/build['library'])!=build['library_sha256']:raise RuntimeError('Stale C++ class/library')
 e=Experiment('I1','NPP/nppCanny::npp_canny_simple.cpp','rocm-C++-runtime',sources=[__file__,source,spec,*dependencies()],parent=build['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';out.mkdir();core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';prefix=ROOT/'build/image-opencv';library=ROOT/build['library'];binary=e.path/'class-contract'
 flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/common/image'),'-I'+str(prefix/'include/opencv4'),'-x','hip',str(source),'-L'+str(library.parent),'-limage_canny_color','-Wl,-rpath,'+str(library.parent),'-L'+str(prefix/'lib'),'-Wl,-rpath,'+str(prefix/'lib'),'-lopencv_imgcodecs','-lopencv_imgproc','-lopencv_core','-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)]
 rc=e.command(flags,'build-actual-class-contract',timeout=300);env=dict(os.environ,LD_LIBRARY_PATH=str(prefix/'lib')+':'+os.environ.get('LD_LIBRARY_PATH',''))
 if not rc:rc=e.command([str(binary),str(fixture),str(out)],'actual-host-ROI-and-C++-errors',env=env,timeout=180)
 result=dict(return_code=rc,experiment_id=e.id,build=build,outputs=str(out.relative_to(ROOT)),binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if binary.exists() else None,fixture=str(fixture.relative_to(ROOT)));write(e.path/'run.json',result);result['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/canny-color-cpp-runtime.json',result);record('I1','C3真实C++ class非连续host ROI、尺寸/type/阈值/构造错误及恢复调用：rc='+str(rc)+'；CPU完整像素与诊断核对待执行。',[result['evidence']]);print(rc,result['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
