#!/usr/bin/env python3
"""Build shared GPU CCL and the two original C++ workflows/compile branches."""
import ctypes,json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
def dependencies():return [ROOT/'rocm/common/image'/n for n in ['connectivity.h','connectivity.hip','image_memory.hpp','ccl.h','ccl.hip','ccl_sample.hpp']]+[ROOT/'rocm/ported'/p for p in ['NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp','NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp']]+[ROOT/'migration/rewrite/image-ccl-profile.json']
def main():
 e=Experiment('I2','CCL-shared-GPU-and-original-build','rocm-build',sources=[__file__,*dependencies()]);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';common=ROOT/'rocm/common/image';flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-fPIC','-D__HIP_PLATFORM_AMD__'];links=['-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64'];objects=[];rc=0
 for name in ['connectivity','ccl']:
  obj=e.path/(name+'.o');objects.append(obj);rc=e.command(flags+['-MMD','-MF',str(e.path/(name+'.d')),'-x','hip','-c',str(common/(name+'.hip')),'-o',str(obj)],'compile-'+name,timeout=300)
  if rc:break
 library=e.path/'libimage_ccl.so'
 if not rc:rc=e.command(flags+['-shared',*map(str,objects),*links,'-o',str(library)],'link-GPU-CCL',timeout=300)
 binaries=[]
 for family,mode in [('NPP','default'),('NPP+','default'),('NPP+','batch-compression')]:
  if rc:break
  source=ROOT/'rocm/ported'/family/'batchedLabelMarkersAndCompression'/('batchedLabelMarkersAndCompression.cpp' if family=='NPP' else 'batchedLabelMarkersAndCompressionNPPPlus.cpp');binary=e.path/(family+'-'+mode);rc=e.command(flags+(['-DCUDA11U1'] if mode=='batch-compression' else [])+['-I'+str(common),'-x','hip',str(source),'-L'+str(e.path),'-limage_ccl','-Wl,-rpath,'+str(e.path),*links,'-o',str(binary)],'actual-'+family+'-'+mode,timeout=300)
  binaries.append(dict(family=family,mode=mode,binary=str(binary.relative_to(ROOT)),sha256=digest(binary) if not rc else None))
 result=dict(status='BUILT' if not rc else 'BUILD_ERROR',experiment_id=e.id,library=str(library.relative_to(ROOT)),library_sha256=digest(library) if not rc else None,binaries=binaries,dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()},build_recipe_sha256=digest(__file__))
 if not rc:
  lib=ctypes.CDLL(str(library));lib.rocm_image_ccl8_abi_version.restype=ctypes.c_uint32
  if lib.rocm_image_ccl8_abi_version()!=1:rc=1;result['status']='ABI_ERROR'
 write(e.path/'build.json',result);result['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-ccl-build.json',result);record('I2','共享HIP等值CCL/前缀压缩、两个真实C++入口及NPP+条件分支构建：'+result['status'],[result['evidence']]);print(result['status'],result['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
