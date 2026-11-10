#!/usr/bin/env python3
import subprocess,tarfile,json,pathlib,sys,shutil
from catalog import ROOT
from batches9_11_spec import GROUPS
from run import evidence_directory
selected={s for g in sys.argv[1:] for s in GROUPS[g]} if len(sys.argv)>1 else set();remote='/home/zihaomu/cuda_samples_on_rocm_compare'
script='''import pathlib,json,tarfile
root=pathlib.Path(REMOTE);report=root/'migration/reports/batches9_11-cuda.json'
with tarfile.open(root/'build/batches9_11-cuda-evidence.tar','w') as t:
 t.add(report,arcname=str(report.relative_to(root)))
 for row in json.loads(report.read_text()):
  if SELECTED and row['source'] not in SELECTED:continue
  for p in (root/row['evidence']).rglob('*'):
   if p.is_file() and p.name!='sample':t.add(p,arcname=str(p.relative_to(root)))
'''.replace('REMOTE',repr(remote)).replace('SELECTED',repr(selected));subprocess.run(['ssh','nvidia-5090x2','python3','-'],input=script,text=True,check=True);p=ROOT/'build/batches9_11-cuda-evidence.tar';subprocess.run(['scp','-q','nvidia-5090x2:'+remote+'/build/'+p.name,str(p)],check=True)
with tarfile.open(p) as t:t.extractall(ROOT,filter='data')
for backend in ['rocm','cuda']:
 report=ROOT/'migration/reports'/('batches9_11-'+backend+'.json')
 if not report.exists():continue
 for row in json.loads(report.read_text()):
  if row['batch']!='b9' or row['build_return_code']:continue
  original=next((c for c in row['runs'] if c['case']=='original' and c['return_code']==0),None)
  if not original:continue
  d=evidence_directory(original['evidence']);target=ROOT/'build/b9-cross-fixtures'/backend/row['source'].replace('/','_');target.mkdir(parents=True,exist_ok=True)
  for file in d.glob('gpu_compressed_*.bin'):shutil.copyfile(file,target/file.name)
  (target/'provenance.json').write_text(json.dumps(dict(producer=row,case=original['case']),indent=2)+'\n')
print('Collected CUDA observations; staged independently captured raw blocks for bidirectional native GPU interoperability')
