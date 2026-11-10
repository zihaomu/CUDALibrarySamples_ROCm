#!/usr/bin/env python3
"""Freeze original Fortran CSR arrays and explicit layout/error extensions."""
import json
import numpy as np
from experiment import ROOT,digest,write
CASES=['original','changed-values','layout','base0','repeat','irregular','singular-info']
KINDS=['batch','uniform_batch','reordering_phase','residual']
def system(n=5):
 if n==5:return dict(n=5,rows=[1,3,5,7,8,9],columns=[1,3,2,3,3,5,4,5],values=[4,1,3,2,5,1,1,2],rhs=[7,12,25,4,13])
 return dict(n=6,rows=[1,3,5,8,9,11,12],columns=[1,6,2,5,3,5,6,4,5,6,6],values=[3,1,2,1,6,2,2,5,7,3,8],rhs=[9,9,40,20,61,70])
def irregular(n,mtype):
 rows=[1];cols=[];vals=[]
 for i in range(n):
  for j in range(max(i-1,0) if not mtype else i,min(i+2,n)):
   cols.append(j+1);vals.append(4 if i==j else -.25)
  rows.append(len(cols)+1)
 return dict(n=n,rows=rows,columns=cols,values=vals,rhs=list(range(1,n+1)))
def generate(kind,case):
 systems=[system()]
 if kind=='batch':systems.append(system(6))
 if kind=='uniform_batch':
  systems.append(system());systems[1].update(values=[2,1,3,1,6,2,4,8],rhs=[13,15,29,8,14])
 if case=='irregular':systems=[irregular(7 if i==0 or kind=='uniform_batch' else 9,int(kind!='residual')) for i in range(len(systems))]
 metadata=[];payload={};config=[f'{kind} {len(systems)}']
 for i,s in enumerate(systems):
  n=s['n'];nrhs=2 if kind=='residual' else 1;ldb=n+n//2 if kind=='residual' else n;ldx=n+5 if kind=='residual' else n;base=0 if case=='base0' else 1;mtype=int(kind!='residual');reorder=1
  if case=='layout':ldb=n+3;ldx=n+7
  rows=np.array(s['rows'],dtype='<i4')-1+base;cols=np.array(s['columns'],dtype='<i4')-1+base;values=np.array(s['values'],dtype='<f8')
  if case=='changed-values':values*=1.25
  if case=='singular-info':values[:int(rows[1]-base)]=0
  b=np.full((nrhs,ldb),-97.,dtype='<f8');x=np.full((nrhs,ldx),-71.,dtype='<f8')
  for j in range(nrhs):b[j,:n]=j+1 if kind=='residual' else s['rhs']
  # Original residual initializes the complete X stride to zero.
  if kind=='residual' and case in ['original','repeat']:x.fill(0)
  else:x[:,:n]=0
  label='b'+str(i);description=dict(n=n,nnz=len(values),nrhs=nrhs,ldb=ldb,ldx=ldx,base=base,mtype=mtype,reorder=reorder,label=label)
  metadata.append(description);config.append(' '.join(str(description[k]) for k in ['n','nnz','nrhs','ldb','ldx','base','mtype','reorder']))
  for name,data in [('rows',rows),('columns',cols),('values',values),('B',b),('X',x)]:payload[label+'_'+name+'.bin']=data.tobytes()
 payload['config.txt']=('\n'.join(config)+'\n').encode()
 return metadata,payload
def main():
 profiles=[]
 for kind in KINDS:
  for case in CASES:
   root=ROOT/'tests/fixtures/rewrite-bindings'/kind/case;root.mkdir(parents=True,exist_ok=True);systems,payload=generate(kind,case)
   for name,value in payload.items():(root/name).write_bytes(value)
   write(root/'manifest.json',dict(kind='sparse-binding',profile=kind,case=case,systems=systems,expected_exit=2 if case=='singular-info' else 0,generator_sha256=digest(__file__),files={name:dict(bytes=len(value),sha256=digest(root/name)) for name,value in payload.items()}))
 for language,extension in [('fortran','f90'),('nvfortran','cuf')]:
  for kind in KINDS:
   source=f'cuDSS/{language}/{kind}/{kind}.{extension}';sid=f'cuDSS/{language}/{kind}::{kind}.{extension}';profiles.append(dict(sample_id=sid,source=source,original_sha256=digest(ROOT/source),kind=kind,language=language,implementation=f'rocm/ported/cuDSS/{language}/{kind}/{kind}.f90',fixture_root='tests/fixtures/rewrite-bindings/'+kind,cases=CASES,route='standard Fortran ISO_C_BINDING; CPU symbolic min-degree + project HIP CSR pivot LU/solve; vendor Fortran syntax converted, not nvfortran compiler support'))
 write(ROOT/'migration/rewrite/sparse-bindings.json',dict(schema_version=1,batch='R5',profiles=profiles,core='rocm/adapters/fortran/sparse_bridge.cpp'))
 print(len(profiles),'profiles',len(KINDS)*len(CASES),'distinct frozen input fixtures')
if __name__=='__main__':main()
