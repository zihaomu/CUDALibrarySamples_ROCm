"""Independent sparse reconstruction, solve, LU/LDL, configuration and query validation."""
import hashlib,json
from validate_blas import np,observed
from scipy.sparse import csr_matrix,tril,triu,eye
from scipy.sparse.linalg import spsolve
from batches9_11_spec import kind

def validate(source,case,d):
 o=observed(d/'run.log');checks=[];outputs={};k=kind(source)
 def gate(name,v,**kw):checks.append(dict(check=name,passed=bool(v),**kw))
 def check(name,a,b,tol=1e-9):
  delta=a-b;err=float(np.linalg.norm(delta.data)) if hasattr(delta,'tocsr') else float(np.linalg.norm(delta));norm=float(np.linalg.norm(b.data)) if hasattr(b,'tocsr') else float(np.linalg.norm(b));finite=np.isfinite(delta.data).all() if hasattr(delta,'tocsr') else np.isfinite(delta).all();gate(name,finite and err<=tol*max(1,norm),error=err,bound=tol*max(1,norm))
 gate('config-get-real-flags',o['config_matching_get'][0]==o['input_matching'][0] and o['config_superpanels_get'][0]==o['input_fused'][0]);analysis=bool(o['input_analysis_only'][0]);count=int(o['input_count'][0]);identity={name:np.asarray(v,dtype=np.float64).tolist() for name,v in o.items() if name.startswith('input_')}
 for batch in range(count):
  p='b'+str(batch);n=int(o['input_n_'+p][0]);nrhs=int(o['input_nrhs_'+p][0]);mtype=int(o['input_mtype_'+p][0]);A=csr_matrix((o['input_values_'+p],o['input_columns_'+p].astype(int),o['input_rows_'+p].astype(int)),shape=(n,n))
  if mtype:A=A+A.T-csr_matrix((A.diagonal(),(np.arange(n),np.arange(n))),shape=(n,n))
  b=o['input_rhs_'+p].reshape(n,nrhs,order='F');
  if o['input_uniform_index'][0]>=0 and batch!=o['input_uniform_index'][0]:gate('unselected-batch-untouched',len(o['untouched_'+p])==(n+5)*nrhs and np.all(o['untouched_'+p]==-97) and o['skipped_GPU_buffer_'+p][0]==1);continue
  perm=o['permutation_'+p].astype(int);gate('permutation-bijection-'+p,np.array_equal(np.sort(perm),np.arange(n)));gate('natural-reorder-'+p,o['input_reorder'][0] or np.array_equal(perm,np.arange(n)));fr=o['factor_rows_'+p].astype(int);fc=o['factor_columns_'+p].astype(int);gate('CSR-factor-symbolic-shape-'+p,len(fr)==n+1 and fr[0]==0 and fr[-1]==len(fc) and np.all(np.diff(fr)>0));gate('column-permutation-bijection-'+p,np.array_equal(np.sort(o['column_permutation_'+p].astype(int)),np.arange(n)));gate('real-query-sizes-'+p,o['query_lu_nnz_'+p][0]==len(fc) and o['query_perm_bytes_'+p][0]==n*4 and o['query_gpu_allocated_bytes_'+p][0]>0);gate('core-memory-query-'+p,o['query_memory_core_'+p][0]==o['query_gpu_allocated_bytes_'+p][0] and o['query_memory_core_'+p][1]>0 and o['query_info_bytes_'+p][0]==4 and o['query_lu_nnz_bytes_'+p][0]==8);scale=o['row_scale_'+p];check('positive-column-scales-'+p,scale,o['column_scale_'+p],0);gate('scales-finite-positive-'+p,np.isfinite(scale).all() and np.all(scale>0));gate('matching-disabled-'+p,o['input_matching'][0] or np.all(scale==1))
  pattern=csr_matrix((np.ones(len(fc)),fc,fr),shape=(n,n));initial=csr_matrix((np.ones(len(o['input_values_'+p])),o['input_columns_'+p].astype(int),o['input_rows_'+p].astype(int)),shape=(n,n))
  if mtype:initial=initial+initial.T
  initial=initial[perm,:][:,o['column_permutation_'+p].astype(int)];gate('symbolic-retains-every-stored-input-'+p,(initial-initial.multiply(pattern)).nnz==0)
  if n==1000:gate('original-stays-sparse-no-dense-factor-buffer',len(fc)<n*n//2 and A.nnz==6400)
  if analysis:gate('analysis-only-no-numeric-output-'+p,'solution_'+p not in o);continue
  singular=np.linalg.matrix_rank(A.toarray())<n if n<=64 else False;info=o['factor_info_'+p][0];perturbed=int(o.get('cuda_native_perturbed_1x1_pivots_'+p,[0])[0]);gate('singular-info-or-declared-regularization-'+p,(info>0 or perturbed>0) if singular else info==0)
  if singular:
   if info==0:
    gate('native-regularization-is-not-original-solution-'+p,perturbed>0 and np.isfinite(o['solution_'+p]).all(),perturbed_1x1_pivots=perturbed,outcome='Native CUDA perturbs the singular system; no solution of the original singular system is qualified and no solution vector is compared to AMD rejection.')
   continue
  ldx=int(o['ldx_'+p][0]);X=o['solution_'+p].reshape(ldx,nrhs,order='F');check('solution-CPU-sparse-'+p,X[:n],np.asarray(spsolve(A,b)).reshape(n,nrhs));check('true-residual-'+p,A@X[:n],b);check('GPU-residual-'+p,o['residual_'+p].reshape(n,nrhs,order='F'),A@X[:n]-b);gate('solution-padding-'+p,np.all(X[n:]==-97));outputs[p]=X[:n].ravel().tolist()
  if 'factor_values_'+p in o:
   lu=csr_matrix((o['factor_values_'+p],fc,fr),shape=(n,n));piv=o['pivot_rows_'+p].astype(int);ordered=lu[piv,:];L=tril(ordered,-1)+eye(n);U=triu(ordered);colperm=o['column_permutation_'+p].astype(int);scaled=A[perm,:][:,colperm].multiply(scale[:,None]).multiply(scale[None,:]).tocsr();check('actual-GPU-LU-reconstruction-'+p,L@U,scaled[piv,:]);gate('actual-factor-policy-'+p,o['factor_launches_'+p][0]==(1 if o['input_fused'][0] or n>64 else n))
   if mtype and n<=64 and 'query_diagonal_'+p in o:
    ld=csr_matrix((o['query_ldl_values_'+p],fc,fr),shape=(n,n));low=tril(ld,-1).toarray()+np.eye(n);D=o['query_diagonal_'+p];check('GPU-query-LDL-'+p,(low*D)@low.T,scaled.toarray());eig=np.linalg.eigvalsh(A.toarray());check('GPU-inertia-query-'+p,o['query_inertia_'+p],[np.sum(eig>1e-10),np.sum(eig< -1e-10)],0)
 if case=='original':
  if k=='simple_residual':gate('original-GENERAL-1000-2RHS',o['input_n_b0'][0]==1000 and o['input_mtype_b0'][0]==0 and o['input_nrhs_b0'][0]==2)
  elif k=='simple_get_set':gate('original-SYMMETRIC-type',o['input_mtype_b0'][0]==2 and o['input_refinement'][0]==2 and o['input_fused'][0]==0)
  elif k=='simple_batch':gate('original-heterogeneous-batch',count==2 and o['input_n_b0'][0]==5 and o['input_n_b1'][0]==6)
  elif k=='simple_uniform_batch':gate('original-uniform-batch',count==2 and o['input_n_b0'][0]==o['input_n_b1'][0]==5)
 return dict(status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',checks=checks,input_sha256=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest(),output_values=outputs,oracle='Independent SciPy sparse solve and LU/LDL reconstruction, original GENERAL/SPD/SYMMETRIC profiles, residual, permutations, actual factor/config/query behavior')
