#!/usr/bin/env python3
"""Independent CPU BLAS/LAPACK and contract checks for the first rewrite batch."""
import ctypes
import ctypes.util
import json
from pathlib import Path
import sys
from experiment import ROOT
sys.path.insert(0,str(ROOT/'build/python-reference'))
import numpy as np


def validate(kind,case,out,backend='rocm',inputs=None):
    src=Path(inputs) if inputs else out.parent/'inputs'
    c=json.loads((src/'config.json').read_text());checks=[]
    m,n,k,lda,ldb,ldc=[int(c[x]) for x in ['m','n','k','lda','ldb','ldc']]
    def gate(name,value,**kw):checks.append(dict(check=name,passed=bool(value),**kw))
    def read(name,dtype):return np.fromfile(src/(name+'.bin'),dtype)
    def result(name,dtype):return np.fromfile(out/(name+'.bin'),dtype)
    def near(name,actual,expected,rtol=1e-4,atol=2e-5):
        if actual.shape!=expected.shape:gate(name,False,actual_shape=list(actual.shape),expected_shape=list(expected.shape));return
        if np.iscomplexobj(actual) or np.iscomplexobj(expected):
            near(name+'-real',actual.real,expected.real,rtol,atol);near(name+'-imag',actual.imag,expected.imag,rtol,atol);return
        gate(name+'-nonfinite-pattern',np.array_equal(np.isnan(actual),np.isnan(expected)) and np.array_equal(np.isposinf(actual),np.isposinf(expected)) and np.array_equal(np.isneginf(actual),np.isneginf(expected)))
        mask=np.isfinite(expected);delta=np.abs(actual[mask]-expected[mask]);bound=atol+rtol*np.abs(expected[mask]);gate(name,np.all(np.isfinite(actual[mask])) and np.all(delta<=bound),max_abs=float(delta.max(initial=0)),atol=atol,rtol=rtol)
    if kind in ['gemm3m','herk3m','syrk3m']:
        opa,opb=int(c['opa']),int(c['opb']);ac=m if opa else k;bc=k if opb else n
        a=read('A',np.complex64).reshape(lda,ac,order='F');a=a[:k,:m].T if opa else a[:m,:k]
        if opa==2:a=a.conj()
        if kind=='gemm3m':
            b=read('B',np.complex64).reshape(ldb,bc,order='F');b=b[:n,:k].T if opb else b[:k,:n]
            if opb==2:b=b.conj()
        else:b=a.conj().T if kind=='herk3m' else a.T
        alpha=complex(c['alpha_r'],c['alpha_i']);beta=complex(c['beta_r'],c['beta_i']);expected=read('C',np.complex64).reshape(ldc,n,order='F').astype(np.complex128)
        prod=alpha*(a.astype(np.complex128)@b.astype(np.complex128))
        if beta!=0:
            old=expected[:m].copy()
            if kind=='herk3m':np.fill_diagonal(old,np.diag(old).real)
            prod+=beta*old
        if kind=='herk3m':np.fill_diagonal(prod,np.diag(prod).real)
        if c['triangle']:
            ii,jj=np.triu_indices(n) if c['triangle']==1 else np.tril_indices(n);expected[ii,jj]=prod[ii,jj]
        else:expected[:m]=prod
        actual=result('output',np.complex64).reshape(ldc,n,order='F');near('direct-complex-product',actual,expected)
        written=np.zeros((ldc,n),dtype=bool)
        if c['triangle']:written[ii,jj]=True
        else:written[:m]=True
        initial=read('C',np.complex64).reshape(ldc,n,order='F')
        gate('untouched-complex-storage-bit-exact',np.array_equal(actual[~written].view(np.uint8),initial[~written].view(np.uint8)))
        trace=result('trace',np.int32);gate('actual-real-SGEMM-count' if backend=='rocm' else 'native-CUDA-call-count',trace[0]==c['repeat']*(3 if backend=='rocm' else 1))
    elif kind=='planar':
        def unpack(name,rows,cols,ld):
            v=read(name,np.float16);return (v[ld*cols:].astype(np.float64)+1j*v[:ld*cols].astype(np.float64)).reshape(ld,cols,order='F')[:rows]
        a=unpack('A',m,k,lda);b=unpack('B',k,n,ldb);expected=read('C',np.float16).copy();z=(complex(c['alpha_r'],c['alpha_i']))*(a@b)
        if c['beta_r'] or c['beta_i']:z+=complex(c['beta_r'],c['beta_i'])*unpack('C',m,n,ldc)
        with np.errstate(over='ignore'):
            xr=z.real.astype(np.float16);xi=z.imag.astype(np.float16)
        for j in range(n):expected[j*ldc:j*ldc+m]=xi[:,j];expected[ldc*n+j*ldc:ldc*n+j*ldc+m]=xr[:,j]
        actual=result('output',np.float16);finite=np.isfinite(expected)
        def ordered(v):
            bits=v.view(np.uint16).astype(np.int32)
            return np.where(bits&0x8000,0x8000-(bits&0x7fff),0x8000+bits)
        distance=np.abs(ordered(actual[finite])-ordered(expected[finite]));delta=np.abs(actual[finite].astype(np.float64)-expected[finite].astype(np.float64))
        gate('finite-half-output-within-2ULP',actual.shape==expected.shape and np.all(np.isfinite(actual[finite])) and np.all(distance<=2),max_abs=float(delta.max(initial=0)),max_ulp=int(distance.max(initial=0)))
        active=np.zeros(actual.size,dtype=bool)
        for j in range(n):active[j*ldc:j*ldc+m]=True;active[ldc*n+j*ldc:ldc*n+j*ldc+m]=True
        initial=read('C',np.float16)
        gate('untouched-half-storage-bit-exact',np.array_equal(actual[~active].view(np.uint16),initial[~active].view(np.uint16)))
        gate('half-overflow-and-NaN-mask',np.array_equal(np.isposinf(actual),np.isposinf(expected)) and np.array_equal(np.isneginf(actual),np.isneginf(expected)) and np.array_equal(np.isnan(actual),np.isnan(expected)))
        if case in ['original','repeat']:gate('original-negative-plane-offset-and-overflow',m==n==k==16 and np.all(np.isposinf(actual)),plane_offset_bytes=-2*ldc*n)
    elif kind=='igemm':
        a=read('A',np.int8).reshape(lda,k,order='F');b=read('B',np.int8).reshape(ldb,n,order='F');initial=read('C',np.int32).reshape(ldc,n,order='F');expected=initial.astype(np.int64);expected[:m]=int(c['alpha_r'])*(a[:m].astype(np.int64)@b[:k].astype(np.int64))+(int(c['beta_r'])*initial[:m] if c['beta_r'] else 0)
        gate('int32-domain',np.all(expected>=-(2**31)) and np.all(expected<2**31));gate('integer-full-output-exact',np.array_equal(result('output',np.int32).reshape(ldc,n,order='F'),expected))
        if backend=='rocm':
            pa=result('packed_A',np.int8);pb=result('packed_B',np.int8);pc=result('packed_C',np.int32);ald=32*m;bld=32*((n+7)//8*8);cld=32*m
            gold=json.loads((ROOT/'migration/rewrite/native-col4-map.json').read_text())['map']
            ea=np.full(pa.size,85,dtype=np.int8);eb=np.full(pb.size,85,dtype=np.int8)
            for j in range(k):
                for i in range(m):ea[j//32*ald+i*32+j%32]=a[i,j]
                for i in range(n):eb[j//32*bld+i//8*256+gold[i%8+(j%32)*8]]=b[j,i]
            gate('COL32-all-bytes-and-guards',np.array_equal(pa,ea));gate('COL4-native-map-all-bytes-and-guards',np.array_equal(pb,eb));gate('packed-C-tail-guard',np.all(pc[-16:]==0x12345678))
            trace=result('trace',np.int32);gate('native-INT8-hipBLAS-calls',len(trace)>9 and trace[8]==c['repeat'] and trace[9]==0)
    elif kind=='lu':
        raw=read('A',np.complex64).reshape(lda,n,order='F');a=np.array(raw[:m],order='F',copy=True);piv=np.empty(min(m,n),np.int32);info=ctypes.c_int();mm=ctypes.c_int(m);nn=ctypes.c_int(n);ld=ctypes.c_int(m)
        lapack=ctypes.CDLL(ctypes.util.find_library('lapack'));lapack.cgetrf_(ctypes.byref(mm),ctypes.byref(nn),a.ctypes.data_as(ctypes.c_void_p),ctypes.byref(ld),piv.ctypes.data_as(ctypes.c_void_p),ctypes.byref(info))
        actual=result('output',np.complex64).reshape(lda,n,order='F');ip=result('pivots',np.int32);gate('independent-LAPACK-pivots-exact',np.array_equal(ip,piv));gate('independent-LAPACK-info',result('info',np.int32).tolist()==[info.value]);near('LAPACK-LU-factors',actual[:m],a)
        permuted=raw[:m].astype(np.complex128).copy()
        for j,pivot in enumerate(ip):permuted[[j,pivot-1]]=permuted[[pivot-1,j]]
        lower=np.tril(actual[:m,:min(m,n)],-1).astype(np.complex128)+np.eye(m,min(m,n));upper=np.triu(actual[:min(m,n)]).astype(np.complex128);near('P-A-equals-L-U',lower@upper,permuted)
        near('global-LDA-padding-preserved',actual[m:],raw[m:],0,0)
    elif kind=='posv':
        nrhs,batch=int(c['nrhs']),int(c['batch']);av=read('A',np.complex128).reshape(batch,lda*n);bv=read('B',np.complex128).reshape(batch,ldb*nrhs);fac=result('factor',np.complex128).reshape(batch,lda*n);solution=result('output',np.complex128).reshape(batch,ldb*nrhs);info=result('info',np.int32)
        for h in range(batch):
            aa=av[h].reshape(lda,n,order='F');bb=bv[h].reshape(ldb,nrhs,order='F');ff=fac[h].reshape(lda,n,order='F');xx=solution[h].reshape(ldb,nrhs,order='F');herm=np.tril(aa[:n],-1);herm=herm+herm.conj().T+np.diag(np.diag(aa[:n]).real)
            probe=np.array(aa[:n],order='F',copy=True);nn=ctypes.c_int(n);ld=ctypes.c_int(n);code=ctypes.c_int()
            ctypes.CDLL(ctypes.util.find_library('lapack')).zpotrf_(ctypes.c_char_p(b'L'),ctypes.byref(nn),probe.ctypes.data_as(ctypes.c_void_p),ctypes.byref(ld),ctypes.byref(code),ctypes.c_size_t(1))
            gate('independent-LAPACK-info-'+str(h),int(info[h])==code.value)
            ii,jj=np.triu_indices(n,1)
            gate('unused-upper-bit-exact-'+str(h),np.array_equal(ff[ii,jj].view(np.uint8),aa[ii,jj].view(np.uint8)))
            gate('A-padding-bit-exact-'+str(h),np.array_equal(ff[n:].ravel().view(np.uint8),aa[n:].ravel().view(np.uint8)))
            gate('B-padding-bit-exact-'+str(h),np.array_equal(xx[n:].ravel().view(np.uint8),bb[n:].ravel().view(np.uint8)))
            if code.value>0:
                gate('non-SPD-RHS-not-solved-'+str(h),np.array_equal(xx.ravel().view(np.uint8),bb.ravel().view(np.uint8)))
                continue
            ll=np.linalg.cholesky(herm)
            gate('SPD-info-zero-'+str(h),info[h]==0);lower=np.tril(ff[:n]);near('Cholesky-reconstruction-'+str(h),lower@lower.conj().T,herm,5e-12,2e-12);near('independent-factor-'+str(h),lower,ll,5e-12,2e-12);near('independent-solution-'+str(h),xx[:n],np.linalg.solve(herm,bb[:n]),5e-12,2e-12);near('A-X-equals-B-'+str(h),herm@xx[:n],bb[:n],5e-12,2e-12);ii,jj=np.triu_indices(n,1);near('unused-upper-'+str(h),ff[ii,jj],aa[ii,jj],0,0);near('A-padding-'+str(h),ff[n:],aa[n:],0,0);near('B-padding-'+str(h),xx[n:],bb[n:],0,0)
    else:
        a=read('A',np.float64).reshape(lda,n,order='F');b=read('B',np.float64).reshape(ldb,n,order='F');actual=result('output',np.float64).reshape(ldb,n,order='F');lower=np.tril(a[:n]);expected=np.linalg.solve(lower.T,b[:m].T).T;near('right-lower-TRSM',actual[:m],expected,5e-12,2e-12);near('X-L-equals-B',actual[:m]@lower,b[:m],5e-12,2e-12);near('B-padding',actual[m:],b[m:],0,0);near('A-unchanged',result('A_after',np.float64),a.ravel(order='F'),0,0)
    if kind in ['lu','posv','trsm'] and backend=='rocm':
        trace=result('trace',np.int32);gate('actual-device-calls',trace[0]==c['repeat']*(c['batch'] if kind=='posv' else 1));gate('actual-block-width',trace[1]==c['threads']);gate('actual-wave-width',trace[2] in [32,64]);gate('shared-padding-sentinel',trace[3]==1)
        if kind=='lu' and case in ['original','repeat']:gate('original-explicit-33-threads',trace[1]==33 and m==48 and n==32)
    return dict(status='PASSED' if checks and all(x['passed'] for x in checks) else 'FAILED',checks=checks,
                oracle='Independent CPU NumPy complex products/solves/Cholesky, system LAPACK cgetrf, int64 dot and native NVIDIA layout map')


if __name__=='__main__':
    import argparse
    from experiment import write
    p=argparse.ArgumentParser();p.add_argument('--kind',required=True);p.add_argument('--case',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--backend',default='rocm');a=p.parse_args()
    report=validate(a.kind,a.case,a.output,a.backend,a.input);write(a.report,report)
    print(json.dumps(report));raise SystemExit(0 if report['status']=='PASSED' else 1)
