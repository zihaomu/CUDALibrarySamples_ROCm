#!/usr/bin/env python3
"""Fetch only this batch's CUDA evidence; never overwrite the AMD catalog."""
import subprocess, tarfile, json, os,sys
from batches4_8_spec import GROUPS
selected={s for g in sys.argv[1:] for s in GROUPS[g]} if len(sys.argv)>1 else set()
from run import evidence_directory
from catalog import ROOT
remote = '/home/zihaomu/cuda_samples_on_rocm_compare'
script = '''import json,pathlib,tarfile
root=pathlib.Path(REMOTE)
report=root/'migration/reports/batches4_8-cuda.json'
files={report}
for row in json.loads(report.read_text()):
 if SELECTED and row['source'] not in SELECTED:continue
 for p in (root/row['evidence']).rglob('*'):
  if p.is_file() and p.suffix in {'.json','.log','.bin'} and not (row['source'].startswith('cuTENSOR/') and p.name.startswith('input_')):files.add(p)
with tarfile.open(root/'build/batches4_8-cuda-evidence.tar','w') as t:
 for p in sorted(files):t.add(p,arcname=str(p.relative_to(root)))
'''.replace('REMOTE', repr(remote)).replace('SELECTED',repr(selected))
subprocess.run(['ssh','nvidia-5090x2','python3','-'],input=script,text=True,check=True)
p=ROOT/'build/batches4_8-cuda-evidence.tar'
subprocess.run(['scp','-q','nvidia-5090x2:'+remote+'/build/'+p.name,str(p)],check=True)
with tarfile.open(p) as t:t.extractall(ROOT,filter='data')
print('Collected selected CUDA reports, logs and binary observations')

amd={r['source']:r for r in json.loads((ROOT/'migration/reports/batches4_8-rocm.json').read_text())}
for r in json.loads((ROOT/'migration/reports/batches4_8-cuda.json').read_text()):
 if not r['source'].startswith('cuTENSOR/') or r['source'] not in amd:continue
 for c in r['runs']:
  d=evidence_directory(c['evidence']);ar=next((v for v in amd[r['source']]['runs'] if v['case']==c['case']),None)
  if not ar:continue
  a=evidence_directory(ar['evidence']);cm=json.loads((d/'binary-outputs.json').read_text());am=json.loads((a/'binary-outputs.json').read_text())
  for name,meta in cm.items():
   if not name.startswith('input_'):continue
   if meta!=am.get(name):raise RuntimeError('CUDA/AMD captured input identity differs: '+name)
   if not (d/name).exists():os.link(a/name,d/name)
print('Reused independently captured matching CUDA/AMD inputs by SHA256; outputs fetched separately')
