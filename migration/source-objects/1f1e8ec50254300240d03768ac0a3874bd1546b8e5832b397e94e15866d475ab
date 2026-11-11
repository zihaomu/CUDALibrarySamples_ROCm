#!/usr/bin/env python3
"""Produce deterministic images for native Canny contract investigation."""
import json,hashlib
from pathlib import Path
import cv2,numpy as np
from experiment import ROOT,write,digest

def main():
 base=ROOT/'tests/fixtures/image-canny';base.mkdir(exist_ok=True);cases=[];image=cv2.imread(str(ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg'));assert image is not None
 images=[('teapot-c3',image),('teapot-c1',cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)),('noise-c3',np.random.default_rng(20261111).integers(0,256,(41,53,3),np.uint8)),('noise-c1',np.random.default_rng(124).integers(0,256,(43,51),np.uint8)),('ties-c1',(np.indices((33,41)).sum(0)%8*32).astype(np.uint8)),('step-c1',np.where(np.indices((33,41))[1]>20,200,30).astype(np.uint8)),('tiny-c1',np.zeros((8,9),np.uint8))]
 images += [('equal'+str(t)+'-c'+str(c),image if c==3 else cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)) for t in [0,1,50,100,256] for c in [1,3]]
 images += [('noise-equal'+str(t)+'-c1',np.random.default_rng(124).integers(0,256,(43,51),np.uint8)) for t in [1,72,100,256]]
 images += [('high'+str(t)+'-c'+str(c),image if c==3 else cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)) for t in [512,10000] for c in [1,3]]
 yy,xx=np.indices((67,79))
 images += [('holdout-weak-step-c1',np.where(xx>31,50,30).astype(np.uint8)),
            ('holdout-weak-cross-c1',np.where((abs(xx-39)<3)|(abs(yy-33)<3),55,30).astype(np.uint8)),
            ('holdout-weak-diagonal-c1',np.where(abs(xx-yy)<3,60,30).astype(np.uint8)),
            ('holdout-low-noise-c1',np.random.default_rng(928734).integers(0,65,(67,79),np.uint8)),
            ('holdout-mixed-noise-c1',np.random.default_rng(837462).integers(0,256,(73,91),np.uint8))]
 images += [('border-check'+str(seed)+'-c1',np.random.default_rng(seed).integers(0,65,shape,np.uint8)) for seed,shape in [(91203,(13,19)),(40519,(65,63)),(83914,(32,35))]]
 for name,a in images:
  d=base/name;d.mkdir(exist_ok=True);h,w=a.shape[:2];c=1 if a.ndim==2 else a.shape[2];pitch=w*c+7;data=np.full((h,pitch),149,np.uint8);data[:,:w*c]=a.reshape(h,w*c);data.tofile(d/'input.bin');params=[w,h,c,pitch,0,0,w,h,50 if c==3 else 72,100 if c==3 else 256,w+5];
  if name.startswith('equal'):params[8]=params[9]=int(name.split('-')[0].replace('equal',''))
  if name.startswith('noise-equal'):params[8]=params[9]=int(name.split('-')[1].replace('equal',''))
  if name.startswith('high'):params[9]=int(name.split('-')[0].replace('high',''))
  (d/'params.txt').write_text(' '.join(map(str,params))+'\n');config=dict(case=name,width=w,height=h,channels=c,pitch=pitch,roi=[0,0,w,h],low=params[8],high=params[9],output_pitch=w+5,kind='canny-native-contract-investigation');write(d/'config.json',config);manifest=dict(kind='canny-native-contract-investigation',case=name,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in [d/'input.bin',d/'params.txt',d/'config.json']});write(d/'manifest.json',manifest);cases.append(config)
 write(ROOT/'migration/rewrite/image-canny-probe-cases.json',cases);print(len(cases))
if __name__=='__main__':main()
