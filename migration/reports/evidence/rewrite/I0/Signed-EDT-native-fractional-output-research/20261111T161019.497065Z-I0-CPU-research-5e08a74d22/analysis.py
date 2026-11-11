import json,sys,numpy as np
from pathlib import Path
root=Path(sys.argv[1]);rows=[]
for stem,src,dtype,w,h in [('Circle','SignedCircle_256x206_64f.raw','<f8',256,206),('CircleInverted','SignedCircle_256x206_Inverted_64f.raw','<f8',256,206),('Lith','SignedLith_554x554_32f.raw','<f4',554,554)]:
 a=np.fromfile(root/src,dtype).reshape(h,w);a=2*a-1 if stem.startswith('Circle') else a
 name='SignedDistanceLithTransform_554x554_64f.raw' if stem=='Lith' else 'SignedDistanceCircleTransform_256x206_'+('Inverted_' if stem=='CircleInverted' else '')+'64f.raw';d=np.fromfile(root/name,'<f8').reshape(h,w);idx=None;rel=None
 if stem=='Lith':idx=np.fromfile(root/'SignedDistanceLithTransformVoronoiIndices_554x554_16s.raw','<i2').reshape(h,w,2);rel=np.fromfile(root/'SignedDistanceLithTransformVoronoiRelativeManhattan_554x554_16s.raw','<i2').reshape(h,w,2)
 row=dict(input=src,distance=name,input_min=float(a.min()),input_max=float(a.max()),distance_min=float(d.min()),distance_max=float(d.max()),nonfinite=int((~np.isfinite(d)).sum()),positive=int((d>0).sum()),negative=int((d<0).sum()),zero=int((d==0).sum()),sign_checks=[dict(cutoff=t,mismatches=int(np.count_nonzero((d>=0)!=(a>=t)))) for t in [0,.1,.5,1]],samples=[dict(x=x,y=y,input=float(a[y,x]),distance=float(d[y,x]),indices=None if idx is None else idx[y,x].tolist(),relative=None if rel is None else rel[y,x].tolist()) for y,x in [(0,0),(h//2,w//2),(h//2,w//4),(h//4,w//2),(h-1,w-1)]])
 if idx is not None:row.update(indices_min=idx.min(axis=(0,1)).tolist(),indices_max=idx.max(axis=(0,1)).tolist(),relative_min=rel.min(axis=(0,1)).tolist(),relative_max=rel.max(axis=(0,1)).tolist())
 rows.append(row)
Path(sys.argv[2]).write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
