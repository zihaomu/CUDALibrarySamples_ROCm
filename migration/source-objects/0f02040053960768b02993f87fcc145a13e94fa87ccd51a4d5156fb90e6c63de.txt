#!/usr/bin/env python3
"""Build the first full GPU contour graph/order/rasterization backend."""
import ctypes,json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

def dependencies():return [ROOT/'rocm/common/image'/n for n in ['connectivity.h','connectivity.hip','image_memory.hpp','ccl.h','ccl.hip','contour.h','contour.hip']]+[ROOT/'migration/rewrite/image-contour-profile.json']
def main():
 e=Experiment('I2','Contour-GPU-geometry-build','rocm-build',sources=[__file__,*dependencies()]);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';common=ROOT/'rocm/common/image';flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-fPIC','-D__HIP_PLATFORM_AMD__'];rc=0;objects=[]
 for name in ['connectivity','ccl','contour']:
  obj=e.path/(name+'.o');objects.append(obj);rc=e.command(flags+['-MMD','-MF',str(e.path/(name+'.d')),'-x','hip','-c',str(common/(name+'.hip')),'-o',str(obj)],'compile-'+name,timeout=300)
  if rc:break
 lib=e.path/'libimage_contour.so'
 if not rc:rc=e.command(flags+['-shared',*map(str,objects),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(lib)],'link-full-GPU-contour-library',timeout=300)
 abi=None
 if not rc:
  library=ctypes.CDLL(str(lib));library.rocm_image_contour_abi_version.restype=ctypes.c_uint32;abi=library.rocm_image_contour_abi_version();rc=0 if abi==2 else 1
 r=dict(status='BUILT' if not rc else 'BUILD_ERROR',experiment_id=e.id,abi_version=abi,library=str(lib.relative_to(ROOT)),library_sha256=digest(lib) if not rc else None,dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},build_recipe_sha256=digest(__file__));write(e.path/'build.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-contour-build.json',r);record('I2','HIP contour标签/边图/循环并查集/指针跳跃排序/前缀压缩/geometry顶点重建共享库构建：'+r['status']+'；尚待GPU数值与完整入口验收。',[r['evidence']]);print(r['status'],r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
