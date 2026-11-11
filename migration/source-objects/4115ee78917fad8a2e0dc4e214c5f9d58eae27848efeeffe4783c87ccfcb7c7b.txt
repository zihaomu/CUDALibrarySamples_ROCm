#!/usr/bin/env python3
"""Build the two real C++ original contour callers against the frozen HIP backend."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_contour_build import dependencies
from snapshot import capture
from image_progress import record

def main():
 b=json.loads((ROOT/'migration/reports/image-contour-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());common=ROOT/'rocm/common/image';sources=[__file__,common/'contour_sample.hpp',*dependencies(),ROOT/'rocm/ported/NPP/findContour/findContour.cpp',ROOT/'rocm/ported/NPP+/findContour/findContourNPPPlus.cpp'];e=Experiment('I2','Contour-two-original-C++-build','rocm-build',sources=sources,parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(common)];rows=[];rc=0
 for family in ['NPP','NPP+']:
  source=ROOT/'rocm/ported'/family/'findContour'/('findContour.cpp' if family=='NPP' else 'findContourNPPPlus.cpp');binary=e.path/(family+'-contour');rc=e.command(flags+['-x','hip',str(source),'-L'+str((ROOT/b['library']).parent),'-limage_contour','-Wl,-rpath,'+str((ROOT/b['library']).parent),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],'compile-real-'+family+'-C++',timeout=300);rows.append(dict(family=family,binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if not rc else None,source=str(source.relative_to(ROOT))))
  if rc:break
 r=dict(status='BUILT' if not rc else 'BUILD_ERROR',backend=b,binaries=rows,dependencies={str(p.relative_to(ROOT)):digest(p) for p in sources if str(p)!=__file__},build_recipe_sha256=digest(__file__),experiment_id=e.id);write(e.path/'build.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-contour-frontends-build.json',r);record('I2','两个真实C++ contour原入口构建：'+r['status']+'；共享HIP几何库不变，后续完整文件/范围/诊断验收单列。',[r['evidence']]);print(r['status'],r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
