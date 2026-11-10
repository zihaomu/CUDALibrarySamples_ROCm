#!/usr/bin/env python3
"""Fetch only this batch's CUDA evidence; never overwrite the AMD catalog."""
import subprocess, tarfile
from catalog import ROOT
remote = '/home/zihaomu/cuda_samples_on_rocm_compare'
script = '''import json,pathlib,tarfile
root=pathlib.Path(REMOTE)
report=root/'migration/reports/batches4_8-cuda.json'
files={report}
for row in json.loads(report.read_text()):
 for p in (root/row['evidence']).rglob('*'):
  if p.is_file() and p.suffix in {'.json','.log','.bin'}:files.add(p)
with tarfile.open(root/'build/batches4_8-cuda-evidence.tar.gz','w:gz') as t:
 for p in sorted(files):t.add(p,arcname=str(p.relative_to(root)))
'''.replace('REMOTE', repr(remote))
subprocess.run(['ssh','nvidia-5090x2','python3','-'],input=script,text=True,check=True)
p=ROOT/'build/batches4_8-cuda-evidence.tar.gz'
subprocess.run(['scp','-q','nvidia-5090x2:'+remote+'/build/'+p.name,str(p)],check=True)
with tarfile.open(p) as t:t.extractall(ROOT,filter='data')
print('Collected selected CUDA reports, logs and binary observations')
