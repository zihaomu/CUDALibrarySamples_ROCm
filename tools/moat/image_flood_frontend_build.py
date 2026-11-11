#!/usr/bin/env python3
"""Build the complete original flood C++ caller with explicit compilation closure."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_flood_build import dependencies
from snapshot import capture
from image_progress import record
def main():
 b=json.loads((ROOT/'migration/reports/image-flood-build.json').read_text());source=ROOT/'rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp';deps=[*dependencies(),ROOT/'rocm/common/image/flood_sample.hpp',source];assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I3','FloodFill-full-five-workflow-C++-build','rocm-build',sources=[__file__,*deps],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=ROOT/'build/rocm-sdk-overlay';binary=e.path/'flood-original';rc=e.command(['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-x','hip',str(source),'-L'+str((ROOT/b['library']).parent),'-limage_flood','-Wl,-rpath,'+str((ROOT/b['library']).parent),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(binary)],'compile-full-RGB-original-file-workflow',timeout=300);r=dict(status='BUILT' if not rc else 'BUILD_ERROR',backend=b,binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if not rc else None,implementation=str(source.relative_to(ROOT)),dependencies={str(p.relative_to(ROOT)):digest(p) for p in deps},build_recipe_sha256=digest(__file__),experiment_id=e.id);write(e.path/'build.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-flood-frontend-build.json',r);record('I3','flood五完整RGB流程C++原入口构建：'+r['status']+'；完整20产品及运行合同待验。',[r['evidence']]);print(r['status'],r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
