#!/usr/bin/env python3
"""Freeze FP16 defaults and 2:4 tile/layout/activation extensions."""
import ctypes,json
import numpy as np
from experiment import ROOT,digest,write
CASES=['original','changed-values','layout','irregular','zero-A','ties','repeat']
def generate(advanced,case):
 m,n,k,batch=(32,16,32,2) if advanced else (32,32,64,1)
 if case=='irregular':m,n,k=16,32,32
 lda=k;ldb=k;ldc=n
 if case=='layout':lda+=8;ldb+=8;ldc+=8
 sa=m*lda+(128 if advanced or case=='layout' else 0);sb=n*ldb+(128 if advanced or case=='layout' else 0);sc=m*ldc+(128 if advanced or case=='layout' else 0)
 config=dict(m=m,n=n,k=k,batch=batch,lda=lda,ldb=ldb,ldc=ldc,stride_a=sa,stride_b=sb,stride_c=sc,transpose_b=1,search=int(not advanced),alpha=1,beta=1,relu_threshold=1,relu_upper=15,dtype=16)
 libc=ctypes.CDLL(None);libc.srand(1);rng=np.random.default_rng(137 if advanced else 71)
 a=np.zeros(batch*sa,dtype='<f2');b=np.zeros(batch*sb,dtype='<f2');c=np.zeros(batch*sc,dtype='<f2');bias=np.ones(m,dtype='<f2')
 for array,stride,rows,cols,ld in [(a,sa,m,k,lda),(b,sb,n,k,ldb),(c,sc,n if advanced and case in ['original','repeat'] else m,n,ldc)]:
  for z in range(batch):
   for i in range(rows):
    for j in range(cols):array[z*stride+i*ld+j]=(libc.rand()%10 if advanced else libc.rand()%5-2)
 if case=='changed-values':
  for array in [a,b,c]:array[:]=rng.uniform(-2,2,array.size).astype('<f2')
  bias=np.linspace(-.5,1.5,m,dtype='<f2');config.update(alpha=.75,beta=-.5)
 if case=='zero-A':
  a.fill(0)
  if advanced:
   edge=np.array([0,-.5,.5,14,14.5,15,-1,1],dtype='<f2')
   for z in range(batch):
    for i in range(m):c[z*sc+i*ldc:z*sc+i*ldc+n]=np.resize(edge,n)
 if case=='ties':
  for z in range(batch):
   for i in range(m):a[z*sa+i*lda:z*sa+i*lda+k]=1 if i%2 else -1
 return config,dict(A=a,B=b,C=c,bias=bias)
def main():
 profiles=[]
 for advanced in [False,True]:
  kind='sparse24_advanced' if advanced else 'sparse24';directory='matmul_advanced' if advanced else 'matmul';source=f'cuSPARSELt/{directory}/{directory}_example.cpp'
  for case in CASES:
   config,arrays=generate(advanced,case);root=ROOT/'tests/fixtures/rewrite-extensions'/kind/case;root.mkdir(parents=True,exist_ok=True);payload={name+'.bin':value.tobytes() for name,value in arrays.items()};payload['config.txt']=(''.join(f'{name} {value}\n' for name,value in config.items())).encode();payload['config.json']=(json.dumps(config,sort_keys=True)+'\n').encode()
   for name,value in payload.items():(root/name).write_bytes(value)
   write(root/'manifest.json',dict(kind=kind,case=case,config=config,advanced=advanced,generator_sha256=digest(__file__),original_source_sha256=digest(ROOT/source),storage='FP16 A/B/C/bias, FP32 accumulation; row major A N/B T; TILE max L1 2-per-row-and-column',files={name:dict(bytes=len(value),sha256=digest(root/name)) for name,value in payload.items()}))
  profiles.append(dict(kind=kind,batch='R7',sample_id=f'cuSPARSELt/{directory}::{directory}_example.cpp',source=source,implementation='rocm/ported/'+source,fixture_root='tests/fixtures/rewrite-extensions/'+kind,cases=CASES,route='project HIP 4x4 TILE pruning, two packed FP16 values plus nibble metadata per group of four; sparse-only HIP matmul; explicit GPU search or bias/ReLU; not native hipSPARSELt or vendor opaque format'))
 path=ROOT/'migration/rewrite/extensions.json';spec=json.loads(path.read_text());spec['profiles']=[p for p in spec['profiles'] if p['kind'] not in ['sparse24','sparse24_advanced']]+profiles;write(path,spec);print('2 profiles, 14 immutable cases')
if __name__=='__main__':main()
