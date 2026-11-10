"""Full FP64 CPU GEMM reference for every search candidate and selected replay."""
import hashlib,json
from validate_blas import np,observed
from batch4_reference import serial
from batches4_8_spec import kind

def validate(source,case,d):
 o=observed(d/'run.log');checks=[];outputs={};identity={n:serial(np.asarray(v,dtype=np.float64)) for n,v in o.items() if n.startswith('input_')};k=kind(source)
 def gate(name,v,**kw):checks.append(dict(check=name,passed=bool(v),**kw))
 def check(name,a,b,tol):
  a,b=np.asarray(a),np.asarray(b);err=float(np.max(np.abs(a-b),initial=0)) if a.shape==b.shape else float('inf');bound=tol+tol*float(np.max(abs(b),initial=0));gate(name,np.isfinite(a).all() and a.shape==b.shape and np.allclose(a,b,rtol=tol,atol=tol),max_abs=err,bound=bound)
 for g in range(int(o['input_count'][0])):
  p='g'+str(g);count=int(o['candidates_'+p][0]);selected=int(o['selected_'+p][0]);empty='input_m_'+p in o and o['input_m_'+p][0]*o['input_n_'+p][0]==0;gate('nonempty-search-'+p,count==0 if empty else count>=1);gate('selected-algorithm-'+p,selected==-1 if empty else selected>=0)
  if 'input_half_'+p not in o:
   n=int(o['input_n_'+p][0]);A=o['input_A_'+p].reshape(n,n,order='F');B=o['input_B_'+p].reshape(n,n,order='F');C=o['input_C_'+p].reshape(n,n,order='F');alpha=o['input_alpha_'+p][0];beta=o['input_beta_'+p][0];expected=alpha*(A.T if o['input_trans_'+p][0] else A)@B+beta*C
   for i in range(count):check('candidate-'+p+'-'+str(i),o['candidate_'+p+'_'+str(i)].reshape(n,n,order='F'),expected,2e-6 if k=='GemmGroupedBatchedEx' else 1e-12)
   result=o['output_'+p].reshape(n,n,order='F');check('selected-replay-'+p,result,expected,2e-6 if k=='GemmGroupedBatchedEx' else 1e-12);outputs[p]=serial(result)
   if k=='GemmExAutoTuning':gate('multiple-policy-search',count==2)
  else:
   m,n,r=[int(o['input_'+v+'_'+p][0]) for v in ['m','n','k']];dtype=np.dtype('float16' if o['input_half_'+p][0] else 'float32');tol=1e-3 if dtype.itemsize==2 else 8e-6
   def load(name,shape):
    file=d/(name+'_'+p+'.bin');identity[file.name]=hashlib.sha256(file.read_bytes()).hexdigest();return np.fromfile(file,dtype=dtype).reshape(shape,order='F').astype(np.float64)
   A=load('input_A',(m,r));B=load('input_B',(r,n));C=load('input_C',(m,n));bias=load('input_bias',(m,));alpha=o['input_alpha_'+p][0];beta=o['input_beta_'+p][0];expected=alpha*A@B+beta*C
   if o['input_bias_enabled_'+p][0]:expected+=bias[:,None]
   expected=expected.astype(dtype).astype(np.float64);budget=int(o['input_workspace_limit_'+p][0]);gate('workspace-budget-'+p,0<=o['workspace_'+p][0]<=budget);gate('zero-budget-case',case!='limited-workspace' or budget==0)
   for i in range(count):
    actual=np.fromfile(d/('candidate_'+p+'_'+str(i)+'.bin'),dtype=dtype).reshape(m,n,order='F');check('full-candidate-'+p+'-'+str(i),actual,expected,tol);gate('candidate-workspace-'+p+'-'+str(i),0<=o['candidate_workspace_'+p+'_'+str(i)][0]<=budget)
   result=np.fromfile(d/('output_'+p+'.bin'),dtype=dtype).reshape(m,n,order='F');check('selected-replay-'+p,result,expected,tol);outputs[p]=serial(result.ravel()[::max(1,m*n//512)])
   if k in ['LtSgemmCustomFind','LtSgemmSimpleAutoTuning']:gate('multiple-candidate-search',count>=2);gate('original-size',m==1024 and n==(512 if k=='LtSgemmCustomFind' else 1024) and r==(4096 if k=='LtSgemmCustomFind' else 1024))
 return dict(status='PASSED' if checks and all(x['passed'] for x in checks) else 'FAILED',checks=checks,input_sha256=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest(),output_values=outputs,oracle='Independent FP64 CPU GEMM, dtype-rounded full candidate outputs; workspace and replay checked; algorithm identities backend-local')
