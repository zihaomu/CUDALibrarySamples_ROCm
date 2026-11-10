#!/usr/bin/env python3
"""Import original randomized inputs from a successful instrumented native sample."""
import json,shutil
from pathlib import Path
from experiment import ROOT,digest,write
from first_fixtures import create
reports=json.loads((ROOT/'migration/reports/rewrite-native-mathdx.json').read_text())
for kind in ['lu','posv','trsm']:
 r=reports[kind]
 if r['return_code']!=0:raise RuntimeError('native original did not run: '+kind)
 dest=ROOT/'tests/fixtures/rewrite-native-original'/kind;dest.mkdir(parents=True,exist_ok=True)
 inputs={}
 for name in ['A','B']:
  p=ROOT/r['output']/('input_'+name+'.bin')
  if p.exists():shutil.copyfile(p,dest/(name+'.bin'));inputs[name]=dict(sha256=digest(p),bytes=p.stat().st_size)
 write(dest/'provenance.json',dict(native_experiment=r['experiment_id'],native_source=r['original_sha256'],files=inputs))
 for case in ['original','repeat']:create(kind,case)
 print('Imported true native original input:',kind,inputs)
