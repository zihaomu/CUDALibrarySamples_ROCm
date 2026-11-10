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
 return dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,scope='FP64 CSR independent solve/residual; full stride/phase/query and real Fortran data roundtrip' if backend=='rocm' else 'native cuDSS compatible mathematical baseline, not native Fortran compiler')
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--report',required=True);p.add_argument('--backend',default='rocm');args=p.parse_args()
 try:r=validate(args.input,args.output,args.backend)
 except Exception as e:r=dict(status='FAILED',checks=[dict(check='complete-parse-and-reference',passed=False)],error=str(e))
 Path(args.report).write_text(json.dumps(r,indent=2)+'\n');print(r['status'],[c['check'] for c in r['checks'] if not c['passed']]);return int(r['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
