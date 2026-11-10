"""Full-output CPU tensor references, plus real cache import/replay gates."""
import hashlib,json
from validate_blas import np,observed
from run import digest

def validate(source,case,d):
 checks=[];hashes={};outputs={};stem=source.split('/')[-1].split('.')[0]
 def gate(name,yes,**extra):checks.append(dict(check=name,passed=bool(yes),**extra))
 def load(name,shape=None):
  p=d/('input_'+name+'.bin');hashes[name]=digest(p);v=np.memmap(p,np.float32,mode='r');return v.reshape(shape,order='F') if shape else v
 def shape(m,e):return tuple(e[c] for c in m)
 def check_file(name,expected,tol=6e-6):
  actual=np.memmap(d/name,np.float32,mode='r');ref=np.asarray(expected).ravel(order='F');gate(name+'-size',actual.size==ref.size)
  if actual.size!=ref.size:return
  total=0.;denom=0.;maximum=0.;bound=0.;finite=True;yes=True
  for start in range(0,len(ref),1<<20):
   a=np.asarray(actual[start:start+(1<<20)],np.float64);b=np.asarray(ref[start:start+(1<<20)],np.float64);delta=a-b;finite=bool(finite and np.isfinite(a).all() and np.isfinite(b).all());maximum=max(maximum,float(np.max(abs(delta),initial=0)));bound=max(bound,float(np.max(abs(b),initial=0))*tol+tol);total+=float(delta@delta);denom+=float(b@b);yes=bool(yes and np.all(abs(delta)<=tol+tol*abs(b)))
  relative=float(np.sqrt(total/max(denom,1.)));gate(name+'-all-elements',finite and yes and relative<=tol,semantic_elements=int(actual.size),finite=finite,relative_l2=relative,max_abs_error=maximum,max_abs_bound=bound,rtol=tol,atol=tol)
  return actual
 if stem=='einsum':
  configs=[]
  for op in range(5):
   cfg=json.loads((d/f'tensor5-{op}.json').read_text());configs.append(cfg);e=cfg['extents'];am,bm,cm=cfg['modeA'],cfg['modeB'],cfg['modeC'];A=load('A'+str(op),shape(am,e)).astype(np.float64);B=load('B'+str(op),shape(bm,e) if bm else (1,)).astype(np.float64)
   expected=np.einsum(am+(','+bm if bm else '')+'->'+cm,A,*([B] if bm else []),optimize=True);actual=check_file(f'output{op}.bin',expected);outputs[str(op)]=np.asarray(actual).tolist()
 elif stem=='elementwise_permute_padding':
  cfg=json.loads((d/'tensor5.json').read_text());configs=[cfg];e=cfg['extents'];am,cm=cfg['modeA'],cfg['modeC'];av=load('A');as_=np.array(cfg['stridesA']);cs=np.array(cfg['stridesC']);left=cfg['left'];right=cfg['right'];outshape=tuple(e[c]+left[i]+right[i] for i,c in enumerate(cm));n=1+sum((outshape[i]-1)*cs[i] for i in range(4));expected=np.full(n,-97.,np.float64);view=np.lib.stride_tricks.as_strided(expected,shape=outshape,strides=cs*8);view[:]=0
  A=np.lib.stride_tricks.as_strided(av,shape=shape(am,e),strides=as_*4);region=tuple(slice(left[i],left[i]+e[c]) for i,c in enumerate(cm));view[region]=cfg['alpha']*np.transpose(A,tuple(am.index(c) for c in cm));check_file('output.bin',expected,1e-7)
  gate('original-extents',case!='original' or e=={'h':128,'w':32,'c':128,'n':128})
 else:
  cfg=json.loads((d/'tensor5.json').read_text());configs=[cfg];e=cfg['extents'];am,bm,cm,dm=[cfg['mode'+x] for x in ['A','B','C','D']];a=load('A',shape(am,e));b=load('B',shape(bm,e));c=load('C',shape(cm,e));alpha,beta=cfg['alpha'],cfg['beta']
  # Independent FP64 CPU contractions; GPU uses packed FP32 BLAS or native cuTENSOR.
  if stem=='contraction_trinary':
   original=load('D',shape(dm,e));mid=np.einsum(am+','+bm+'->majbn',np.asarray(a,np.float64),np.asarray(b,np.float64),optimize=True);product=np.einsum('majbn,'+cm+'->'+dm,mid,np.asarray(c,np.float64),optimize=True);expected=alpha*(1+beta+beta*beta)*product+(beta**3)*original;del mid,product
   gate('original-extents',case!='original' or e=={'m':256,'a':32,'b':32,'n':64,'r':64,'k':8,'i':8,'j':64})
   check_file('output.bin',expected)
  else:
   expected=alpha*np.einsum(am+','+bm+'->'+cm,np.asarray(a,np.float64),np.asarray(b,np.float64),optimize=True)+beta*c;check_file('output.bin',expected)
   gate('native-or-adapter-cache-written',(d/'planCache.bin').stat().st_size>0);o=observed(d/'run.log');replay=observed(d/'replay.log');gate('first-load-behavior',o['cache_read_status'][0]==0 if case=='changed-descriptor' and 'cache_candidate_runs' not in o else o['cache_read_status'][0]!=0)
   gate('cache-write-success',o['cache_write_status'][0]==0);gate('new-process-cache-import',replay['cache_read_status'][0]==0);gate('new-process-cache-write-success',replay['cache_write_status'][0]==0);check_file('replay_output.bin',expected)
   if 'cache_candidate_runs' in o:gate('real-plan-search',o['cache_candidate_runs'][0]==3);gate('replay-reuses-plan',replay['cache_candidate_runs'][0]==0);gate('cached-policy-used',o['cached_row_block'][0]==replay['cached_row_block'][0]>0)
   gate('original-extents',case!='original' or e=={'m':96,'n':96,'u':96,'v':64,'h':64,'k':64})
  del expected
 identity=hashlib.sha256(json.dumps({'configs':configs,'inputs':hashes},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'status':'PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED','checks':checks,'input_sha256':identity,'input_file_hashes':hashes,'configuration':configs,'output_values':outputs,'oracle':'Independent FP64 NumPy einsum and explicit stride/padding; every semantic output checked in bounded chunks; separate process cache replay'}
