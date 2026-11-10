"""Independent mathematics/structure/semantics; no success from process exit alone."""
import hashlib,json
from validate_blas import np,observed
from batches4_8_spec import kind

def serial(v):
 a=np.asarray(v)
 return np.stack([a.real,a.imag],axis=-1).tolist() if np.iscomplexobj(a) else a.tolist()

def validate(source,case,d):
 o=observed(d/'run.log');k=kind(source);checks=[];outputs={}
 def gate(name,yes,**details):checks.append(dict(check=name,passed=bool(yes),**details))
 def check(name,a,b,tol=1e-10):
  a,b=np.asarray(a),np.asarray(b);shape=a.shape==b.shape;finite=np.isfinite(a).all() and np.isfinite(b).all()
  error=float(np.linalg.norm((a-b).ravel())) if shape else None;bound=tol*max(1.,float(np.linalg.norm(b.ravel())))
  gate(name,shape and finite and error<=bound,error=error,bound=bound)
 def output(name,v):outputs[name]=serial(v)
 if k in ['CherkEx','CsyrkEx']:
  A=o['input_A'].reshape(2,2,order='F');initial=o['input_C'].reshape(2,2,order='F');a=o['input_alpha'][0];b=o['input_beta'][0];actual=o['C'].reshape(2,2,order='F')
  expected_beta=(-.5 if k=='CherkEx' else complex(-.5,.25)) if case=='nonzero-beta' else 0
  check('case-beta',[b],[expected_beta],0)
  if case in ['transpose','conjugate']:A=A.conj().T if k=='CherkEx' else A.T
  expected=a*A@(A.conj().T if k=='CherkEx' else A.T)+b*initial
  if k=='CherkEx':expected[np.diag_indices(2)]=expected.diagonal().real
  ids=np.tril_indices(2) if case=='lower' else np.triu_indices(2);other=np.triu_indices(2,1) if case=='lower' else np.tril_indices(2,-1)
  check('rank-k-selected-triangle',actual[ids],expected[ids],2e-6);check('other-triangle-preserved',actual[other],initial[other],0)
  output('triangle',actual[ids])
 elif k=='GemmBatchedEx':
  a=o['input_alpha'][0];b=o['input_beta'][0];check('case-beta',[b],[-.5 if case=='nonzero-beta' else 0],0)
  for i in range(2):
   A=o[f'input_A_{i}'].reshape(2,2,order='F');B=o[f'input_B_{i}'].reshape(2,2,order='F');C=o[f'input_C_{i}'].reshape(2,2,order='F')
   if case=='transpose':A=A.T
   result=o[f'C_{i}'].reshape(2,2,order='F');check('batch'+str(i),result,a*A@B+b*C);output('batch'+str(i),result)
 elif k in ['tpttr','trttp']:
  n=int(o['input_n'][0]);lda=int(o['input_lda'][0]);upper=bool(o['input_upper'][0]);A=o['A'].reshape(lda,n,order='F');P=o['AP'];inpA=o['input_A'].reshape(lda,n,order='F');inpP=o['input_AP'];ids=[(i,j) for j in range(n) for i in range(n) if (i<=j if upper else i>=j)];m=n*(n+1)//2
  actual=np.array([A[i,j] for i,j in ids]) if k=='tpttr' else P[:m];expected=inpP[:m] if k=='tpttr' else np.array([inpA[i,j] for i,j in ids]);check('packed-column-major-layout',actual,expected,0);output('defined-result',actual)
  if k=='trttp':check('tail-canary',P[m:],np.full(len(P)-m,-97.),0)
  if lda>n:check('lda-padding-canary',A[n:],np.full((lda-n,n),-97.),0)
 elif k=='ormqr':
  A=o['input_A'].reshape(3,3,order='F');B=o['input_B'].reshape(3,-1,order='F');packed=o['QR'].reshape(3,3,order='F');tau=o['tau'];Q=np.eye(3)
  for j,t in enumerate(tau):
   u=np.zeros(3);u[j]=1;u[j+1:]=packed[j+1:,j];Q=Q@(np.eye(3)-t*np.outer(u,u))
  check('info',o['info'],[0],0);check('QR-reconstruction',Q@np.triu(packed),A);check('Q-orthogonality',Q.T@Q,np.eye(3));check('Q-application',o['QTB'].reshape(B.shape,order='F'),Q.T@B)
  X=o['XC'].reshape(B.shape,order='F');check('solve-residual',A@X,B);check('independent-CPU-solve',X,np.linalg.solve(A,B));output('solution',X)
 elif k=='spsv_sell':
  ptr=o['input_offsets'].astype(int);cols=o['input_columns'].astype(int);vals=o['input_values'];A=np.zeros((4,4));counts=[]
  for r in range(4):
   s,l=divmod(r,2);row=[]
   for q in range(ptr[s]+l,ptr[s+1],2):
    if cols[q]>=0:A[r,cols[q]]=vals[q];row.append((cols[q],vals[q]))
   counts.append(row)
  upper=bool(o['input_upper'][0]);unit=bool(o['input_unit'][0]);T=np.triu(A) if upper else np.tril(A)
  if unit:np.fill_diagonal(T,1)
  rhs=o['input_alpha'][0]*o['input_X'];y=o['Y'];check('triangular-solve',y,np.linalg.solve(T,rhs),2e-6);check('true-residual',T@y,rhs,2e-6);output('solution',y)
  if 'bridge_rows' in o:
   expected_ptr=np.r_[0,np.cumsum([len(r) for r in counts])];check('GPU-format-row-offsets',o['bridge_rows'],expected_ptr,0);check('GPU-format-columns',o['bridge_columns'],[v[0] for r in counts for v in r],0);check('GPU-format-values',o['bridge_values'],[v[1] for r in counts for v in r],0)
 elif k=='sddmm_bsr':
  A=o['input_A'].reshape(8,8);B=o['input_B'].reshape(8,8);ptr=o['input_offsets'].astype(int);col=o['input_columns'].astype(int);initial=o['input_C'];order='F' if o['input_column_order'][0] else 'C';product=A@B;expected=[]
  for br in range(2):
   for p in range(ptr[br],ptr[br+1]):
    block=product[br*4:br*4+4,col[p]*4:col[p]*4+4];expected.extend((o['input_alpha'][0]*block+o['input_beta'][0]*initial[p*16:(p+1)*16].reshape(4,4,order=order)).ravel(order=order))
  check('all-stored-block-values',o['C'],expected,2e-6);output('blocks',o['C'])
  if 'bridge_rows' in o:
   check('bridge-nnz',[o['bridge_rows'][-1]],[32],0);gate('bridge-structure',np.all(np.diff(o['bridge_rows'])==4) and np.all((o['bridge_columns']>=0)&(o['bridge_columns']<8)))
 else:
  raise ValueError('Independent oracle pending for '+source)
 identity=hashlib.sha256(json.dumps({n:serial(v) for n,v in o.items() if n.startswith('input_')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'status':'PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED','checks':checks,'input_sha256':identity,'output_values':outputs,'oracle':'Independent NumPy/SciPy mathematical/structural reference; explicit execution-semantic checks'}
