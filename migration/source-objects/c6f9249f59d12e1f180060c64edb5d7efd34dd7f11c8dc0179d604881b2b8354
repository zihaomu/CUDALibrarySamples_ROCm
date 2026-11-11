#!/usr/bin/env python3
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture

def main():
 folder=ROOT/'rocm/backends/codec';src=ROOT/'rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp';headers=[folder/'crc_benchmark_compat.hpp',folder/'crc_benchmark_observe.hpp'];sources=[src]+headers+[ROOT/'nvCOMP/benchmarks/benchmark_crc32.cpp',ROOT/'tools/moat/prepare_crc_benchmark.py',__file__];e=Experiment('R9','nvCOMP/benchmarks::benchmark_crc32.cpp','rocm-build',sources=sources);write(e.path/'backend.observed.json',capture());core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=Path('/opt/rocm/core-10.1');binary=e.path/'benchmark';dep=e.path/'dependencies.d';libraries=[core/'lib',core.parent/'_rocm_sdk_libraries/lib',native/'lib']
 cmd=['hipcc','--rocm-path='+str(ROOT/'build/rocm-sdk-overlay'),'--hip-path='+str(ROOT/'build/rocm-sdk-overlay'),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-MMD','-MF',str(dep),'-I'+str(folder),'-I'+str(core/'include'),'-I'+str(native/'include'),'-x','hip',str(src),'-o',str(binary)]+['-L'+str(p) for p in libraries]+['-Wl,-rpath,'+str(p) for p in libraries]+['-lhiprand','-lamdhip64']
 rc=e.command(cmd,'build-original-harness-and-GPU-CRC-search',timeout=300);dependencies={str(p.relative_to(ROOT)):digest(p) for p in [src]+headers};result=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if binary.exists() else None,dependencies=dependencies,build_recipe_sha256=digest(__file__),experiment_id=e.id)
 write(e.path/'build-result.json',result);write(e.path/'compiled-dependencies.json',dependencies);result['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR');write(ROOT/'migration/reports/rewrite-R9-crc-benchmark-build.json',result);print(result['status'],result['evidence']);return int(bool(rc))
if __name__=='__main__':raise SystemExit(main())
