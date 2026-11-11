#!/usr/bin/env python3
"""Recreate all frozen inputs without replacing the profile or its provenance."""
import importlib.util,json,shutil,tempfile
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from canny_plus_fixtures import original_gray
from image_progress import record

def main():
 profile=ROOT/'migration/rewrite/canny-plus-profile.json';spec=json.loads(profile.read_text());image=ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg'
 sources=[__file__,ROOT/'tools/moat/canny_plus_fixtures.py',ROOT/'tools/moat/image_canny_fixtures.py',profile,image]
 e=Experiment('I1','CannyPlus-deterministic-fixture-replay','CPU-fixtures',sources=sources);checks=[]
 with tempfile.TemporaryDirectory(prefix='canny-fixtures-') as temporary:
  root=__import__('pathlib').Path(temporary);(root/'tests/fixtures').mkdir(parents=True);(root/'NPP+/cannyEdgeDetectorPython').mkdir(parents=True);shutil.copyfile(image,root/'NPP+/cannyEdgeDetectorPython/Teapot.jpg')
  module_spec=importlib.util.spec_from_file_location('fixture_builder',ROOT/'tools/moat/image_canny_fixtures.py');module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module);module.ROOT=root;module.main()
  bgr=cv2.imread(str(image));yy,xx=np.indices((47,63));impulse=np.zeros((63,65),np.uint8);impulse[31,32]=255
  arrays={'new-one-pixel':np.zeros((1,1),np.uint8),'new-single-row':np.arange(37,dtype=np.uint8)[None,:],'new-single-column':np.arange(35,dtype=np.uint8)[:,None],'new-flat':np.full((35,49),127,np.uint8),'new-odd-noise':np.random.default_rng(9912026).integers(0,256,(97,131),np.uint8),'new-boundary-step':np.where(xx>0,50,30).astype(np.uint8),'new-weak-cross':np.where((abs(xx-31)<2)|(abs(yy-23)<2),55,30).astype(np.uint8),'new-impulse':impulse,'new-equal-threshold':np.where(xx>31,48,30).astype(np.uint8),'new-high-threshold':np.where(xx>31,180,30).astype(np.uint8)}
  for case in spec['cases']:
   name=case['case'];low,high=72,256;extra={}
   if case['kind']=='original':
    w,h=map(int,name.removeprefix('original-').split('x'));a=original_gray(cv2.resize(bgr,(w,h)));extra=dict(original_file_sha256=digest(image),preprocess='Original BGR input deliberately passed to torchvision RGB weights; float32 arithmetic then uint8 truncation.')
   elif case['kind']=='registered-research':
    d=root/'tests/fixtures/image-canny'/name.removeprefix('registered-');c=json.loads((d/'config.json').read_text());a=np.fromfile(d/'input.bin',np.uint8).reshape(c['height'],c['pitch'])[:,:c['width']];low,high=c['low'],c['high']
   else:
    a=arrays[name]
    if name=='new-equal-threshold':low,high=72,72
    if name=='new-high-threshold':low,high=72,32767
   h,w=a.shape;pitch=w+7;out_pitch=w+5;d=ROOT/case['fixture'];d.mkdir(parents=True,exist_ok=True);data=np.full((h,pitch),149,np.uint8);data[:,:w]=a;data.tofile(d/'input.bin')
   (d/'params.txt').write_text(' '.join(map(str,[w,h,1,pitch,0,0,w,h,low,high,out_pitch]))+'\n');write(d/'config.json',dict(case=name,width=w,height=h,channels=1,pitch=pitch,output_pitch=out_pitch,low=low,high=high,kind=case['kind'],**extra));write(d/'manifest.json',dict(case=name,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in [d/'input.bin',d/'params.txt',d/'config.json']}))
   checks.append(dict(check=name,passed=digest(d/'manifest.json')==case['manifest_sha256']))
 v=dict(status='PASSED' if len(checks)==31 and all(c['passed'] for c in checks) else 'FAILED',checks=checks);write(e.path/'replay.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',v);write(ROOT/'migration/reports/canny-plus-fixture-replay.json',v)
 record('I1','31组原始/随机/几何输入从源码重新生成：'+v['status']+'；未替换冻结profile或历史来源。',[v['evidence']]);print(v['status'],[c for c in checks if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
