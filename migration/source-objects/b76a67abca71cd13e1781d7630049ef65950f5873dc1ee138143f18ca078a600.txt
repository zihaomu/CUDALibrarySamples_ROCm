#!/usr/bin/env python3
"""Independent FP64 CSR reconstruction/solve and actual Fortran readback checks."""
import argparse,json
from pathlib import Path
import numpy as np
from qualification_common import fixture
def validate(src,out,backend='rocm'):
 src=Path(src);out=Path(out);mf=fixture(src,kind='sparse-binding');checks=[]
 def check(name,value):checks.append(dict(check=name,passed=bool(value)))
 def read(root,name,dtype,count):
  p=root/name;dt=np.dtype(dtype)
  if p.stat().st_size!=count*dt.itemsize:raise ValueError('whole file byte count: '+name)
  return np.fromfile(p,dtype=dt)
 for s in mf['systems']:
  label=s['label'];n=s['n'];nnz=s['nnz'];nrhs=s['nrhs'];ldb=s['ldb'];ldx=s['ldx'];base=s['base'];typ=s['mtype']
  rows=read(src,label+'_rows.bin','<i4',n+1)-base;cols=read(src,label+'_columns.bin','<i4',nnz)-base;vals=read(src,label+'_values.bin','<f8',nnz);b=read(src,label+'_B.bin','<f8',nrhs*ldb).reshape(nrhs,ldb);initial=read(src,label+'_X.bin','<f8',nrhs*ldx).reshape(nrhs,ldx)
  a=np.zeros((n,n),dtype=np.float64)
  for i in range(n):
   for p in range(rows[i],rows[i+1]):
    j=cols[p];a[i,j]=vals[p]
    if typ and i!=j:a[j,i]=vals[p]
  check(label+'/descriptor',np.array_equal(read(out,label+'_dimensions.bin','<i4',7),[n,nnz,nrhs,ldb,ldx,base,typ]));info=read(out,label+'_info.bin','<i4',1)[0];x=read(out,label+'_solution.bin','<f8',nrhs*ldx).reshape(nrhs,ldx);perm=read(out,label+'_permutation.bin','<i4',n);cp=read(out,label+'_column_permutation.bin','<i4',n)
  check(label+'/permutation-bijection',sorted(perm)==list(range(n)) and sorted(cp)==list(range(n)));check(label+'/B-unchanged',np.array_equal(read(out,label+'_B_after.bin','<f8',nrhs*ldb).reshape(nrhs,ldb),b));check(label+'/padding-unchanged',np.array_equal(x[:,n:],initial[:,n:]));check(label+'/X-finite',np.isfinite(x).all())
  singular=np.linalg.matrix_rank(a)<n
  check(label+'/info-propagation',(info>0) if singular else info==0)
  phase=read(out,label+'_phase.bin','<i4',3 if singular else 4);check(label+'/phase-order',np.array_equal(phase,[0,1,2] if singular else [0,1,2,3]))
  if not singular:
   reference=np.linalg.solve(a,b[:,:n].T).T
   check(label+'/independent-solve',np.allclose(x[:,:n],reference,atol=2e-11,rtol=2e-11))
   for j in range(nrhs):
    residual=np.linalg.norm(a@x[j,:n]-b[j,:n])/(np.linalg.norm(a)*np.linalg.norm(x[j,:n])+np.linalg.norm(b[j,:n]));check(label+'/relative-residual-'+str(j),np.isfinite(residual) and residual<1e-12)
   if backend=='rocm' and mf['profile']=='residual':
    actual=read(out,label+'_fortran_residual.bin','<f8',nrhs+1);expected=np.array([np.linalg.norm(a@x[j,:n]-b[j,:n])/(np.linalg.norm(a)*np.linalg.norm(x[j,:n])+np.linalg.norm(b[j,:n])) for j in range(nrhs)]);check(label+'/actual-Fortran-residual',np.isfinite(actual).all() and np.allclose(actual[:-1],expected,atol=5e-17,rtol=1e-10) and actual[-1]==np.max(actual[:-1]) and actual[-1]<=1e-12)
  else:check(label+'/singular-keeps-X',np.array_equal(x,initial))
  if backend=='rocm':
   check(label+'/actual-Fortran-X',np.array_equal(read(out,label+'_fortran_X.bin','<f8',nrhs*ldx).reshape(nrhs,ldx),x));check(label+'/Fortran-kind-size_t',read(out,label+'_fortran_query_bytes.bin','<u8',1)[0]==n*4);q=read(out,label+'_fortran_permutation.bin','<i4',2*n);check(label+'/Fortran-index-base',np.array_equal(q,np.r_[perm+base,cp+base]))
   # Factor reconstruction independently verifies that the queried P was used.
   frpath=out/(label+'_factor_rows.bin');fr=np.fromfile(frpath,dtype='<i4');check(label+'/factor-row-bytes',frpath.stat().st_size==(n+1)*4);fcpath=out/(label+'_factor_columns.bin');fvpath=out/(label+'_factor_values.bin');count=int(fr[-1]);check(label+'/factor-array-bytes',fcpath.stat().st_size==count*4 and fvpath.stat().st_size==count*8);fc=read(out,label+'_factor_columns.bin','<i4',count);fv=read(out,label+'_factor_values.bin','<f8',count);piv=read(out,label+'_factor_pivots.bin','<i4',n);check(label+'/pivot-bijection',sorted(piv)==list(range(n)))
   if not singular:
    packed=np.zeros((n,n))
    for i in range(n):packed[i,fc[fr[i]:fr[i+1]]]=fv[fr[i]:fr[i+1]]
    lu=packed[piv];lower=np.tril(lu,-1)+np.eye(n);upper=np.triu(lu);permuted=a[np.ix_(perm,cp)];check(label+'/queried-permutation-actually-factored',np.allclose(lower@upper,permuted[piv],atol=1e-11,rtol=1e-11))
  if singular:break # Both actual language entries stop after the first numerical failure.
 if mf['profile']=='uniform_batch' and mf['case']!='singular-info':
  s=mf['systems'][1];n=s['n'];nrhs=s['nrhs'];ldx=s['ldx'];ldb=s['ldb'];nnz=s['nnz'];base=s['base'];rows=read(src,'b1_rows.bin','<i4',n+1)-base;cols=read(src,'b1_columns.bin','<i4',nnz)-base;v=read(src,'b1_values.bin','<f8',nnz);b=read(src,'b1_B.bin','<f8',nrhs*ldb).reshape(nrhs,ldb);a=np.zeros((n,n))
  for i in range(n):
   for p in range(rows[i],rows[i+1]):
    j=cols[p];a[i,j]=v[p]
    if s['mtype'] and i!=j:a[j,i]=v[p]
  prefix='selected' if backend=='rocm' else 'uniform_selected';selected=read(out,prefix+'_solution.bin','<f8',nrhs*ldx).reshape(nrhs,ldx);check('uniform/selected-index-one-numerical-solve',np.isfinite(selected).all() and np.allclose(selected[:,:n],np.linalg.solve(a,b[:,:n].T).T,atol=2e-11,rtol=2e-11));final=read(out,'uniform_final_X.bin','<f8',2*nrhs*ldx).reshape(2,nrhs,ldx);before0=read(out,'b0_solution.bin','<f8',nrhs*ldx).reshape(nrhs,ldx);before1=read(out,'b1_solution.bin','<f8',nrhs*ldx).reshape(nrhs,ldx);check('uniform/selected-destination-slot-zero',np.array_equal(final[0],selected));check('uniform/other-output-slot-preserved',np.array_equal(final[1],before1));check('uniform/selected-output-padding',np.array_equal(selected[:,n:],before0[:,n:]));check('uniform/selection-descriptor',np.array_equal(read(out,'selection.bin' if backend=='rocm' else 'uniform_selection.bin','<i4',3),[1,0,2]))
  if backend=='cuda':
   initial_uniform=read(out,'uniform_initial_X.bin','<f8',2*nrhs*ldx).reshape(2,nrhs,ldx);check('uniform/native-full-batch-initial-solve',np.allclose(initial_uniform[0,:,:n],before0[:,:n],atol=2e-11,rtol=2e-11) and np.allclose(initial_uniform[1,:,:n],before1[:,:n],atol=2e-11,rtol=2e-11));checks=[c for c in checks if c['check']!='uniform/other-output-slot-preserved'];check('uniform/other-output-slot-preserved',np.array_equal(final[1],initial_uniform[1]))
   expected_b=np.concatenate([read(src,'b'+str(i)+'_B.bin','<f8',nrhs*ldb) for i in range(2)]);expected_v=np.concatenate([read(src,'b'+str(i)+'_values.bin','<f8',nnz) for i in range(2)])
   for stage in ['initial','selected']:
    check('uniform/native-'+stage+'-RHS-unchanged',np.array_equal(read(out,'uniform_'+stage+'_B_after.bin','<f8',2*nrhs*ldb),expected_b));check('uniform/native-'+stage+'-matrix-values-unchanged',np.array_equal(read(out,'uniform_'+stage+'_values_after.bin','<f8',2*nnz),expected_v))
   for slot in range(2):
    frozen_x=read(src,'b'+str(slot)+'_X.bin','<f8',nrhs*ldx).reshape(nrhs,ldx);check('uniform/native-initial-padding-'+str(slot),np.array_equal(initial_uniform[slot,:,n:],frozen_x[:,n:]));check('uniform/native-final-padding-'+str(slot),np.array_equal(final[slot,:,n:],frozen_x[:,n:]))
  if backend=='rocm':
   check('uniform/actual-Fortran-selected-X',np.array_equal(read(out,'selected_fortran_X.bin','<f8',nrhs*ldx).reshape(nrhs,ldx),selected));check('uniform/selected-refactor-phase',np.array_equal(read(out,'selected_phase.bin','<i4',7),[0,1,2,3,4,2,3]));check('uniform/selected-RHS-pointer',np.array_equal(read(out,'selected_B_after.bin','<f8',nrhs*ldb).reshape(nrhs,ldb),b));check('uniform/selected-output-initial-slot-zero',np.array_equal(read(out,'selected_X_initial.bin','<f8',nrhs*ldx).reshape(nrhs,ldx),before0))
   stores=[read(out,'b'+str(i)+'_factor_storage.bin','<u8',3) for i in range(2)];check('uniform/distinct-resident-GPU-factors',stores[0][0]>0 and stores[1][0]>0 and stores[0][0]!=stores[1][0] and stores[0][1]!=stores[1][1]);check('uniform/selected-GPU-factor-storage-reused',np.array_equal(read(out,'selected_factor_storage.bin','<u8',3),stores[1]) and np.array_equal(read(out,'retained_b1_factor_storage.bin','<u8',3),stores[1]))
   for name in ['factor_storage','factor_rows','factor_columns','factor_values','factor_pivots','phase']:
    check('uniform/unselected-factor-preserved/'+name,(out/('b0_'+name+'.bin')).read_bytes()==(out/('retained_b0_'+name+'.bin')).read_bytes())
  else:check('uniform/native-selected-status',np.array_equal(read(out,'uniform_native_info.bin','<i4',2),[0,0]))
 return dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,scope='FP64 CSR independent solve/residual; full stride/phase/query and real Fortran data roundtrip' if backend=='rocm' else 'native cuDSS compatible mathematical baseline, not native Fortran compiler')
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);p.add_argument('--backend',default='rocm');args=p.parse_args()
 try:r=validate(args.input,args.output,args.backend)
 except Exception as e:r=dict(status='FAILED',checks=[dict(check='complete-parse-and-reference',passed=False)],error=str(e))
 Path(args.report).write_text(json.dumps(r,indent=2)+'\n');print(r['status'],[c['check'] for c in r['checks'] if not c['passed']]);return int(r['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
