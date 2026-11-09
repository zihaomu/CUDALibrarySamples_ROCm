#!/usr/bin/env python3
"""Package only selected observation sources and exact tensor fixtures for CUDA."""
import json,pathlib,tarfile,shutil
from catalog import ROOT
from batch2_spec import ALL
from run import digest,evidence_directory
files=[ROOT/'build/cuda-observed'/s for s in ALL];files+=[ROOT/'build/cuda-observed/cuTENSOR/utils.cuh'];files+=[ROOT/'rocm/common'/n for n in ['observe.hpp','batch2_tensor_io.hpp']];files+=[ROOT/'tools/migration'/n for n in ['batch2_run.py','batch2_spec.py','run.py','catalog.py']]
for family in ['cuBLAS','cuSOLVER']:files+=[p for p in (ROOT/'build/cuda-observed'/family/'utils').glob('*') if p.is_file()]
with tarfile.open(ROOT/'build/batch2-cuda-sources.tar.gz','w:gz') as t:
 for p in files:
  info=t.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.mtime=0
  with p.open('rb') as f:t.addfile(info,f)
fixtures=[]
with tarfile.open(ROOT/'build/batch2-tensor-fixtures.tar','w') as t:
 for r in json.loads((ROOT/'migration/reports/batch2-rocm.json').read_text()):
  if not r['source'].startswith('cuTENSOR/'):continue
  for c in r['runs']:
   d=evidence_directory(c['evidence']);cfg=json.loads((d/'tensor.json').read_text());entry={'source':r['source'],'case':c['case'],'configuration':cfg,'inputs':{}}
   for p in d.glob('input_*.bin'):
    info=t.gettarinfo(str(p),arcname='build/batch2-tensor-fixtures/'+r['source'].replace('/','_')+'/'+c['case']+'/'+p.name);info.mtime=0
    with p.open('rb') as f:t.addfile(info,f)
    entry['inputs'][p.name]={'sha256':digest(p),'bytes':p.stat().st_size}
    if p.stat().st_size<65536:
     q=ROOT/'tests/fixtures/batch2'/pathlib.Path(r['source']).stem/c['case']/p.name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
   fixtures.append(entry)
(ROOT/'migration/reports/batch2-fixtures.json').write_text(json.dumps({'dtype':'float32','endianness':'little','recipe':'uint32 index + seed + ASCII(buffer)*0x9e3779b9; xor>>16, multiply0x7feb352d, xor>>15, multiply0x846ca68b, xor>>16; high24 bits / 2^24. See regenerate_batch2_fixtures.py; matches actual captured inputs.','fixtures':fixtures},indent=2)+'\n');print('Packaged',len(fixtures),'tensor fixtures')
