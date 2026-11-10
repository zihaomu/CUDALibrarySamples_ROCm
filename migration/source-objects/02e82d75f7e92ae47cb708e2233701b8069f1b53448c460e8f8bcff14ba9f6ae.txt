#!/usr/bin/env python3
"""Independent FP64 SVD, low-rank optimality, strides and reported residual checks."""
import argparse,json,sys
from pathlib import Path
from experiment import ROOT,write
sys.path.insert(0,str(ROOT/'build/python-reference'));import numpy as np

def validate(inputs,out):
 c=json.loads((inputs/'config.json').read_text());m,n,rank,batch,lda,ldu,ldv,sa,ss,su,sv=[c[k] for k in ['m','n','rank','batch','lda','ldu','ldv','strideA','strideS','strideU','strideV']];checks=[]
 def gate(name,value,**fields):checks.append(dict(check=name,passed=bool(value),**fields))
 for name,size in [('S',batch*ss*4),('U',batch*su*4),('V',batch*sv*4),('RnrmF',batch*8),('info',batch*4),('A_after',batch*sa*4)]:gate(name+'-exact-output-bytes',(out/(name+'.bin')).is_file() and (out/(name+'.bin')).stat().st_size==size,expected_bytes=size)
 if (out/'RnrmF_native.bin').exists():gate('native-norm-exact-output-bytes',(out/'RnrmF_native.bin').stat().st_size==batch*8)
 if not all(c['passed'] for c in checks):return dict(status='FAILED',checks=checks,oracle='Exact whole-file output sizes before numerical parsing')
 a=np.fromfile(inputs/'A.bin',np.float32);after=np.fromfile(out/'A_after.bin',np.float32);s=np.fromfile(out/'S.bin',np.float32);u=np.fromfile(out/'U.bin',np.float32);v=np.fromfile(out/'V.bin',np.float32);norm=np.fromfile(out/'RnrmF.bin',np.float64);info=np.fromfile(out/'info.bin',np.int32)
 for name,array in [('S',s),('U',u),('V',v),('RnrmF',norm),('A_after',after)]:gate(name+'-whole-output-finite',np.isfinite(array).all())
 gate('reported-residual-nonnegative',np.all(norm>=0))
 gate('all-batches-info-zero',info.tolist()==[0]*batch);gate('input-global-padding-untouched',np.array_equal(a.view(np.uint32),after.view(np.uint32)))
 for h in range(batch):
  aa=a[h*sa:h*sa+lda*n].reshape(lda,n,order='F')[:m].astype(np.float64);singular=s[h*ss:h*ss+rank].astype(np.float64);uu=u[h*su:h*su+ldu*rank].reshape(ldu,rank,order='F')[:m].astype(np.float64);vv=v[h*sv:h*sv+ldv*rank].reshape(ldv,rank,order='F')[:n].astype(np.float64);gold=np.linalg.svd(aa,compute_uv=False);reconstruction=(uu*singular)@vv.T;actual_res=float(np.linalg.norm(aa-reconstruction));optimal=float(np.linalg.norm(gold[rank:]));bound=5e-4*max(1,float(np.linalg.norm(aa)))
  gate('singular-values-'+str(h),np.allclose(singular,gold[:rank],atol=2e-5,rtol=3e-4),max_abs=float(np.max(np.abs(singular-gold[:rank]))));gate('descending-nonnegative-'+str(h),np.all(np.diff(singular)<=0) and np.all(singular>=0));gate('U-orthonormal-'+str(h),np.allclose(uu.T@uu,np.eye(rank),atol=5e-4,rtol=0));gate('V-orthonormal-'+str(h),np.allclose(vv.T@vv,np.eye(rank),atol=5e-4,rtol=0));gate('rank-approximation-optimal-'+str(h),abs(actual_res-optimal)<=bound,actual=actual_res,optimal=optimal,bound=bound);gate('reported-GPU-Frobenius-norm-'+str(h),np.isfinite(norm[h]) and abs(norm[h]-actual_res)<=2e-8*max(1,actual_res),actual=float(norm[h]),expected=actual_res)
  if (out/'RnrmF_native.bin').exists():
   estimate=np.fromfile(out/'RnrmF_native.bin',np.float64)[h];gate('native-approximate-norm-FP32-backward-error-'+str(h),np.isfinite(estimate) and estimate>=0 and abs(estimate-actual_res)<=bound,reported=float(estimate),observed_residual=actual_res,bound=bound)
  for name,array,stride,ld,rows in [('S',s,ss,rank,rank),('U',u,su,ldu,m),('V',v,sv,ldv,n)]:
   mask=np.zeros(stride,dtype=bool)
   if name=='S':mask[:rank]=True
   else:
    for j in range(rank):mask[j*ld:j*ld+rows]=True
   gate(name+'-stride-padding-exact-'+str(h),np.all(array[h*stride:(h+1)*stride][~mask].view(np.uint32)==np.array([-97],np.float32).view(np.uint32)[0]))
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,oracle='Independent NumPy FP64 SVD, orthogonality, Eckart-Young tail norm and direct FP64 residual from returned U/S/V')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();r=validate(a.input,a.output);write(a.report,r);print(json.dumps(r));raise SystemExit(r['status']!='PASSED')
