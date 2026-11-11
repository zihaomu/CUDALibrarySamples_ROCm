#!/usr/bin/env python3
"""Independent full-capacity state oracle, including untouched reuse tails."""
import numpy as np
from image_contour_model import model

def expected_state(data,w,h,pitch,previous=None):
 v=model(np.frombuffer(data,np.uint8).reshape(h,pitch)[:,:w]);n=w*h;k,m,_=map(int,v['totals']);out={'src':data}
 for name,step,pad,key in [('raw',4*w+20,167,'raw'),('labels',4*w+28,185,'labels'),('mask',w+13,171,'mask')]:
  a=np.frombuffer(previous[name],np.uint8).reshape(h,step).copy() if previous is not None else np.full((h,step),pad,np.uint8);b=v[key].astype('u1' if name=='mask' else '<u4').view(np.uint8).reshape(h,-1);a[:,:b.shape[1]]=b;out[name]=a.tobytes()
 for name,size,pad in [('info',n*28,221),('geometry',4*n*36,205)]:
  b=bytearray(previous[name]) if previous is not None else bytearray([pad]*size);prefix=v[name].astype('<u4').tobytes();b[:len(prefix)]=prefix;out[name]=bytes(b)
 out['totals']=v['totals'].astype('<u4').tobytes();return out,v
