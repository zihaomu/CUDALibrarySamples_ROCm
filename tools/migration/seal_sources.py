#!/usr/bin/env python3
"""Content-address final port/tool source, with per-entry implementation identities."""
import hashlib,json,pathlib
from catalog import ROOT,BASE
objects=ROOT/'migration/source-objects';objects.mkdir(parents=True,exist_ok=True);files={};ext={'.cpp','.cu','.c','.hip','.h','.hpp','.cuh','.hxx','.inl','.f90','.cuf','.py','.sh','.txt'}
for root in [ROOT/'rocm',ROOT/'tools/migration',ROOT/'build/cuda-observed',ROOT/'build/cuda-observed-fft']:
 for p in root.rglob('*'):
  if p.is_file() and (p.suffix in ext or p.name=='CMakeLists.txt'):
   data=p.read_bytes();sha=hashlib.sha256(data).hexdigest();obj=objects/(sha+'.txt')
   if not obj.exists():obj.write_bytes(data)
   files[str(p.relative_to(ROOT))]={'sha256':sha,'object':str(obj.relative_to(ROOT)),'bytes':len(data)}
identity=hashlib.sha256(''.join(k+'\0'+v['sha256']+'\n' for k,v in sorted(files.items())).encode()).hexdigest();report={'upstream_commit':BASE,'scope':'Final source tree for replay; historical attempts retain their original per-attempt hashes/logs','tree_sha256':identity,'files':files,'fixtures':{str(p.relative_to(ROOT)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in (ROOT/'tests/fixtures').rglob('*') if p.is_file()}};(ROOT/'migration/source-tree.json').write_text(json.dumps(report,indent=2)+'\n');print('Sealed',len(files),'files',identity)
