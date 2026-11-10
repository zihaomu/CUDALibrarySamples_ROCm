"""Independent SciPy sparse structure and mathematical/custom operation references."""
import hashlib,json
from validate_blas import np,observed
from scipy.sparse import csr_matrix
from batch4_reference import serial
from batches4_8_spec import kind

def validate(source,case,d):
 o=observed(d/'run.log');k=kind(source);checks=[];outputs={};r=o['input_offsets'].astype(int);c=o['input_columns'].astype(int);v=o['input_values'];base=int(o['input_base'][0]);A=csr_matrix((v,c-base,r-base),shape=(4,4));dense=A.toarray()
 def gate(name,v,**kw):checks.append(dict(check=name,passed=bool(v),**kw))
 def check(name,a,b,tol=1e-6):
  a,b=np.asarray(a),np.asarray(b);err=float(np.max(abs(a-b),initial=0)) if a.shape==b.shape else float('inf');gate(name,a.shape==b.shape and np.isfinite(a).all() and np.allclose(a,b,rtol=tol,atol=tol),max_abs_error=err)
 gate('valid-CSR',r[0]==base and r[-1]-base==len(v) and len(c)==len(v) and np.all(np.diff(r)>=0) and np.all((c-base>=0)&(c-base<4)))
 if case=='empty-row':gate('empty-row-profile',np.any(np.diff(r)==0))
 if k=='spmat_convert':
  expected=A.tocsc();check('CSC-offsets',o['CSC_offsets'],expected.indptr+base,0);check('CSC-rows',o['CSC_rows'],expected.indices+base,0);check('CSC-values',o['CSC_values'],expected.data);outputs['values']=serial(o['CSC_values'])
 elif k=='spgemm_mem':
  B=csr_matrix((o['input_B_values'],o['input_B_columns'].astype(int),o['input_B_offsets'].astype(int)),shape=(4,4));expected=(A@B).tocsr();expected.sort_indices();check('SpGEMM-offsets',o['C_offsets'],expected.indptr,0);check('SpGEMM-columns',o['C_columns'],expected.indices,0);check('SpGEMM-values',o['C_values'],expected.data);outputs['values']=serial(o['C_values']);check('chunk-fraction',o['input_chunk_fraction'],[.05 if case=='small-budget' else .2])
  if 'numeric_chunks' in o:gate('workspace-limit',0<o['peak_numeric_workspace'][0]<=o['budget_bytes'][0]);gate('real-chunking',o['numeric_chunks'][0]==(4 if case=='small-budget' else 1))
  else:check('native-CUDA-chunk-policy',o['cuda_chunk_fraction'],o['input_chunk_fraction'])
 elif k=='spmv_symmetric_csr':
  S=dense+dense.T-np.diag(np.diag(dense));expected=o['input_alpha'][0]*S@o['input_X']+o['input_beta'][0]*o['input_Y'];check('symmetric-SpMV',o['Z'],expected);check('input-Y-preserved',o['Y_after'],o['input_Y'],0);outputs['Z']=serial(o['Z'])
  if 'bridge_offsets' in o:
   csr=csr_matrix(S);check('expanded-offsets',o['bridge_offsets'],csr.indptr+base,0);check('expanded-columns',o['bridge_columns'],csr.indices+base,0);check('expanded-values',o['bridge_values'],csr.data)
 elif k=='spmvop_csr':
  raw=dense@o['input_X']+3*o['input_Y'];scale=np.array([o['input_even'][0],o['input_odd'][0]]*2);expected=scale*raw;check('custom-epilogue',o['Z'],expected,1e-12);check('Y-preserved',o['Y_after'],o['input_Y'],0);gate('custom-differs-from-standard',not np.allclose(expected,raw));outputs['Z']=serial(o['Z'])
 elif k=='spmm_csr_op':
  B=o['input_B'].reshape(4,3);C=o['input_C'].reshape(4,3);raw=dense@B;expected=2*raw+C;check('custom-add-mul-and-epilogue',o['C'].reshape(4,3),expected);gate('custom-differs-from-standard',not np.allclose(expected,raw));outputs['C']=serial(o['C'])
 else:raise ValueError(k)
 identity=hashlib.sha256(json.dumps({n:serial(v) for n,v in o.items() if n.startswith('input_')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return dict(status='PASSED' if checks and all(x['passed'] for x in checks) else 'FAILED',checks=checks,input_sha256=identity,output_values=outputs,oracle='Independent SciPy CSR/CSC/SpGEMM, explicit symmetry, original custom device formulas, budget/chunk-policy validation')
