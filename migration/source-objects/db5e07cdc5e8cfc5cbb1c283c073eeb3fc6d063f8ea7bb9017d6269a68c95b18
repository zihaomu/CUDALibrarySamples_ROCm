#!/usr/bin/env python3
"""Freeze a separate classical connected-hysteresis contract for both C3 callers."""
import json
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 cpp=ROOT/'NPP/nppCanny/npp_canny_simple.cpp';py=cpp.with_suffix('.py');image=ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg'
 e=Experiment('I1','C3-Canny-contract-and-fixtures','CPU-fixtures',sources=[__file__,cpp,py,image]);base=ROOT/'build/canny-color-fixtures';base.mkdir(parents=True,exist_ok=True);cases=[]
 def add(name,a,low=50,high=100,semantic='general',kind='holdout'):
  h,w=a.shape[:2];d=base/name;d.mkdir(exist_ok=True);pitch=3*w+7;opitch=w+5;raw=np.full((h,pitch),149,np.uint8);raw[:,:3*w]=a.reshape(h,3*w);raw.tofile(d/'input.bin')
  (d/'params.txt').write_text(' '.join(map(str,[w,h,3,pitch,0,0,w,h,low,high,opitch]))+'\n');config=dict(case=name,width=w,height=h,channels=3,pitch=pitch,output_pitch=opitch,low=low,high=high,kind=kind,semantic=semantic);write(d/'config.json',config)
  cv2.imwrite(str(d/'image.png'),a);write(d/'manifest.json',dict(case=name,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in [d/'input.bin',d/'params.txt',d/'config.json',d/'image.png']}));cases.append(dict(case=name,fixture=str(d.relative_to(ROOT)),manifest_sha256=digest(d/'manifest.json'),semantic=semantic,kind=kind))
 add('original-teapot',cv2.imread(str(image)),kind='original')
 yy,xx=np.indices((67,91));flat=np.zeros((67,91,3),np.uint8)
 add('constant-zero',flat.copy(),semantic='empty');add('constant-gray',np.full_like(flat,77),semantic='empty')
 for channel in range(3):
  a=flat.copy();a[:,:,channel]=np.where(xx>45,200,0);add('step-channel-'+str(channel),a,semantic='straight-edge')
 a=np.zeros_like(flat);a[:,:46,0]=255;a[:,46:,2]=97;add('isoluminant-color-step',a,semantic='color-edge-gray-empty')
 a=np.where(xx[:,:,None]>45,18,0).astype(np.uint8);a=np.repeat(a,3,2);add('isolated-weak-step',a,semantic='no-strong-empty')
 b=a.copy();b[20:40,46:,:]=80;add('weak-step-with-strong-seed',b,semantic='strong-seeded-component')
 a=np.zeros_like(flat);a[(abs(xx-45)<2)|(abs(yy-33)<2)]=180;add('strong-cross',a,semantic='nonempty')
 a=np.zeros_like(flat);a[abs(xx-yy)<2]=180;add('strong-diagonal',a,semantic='nonempty')
 a=np.zeros_like(flat);a[0,:]=a[-1,:]=a[:,0]=a[:,-1]=255;add('border-frame',a,semantic='nonempty')
 a=np.zeros_like(flat);a[33,45]=255;add('impulse',a,semantic='nonempty')
 for seed,shape in [(128374,(43,59,3)),(983743,(97,131,3)),(762321,(73,85,3))]:add('independent-noise-'+str(seed),np.random.default_rng(seed).integers(0,256,shape,np.uint8))
 add('one-pixel',np.zeros((1,1,3),np.uint8),semantic='empty');add('single-row',np.repeat(np.arange(49,dtype=np.uint8)[None,:,None],3,2));add('single-column',np.repeat(np.arange(41,dtype=np.uint8)[:,None,None],3,2))
 a=np.random.default_rng(76128).integers(0,256,(47,63,3),np.uint8);add('equal-threshold',a,72,72);add('high-threshold',a,50,32767,semantic='no-strong-empty');add('zero-threshold',a,0,0)
 spec=dict(schema_version=1,status='FROZEN_IMPLEMENTATION_PROFILE',sample_ids=['NPP/nppCanny::npp_canny_simple.cpp','NPP/nppCanny::npp_canny_simple.py'],sources={str(p.relative_to(ROOT)):digest(p) for p in [cpp,py,image]},implementations=['rocm/ported/NPP/nppCanny/npp_canny_simple.cpp','rocm/ported/NPP/nppCanny/npp_canny_simple.py'],comparison_mode='ALGORITHM_VARIANT',algorithm=dict(stages='Sobel3, first maximum squared-gradient channel, floor integer L2, NMS >= both; replicate whole-image border',weak='suppressed > low',strong='suppressed > high',connection='Keep each complete 8-connected weak component if and only if it contains a strong pixel',production='GPU gradients, weak mask, union/find, strong-root mark and final binary mask; host may read only one convergence scalar'),original=dict(warmup=1,iterations=10,outputs=['edges_npp.png','edges_opencv_gray.png','edges_opencv_3ch.png'],CPU_comparisons='Original grayscale and three per-channel Canny/OR comparisons retained explicitly'),native_policy=dict(natural='Full native difference/IoU/edge/component statistics reported; this explicit classical algorithm variant does not promise NPP internal mask identity',geometric='Flat and isolated-weak cases must be empty; color/strong step must detect meaningful edges; primary CPU all pixels exact',scope='The accepted C1 three-border-pixel exception is not reused for C3'),cases=cases)
 write(e.path/'profile.json',spec);ref=e.finish('OBSERVED');spec['fixture_evidence']=ref;write(ROOT/'migration/rewrite/canny-color-profile.json',spec);record('I1',f'C3经典8连接滞后算法与{len(cases)}组输入已冻结：原始Teapot、单色/等亮度颜色边缘、强弱连接、边框/对角/噪声及阈值/小尺寸；保留C++/Python三输出和10次原流程。',[ref]);print(len(cases),ref)
if __name__=='__main__':main()
