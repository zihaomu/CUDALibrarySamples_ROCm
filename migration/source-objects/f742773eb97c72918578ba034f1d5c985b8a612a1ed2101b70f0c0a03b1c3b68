#!/usr/bin/env python3
"""Compile both original-format watershed entrypoints against one project HIP core."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

PORTS={
 'NPP':'rocm/ported/NPP/watershedSegmentation/watershedSegmentation.cpp',
 'NPP+':'rocm/ported/NPP+/watershedSegmentation/watershedSegmentationNPPPlus.cpp',
}
CORE=ROOT/'rocm/common/image'
def dependencies():return [ROOT/'migration/rewrite/image-watershed-profile.json',
 CORE/'watershed.h',CORE/'watershed.hip',CORE/'watershed_sample.hpp',
 *[ROOT/path for path in PORTS.values()]]

def main():
 e=Experiment('I3','two-original-watershed-entrypoints-HIP-build','rocm-build',
   sources=[__file__,*dependencies()])
 write(e.path/'backend.observed.json',capture())
 profile=json.loads((ROOT/'migration/rewrite/image-watershed-profile.json').read_text())
 core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
 overlay=ROOT/'build/rocm-sdk-overlay'
 flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
  '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
  '--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__',
  '-I'+str(CORE),'-x','hip']
 binaries={};rc=0
 if profile['status']!='FROZEN':rc=1
 for family,path in PORTS.items():
  if rc:break
  output=e.path/('watershedNPPPlus' if family=='NPP+' else 'watershedNPP')
  rc=e.command([*flags,str(ROOT/path),str(CORE/'watershed.hip'),
   '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64',
   '-o',str(output)],'build-'+family+'-original-entry',timeout=300)
  if not rc:binaries[family]=dict(path=str(output.relative_to(ROOT)),sha256=digest(output))
 result=dict(status='BUILT' if not rc and len(binaries)==2 else 'BUILD_ERROR',
  return_code=rc,experiment_id=e.id,binaries=binaries,
  dependencies={str(p.relative_to(ROOT)):digest(p) for p in dependencies()})
 write(e.path/'build.json',result)
 result['evidence']=e.finish('EXECUTED' if result['status']=='BUILT' else 'BUILD_ERROR',
   dict(status=result['status'],checks=[dict(check='both-fully-compiled-HIP-entries',passed=result['status']=='BUILT')]))
 write(ROOT/'migration/reports/image-watershed-build.json',result)
 record('I3','NPP/NPP+两个完整文件入口共享项目HIP八邻域分水岭核构建：'+result['status']+'；尚未签发数值资格。',[result['evidence']])
 print(result['status'],result['evidence'])
 return int(result['status']!='BUILT')
if __name__=='__main__':raise SystemExit(main())
