#!/usr/bin/env python3
"""Package only selected observation sources and exact sparse RHS fixtures for CUDA."""
import json,pathlib,tarfile,shutil
from catalog import ROOT
from batches4_8_spec import ALL
from run import digest,evidence_directory
files=[ROOT/'build/cuda-observed'/s for s in ALL if (ROOT/'build/cuda-observed'/s).exists()];files+=[ROOT/'rocm/common'/n for n in ['observe.hpp','binary_observe.hpp','batches_runtime.hpp','batch4_packed.hpp','batch4_sparse.hpp']];files+=[ROOT/'tools/migration'/n for n in ['batches4_8_run.py','batches4_8_spec.py','run.py','catalog.py']]
for family in ['cuSOLVER','cuBLAS']:files+=[p for p in (ROOT/'build/cuda-observed'/family/'utils').glob('*') if p.is_file()]
files += [ROOT/'migration/roadmap.json']
with tarfile.open(ROOT/'build/batches4_8-cuda-sources.tar.gz','w:gz') as t:
 for p in files:
  info=t.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.mtime=0
  with p.open('rb') as f:t.addfile(info,f)
print('Packaged selected batch 3 CUDA sources')
