#!/usr/bin/env python3
"""Fault injection into captured outputs; every one of the 26 independent oracles must reject."""
import hashlib,json,pathlib,tempfile,shutil
from catalog import ROOT
from batches4_8_spec import GROUPS,kind
from batches4_8_reference import validate,np
from run import evidence_directory
rows=json.loads((ROOT/'migration/reports/batches4_8-validation.json').read_text());results=[]
for row in rows:
 k=kind(row['source']);choices={'elementwise_permute_padding':'small-strided','einsum':'non-square','contraction_trinary':'small-nonzero-beta','contraction_plan_cache':'changed-descriptor','Xtrtri':'lower'};case=choices.get(k,'original');original=evidence_directory(next(c['evidence'] for c in row['runs'] if c['case']==case));baseline=validate(row['source'],case,original);assert baseline['status']=='PASSED',(row['source'],baseline)
 for fault in ['finite','nan']:
  with tempfile.TemporaryDirectory(prefix='b4-b8-negative-',dir=ROOT/'build') as tmp:
   d=pathlib.Path(tmp)
   for p in original.iterdir():
    if p.is_file():(d/p.name).symlink_to(p.resolve())
   target=None
   if row['batch']=='b5':target=d/('output0.bin' if k=='einsum' else 'output.bin');dtype=np.float32
   elif row['batch']=='b7' and k.startswith('Lt'):target=d/'output_g0.bin';dtype=np.float16 if k=='LtHSHgemmGroupedSimple' else np.float32
   if target:
    data=target.read_bytes();target.unlink();target.write_bytes(data);a=np.memmap(target,dtype=dtype,mode='r+');a[0]=a[0]+100 if fault=='finite' else np.nan;a.flush();del a
   else:
    names={'GemmBatchedEx':'C_0','CherkEx':'C','CsyrkEx':'C','trttp':'AP','tpttr':'A','ormqr':'XC','spsv_sell':'Y','sddmm_bsr':'C','Xgetrf':'LU','Xsyevdx':'eigenvalues','Xtrtri':'inverse','Xgesvd':'S','GemmGroupedBatchedEx':'output_g0','GemmExAutoTuning':'output_g0','spmat_convert':'CSC_values','spgemm_mem':'C_values','spmv_symmetric_csr':'Z','spmvop_csr':'Z','spmm_csr_op':'C'};name=names[k];lines=[];changed=False
    for line in (d/'run.log').read_text().splitlines():
     if line.startswith('{"observe":'):
      x=json.loads(line)
      if x['observe']==name:
       # packed upper/lower matrices have first defined element at index zero.
       value=x['values'][0];value=value[0] if isinstance(value,list) else value
       replacement=value+100 if fault=='finite' else None
       if isinstance(x['values'][0],list):x['values'][0][0]=replacement
       else:x['values'][0]=replacement
       line=json.dumps(x,separators=(',',':'));changed=True
     lines.append(line)
    assert changed,name;file=d/'run.log';file.unlink();file.write_text('\n'.join(lines)+'\n')
   try:out=validate(row['source'],case,d);rejected=out['status']!='PASSED'
   except (ValueError,KeyError,TypeError,IndexError,AssertionError):rejected=True
   results.append(dict(source=row['source'],batch=row['batch'],case=case,fault=fault,rejected=bool(rejected)));assert rejected,(row['source'],fault)
 print(row['source'],'rejected finite/NaN',flush=True)
(ROOT/'migration/reports/batches4_8-negative.json').write_text(json.dumps(dict(status='PASSED',tests=results,oracles=len(rows),rejected=sum(x['rejected'] for x in results),generator_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
