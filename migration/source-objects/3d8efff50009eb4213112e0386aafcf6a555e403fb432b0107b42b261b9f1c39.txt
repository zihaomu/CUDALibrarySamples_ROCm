#!/usr/bin/env python3
"""Restore archived output-only CUDA observation sources under this project's build/."""
import hashlib,json
from catalog import ROOT
manifest=json.loads((ROOT/'migration/source-tree.json').read_text());count=0
for name,row in manifest['files'].items():
 if not name.startswith(('build/cuda-observed/','build/cuda-observed-fft/')):continue
 data=(ROOT/row['object']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'];p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);count+=1
print('Restored',count,'CUDA observation/fixture-adapter source files; original CUDA tree untouched')
