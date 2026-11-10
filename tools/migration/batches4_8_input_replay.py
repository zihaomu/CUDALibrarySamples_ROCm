#!/usr/bin/env python3
"""Rebuild B5 deterministic inputs in bounded CPU chunks; verify all captured hashes."""
import hashlib,json
from catalog import ROOT
from run import evidence_directory,digest
from validate_blas import np
cache={};checks=[]
for row in json.loads((ROOT/'migration/reports/batches4_8-rocm.json').read_text()):
 if not row['source'].startswith('cuTENSOR/'):continue
 for case in row['runs']:
  d=evidence_directory(case['evidence']);meta=json.loads((d/'binary-outputs.json').read_text())
  for name,expected in meta.items():
   if not name.startswith('input_'):continue
   label=name.removeprefix('input_').removesuffix('.bin');n=expected['bytes']//4;changed=case['case']=='changed-values';key=(label[0],n,changed)
   if key not in cache:
    sha=hashlib.sha256();base=np.uint32((20261110+ord(label[0])*0x9e3779b9)&0xffffffff)
    for first in range(0,n,1<<20):
     x=np.arange(first,min(n,first+(1<<20)),dtype=np.uint32)+base;x^=x>>np.uint32(16);x*=np.uint32(0x7feb352d);x^=x>>np.uint32(15);x*=np.uint32(0x846ca68b);x^=x>>np.uint32(16);values=(x>>np.uint32(8)).astype('<f4')*np.float32(1/16777216)
     if changed:values=values*np.float32(-.5)+np.float32(.125)
     sha.update(values.tobytes())
    cache[key]=sha.hexdigest()
   actual=cache[key];passed=actual==expected['sha256'];checks.append(dict(source=row['source'],case=case['case'],buffer=name,bytes=expected['bytes'],sha256=actual,passed=passed));assert passed,(row['source'],case['case'],name)
report=dict(status='PASSED',seed=20261110,checks=checks,unique_recipes=len(cache),generator_sha256=digest(__import__('pathlib').Path(__file__)));(ROOT/'migration/reports/batches4_8-input-replay.json').write_text(json.dumps(report,indent=2)+'\n');print('Regenerated',len(checks),'input buffers;',len(cache),'unique bounded-memory recipes')
