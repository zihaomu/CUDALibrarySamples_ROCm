#!/usr/bin/env python3
import json,sys
from experiment import ROOT,write,digest
sys.path.insert(0,str(ROOT/'build/python-reference'));import numpy as np
original=np.array([1,4,2,2,5,1,10,8,6,9,7,5],np.float32)
for case in ['original','changed-values','irregular','layout','repeat','rank-deficient','rank-truncated']:
 m,n,batch,rank=3,2,2,2
 if case=='irregular':m,n,batch,rank=7,4,3,3
 if case=='rank-truncated':m,n,rank=8,5,2
 lda=m+3 if case=='layout' else m;ldu=m+2 if case=='layout' else m;ldv=n+2 if case=='layout' else n
 cfg=dict(m=m,n=n,rank=rank,batch=batch,lda=lda,ldu=ldu,ldv=ldv,strideA=lda*n+(7 if case=='layout' else 0),strideS=rank+(3 if case=='layout' else 0),strideU=ldu*rank+(5 if case=='layout' else 0),strideV=ldv*rank+(5 if case=='layout' else 0),repeat=3 if case=='repeat' else 1)
 a=np.full(batch*cfg['strideA'],-97,np.float32)
 for h in range(batch):
  matrix=original[h*6:(h+1)*6].reshape(3,2,order='F').copy() if m==3 and n==2 else np.random.default_rng(1234+h).normal(size=(m,n)).astype(np.float32)
  if case=='changed-values':matrix=-.7*matrix+np.arange(m)[:,None]
  if case=='rank-deficient':matrix[:,1]=2*matrix[:,0]
  view=a[h*cfg['strideA']:h*cfg['strideA']+lda*n].reshape(lda,n,order='F');view[:m]=matrix
 p=ROOT/'tests/fixtures/rewrite-extensions/svd'/case;p.mkdir(parents=True,exist_ok=True);a.tofile(p/'A.bin');write(p/'config.json',cfg);(p/'config.txt').write_text(''.join(f'{k} {v}\n' for k,v in cfg.items()));write(p/'manifest.json',dict(kind='svd',case=case,config=cfg,generator_sha256=digest(__file__),files={f.name:dict(sha256=digest(f),bytes=f.stat().st_size) for f in p.iterdir() if f.name!='manifest.json'}))
 print(case,cfg)
