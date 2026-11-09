"""Independent complete CPU permutation/elementwise/reduction for saved inputs."""
import hashlib,json,pathlib
from validate_blas import np
from run import digest
def validate(source,case,d):
 cfg=json.loads((d/'tensor.json').read_text());kind=pathlib.PurePosixPath(source).stem;extent=cfg['extents'];target=cfg['modeC'];files={};arrays={}
 for name in ['A','B','C']:
  p=d/('input_'+name+'.bin')
  if not p.exists():continue
  mode=cfg['mode'+name] if name!='C' else target;shape=tuple(extent[m] for m in mode);v=np.memmap(p,np.float32,mode='r');assert v.size==int(np.prod(shape));arrays[name]=v.reshape(shape,order='F');files[name]=digest(p)
 actual=np.memmap(d/'output.bin',np.float32,mode='r').reshape(tuple(extent[m] for m in target),order='F');A=arrays['A'];alpha,beta,gamma=[cfg[n] for n in ['alpha','beta','gamma']]
 if kind=='reduction':axes=tuple(i for i,m in enumerate(cfg['modeA']) if m not in target);ref=alpha*np.sum(A,axis=axes,dtype=np.float64)+beta*arrays['C']
 else:
  axes=tuple(cfg['modeA'].index(m) for m in target);ref=alpha*np.transpose(A,axes).astype(np.float64)
  if kind=='elementwise_binary':ref+=gamma*arrays['C']
  if kind=='elementwise_trinary':ref+=beta*np.transpose(arrays['B'],tuple(cfg['modeB'].index(m) for m in target))+gamma*arrays['C']
 diff=np.asarray(actual,dtype=np.float64)-ref;finite=bool(np.isfinite(actual).all() and np.isfinite(ref).all());rel=float(np.linalg.norm(diff.ravel())/max(np.linalg.norm(ref.ravel()),1));maxerr=float(np.max(abs(diff)));bound=float((12*np.finfo(np.float32).eps*max(1,float(np.max(abs(ref))))) if kind=='reduction' else 2e-6+2e-6*float(np.max(abs(ref))));passed=bool(finite and rel<2e-6 and maxerr<=bound);identity=hashlib.sha256(json.dumps({'input_files':files,'config':cfg},sort_keys=True).encode()).hexdigest()
 return {'status':'PASSED' if passed else 'FAILED','input_sha256':identity,'input_file_hashes':files,'configuration':cfg,'checks':[{'check':'all-semantic-elements-independent-cpu','passed':passed,'semantic_elements':int(actual.size),'finite':finite,'relative_l2':rel,'relative_l2_limit':2e-6,'max_abs_error':maxerr,'max_abs_limit':bound}],'output_values':{},'output_sha256':digest(d/'output.bin'),'oracle':'NumPy CPU, explicitly reconstructed column-major tensor modes and FP64 arithmetic/reduction, every output checked'}
