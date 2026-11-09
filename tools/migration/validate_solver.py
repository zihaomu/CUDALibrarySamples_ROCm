#!/usr/bin/env python3
"""Finite residual/orthogonality checks against independent NumPy/SciPy references."""
import collections,fcntl,json
from validate_blas import ROOT,np,literals,observed
from scipy.linalg import eigh
from run import digest
results=[]
with (ROOT/'migration/.state.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
 for s in cat['samples']:
  if s['family']!='cuSOLVER':continue
  a=s.get('original_port',{})
  if a.get('return_code')!=0 or not a.get('qualified_physical_devices'):continue
  if digest(ROOT/a['implementation'])!=a['implementation_sha256']:continue
  r={'id':s['id'],'status':'PENDING','evidence':a['evidence'],'checks':[]}
  try:
   src=(ROOT/s['source']).read_text();e,v=literals(src);o=observed(ROOT/a['evidence']/'run.log');kind=s['source'].split('/')[1];n=int(e.get('n',e.get('m',0)));m=int(e.get('m',n));lda=int(e.get('lda',m));A=v['A'].reshape((lda,-1),order='F')[:m,:];checks=[]
   def check(name,actual,expected,tol=1e-10):
    actual=np.asarray(actual);expected=np.asarray(expected);error=float(np.linalg.norm(actual-expected));bound=tol*max(1,float(np.linalg.norm(expected)));checks.append({'check':name,'passed':bool(np.all(np.isfinite(actual)) and error<=bound),'error_frobenius':error,'bound':bound})
   if kind=='gesvd':
    U=o['U'].reshape((int(e['ldu']),m),order='F')[:m,:];VT=o['VT'].reshape((int(e['ldvt']),n),order='F')[:n,:];sv=o['S'];check('singular-values-cpu',sv,np.linalg.svd(A,compute_uv=False));check('reconstruction',U[:,:n]@np.diag(sv)@VT,A);check('U-orthogonality',U.T@U,np.eye(m));check('VT-orthogonality',VT@VT.T,np.eye(n))
   elif kind in {'syevd','syevj','Xsyevd','sygvd','sygvj'}:
    n=m;W=o['W'];V=o['V'].reshape((lda,n),order='F')[:n,:];A=A[:n,:n]
    if kind.startswith('syg'):
     B=v['B'].reshape((lda,n),order='F');ref=eigh(A,B,eigvals_only=True);check('eigenvalues-cpu',W,ref);check('generalized-eigen-residual',A@V,B@V@np.diag(W));check('B-orthogonality',V.T@B@V,np.eye(n))
    else:
     check('eigenvalues-cpu',W,np.linalg.eigvalsh(A));check('eigen-residual',A@V,V@np.diag(W));check('orthogonality',V.T@V,np.eye(n))
   elif kind=='orgqr':
    Q=o['Q'].reshape((lda,n),order='F')[:m,:];check('orthogonality',Q.T@Q,np.eye(n));R=Q.T@A;check('QR-reconstruction',Q@R,A);check('R-upper-triangular',np.tril(R,-1),np.zeros_like(R))
   elif kind=='gesvdj':
    sv=o['S'];U=o['U'].reshape((int(e['ldu']),-1),order='F')[:m,:];V=o['V'].reshape((int(e['ldv']),-1),order='F')[:n,:];check('singular-values-cpu',np.sort(sv),np.sort(np.linalg.svd(A,compute_uv=False)));check('reconstruction',U[:,:n]@np.diag(sv)@V.T,A);check('U-orthogonality',U[:,:n].T@U[:,:n],np.eye(n));check('V-orthogonality',V.T@V,np.eye(n))
   else:raise ValueError('specialized oracle not implemented for '+kind)
   r.update(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,source_sha256=s['source_sha256'],implementation_sha256=a['implementation_sha256'],oracle='Independent NumPy/SciPy CPU factorization; GPU output checked for finiteness, reconstruction/residual and orthogonality',scope='Original fixed teaching matrix; no sign/phase-sensitive raw eigenvector comparison')
   if r['status']=='PASSED':
    s['original_profile_validation']=r;s['evidence'].append('migration/reports/solver-original-validation.json')
    if not s.get('passed_cases'):s.update(status='PASSED',level='L4',actual_library='hipSOLVER + hipBLAS',backend_library='rocSOLVER/rocBLAS',required_cases=[v['check'] for v in checks],passed_cases=[v['check'] for v in checks],reason_code='VALIDATED_ORIGINAL_PROFILE',reason='使用 hipSOLVER/rocSOLVER 与 hipBLAS 保留原始固定教学矩阵；通过独立 NumPy/SciPy 特征值/奇异值、重构/残差和正交性检查，见逐项误差与阈值。')
  except Exception as ex:r['reason']=str(ex)
  results.append(r)
 p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
(ROOT/'migration/reports/solver-original-validation.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n');print(collections.Counter(v['status'] for v in results));print([(v['id'],v.get('reason',v['checks'])) for v in results if v['status']=='FAILED'])
