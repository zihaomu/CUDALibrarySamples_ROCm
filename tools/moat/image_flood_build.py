#!/usr/bin/env python3
"""Build RGB flood fill using the unchanged shared GPU connectivity primitive."""
import ctypes,json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
def dependencies():return [ROOT/'rocm/common/image'/n for n in ['flood.h','flood.hip','connectivity.h','connectivity.hip','image_memory.hpp']]+[ROOT/'migration/rewrite/image-flood-profile.json']
def main():
 e=Experiment('I3','FloodFill-full-RGB-GPU-backend-build','rocm-build',sources=[__file__,*dependencies()]);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';lib=e.path/'libimage_flood.so';flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-fPIC','-D__HIP_PLATFORM_AMD__'];rc=e.command([*flags,'-x','hip','-shared',str(ROOT/'rocm/common/image/flood.hip'),str(ROOT/'rocm/common/image/connectivity.hip'),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(lib)],'compile-RGB-predicates-source-copy-components-boundary-and-device-metadata',timeout=300);abi=None
 if not rc:
  l=ctypes.CDLL(str(lib));l.rocm_image_flood_abi_version.restype=ctypes.c_uint32;abi=l.rocm_image_flood_abi_version();rc=0 if abi==1 else 1
 r=dict(status='BUILT' if not rc else 'BUILD_ERROR',abi_version=abi,experiment_id=e.id,library=str(lib.relative_to(ROOT)),library_sha256=digest(lib) if not rc else None,dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},build_recipe_sha256=digest(__file__));write(e.path/'build.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-flood-build.json',r);record('I3','完整RGB flood fill固定seed谓词/连接分量/内边界/原色与inclusive bbox GPU后端：'+r['status']+'；无整例资格。',[r['evidence']]);print(r['status'],r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
