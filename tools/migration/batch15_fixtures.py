#!/usr/bin/env python3
"""Original image bytes plus deterministic boundary/stride/ROI fixtures."""
import pathlib,json,hashlib,sys,ctypes
from catalog import ROOT
sys.path.insert(0,str(ROOT/'build/python-reference'))
import numpy as np
from PIL import Image
libc=ctypes.CDLL(None)
base=ROOT/'build/batch15-fixtures';records=[]
cases=['original','irregular','changed-values','boundary','repeat','singular-or-empty']
for kind in ['canny','ncc','distance','flood']:
 for case in cases:
  images=[]
  if case in ['original','repeat']:
   if kind=='canny':images=[np.asarray(Image.open(ROOT/'NPP/nppCanny/example_input.png').convert('RGB'))[:,:,::-1].copy()]
   elif kind=='ncc':images=[np.fromfile(ROOT/'NPP/templateMatching/images/CircuitBoard_2048x1024_8u.raw',np.uint8).reshape(1024,2048,1)]
   elif kind=='distance':images=[np.fromfile(ROOT/('NPP/distanceTransform/images/'+f),np.uint8).reshape(h,w,1) for f,w,h in [('Dolphin1_313x317_8u.raw',313,317),('TestImage3_diamond_64x64_8u.raw',64,64)]]
   else:images=[np.fromfile(ROOT/('NPP+/floodFill/images/'+f),np.uint8).reshape(h,w,3) for f,w,h in [('RainbowChart_RGB_C3_1024x445_8u.raw',1024,445),('SeabedSampler_RGB_C3_675x1024_8u.raw',675,1024)]]
  else:
   h,w=(29,37) if case=='irregular' else (11,13) if case=='boundary' else (57,73);c=3 if kind in ['canny','flood'] else 1;rng=np.random.default_rng(20261110);img=rng.integers(0,256,(h,w,c),dtype=np.uint8)
   if kind=='distance':img.fill(255);img[::7,::11]=0
   if kind=='flood':img[:]=[50,60,80];img[:,w//2:w//2+1]=[240,250,254];img[h//3:2*h//3,w//4:w//3]=[51,61,81]
   if case=='singular-or-empty':img.fill(255 if kind=='distance' else 0)
   images=[img]
  target=base/kind/case;target.mkdir(parents=True,exist_ok=True);index=0
  for image_index,img in enumerate(images):
   h,w,c=img.shape;pad=7 if case in ['irregular','boundary'] else 0;stride=w*c+pad;raw=np.full((h,stride),173,np.uint8);raw[:,:w*c]=img.reshape(h,w*c);rx,ry,rw,rh=(1,1,w-2,h-2) if case=='boundary' else (0,0,w,h);modes=range(3) if kind=='flood' and image_index==0 and case in ['original','repeat'] else range(3,5) if kind=='flood' and case in ['original','repeat'] else [4 if kind=='flood' and case=='boundary' else 0]
   for mode in modes:
    prefix=target/str(index);prefix.mkdir(exist_ok=True);(prefix/'input.bin').write_bytes(raw.tobytes());p0,p1=(100,180) if case=='changed-values' else (50,100);sx,sy=(327,426) if kind=='flood' and image_index==0 and case in ['original','repeat'] else (20,24) if kind=='flood' and case in ['original','repeat'] else (rw//4,rh//2);tw,th,tx,ty=96,64,1300,850
    if kind=='ncc':
     if case not in ['original','repeat']:tw,th=min(8,rw),min(8,rh);tx=rw//3;ty=rh//3;tx=min(tx,rw-tw);ty=min(ty,rh-th)
     crop=img[ry+ty:ry+ty+th,rx+tx:rx+tx+tw,0].astype(np.float64);libc.srand(1234);noise=np.asarray([(libc.rand()%7)-3 for _ in range(tw*th)]).reshape(th,tw);tpl=np.clip(.6*crop+30+noise+.5,0,255).astype(np.uint8);(prefix/'template.bin').write_bytes(tpl.tobytes())
    cfg=[w,h,c,stride,rx,ry,rw,rh,p0,p1,4 if case=='boundary' else 8,sx,sy,mode,tw,th,tx,ty]
    (prefix/'params.txt').write_text(' '.join(map(str,cfg))+'\n');records.append(dict(kind=kind,case=case,index=index,params=cfg,input_sha256=hashlib.sha256(raw.tobytes()).hexdigest(),template_sha256=hashlib.sha256((prefix/'template.bin').read_bytes()).hexdigest() if kind=='ncc' else None));index+=1
  (target/'count.txt').write_text(str(index)+'\n')
(ROOT/'migration/environments/batch15-fixtures.json').write_text(json.dumps(dict(seed=20261110,records=records),indent=2)+'\n');print('Prepared',len(records),'image profiles')
