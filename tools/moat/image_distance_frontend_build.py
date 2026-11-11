#!/usr/bin/env python3
"""Build the original full five-image C++ workflow against the HIP backend."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_distance_build import dependencies
from snapshot import capture
from image_progress import record

def main():
 b=json.loads((ROOT/'migration/reports/image-distance-build.json').read_text());assert b['status']=='BUILT' and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items()) and digest(ROOT/b['library'])==b['library_sha256'];source=ROOT/'rocm/ported/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp';deps=[*dependencies(),ROOT/'rocm/common/image/distance_sample.hpp',source];e=Experiment('I2','Distance-full-original-C++-build','rocm-build',sources=[__file__,*deps],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';binary=e.path/'distance-original';rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-ffp-contract=off','-D__HIP_PLATFORM_AMD__','-x','hip',str(source),'-L'+str((ROOT/b['library']).parent),'-limage_distance','-Wl,-rpath,'+str((ROOT/b['library']).parent),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],'compile-real-five-image-original-C++-caller',timeout=300);r=dict(status='BUILT' if not rc else 'BUILD_ERROR',backend=b,binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if not rc else None,implementation=str(source.relative_to(ROOT)),dependencies={str(p.relative_to(ROOT)):digest(p) for p in deps},build_recipe_sha256=digest(__file__),experiment_id=e.id);write(e.path/'build.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-distance-frontend-build.json',r);record('I2','Signed/unsigned完整五图C++原入口构建：'+r['status']+'；待四实际完整流程、48产品文件及审计独立验收。',[r['evidence']]);print(r['status'],r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
