#!/usr/bin/env python3
"""Ensure the oracles reject corrupted captured outputs, not just exit-code failures."""
import json,pathlib,shutil,tempfile
from catalog import ROOT
from batch2_validate import validate,np
from run import evidence_directory,digest
runs=json.loads((ROOT/'migration/reports/batch2-rocm.json').read_text());checks=[]
for run in runs:
 source=run['source'];tensor=source.startswith('cuTENSOR/');case='small-nonzero' if tensor else 'original';record=next(c for c in run['runs'] if c['case']==case);original=evidence_directory(record['evidence']);kind=pathlib.PurePosixPath(source).parent.name
 for corrupt in (['finite-wrong-value','NaN'] if tensor else ['finite-wrong-value']):
  with tempfile.TemporaryDirectory(prefix='batch2-negative-',dir=ROOT/'build') as temporary:
   d=pathlib.Path(temporary)
   for p in original.iterdir():
    if p.suffix in {'.json','.log','.bin'} and p.is_file():shutil.copyfile(p,d/p.name)
   if tensor:
    p=d/'output.bin';v=np.fromfile(p,np.float32);v[0]=np.nan if corrupt=='NaN' else v[0]+1;v.tofile(p)
   else:
    buffer,count= ('result',1) if kind in ['amax','amin','spvv'] else ('A',1) if kind=='rotg' else ('A',4) if kind=='rotm' else ('param',5) if kind=='rotmg' else ('B_0',4) if kind=='trsmBatched' else ('C_0',4) if kind in ['gemmBatched','gemmGroupedBatched'] else ('hC_values_tmp',12) if kind in ['spgemm','spgemm_reuse'] else ('A',9) if kind=='Xgeqrf' else ('L',9)
    vals=[999.]*count
    if kind=='rotmg':vals=[1.,999.,6.,7.,999.]
    with (d/'run.log').open('a') as f:f.write('\n'+json.dumps({'observe':buffer,'values':vals})+'\n')
   try:rejected=validate(source,case,d)['status']=='FAILED'
   except ValueError:rejected=True
   checks.append({'source':source,'corruption':corrupt,'rejected':rejected})
report={'status':'PASSED' if all(c['rejected'] for c in checks) else 'FAILED','scope':'Actual captured outputs copied locally then corrupted; original evidence untouched; no GPU rerun.','checks':checks,'oracle_sources':{p:digest(ROOT/p) for p in ['tools/migration/batch2_validate.py','tools/migration/tensor_reference.py']}};(ROOT/'migration/reports/batch2-negative-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks),'corrupted outputs rejected');raise SystemExit(report['status']!='PASSED')
