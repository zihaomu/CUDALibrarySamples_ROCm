"""Independent CPU mathematics and execution-semantic gates for batch 3."""
import hashlib, json, pathlib
from validate_blas import np, observed
from scipy import linalg, sparse
from scipy.sparse import linalg as spla

def validate(source, case, d):
    o = observed(d/'run.log')
    kind = pathlib.PurePosixPath(source).parent.name
    checks, outputs = [], {}
    inputs = {k:v.tolist() for k,v in o.items() if k.startswith('input_')}
    def gate(name, yes, **detail):
        checks.append(dict(check=name, passed=bool(yes), **detail))
    def check(name, actual, expected, tol=1e-10):
        a, b = np.asarray(actual), np.asarray(expected)
        shape = a.shape == b.shape
        finite = np.isfinite(a).all() and np.isfinite(b).all()
        error = float(np.linalg.norm((a-b).ravel())) if shape else None
        bound = tol*max(1.,float(np.linalg.norm(b.ravel())))
        gate(name, shape and finite and error <= bound, error=error, bound=bound)
    def binary(name, dtype):
        p=d/name
        value=np.fromfile(p,dtype)
        if name.startswith('input_'):
            inputs[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        return value

    if kind in ['cg','bicgstab']:
        ptr=binary('input_rows.bin',np.int32); col=binary('input_columns.bin',np.int32)
        val=binary('input_values.bin',np.float64); b=binary('input_rhs.bin',np.float64)
        x0=binary('input_initial.bin',np.float64); known=binary('input_manufactured.bin',np.float64)
        x=binary('solution.bin',np.float64); n=len(b)
        structure=(len(ptr)==n+1 and ptr[0]==0 and ptr[-1]==len(col)==len(val) and
                   np.all(np.diff(ptr)>0) and np.all((col>=0)&(col<n)))
        gate('CSR-structure',structure,rows=n,nnz=len(val))
        if not structure:raise ValueError('Invalid CSR structure')
        A=sparse.csr_matrix((val,col,ptr),shape=(n,n))
        gate('sorted-unique-columns',A.has_canonical_format)
        gate('original-or-variant-size',n==({'original':700**2,'small-varied':23**2,'nonzero-initial':31**2}[case]))
        check('manufactured-RHS',b,0.75*(A@known),1e-13)
        check('GPU-generated-RHS',binary('generated_rhs.bin',np.float64),0.75*(A@known),1e-13)
        initial=float(np.linalg.norm(b-A@x0));residual=float(np.linalg.norm(b-A@x))
        tol=float(o['input_tolerance'][0]);threshold=tol*initial
        check('reported-initial-residual',o['initial_residual'],[initial],1e-12)
        check('reported-threshold',o['threshold'],[threshold],1e-12)
        check('reported-final-residual',o['final_residual'],[residual],1e-11)
        gate('true-residual-converged',np.isfinite(x).all() and residual<=threshold*1.01+1e-11,
             residual=residual,threshold=threshold)
        it=float(o['iterations'][0]);maximum=int(o['input_max_iterations'][0])
        gate('iteration-budget',it.is_integer() and 0<it<=maximum,iterations=it,maximum=maximum)
        if kind=='cg':gate('CG-symmetric-positive-diagonal',(A-A.T).nnz==0 and np.all(A.diagonal()>0))
        # Independent unpreconditioned CPU solver, not the GPU IC0/ILU0 algorithm.
        cpu,info=(spla.cg if kind=='cg' else spla.bicgstab)(A,b,rtol=1e-12,atol=0,maxiter=4000)
        gate('CPU-solver-converged',info==0,info=int(info))
        check('CPU-reference-residual',A@cpu,b,2e-12)
        check('GPU-vs-CPU-solution',x,cpu,2e-7 if kind=='cg' else 1e-8)
        check('manufactured-solution',x,0.75*known,2e-7 if kind=='cg' else 1e-8)
        outputs['solution-summary']=[float(np.linalg.norm(x)),float(np.mean(x))]
    elif kind=='gpsvInterleavedBatch':
        for name in ['S','L','M','U','W','B']:
            check('interleaved-'+name,o['interleaved_'+('X' if name=='B' else name)],
                  o['input_'+name].reshape(2,4).T.ravel(),0)
        x=o['solution'].reshape(2,4)
        check('output-interleaved-layout',o['solution_interleaved'],x.T.ravel(),0)
        for batch in range(2):
            A=np.zeros((4,4))
            for band,offset in [('S',-2),('L',-1),('M',0),('U',1),('W',2)]:
                values=o['input_'+band].reshape(2,4)[batch]
                for row in range(4):
                    if 0<=row+offset<4:A[row,row+offset]=values[row]
            b=o['input_B'].reshape(2,4)[batch]
            check(f'batch{batch}-CPU-solve',x[batch],np.linalg.solve(A,b),2e-6)
            check(f'batch{batch}-residual',A@x[batch],b,2e-6)
        outputs['solution']=x.ravel().tolist()
    elif kind=='gesvdjBatched':
        check('info',o['info'],np.zeros(2),0)
        spectra=[]
        for b in range(2):
            A=o['input_A'][b*6:(b+1)*6].reshape(3,2,order='F')
            U=o['U'][b*9:(b+1)*9].reshape(3,3,order='F')
            V=o['V'][b*4:(b+1)*4].reshape(2,2,order='F');sv=o['S'][b*2:(b+1)*2]
            gate(f'batch{b}-nonnegative-singular-values',np.isfinite(sv).all() and np.all(sv>=0))
            check(f'batch{b}-singular-values',np.sort(sv),np.sort(np.linalg.svd(A,compute_uv=False)),2e-7)
            check(f'batch{b}-SVD-reconstruction',U[:,:2]@np.diag(sv)@V.T,A,2e-7)
            check(f'batch{b}-U-orthogonality',U.T@U,np.eye(3),2e-7)
            check(f'batch{b}-V-orthogonality',V.T@V,np.eye(2),2e-7)
            spectra.extend(np.sort(sv).tolist())
        outputs['spectrum']=spectra
    elif kind=='syevjBatched':
        check('info',o['info'],np.zeros(2),0)
        spectra=[]
        for b in range(2):
            A=o['input_A'][b*9:(b+1)*9].reshape(3,3,order='F')
            V=o['V'][b*9:(b+1)*9].reshape(3,3,order='F');w=o['W'][b*3:(b+1)*3]
            check(f'batch{b}-eigenvalue-multiset',np.sort(w),np.linalg.eigvalsh(A),2e-7)
            # Do not sort W independently of V in residual checks.
            check(f'batch{b}-paired-eigen-residual',A@V,V@np.diag(w),2e-7)
            check(f'batch{b}-orthogonality',V.T@V,np.eye(3),2e-7)
            if case=='sorted':gate(f'batch{b}-sorted',np.all(np.diff(w)>=0))
            spectra.extend(np.sort(w).tolist())
        outputs['spectrum']=spectra
    elif kind in ['syevdx','sygvdx']:
        check('info',o['info'],[0],0)
        A=o['input_A'].reshape(3,3,order='F')
        B=o['input_B'].reshape(3,3,order='F') if kind=='sygvdx' else np.eye(3)
        expected=linalg.eigh(A,B,eigvals_only=True)
        if case=='original':expected=expected[int(o['input_il'][0])-1:int(o['input_iu'][0])]
        elif case in ['value-range','empty-range']:
            expected=expected[(expected>o['input_vl'][0])&(expected<=o['input_vu'][0])]
        count=int(o['meig'][0]);gate('returned-meig',float(count)==o['meig'][0] and count==len(expected),returned=count,expected=len(expected))
        w=o['W'];V=o['V'].reshape(3,count,order='F')
        check('only-returned-eigenvalues',w,expected,1e-10)
        check('paired-eigen-residual',A@V,B@V@np.diag(w),1e-10)
        check('B-orthogonality' if kind=='sygvdx' else 'orthogonality',V.T@B@V,np.eye(count),1e-10)
        outputs['spectrum']=w.tolist()
    elif kind=='graph_capture':
        idx=o['input_indices'].astype(int);x=o['input_X'];size=int(o['input_size'][0]);capture=int(o['capture_calls'][0])
        gate('SpVV-indices',len(idx)==len(x) and np.all((idx>=0)&(idx<size)) and len(set(idx))==len(idx))
        gate('graph-nonempty',o['graph_nodes'][0]>0,nodes=float(o['graph_nodes'][0]))
        gate('captured-GPU-kernels',o['graph_kernels'][0]>=capture,kernels=float(o['graph_kernels'][0]),calls=capture)
        gate('original-capture-workload',capture==(1000 if case=='original' else 7))
        gate('three-actual-replays',o['replay_count'][0]==3)
        results=[]
        for replay in range(3):
            y=o['input_Y_'+str(replay)];r=o['replay_'+str(replay)]
            gate('dense-size-'+str(replay),len(y)==size)
            check('replay-dot-'+str(replay),r,[np.dot(x,y[idx])],1e-6)
            results.append(float(r[0]))
        check('standard-call',o['standard_result'],[np.dot(x,o['input_Y_0'][idx])],1e-6)
        gate('changed-input-changes-output',results[0]!=results[1] and results[1]!=results[2])
        gate('zero-input-replay',results[2]==0)
        outputs['replay-results']=results
    else:raise ValueError('No oracle for '+source)
    identity=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'status':'PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED',
            'checks':checks,'input_sha256':identity,'output_values':outputs,
            'oracle':'Independent CPU NumPy/SciPy sparse and dense solvers; residual, structure, pairing and actual graph execution checks'}
