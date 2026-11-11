import json,sys,numpy as np
from scipy.spatial import cKDTree
from pathlib import Path
root=Path(sys.argv[1]);rows=[]
for stem,src,dtype,w,h in [('Circle','SignedCircle_256x206_64f.raw','<f8',256,206),('CircleInverted','SignedCircle_256x206_Inverted_64f.raw','<f8',256,206),('Lith','SignedLith_554x554_32f.raw','<f4',554,554)]:
 a=np.fromfile(root/src,dtype).reshape(h,w).astype(np.float64);z=(a-.5)*2 if stem.startswith('Circle') else a-float(np.float32(.1));points=[];yy,xx=np.nonzero(z==0);points.append(np.column_stack((xx,yy)).astype(np.float64))
 for axis in [1,0]:
  left=z[:,:-1] if axis==1 else z[:-1,:];right=z[:,1:] if axis==1 else z[1:,:];cross=((left<0)&(right>0))|((left>0)&(right<0));y,x=np.nonzero(cross);alpha=-left[cross]/(right[cross]-left[cross]);points.append(np.column_stack((x+alpha if axis==1 else x,y if axis==1 else y+alpha)))
 p=np.concatenate(points);yy,xx=np.indices(z.shape);query=np.column_stack((xx.ravel(),yy.ravel()));dist=cKDTree(p).query(query,workers=1)[0].reshape(z.shape);dist*=np.sign(z);name='SignedDistanceLithTransform_554x554_64f.raw' if stem=='Lith' else 'SignedDistanceCircleTransform_256x206_'+('Inverted_' if stem=='CircleInverted' else '')+'64f.raw';native=np.fromfile(root/name,'<f8').reshape(h,w);delta=np.abs(dist-native);rows.append(dict(input=src,level=0 if stem.startswith('Circle') else float(np.float32(.1)),sites=len(p),max_abs_difference_from_native=float(delta.max()),mean_abs_difference=float(delta.mean()),p99_abs_difference=float(np.quantile(delta,.99)),sign_disagreement=int(np.count_nonzero(np.sign(dist)!=np.sign(native))),project_min=float(dist.min()),project_max=float(dist.max()),scope='Candidate mathematical definition only; exact zero-crossing point-set Euclidean distance with source sign. No GPU implementation or support claim.'))
Path(sys.argv[2]).write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
