#!/usr/bin/env python3
"""Reject lost cache/search/budget/symmetry/custom-operator execution semantics."""
import json,pathlib,tempfile,hashlib
from catalog import ROOT
from run import evidence_directory,digest
from batches4_8_reference import validate,np
from validate_blas import observed
rows=json.loads((ROOT/'migration/reports/batches4_8-validation.json').read_text());tests=[]
scenarios=[('contraction_plan_cache','changed-descriptor','run.log','cache_read_status',[0]),('contraction_plan_cache','changed-descriptor','run.log','cache_candidate_runs',[0]),('contraction_plan_cache','changed-descriptor','replay.log','cache_read_status',[3]),('LtSgemmCustomFind','limited-workspace','run.log','candidate_workspace_g0_0',[1]),('spgemm_mem','small-budget','run.log','numeric_chunks',[1]),('spmv_symmetric_csr','original','run.log','bridge_values',None),('spmvop_csr','original','run.log','Z',None),('spmm_csr_op','original','run.log','C',None)]
for substring,case,log,key,value in scenarios:
 row=next(r for r in rows if substring in r['source']);origin=evidence_directory(next(c['evidence'] for c in row['runs'] if c['case']==case));o=observed(origin/'run.log')
 if value is None:
  if key=='bridge_values':value=o[key].copy();value[0]*=2;value=value.tolist()
  else:
   A=np.zeros((4,4));r=o['input_offsets'].astype(int);c=o['input_columns'].astype(int)
   for i in range(4):A[i,c[r[i]:r[i+1]]]=o['input_values'][r[i]:r[i+1]]
   value=(A@o['input_X']+3*o['input_Y']).tolist() if key=='Z' else (A@o['input_B'].reshape(4,3)).ravel().tolist()
 with tempfile.TemporaryDirectory(prefix='b4-b8-semantic-',dir=ROOT/'build') as tmp:
  d=pathlib.Path(tmp)
  for p in origin.iterdir():
   if p.is_file():(d/p.name).symlink_to(p.resolve())
  lines=[];changed=False
  for line in (d/log).read_text().splitlines():
   if line.startswith('{"observe":'):
    item=json.loads(line)
    if item['observe']==key:item['values']=value;line=json.dumps(item,separators=(',',':'));changed=True
   lines.append(line)
  assert changed,key;(d/log).unlink();(d/log).write_text('\n'.join(lines)+'\n')
  try:rejected=validate(row['source'],case,d)['status']=='FAILED'
  except (ValueError,KeyError,IndexError):rejected=True
  assert rejected,(substring,key);tests.append(dict(source=row['source'],case=case,fault=log+':'+key,rejected=bool(rejected)))
(ROOT/'migration/reports/batches4_8-semantic-negative.json').write_text(json.dumps(dict(status='PASSED',tests=tests,generator_sha256=digest(pathlib.Path(__file__))),indent=2)+'\n');print('Rejected semantic faults',len(tests))
