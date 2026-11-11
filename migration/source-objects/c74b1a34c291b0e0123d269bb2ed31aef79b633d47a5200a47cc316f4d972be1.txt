#!/usr/bin/env python3
"""Build the reusable HIP Canny library and seal the complete source closure."""
import ctypes,json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

def dependencies():
 return [ROOT/'rocm/common/image'/n for n in ['canny_stages.h','canny_stages.hip','canny.h','canny.hip']]+[ROOT/'rocm/python/image/canny.py',ROOT/'rocm/python/image/__init__.py',ROOT/'rocm/ported/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py',ROOT/'migration/rewrite/canny-plus-profile.json']

def main():
 files=dependencies();e=Experiment('I1','CannyPlus-full-library-build','rocm-build',sources=[__file__,*files]);write(e.path/'backend.observed.json',capture())
 core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay'
 flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-fPIC','-D__HIP_PLATFORM_AMD__']
 rc=0;objects=[]
 for name in ['canny_stages','canny']:
  obj=e.path/(name+'.o');objects.append(obj)
  rc=e.command(flags+['-MMD','-MF',str(e.path/(name+'.d')),'-x','hip','-c',str(ROOT/'rocm/common/image'/(name+'.hip')),'-o',str(obj)],'compile-'+name,timeout=300)
  if rc:break
 library=e.path/'libimage_canny.so'
 if not rc:rc=e.command(flags+['-shared',*[str(p) for p in objects],'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(library)],'link-shared-Canny',timeout=300)
 if not rc:rc=e.command(['ldd',str(library)],'actual-library-links')
 if not rc:
  lib=ctypes.CDLL(str(library));lib.rocm_image_canny_abi_version.restype=ctypes.c_uint32
  if lib.rocm_image_canny_abi_version()!=1:rc=1
 result=dict(status='BUILT' if not rc else 'BUILD_ERROR',dependencies={str(p.relative_to(ROOT)):digest(p) for p in files},library=str(library.relative_to(ROOT)),experiment_id=e.id,build_recipe_sha256=digest(__file__))
 if not rc:
  result['library_sha256']=digest(library);target=ROOT/'build/image/libimage_canny.so';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(library,target);result['installed_library']=str(target.relative_to(ROOT))
 write(e.path/'build.json',result);ref=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');result['evidence']=ref;write(ROOT/'migration/reports/canny-plus-build.json',result)
 record('I1','完整HIP Canny共享库构建：'+result['status']+'；独立对象/显式依赖、实际链接和ABI版本已记录。',[ref]);print(result['status'],ref);return rc
if __name__=='__main__':raise SystemExit(main())
