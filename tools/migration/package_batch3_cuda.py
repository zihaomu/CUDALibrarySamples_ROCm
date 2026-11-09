#!/usr/bin/env python3
"""Package only selected observation sources and exact sparse RHS fixtures for CUDA."""
import json,pathlib,tarfile,shutil
from catalog import ROOT
from batch3_spec import ALL
from run import digest,evidence_directory
files=[ROOT/'build/cuda-observed'/s for s in ALL];files+=[ROOT/'rocm/common'/n for n in ['observe.hpp','binary_observe.hpp']];files+=[ROOT/'tools/migration'/n for n in ['batch3_run.py','batch3_spec.py','run.py','catalog.py']]
for family in ['cuSOLVER']:files+=[p for p in (ROOT/'build/cuda-observed'/family/'utils').glob('*') if p.is_file()]
with tarfile.open(ROOT/'build/batch3-cuda-sources.tar.gz','w:gz') as t:
 for p in files:
  info=t.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.mtime=0
  with p.open('rb') as f:t.addfile(info,f)
print('Packaged selected batch 3 CUDA sources')

rows=json.loads((ROOT/'migration/reports/batch3-rocm.json').read_text())
with tarfile.open(ROOT/'build/batch3-sparse-fixtures.tar','w') as t:
 for r in rows:
  if not any('/'+k+'/' in r['source'] for k in ['cg','bicgstab']):continue
  for c in r['runs']:
   p=evidence_directory(c['evidence'])/'input_rhs.bin'
   info=t.gettarinfo(str(p),arcname='build/batch3-sparse-fixtures/'+r['source'].replace('/','_')+'/'+c['case']+'/input_rhs.bin');info.mtime=0
   with p.open('rb') as f:t.addfile(info,f)
