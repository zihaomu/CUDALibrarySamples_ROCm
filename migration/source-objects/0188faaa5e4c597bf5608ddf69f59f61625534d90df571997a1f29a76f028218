#!/usr/bin/env python3
"""Recreate the frozen C3 images without replacing their immutable profile."""
import json
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 path=ROOT/'migration/rewrite/canny-color-profile.json';spec=json.loads(path.read_text());image=ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg';e=Experiment('I1','C3-Canny-deterministic-fixtures','CPU-fixtures',sources=[__file__,path,image,ROOT/'tools/moat/canny_color_fixtures.py']);yy,xx=np.indices((67,91));flat=np.zeros((67,91,3),np.uint8);arrays={'original-teapot':cv2.imread(str(image)),'constant-zero':flat.copy(),'constant-gray':np.full_like(flat,77)}
 for channel in range(3):
  a=flat.copy();a[:,:,channel]=np.where(xx>45,200,0);arrays['step-channel-'+str(channel)]=a
 a=flat.copy();a[:,:46,0]=255;a[:,46:,2]=97;arrays['isoluminant-color-step']=a;a=np.repeat(np.where(xx[:,:,None]>45,18,0).astype(np.uint8),3,2);arrays['isolated-weak-step']=a;b=a.copy();b[20:40,46:,:]=80;arrays['weak-step-with-strong-seed']=b
 a=flat.copy();a[(abs(xx-45)<2)|(abs(yy-33)<2)]=180;arrays['strong-cross']=a;a=flat.copy();a[abs(xx-yy)<2]=180;arrays['strong-diagonal']=a;a=flat.copy();a[0,:]=a[-1,:]=a[:,0]=a[:,-1]=255;arrays['border-frame']=a;a=flat.copy();a[33,45]=255;arrays['impulse']=a
 for seed,shape in [(128374,(43,59,3)),(983743,(97,131,3)),(762321,(73,85,3))]:arrays['independent-noise-'+str(seed)]=np.random.default_rng(seed).integers(0,256,shape,np.uint8)
 arrays.update({'one-pixel':np.zeros((1,1,3),np.uint8),'single-row':np.repeat(np.arange(49,dtype=np.uint8)[None,:,None],3,2),'single-column':np.repeat(np.arange(41,dtype=np.uint8)[:,None,None],3,2)})
 a=np.random.default_rng(76128).integers(0,256,(47,63,3),np.uint8)
 for name in ['equal-threshold','high-threshold','zero-threshold']:arrays[name]=a
 checks=[]
 for case in spec['cases']:
  name=case['case'];a=arrays[name];h,w=a.shape[:2];lo,hi=(72,72) if name=='equal-threshold' else (50,32767) if name=='high-threshold' else (0,0) if name=='zero-threshold' else (50,100);pitch=w*3+7;opitch=w+5;d=ROOT/case['fixture'];d.mkdir(parents=True,exist_ok=True);raw=np.full((h,pitch),149,np.uint8);raw[:,:3*w]=a.reshape(h,3*w);raw.tofile(d/'input.bin');(d/'params.txt').write_text(' '.join(map(str,[w,h,3,pitch,0,0,w,h,lo,hi,opitch]))+'\n');write(d/'config.json',dict(case=name,width=w,height=h,channels=3,pitch=pitch,output_pitch=opitch,low=lo,high=hi,kind=case['kind'],semantic=case['semantic']));cv2.imwrite(str(d/'image.png'),a);write(d/'manifest.json',dict(case=name,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in [d/'input.bin',d/'params.txt',d/'config.json',d/'image.png']}));checks.append(dict(check=name,passed=digest(d/'manifest.json')==case['manifest_sha256']))
 result=dict(status='PASSED' if len(checks)==22 and all(c['passed'] for c in checks) else 'FAILED',checks=checks);write(e.path/'replay.json',result);result['evidence']=e.finish('PASSED' if result['status']=='PASSED' else 'SELF_TEST_FAILED',result);write(ROOT/'migration/reports/canny-color-fixture-replay.json',result);record('I1','C3全部22组冻结输入从源码重建：'+result['status']+'；原始profile与证据来源不替换。',[result['evidence']]);print(result['status']);return int(result['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
