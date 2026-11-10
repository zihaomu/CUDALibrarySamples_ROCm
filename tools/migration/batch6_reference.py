"""Independent LU/eigen/SVD/triangular residuals, 64-bit pivots and info semantics."""
import hashlib,json
from validate_blas import np,observed
from batches4_8_spec import kind
from batch4_reference import serial
from scipy.linalg import solve_triangular

def validate(source,case,d):
 o=observed(d/'run.log');k=kind(source);checks=[];outputs={}
 def gate(name,v,**kw):checks.append(dict(check=name,passed=bool(v),**kw))
 def check(name,a,b,tol=1e-10):
  a,b=np.asarray(a),np.asarray(b);error=float(np.linalg.norm(a-b)) if a.shape==b.shape else float('inf');bound=tol*max(1,float(np.linalg.norm(b)));gate(name,np.isfinite(a).all() and error<=bound,error=error,bound=bound)
 def output(name,a):outputs[name]=serial(a)
 if k=='Xgetrf':
  A=o['input_A'].reshape(3,3,order='F');LU=o['LU'].reshape(3,3,order='F');p=o['pivots'].astype(np.int64)-1;P=np.eye(3)
  for i,j in enumerate(p):gate('pivot-range-'+str(i),i<=j<3);P[[i,j]]=P[[j,i]]
  check('PA-LU',P@A,(np.tril(LU,-1)+np.eye(3))@np.triu(LU));gate('singular-info',o['factor_info'][0]>0 if case=='singular-info' else o['factor_info'][0]==0)
  if case!='singular-info':check('solve-residual',A@o['X'],o['input_B']);check('independent-solve',o['X'],np.linalg.solve(A,o['input_B']));output('X',o['X'])
  gate('selected-policy',o['input_legacy'][0]==(case=='legacy-algorithm') and o['input_pivot'][0]==(case!='no-pivot'))
 elif k=='Xtrtri':
  n=int(o['input_n'][0]);lda=int(o['input_lda'][0]);upper=bool(o['input_upper'][0]);unit=bool(o['input_unit'][0]);initial=o['input_A'].reshape(lda,n,order='F');A=initial[:n].copy()
  if unit:np.fill_diagonal(A,1)
  gate('original-profile',case!='original' or n==1000 and lda==1001)
  gate('singular-info',o['factor_info'][0]==4 if case=='singular-info' else o['factor_info'][0]==0)
  if case!='singular-info':
   result=o['inverse'].reshape(lda,n,order='F');ids=np.triu_indices(n) if upper else np.tril_indices(n);inv=np.zeros((n,n));inv[ids]=result[:n][ids]
   if unit:np.fill_diagonal(inv,1)
   check('triangular-inverse',inv,solve_triangular(A,np.eye(n),lower=not upper,unit_diagonal=unit));check('inverse-residual',A@inv,np.eye(n));check('lda-padding',result[n:],initial[n:],0)
   output('inverse',inv.ravel()[::max(1,n*n//1000)])
 elif k=='Xsyevdx':
  A=o['input_A'].reshape(3,3,order='F');W=o['eigenvalues'];V=o['vectors'].reshape(3,-1,order='F');expected=np.linalg.eigvalsh(A)
  if o['input_value_range'][0]:expected=expected[(expected>o['input_vl'][0])&(expected<=o['input_vu'][0])]
  gate('info',o['factor_info'][0]==0);gate('meig',o['meig'][0]==len(expected));check('spectrum',W,expected);check('eigenpair-residual',A@V,V*W);check('orthogonality',V.T@V,np.eye(len(W)));output('eigenvalues',W)
 elif k=='Xgesvd':
  m=int(o['input_m'][0]);n=int(o['input_n'][0]);A=o['input_A'].reshape(m,n,order='F');U=o['U'].reshape(m,m,order='F');VT=o['VT'].reshape(n,n,order='F');S=o['S'];gate('info',o['factor_info'][0]==0);check('spectrum',S,np.linalg.svd(A,compute_uv=False));check('SVD-reconstruction',(U[:,:n]*S)@VT,A);check('U-orthogonal',U.T@U,np.eye(m));check('VT-orthogonal',VT@VT.T,np.eye(n));output('spectrum',S)
 else:raise ValueError(k)
 identity=hashlib.sha256(json.dumps({n:serial(v) for n,v in o.items() if n.startswith('input_')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,input_sha256=identity,output_values=outputs,oracle='Independent NumPy/SciPy factors, singular info and phase-invariant full reconstruction')
