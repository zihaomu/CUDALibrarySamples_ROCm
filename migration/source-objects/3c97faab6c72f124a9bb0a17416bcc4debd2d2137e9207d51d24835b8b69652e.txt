#!/usr/bin/env python3
import argparse,subprocess,tarfile
from catalog import ROOT
p=argparse.ArgumentParser();p.add_argument('--native-only',action='store_true');args=p.parse_args()
remote='/home/zihaomu/cuda_samples_on_rocm_compare'
script='''import json,pathlib,tarfile
root=pathlib.Path(REMOTE)
with tarfile.open(root/'build/batches12_15-evidence.tar','w') as t:
 for name in NAMES:
  p=root/'migration/reports'/name
  if not p.exists():continue
  t.add(p,arcname=str(p.relative_to(root)))
  blob=json.loads(p.read_text())
  for r in blob if isinstance(blob,list) else [blob]:
   for f in (root/r['evidence']).rglob('*'):
    if f.is_file() and f.name!='sample':t.add(f,arcname=str(f.relative_to(root)))
'''.replace('REMOTE',repr(remote)).replace('NAMES',repr(['batch15-native-npp.json'] if args.native_only else ['batches12_15-cuda.json','batches12_15-native-cuda.json','batch15-native-npp.json']))
subprocess.run(['ssh','nvidia-5090x2','python3','-'],input=script,text=True,check=True);p=ROOT/'build/batches12_15-evidence.tar';subprocess.run(['scp','-q','nvidia-5090x2:'+remote+'/build/'+p.name,str(p)],check=True)
with tarfile.open(p) as t:t.extractall(ROOT,filter='data')
print('Collected compatible CUDA outputs and distinct original vendor attempts')
