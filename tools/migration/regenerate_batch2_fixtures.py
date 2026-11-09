#!/usr/bin/env python3
"""Regenerate large tensor inputs without storing them in Git; require exact SHA256."""
import argparse,json
from validate_blas import ROOT,np
from run import digest
p=argparse.ArgumentParser();p.add_argument('--output',default='build/batch2-tensor-fixtures');a=p.parse_args();manifest=json.loads((ROOT/'migration/reports/batch2-fixtures.json').read_text());count=0
for row in manifest['fixtures']:
 d=ROOT/a.output/row['source'].replace('/','_')/row['case'];d.mkdir(parents=True,exist_ok=True);seed=row['configuration']['fixture_seed'];assert seed is not None
 for name,record in row['inputs'].items():
  label=name.split('_')[1].split('.')[0];p=d/name;n=record['bytes']//4;base=np.uint32((seed+ord(label)*0x9e3779b9)&0xffffffff)
  with p.open('wb') as f:
   for start in range(0,n,1048576):
    x=np.arange(start,min(n,start+1048576),dtype=np.uint32)+base;x^=x>>16;x*=np.uint32(0x7feb352d);x^=x>>15;x*=np.uint32(0x846ca68b);x^=x>>16;((x>>8).astype('<f4')*np.float32(1./16777216.)).tofile(f)
  assert digest(p)==record['sha256'],name+' fixture hash mismatch';count+=1
print('Regenerated and hash-verified',count,'input buffers')
