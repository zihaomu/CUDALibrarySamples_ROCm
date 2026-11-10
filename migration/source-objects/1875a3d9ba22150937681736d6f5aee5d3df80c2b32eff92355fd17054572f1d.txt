"""Independent full device-function results, cooperation, shared-padding and Philox oracle."""
import json,hashlib,math
from validate_blas import np
from batches12_15_spec import kind

def philox(seed,subsequence,offset,count):
 out=[]
 for index in range(offset,offset+count):
  counter=index//4;c=[counter&0xffffffff,counter>>32,subsequence&0xffffffff,subsequence>>32];key=[seed&0xffffffff,seed>>32]
  for _ in range(10):
   p0=0xd2511f53*c[0];p1=0xcd9e8d57*c[2];c=[((p1>>32)^c[1]^key[0])&0xffffffff,p1&0xffffffff,((p0>>32)^c[3]^key[1])&0xffffffff,p0&0xffffffff];key=[(key[0]+0x9e3779b9)&0xffffffff,(key[1]+0xbb67ae85)&0xffffffff]
  out.append(c[index%4])
 return out

def validate(source,case,d):
 k=kind(source);checks=[];identity={};outputs={}
 def gate(n,v,**kw):checks.append(dict(check=n,passed=bool(v),**kw))
 def read(name,dtype=np.float64):
  p=d/(name+'.bin');v=np.fromfile(p,dtype)
  if name.startswith('input') or name=='config':identity[name]=hashlib.sha256(p.read_bytes()).hexdigest()
  return v
 def near(n,a,b,rtol=2e-11,atol=1e-12):
  delta=np.abs(a-b);gate(n,a.shape==b.shape and np.isfinite(a).all() and np.all(delta<=atol+rtol*np.abs(b)),max_abs=float(delta.max(initial=0)))
 cfg=read('config',np.int32);trace=read('trace',np.int32)
 if k=='introduction_example':
  n,threads,repeat=cfg;a=read('input_A').reshape(n,n);b=read('input_B').reshape(n,n,order='F');c=read('input_C').reshape(n,n,order='F');product=a@b
  for i,expected in enumerate([product+c,2*product+c,product]):near('device-function-phase-'+str(i),read('phase'+str(i)).reshape(n,n,order='F'),expected)
  near('full-GEMM',read('output').reshape(n,n,order='F'),product);gate('three-device-APIs-called',np.all(trace[:3]==repeat))
 elif k=='simple_fft_block':
  n,batch,threads,repeat=cfg;a=read('input',np.complex64).reshape(batch,n);b=read('output',np.complex64).reshape(batch,n);near('block-FFT-all-values',b,np.fft.fft(a,axis=1),3e-5,3e-3);gate('device-function-calls',trace[0]==repeat)
 elif k=='potrf_block':
  n,lda,threads,repeat=cfg;a=read('input_A',np.complex128).reshape(n,n,order='F');f=read('output',np.complex128).reshape(n,n,order='F');info=read('info',np.int32);gate('original-shared-LDA33-padding',lda==33 and trace[5]==1);gate('device-function-calls',trace[0]==repeat)
  if case=='singular-or-empty':gate('nonSPD-positive-info',info[0]==1)
  else:
   h=np.triu(a)+np.triu(a,1).conj().T;upper=np.triu(f);near('complex-upper-Cholesky-reconstruction',upper.conj().T@upper,h);near('independent-CPU-factor',upper,np.linalg.cholesky(h).conj().T);gate('info-zero',info[0]==0);near('unused-lower-triangle-preserved',np.tril(f,-1),np.tril(a,-1),0,0)
 else:
  n,seed,offset,threads,repeat=cfg;v=read('output');raw=read('raw',np.uint32).reshape(n//4,8);ref=np.asarray([philox(int(seed),(int(offset)+i)%65536,(int(offset)+i)//65536,8) for i in range(n//4)],dtype=np.uint32).reshape(n//4,8);gate('independent-Philox-10-counter-subsequence-words',np.array_equal(raw,ref));near('repeat-bit-identity',v,read('first'),0,0);gate('actual-device-thread-calls',trace[0]==n//4*repeat)
  if n:
   words=raw.astype(np.uint64);expected=[]
   for p in range(2):
    j=p*4;u=((words[:,j]>>5).astype(np.float64)*67108864+(words[:,j+1]>>6)+.5)/9007199254740992;z=((words[:,j+2]>>5).astype(np.float64)*67108864+(words[:,j+3]>>6)+.5)/9007199254740992;r=np.sqrt(-2*np.log(u));expected.extend([np.exp(1+.5*r*np.sin(2*np.pi*z)),np.exp(1+.5*r*np.cos(2*np.pi*z))])
   expected=np.stack(expected,axis=1).ravel();near('independent-53bit-Box-Muller-lognormal',v,expected,3e-12,1e-12)
  if n>=5000:
   z=(np.log(v)-1)/.5;gate('lognormal-analytic-moments',abs(z.mean())<.07 and abs(z.var()-1)<.12)
 if case=='original':
  expected={'introduction_example':[32,256,1],'simple_fft_block':[128,2,32,1],'potrf_block':[32,33,256,1],'philox_thread_api':[5000,1234,1,256,1]}[k];gate('original-template-dtype-workload-config',cfg.tolist()==expected)
 gate('cooperative-block-shape',trace[3]==threads if len(read('output')) else trace[3]==0);gate('hardware-warp-width',trace[4] in [32,64] if len(read('output')) else trace[4]==0)
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,input_sha256=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest(),output_values=outputs,oracle='NumPy full GEMM/FFT/complex Cholesky; independent integer Philox10 and FP64 Box-Muller; actual device call/thread/padding evidence')
