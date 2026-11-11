#!/usr/bin/env python3
"""Independent CPU graph oracle for the frozen closed-cell contour profile."""
import numpy as np
from image_ccl_reference import reference

def boundaries8(labels):
 h,w=labels.shape;out=np.zeros((h,w),bool)
 for dy,dx in [(dy,dx) for dy in [-1,0,1] for dx in [-1,0,1] if dy or dx]:
  a=(slice(max(0,-dy),h-max(0,dy)),slice(max(0,-dx),w-max(0,dx)));b=(slice(max(0,dy),h-max(0,-dy)),slice(max(0,dx),w-max(0,-dx)));out[a]|=labels[a]!=labels[b]
 return out

def model(image):
 raw,compact,count=reference(image);labels=compact-1;h,w=image.shape;n=h*w;valid=[]
 for direction in range(4):
  mask=np.ones((h,w),bool)
  if direction==0:mask[1:,:]=labels[1:,:]!=labels[:-1,:]
  elif direction==1:mask[:,1:]=labels[:,1:]!=labels[:,:-1]
  elif direction==2:mask[:-1,:]=labels[:-1,:]!=labels[1:,:]
  else:mask[:,:-1]=labels[:,:-1]!=labels[:,1:]
  y,x=np.nonzero(mask);valid.append(np.column_stack((4*(y*w+x)+direction,labels[y,x],x,y)))
 edges=np.concatenate(valid).astype(np.uint32);edges=edges[np.argsort(edges[:,0])];ids,c,x,y=edges.T;d=ids%4;m=len(edges);x0=x+((d==0)|(d==3));y0=y+((d==2)|(d==3));x1=x+((d==2)|(d==3));y1=y+((d==1)|(d==2));key_base=(np.uint64(y0)*(w+1)+x0)*count+c;keys=key_base*4+d;order=np.argsort(keys);sorted_keys=keys[order];end=(np.uint64(y1)*(w+1)+x1)*count+c;next_index=np.full(m,-1,np.int64)
 for turn in [1,0,3,2]:
  desired=end*4+(d+turn)%4;found=np.searchsorted(sorted_keys,desired);inside=found<m;match=np.zeros(m,bool);match[inside]=sorted_keys[found[inside]]==desired[inside];use=match&(next_index<0);next_index[use]=order[found[use]]
 if np.any(next_index<0) or not np.all(np.bincount(next_index,minlength=m)==1):raise ValueError('CPU edge graph must be a permutation of closed loops')
 visited=np.zeros(m,bool);loop=np.empty(m,np.uint32);position=np.empty(m,np.uint32);roots=[]
 # Sequential graph walking differs from GPU union/find and pointer jumping.
 for i in range(m):
  if visited[i]:continue
  roots.append(i);j=i;k=0
  while not visited[j]:visited[j]=True;loop[j]=ids[i];position[j]=k;k+=1;j=int(next_index[j])
  if j!=i:raise ValueError('CPU graph walk did not close at its start')
 geometry=np.column_stack((c,loop,position,x0,y0,x1,y1,x,y)).astype(np.uint32);geometry=geometry[np.lexsort((geometry[:,2],geometry[:,1]))];boundary=boundaries8(labels);info=np.zeros((count,7),np.uint32);info[:,0]=np.bincount(labels[boundary],minlength=count);info[:,1]=np.bincount(c,minlength=count);info[:,2]=np.bincount(c[np.asarray(roots,np.int64)],minlength=count);info[:,3:5]=np.uint32(0xffffffff);yy,xx=np.indices((h,w),dtype=np.uint32);np.minimum.at(info[:,3],labels.ravel(),xx.ravel());np.minimum.at(info[:,4],labels.ravel(),yy.ravel());np.maximum.at(info[:,5],labels.ravel(),xx.ravel());np.maximum.at(info[:,6],labels.ravel(),yy.ravel());return dict(raw=raw,labels=labels,mask=np.where(boundary,0,255).astype(np.uint8),info=info,geometry=geometry,totals=np.array([count,m,len(roots)],np.uint32))

def reconstruct(geometry,labels,info,start=1,stop=None,limit=262144):
 h,w=labels.shape;k=len(info);stop=k if stop is None else stop
 if not 0<=start<=stop<=k:raise ValueError('half-open marker range')
 out=np.full((h,w),255,np.uint8)
 if not len(geometry):return out
 selected=np.zeros(k,bool);selected[start:stop]=True
 if stop-start>1:selected&=info[:,0]<limit
 g=geometry[selected[geometry[:,0]]]
 if not len(g):return out
 c=g[:,0];px,py=g[:,7].astype(np.int64),g[:,8].astype(np.int64);x0,y0,x1,y1=(g[:,i].astype(np.int64) for i in [3,4,5,6]);top=(x1<x0);left=(y1>y0);bottom=(x1>x0);right=(y1<y0);nx=px-left+right;ny=py-top+bottom;inside=(nx>=0)&(ny>=0)&(nx<w)&(ny<h);g=g[inside];c=c[inside]
 # Only edges bordering an in-ROI foreign cell contribute pixel contours.
 for vx,vy in [(g[:,3].astype(np.int64),g[:,4].astype(np.int64)),(g[:,5].astype(np.int64),g[:,6].astype(np.int64))]:
  for dy in [-1,0]:
   for dx in [-1,0]:
    xx,yy=vx+dx,vy+dy;ok=(xx>=0)&(yy>=0)&(xx<w)&(yy<h);indices=np.flatnonzero(ok);indices=indices[labels[yy[indices],xx[indices]]==c[indices]];out[yy[indices],xx[indices]]=0
 return out
