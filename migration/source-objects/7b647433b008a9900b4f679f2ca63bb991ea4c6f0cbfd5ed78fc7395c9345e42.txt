#!/usr/bin/env python3
import tarfile,pathlib
from catalog import ROOT
from batches12_15_spec import ALL
with tarfile.open(ROOT/'build/batches12_15-cuda.tar','w') as t:
 for source in ALL:
  p=ROOT/'build/cuda-observed'/source
  if p.exists():t.add(p,arcname=str(p.relative_to(ROOT)))
 for p in (ROOT/'rocm/common').iterdir():
  if p.suffix in ['.hpp','.h']:t.add(p,arcname=str(p.relative_to(ROOT)))
 for n in ['catalog.py','run.py','device_guard.py','batches12_15_spec.py','batches12_15_run.py']:
  p=ROOT/'tools/migration'/n;t.add(p,arcname=str(p.relative_to(ROOT)))
 for n in ['migration/roadmap.json','build/mpi','build/mathdx-sdk','build/batch15-fixtures','MathDx','cuBLASMp','cuSOLVERMp','cuSOLVER/utils']:
  p=ROOT/n
  if p.exists():t.add(p,arcname=n)
 for s in ALL:
  if not s.startswith(('MathDx/','cuBLASMp/','cuSOLVERMp/')):t.add(ROOT/s,arcname=s)
print('Packaged compatible CUDA implementations and original native SDK probes')
