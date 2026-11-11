#!/usr/bin/env python3
"""Build the isolated exact site-search HIP distance backend."""
import ctypes,json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

def dependencies():return [ROOT/'rocm/common/image'/n for n in ['distance.h','distance.hip','image_memory.hpp']]+[ROOT/'migration/rewrite/image-distance-profile.json']
def main():
 e=Experiment('I2','Distance-GPU-shared-backend-build','rocm-build',sources=[__file__,*dependencies()]);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';lib=e.path/'libimage_distance.so';flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-ffp-contract=off','-fPIC','-D__HIP_PLATFORM_AMD__'];rc=e.command(flags+['-MMD','-MF',str(e.path/'distance.d'),'-x','hip','-shared',str(ROOT/'rocm/common/image/distance.hip'),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(lib)],'compile-no-FP-contraction-and-link-distance-backend',timeout=300);abi=None
 if not rc:
  l=ctypes.CDLL(str(lib));l.rocm_image_distance_abi_version.restype=ctypes.c_uint32;abi=l.rocm_image_distance_abi_version();rc=0 if abi==1 else 1
 r=dict(status='BUILT' if not rc else 'BUILD_ERROR',abi_version=abi,experiment_id=e.id,library=str(lib.relative_to(ROOT)),library_sha256=digest(lib) if not rc else None,dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},build_recipe_sha256=digest(__file__));write(e.path/'build.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-distance-build.json',r);record('I2','Signed/unsigned HIP距离/插值site/Voronoi/可视化共享库首构建：'+r['status']+'；30输入与完整原入口及运行验收另列，不增加支持数。',[r['evidence']]);print(r['status'],r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
