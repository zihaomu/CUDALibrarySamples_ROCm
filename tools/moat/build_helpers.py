#!/usr/bin/env python3
"""Build the narrow host descriptor ABI on actual HIP memory and nine callers."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from snapshot import capture

def main():
 profiles=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'];sources=list((ROOT/'rocm/adapters/helpers').glob('*'))+[ROOT/p['implementation'] for p in profiles]+[ROOT/p['source'] for p in profiles]+[Path(__file__)];e=Experiment('R9','matrix-helper-language-builds','rocm-build',sources=sources);write(e.path/'backend.observed.json',capture())
 core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');native=Path('/opt/rocm/core-10.1');folder=ROOT/'rocm/adapters/helpers';library=e.path/'libmatrix_helpers.so';dep=e.path/'core.d'
 cmd=['hipcc','--rocm-path='+str(ROOT/'build/rocm-sdk-overlay'),'--hip-path='+str(ROOT/'build/rocm-sdk-overlay'),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-shared','-fPIC','-MMD','-MF',str(dep),'-I'+str(folder),'-I'+str(native/'include'),'-x','hip',str(folder/'matrix_helpers.cpp'),'-o',str(library),'-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64']
 rc=e.command(cmd,'HIP-runtime-descriptor-core');flang=str(native/'lib/llvm/bin/flang');records=[]
 if not rc:rc=e.command(['c++','-std=c++17','-O2','-fPIC','-I'+str(folder),'-c',str(folder/'helper_client.cpp'),'-o',str(e.path/'client.o')],'C++-caller-module')
 if not rc:rc=e.command([flang,'-fPIC','-c',str(folder/'helper_samples.f90'),'-J',str(e.path),'-o',str(e.path/'fortran.o')],'Fortran-actual-C-ABI-module',cwd=e.path)
 for p in profiles:
  if rc:break
  binary=e.path/(p['language']+'_'+p['kind']);compiler='c++' if p['language']=='cpp' else flang;args=['-std=c++17'] if p['language']=='cpp' else ['-x','f95']
  rc=e.command([compiler]+args+['-O2','-I'+str(e.path),str(ROOT/p['implementation'])]+([] if p['language']=='cpp' else ['-x','none'])+[str(e.path/('client.o' if p['language']=='cpp' else 'fortran.o')),'-L'+str(e.path),'-lmatrix_helpers','-Wl,-rpath,'+str(e.path),'-o',str(binary)],'entry-'+p['language']+'-'+p['kind'])
  if not rc:records.append(dict(sample_id=p['sample_id'],binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary),implementation_sha256=digest(ROOT/p['implementation'])))
 dependencies={str(p.relative_to(ROOT)):digest(p) for p in sources if p.is_relative_to(ROOT/'rocm')}
 result=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',experiment_id=e.id,dependencies=dependencies,binaries=records,shared_library=str(library.relative_to(ROOT)),shared_library_sha256=digest(library) if library.exists() else None,build_recipe_sha256=digest(__file__))
 write(e.path/'compiled-dependencies.json',dependencies);write(e.path/'build-result.json',result);result['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR');write(ROOT/'migration/reports/rewrite-R9-helper-build.json',result);print(result['status'],result['evidence']);return int(bool(rc))
if __name__=='__main__':raise SystemExit(main())
