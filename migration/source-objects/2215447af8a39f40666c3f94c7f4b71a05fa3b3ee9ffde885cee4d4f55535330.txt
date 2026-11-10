#!/usr/bin/env python3
"""Keep text/JSON evidence in Git; leave binaries and large outputs in artifacts/."""
import argparse,hashlib,json,pathlib,shutil
from catalog import ROOT
p=argparse.ArgumentParser();p.add_argument('--text-only',action='store_true',help='Refresh text/JSON evidence while retaining the existing large binary hash index');args=p.parse_args()
cat=json.loads((ROOT/'migration/samples.yaml').read_text());base=ROOT/'migration/reports/evidence';outputs={}
if args.text_only:outputs=json.loads((ROOT/'migration/reports/binary-outputs.json').read_text())
# Preserve successful and unsuccessful attempts, with their original relative structure.
for src in (ROOT/'artifacts').rglob('*'):
 if src.is_file() and src.suffix in {'.json','.log','.txt','.csv'}:
  dest=base/src.relative_to(ROOT/'artifacts');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 elif not args.text_only and src.is_file() and src.suffix=='.bin':
  outputs[str(src.relative_to(ROOT))]={'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'bytes':src.stat().st_size,'storage':'Local artifacts; regenerate with recorded source, commands and input recipe/fixture.'}
def saved(path):
 if isinstance(path,str) and path.startswith('artifacts/'):
  candidate=base/pathlib.Path(path).relative_to('artifacts')
  if candidate.exists():return str(candidate.relative_to(ROOT))
 return path
def rewrite(x):
 if isinstance(x,dict):return {k:rewrite(v) for k,v in x.items()}
 if isinstance(x,list):return [rewrite(v) for v in x]
 return saved(x)
cat=rewrite(cat)
for s in cat['samples']:
 if s['source']=='cuSPARSE/spmv_csr/spmv_csr_example.c':
  alt=ROOT/'rocm/cuSPARSE/spmv_csr/sample_rocsparse_v2.cpp';sha=hashlib.sha256(alt.read_bytes()).hexdigest();matches=[a for a in s['attempts'] if a['status']=='PASSED' and a.get('implementation_sha256')==sha]
  if matches:s['alternative_implementations']=[{'library':'rocSPARSE v2','source':str(alt.relative_to(ROOT)),'status':'VALIDATED_EXTENDED_CASES','evidence':matches[-1]['evidence']}]
# Also rewrite the small latest reports, keeping raw archived run snapshots untouched.
for p in (ROOT/'migration/reports').glob('*.json'):
 p.write_text(json.dumps(rewrite(json.loads(p.read_text())),indent=2,ensure_ascii=False)+'\n')
(ROOT/'migration/reports/binary-outputs.json').write_text(json.dumps(outputs,indent=2)+'\n')
(ROOT/'migration/samples.yaml').write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
print('Archived evidence files:',sum(p.is_file() for p in base.rglob('*')))
