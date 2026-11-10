#!/usr/bin/env python3
"""Reprobe actual hipSPARSELt route independently of project sparse kernels."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
observed=capture();core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=Path('/opt/rocm/core-10.1');overlay=ROOT/'build/rocm-sdk-overlay';results=[]
for kind in ['matmul','matmul_advanced']:
 src=ROOT/'rocm/adapters/vendor_contracts/hipsparselt'/(kind+'_native.cpp');e=Experiment('R7','hipSPARSELt-native/'+kind,'rocm-native-probe',sources=[__file__,src]);write(e.path/'backend.observed.json',observed);binary=e.path/'native';libs=[native/'lib',core.parent/'_rocm_sdk_libraries/lib',core/'lib'];cmd=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-x','hip',str(src),'-o',str(binary),'-I'+str(core/'include'),'-I'+str(native/'include')]+['-L'+str(p) for p in libs]+['-Wl,-rpath,'+str(p) for p in libs]+['-lhipsparselt','-lhipsparse','-lamdhip64'];rc=e.command(cmd,'native-compile');run=None
 if rc==0:
  e.command(['ldd',str(binary)],'native-library-resolution');run=e.command([str(binary)],'native-run')
 r=dict(profile=kind,build_return_code=rc,run_return_code=run,source_sha256=digest(src),experiment_id=e.id,environment=observed);r['evidence']=e.finish('OBSERVED' if rc==0 else 'NATIVE_BUILD_FAILED');results.append(r);write(ROOT/'migration/reports/rewrite-sparseLt-native-route.json',dict(profiles=results,scope='Native API reprobe only; failure is retained separately from the project sparse 2:4 rewrite'));print(kind,rc,run,flush=True)
