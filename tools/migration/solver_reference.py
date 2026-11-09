#!/usr/bin/env python3
"""Independent phase-invariant checks shared by additional CUDA comparisons."""
from validate_blas import ROOT,np,literals,observed
from scipy.linalg import eigh

def validate(source,log):
 e,v=literals((ROOT/source).read_text());o=observed(log);kind=source.split('/')[1];n=int(e.get('n',e.get('m',0)));m=int(e.get('m',n));lda=int(e.get('lda',m));A=v['A'].reshape((lda,-1),order='F')[:m,:];checks=[]
 def check(name,actual,expected,tol=1e-10):
  actual=np.asarray(actual);expected=np.asarray(expected);error=float(np.linalg.norm(actual-expected));bound=tol*max(1,float(np.linalg.norm(expected)));checks.append({'check':name,'passed':bool(np.isfinite(actual).all() and error<=bound),'error':error,'bound':bound})
 if kind=='gesvd':
  U=o['U'].reshape((int(e['ldu']),m),order='F')[:m,:];VT=o['VT'].reshape((int(e['ldvt']),n),order='F')[:n,:];sv=o['S'];check('singular-values',sv,np.linalg.svd(A,compute_uv=False));check('reconstruction',U[:,:n]@np.diag(sv)@VT,A);check('U-orthogonality',U.T@U,np.eye(m));check('VT-orthogonality',VT@VT.T,np.eye(n))
 elif kind in {'syevd','syevj','Xsyevd','sygvd','sygvj'}:
  n=m;W=o['W'];V=o['V'].reshape((lda,n),order='F')[:n,:];A=A[:n,:n]
  if kind.startswith('syg'):
   B=v['B'].reshape((lda,n),order='F');check('eigenvalues',W,eigh(A,B,eigvals_only=True));check('residual',A@V,B@V@np.diag(W));check('B-orthogonality',V.T@B@V,np.eye(n))
  else:check('eigenvalues',W,np.linalg.eigvalsh(A));check('residual',A@V,V@np.diag(W));check('orthogonality',V.T@V,np.eye(n))
 elif kind=='Xgeqrf':
  packed=o['A'].reshape((lda,n),order='F')[:m,:];tau=o['tau'];Q=np.eye(m)
  for j,t in enumerate(tau):
   u=np.zeros(m);u[j]=1;u[j+1:]=packed[j+1:,j];Q=Q@(np.eye(m)-t*np.outer(u,u))
  R=np.triu(packed);check('QR-reconstruction',Q@R,A);check('Q-orthogonality',Q.T@Q,np.eye(m))
 elif kind=='Xpotrf':
  L=np.tril(o['L'].reshape((lda,n),order='F')[:m,:]);X=o['X'].reshape((n,-1),order='F');B=v['B'].reshape((m,-1),order='F');check('Cholesky-reconstruction',L@L.T,A);check('solve-residual',A@X,B)
 elif kind=='orgqr':
  Q=o['Q'].reshape((lda,n),order='F')[:m,:];check('orthogonality',Q.T@Q,np.eye(n));R=Q.T@A;check('QR-reconstruction',Q@R,A);check('R-upper',np.tril(R,-1),np.zeros_like(R))
 elif kind=='gesvdj':
  sv=o['S'];U=o['U'].reshape((int(e['ldu']),-1),order='F')[:m,:];V=o['V'].reshape((int(e['ldv']),-1),order='F')[:n,:];check('singular-values',np.sort(sv),np.sort(np.linalg.svd(A,compute_uv=False)));check('reconstruction',U[:,:n]@np.diag(sv)@V.T,A);check('U-orthogonality',U[:,:n].T@U[:,:n],np.eye(n));check('V-orthogonality',V.T@V,np.eye(n))
 else:raise ValueError('No independent oracle for '+kind)
 return checks,o
