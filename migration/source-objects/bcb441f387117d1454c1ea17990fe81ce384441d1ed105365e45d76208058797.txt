#!/usr/bin/env python3
import json
from pathlib import Path
from experiment import Experiment,ROOT,write
from snapshot import capture
core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=Path('/opt/rocm/core-10.1');e=Experiment('R1','native-INT8-capability','rocm-probe',sources=[ROOT/'tools/moat/native_int8.cu'])
write(e.path/'backend.observed.json',capture());binary=e.path/'probe';libs=[native/'lib',core.parent/'_rocm_sdk_libraries/lib',core/'lib']
cmd=['hipcc','--rocm-path='+str(ROOT/'build/rocm-sdk-overlay'),'--hip-path='+str(ROOT/'build/rocm-sdk-overlay'),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17',str(ROOT/'tools/moat/native_int8.cu'),'-I'+str(core/'include'),'-I'+str(native/'include'),'-o',str(binary)]+['-L'+str(x) for x in libs]+['-Wl,-rpath,'+str(x) for x in libs]+['-lhipblas','-lamdhip64']
rc=e.command(cmd,'build',timeout=120)
if rc==0:rc=e.command([str(binary)],'probe',timeout=120)
evidence=e.finish('EXECUTED' if rc==0 else 'PROBE_FAILED',reason=None if rc==0 else f'probe command exit {rc}')
write(ROOT/'migration/reports/rewrite-int8-native-probe.json',dict(return_code=rc,evidence=evidence));print(evidence)
