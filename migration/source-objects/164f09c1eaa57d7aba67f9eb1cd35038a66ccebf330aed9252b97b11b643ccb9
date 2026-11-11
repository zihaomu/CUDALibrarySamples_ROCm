#!/usr/bin/env python3
"""Independent explicit site set and spatial-tree distance reference."""
import numpy as np
from scipy.spatial import cKDTree

def field(a,mode,cutoff,remap):
 z=a.astype(np.float64)
 if remap:z=(z-.5)*2
 if mode:z=z-cutoff
 if not np.all(np.isfinite(z)):raise ValueError('finite effective field required')
 return z

def sites(z,mode):
 h,w=z.shape;n=w*h;points=[];ids=[]
 if not mode:
  y,x=np.nonzero(z==0);return np.column_stack((x,y)).astype(np.float64),(y*w+x).astype(np.uint64)
 for vertical in [False,True]:
  left=z[:-1,:] if vertical else z[:,:-1];right=z[1:,:] if vertical else z[:,1:];cross=((left<0)&(right>0))|((left>0)&(right<0));y,x=np.nonzero(cross);a=left[cross];b=right[cross]
  with np.errstate(over='ignore'):denominator=b-a
  alpha=np.empty(len(a),np.float64);normal=np.isfinite(denominator);alpha[normal]=-a[normal]/denominator[normal]
  if np.any(~normal):aa=np.abs(a[~normal]);bb=np.abs(b[~normal]);scale=np.maximum(aa,bb);aa/=scale;bb/=scale;alpha[~normal]=aa/(aa+bb)
  points.append(np.column_stack((x if vertical else x+alpha,y+alpha if vertical else y)));ids.append((y*w+x+(n if vertical else 0)).astype(np.uint64))
 y,x=np.nonzero(z==0);points.append(np.column_stack((x,y)).astype(np.float64));ids.append((2*n+y*w+x).astype(np.uint64));return np.concatenate(points),np.concatenate(ids)

def model(a,mode,cutoff=0.,remap=0):
 z=field(a,mode,cutoff,remap);h,w=z.shape;n=w*h;points,ids=sites(z,mode);yy,xx=np.indices((h,w));query=np.column_stack((xx.ravel(),yy.ravel())).astype(np.float64);cost=np.full(n,np.inf,np.float64);chosen=np.full(n,np.iinfo(np.uint64).max,np.uint64);xy=np.full((n,2),-32768.,np.float64)
 if len(points):
  tree=cKDTree(points);neighbors=min(2,len(points));dist,ix=tree.query(query,k=neighbors,workers=1)
  if neighbors==1:ix=np.asarray(ix);selected=ix;ties=np.empty(0,np.int64)
  else:selected=ix[:,0].copy();ties=np.flatnonzero(dist[:,1]<=dist[:,0]+1e-10)
  # A tree's arbitrary equal-distance ordering is not a Voronoi tie policy.
  # Recompute all nearby exact costs with the frozen arithmetic and site IDs.
  for at in ties:
   near=np.asarray(tree.query_ball_point(query[at],float(dist[at,0])+1e-10),np.int64);delta=query[at]-points[near];c=delta[:,0]*delta[:,0]+delta[:,1]*delta[:,1];minimum=c.min();tied=near[c==minimum];selected[at]=tied[np.argmin(ids[tied])]
  xy=points[selected];chosen=ids[selected];delta=query-xy;cost=delta[:,0]*delta[:,0]+delta[:,1]*delta[:,1]
 value=np.sqrt(cost)
 if mode:value=np.where(z.ravel()<0,-value,value)
 indices=np.full((n,2),-32768,np.int16);relative=indices.copy();valid=chosen!=np.iinfo(np.uint64).max;indices[valid]=np.floor(xy[valid]).astype(np.int16);relative[valid]=(query[valid]-indices[valid]).astype(np.int16)
 visual=np.clip(np.trunc(value+(32700 if mode else 0)),0,65535).astype(np.uint16)
 return dict(distance=value.reshape(h,w),visualization=visual.reshape(h,w),indices=indices.reshape(h,w,2),relative=relative.reshape(h,w,2),site_ids=chosen.reshape(h,w),sites_xy=xy.reshape(h,w,2),effective_field=z,site_count=len(points))
