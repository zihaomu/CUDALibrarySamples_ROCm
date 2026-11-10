"""Independent global reconstruction of multi-device factors, FFT layouts and contractions."""
import json,hashlib
from validate_blas import np
from batches12_15_spec import kind,model

def validate(source,case,d):
 k=kind(source);checks=[];inputs={};metas=[];outputs={}
 def gate(n,v,**kw):checks.append(dict(check=n,passed=bool(v),**kw))
 def read(rank,name,dtype=np.float64):return np.fromfile(d/f'r{rank}_{name}.bin',dtype)
 def near(n,a,b,tol=2e-10):
  delta=np.abs(a-b);gate(n,a.shape==b.shape and np.isfinite(a).all() and np.all(delta<=tol*np.maximum(1,np.abs(b))),max_abs=float(delta.max(initial=0)))
 for rank in range(2):
  meta=json.loads((d/f'rank{rank}.json').read_text());metas.append(meta);gate('rank-device-'+str(rank),meta['rank']==meta['device']==rank and meta['size']==2)
  cfg=read(rank,'config',np.int32).tolist();inputs[str(rank)]={'config':cfg}
  if k in ['mp_lu','mg_lu','mp_chol','mg_chol']:
   n,nrhs,block,chol,repeat,actual,mg,descriptorA,descriptorB=cfg;cols=read(rank,'columns',np.int32);a=read(rank,'A_local').reshape(n,len(cols),order='F');factor=read(rank,'factor_local').reshape(n,len(cols),order='F');b=read(rank,'rhs').reshape(n,nrhs,order='F');x=read(rank,'solution').reshape(n,nrhs,order='F');piv=read(rank,'pivots',np.int32);info=read(rank,'info',np.int32);inputs[str(rank)].update(A=hashlib.sha256(a.tobytes()).hexdigest(),rhs=hashlib.sha256(b.tobytes()).hexdigest());gate('actual-owned-factor-columns-'+str(rank),np.all(cols//block%2==rank) and actual==repeat*len(cols));gate('actual-GPU-factorization-'+str(rank),meta['broadcast']>0 and meta['kernels']>n and meta['allreduce']==1)
   if rank==0:A=np.zeros((n,n));F=np.zeros((n,n));X=x;P=piv;B=b;I=info
   A[:,cols]=a;F[:,cols]=factor
   near('replicated-solve-consistency-'+str(rank),x,X)
  elif k=='mp_fft':
   nx,ny,nz,xc,x0,yc,y0,repeat,ffts,sends,recvs=cfg;
   if case=='original':gate('original-16-cubed-FFT',nx==ny==nz==16)
   v=read(rank,'input',np.complex64).reshape(xc,ny,nz);out=read(rank,'output',np.complex64).reshape(xc,ny,nz);f=read(rank,'frequency_y_slab',np.complex64).reshape(yc,nz,nx);inputs[str(rank)]['input']=hashlib.sha256(v.tobytes()).hexdigest();gate('native-FFT-and-GPU-transpose-'+str(rank),ffts==4*repeat and sends==recvs==4*repeat and meta['kernels']>=9*repeat);near('inverse-full-slab-'+str(rank),out,v,3e-6)
   if rank==0:full=np.empty((nx,ny,nz),np.complex64);freq=np.empty((nx,ny,nz),np.complex64)
   full[x0:x0+xc]=v;freq[:,y0:y0+yc,:]=f.transpose(2,0,1)
  else:
   n,block,count,start,rows,repeat=cfg;a=read(rank,'A_local',np.float32).reshape(rows,n,order='F');b=read(rank,'B_local',np.float32).reshape(count,n,order='F');o=read(rank,'output',np.float32).reshape(rows,n,order='F');inputs[str(rank)].update(A=hashlib.sha256(a.tobytes()).hexdigest(),B=hashlib.sha256(b.tobytes()).hexdigest());gate('native-partition-GEMM-'+str(rank),meta['blas']==repeat and meta['allgather']==1)
   if rank==0:A=np.empty((n,n),np.float32);B=np.empty((n,n),np.float32);C=np.empty((n,n),np.float32)
   A[start:start+rows]=a;B[start:start+rows]=b[:rows];C[start:start+rows]=o
 gate('two-real-GPU-PCI-devices',len({m['pci'] for m in metas})==2);gate('original-process-model',len({m['pid'] for m in metas})==(1 if model(source)=='threads' else 2))
 if k in ['mp_lu','mg_lu','mp_chol','mg_chol']:
  if case=='singular-or-empty':gate('singular-or-nonSPD-info',I[0]>0)
  else:
   gate('success-info',I[0]==0);near('global-residual',A@X,B);near('independent-CPU-solve',X,np.linalg.solve(A,B))
   if chol:L=np.tril(F);near('global-Cholesky-reconstruction',L@L.T,A)
   else:
    perm=np.arange(n)
    for i,j in enumerate(P):perm[i],perm[j]=perm[j],perm[i]
    L=np.tril(F,-1)+np.eye(n);U=np.triu(F);near('global-pivoted-LU',L@U,A[perm])
  if case=='original':
   gate('original-scale',n==(611 if k=='mg_lu' else 8 if k=='mg_chol' else 10))
   expected=np.diag(np.full(n,2.))+np.diag(np.full(n-1,-1.),1)+np.diag(np.full(n-1,-1.),-1);expected=expected if chol else expected[::-1];near('original-laplacian-class',A,expected,0)
   if k=='mg_lu':gate('original-Mg-input-tile256',block==256 and descriptorA==256 and descriptorB==100)
 elif k=='mp_fft':near('global-frequency-layout',freq,np.fft.fftn(full),3e-5)
 else:
  near('full-contraction-output',C,A.astype(np.float64)@B.astype(np.float64),8e-5)
  if case=='original':gate('original-4096-block2048',n==4096 and block==2048)
 return dict(status='PASSED' if all(x['passed'] for x in checks) else 'FAILED',checks=checks,input_sha256=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),output_values=outputs,oracle='Independent NumPy full residual/factor reconstruction, FFT frequency and inverse slab layouts, FP64 full contraction; process model and actual two-device work/communication')
