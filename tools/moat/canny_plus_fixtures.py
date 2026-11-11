#!/usr/bin/env python3
"""Freeze original preprocessing and new C1 holdouts before the full GPU port."""
import json
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

RESOLUTIONS=[(320,180),(640,360),(800,600),(1280,720),(1920,1080),(2560,1440),(3840,2160),(5120,2880)]

def original_gray(bgr):
    r=bgr[:,:,0].astype(np.float32);g=bgr[:,:,1].astype(np.float32);b=bgr[:,:,2].astype(np.float32)
    return ((r*np.float32(.2989)+g*np.float32(.587))+b*np.float32(.114)).astype(np.uint8)

def main():
    source=ROOT/'NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py';image=source.parent/'Teapot.jpg'
    e=Experiment('I1','CannyPlus-contract-and-fixtures','CPU-fixtures',sources=[__file__,source,image])
    base=ROOT/'build/canny-plus-fixtures';base.mkdir(exist_ok=True)
    bgr=cv2.imread(str(image));assert bgr is not None
    rows=[]
    def add(name,a,low=72,high=256,kind='holdout',extra=None):
        d=base/name;d.mkdir(exist_ok=True);h,w=a.shape;pitch=w+7;out_pitch=w+5
        data=np.full((h,pitch),149,np.uint8);data[:,:w]=a;data.tofile(d/'input.bin')
        (d/'params.txt').write_text(' '.join(map(str,[w,h,1,pitch,0,0,w,h,low,high,out_pitch]))+'\n')
        config=dict(case=name,width=w,height=h,channels=1,pitch=pitch,output_pitch=out_pitch,low=low,high=high,kind=kind,**(extra or {}));write(d/'config.json',config)
        write(d/'manifest.json',dict(case=name,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in [d/'input.bin',d/'params.txt',d/'config.json']}))
        rows.append(dict(case=name,fixture=str(d.relative_to(ROOT)),manifest_sha256=digest(d/'manifest.json'),kind=kind,
                         native_size_extension=h<3 or w<3))
    for w,h in RESOLUTIONS:
        add('original-'+str(w)+'x'+str(h),original_gray(cv2.resize(bgr,(w,h))),kind='original',extra=dict(original_file_sha256=digest(image),preprocess='Original BGR input deliberately passed to torchvision RGB weights; float32 arithmetic then uint8 truncation.'))
    old=json.loads((ROOT/'migration/rewrite/image-canny-stage-cases.json').read_text())['cases']
    for r in old:
        d=ROOT/r['fixture'];c=json.loads((d/'config.json').read_text())
        if c['channels']!=1:continue
        a=np.fromfile(d/'input.bin',np.uint8).reshape(c['height'],c['pitch'])[:,:c['width']]
        add('registered-'+r['case'],a,c['low'],c['high'],kind='registered-research')
    add('new-one-pixel',np.zeros((1,1),np.uint8));add('new-single-row',np.arange(37,dtype=np.uint8)[None,:]);add('new-single-column',np.arange(35,dtype=np.uint8)[:,None])
    add('new-flat',np.full((35,49),127,np.uint8));add('new-odd-noise',np.random.default_rng(9912026).integers(0,256,(97,131),np.uint8))
    yy,xx=np.indices((47,63));add('new-boundary-step',np.where(xx>0,50,30).astype(np.uint8));add('new-weak-cross',np.where((abs(xx-31)<2)|(abs(yy-23)<2),55,30).astype(np.uint8))
    impulse=np.zeros((63,65),np.uint8);impulse[31,32]=255;add('new-impulse',impulse)
    add('new-equal-threshold',np.where(xx>31,48,30).astype(np.uint8),72,72)
    add('new-high-threshold',np.where(xx>31,180,30).astype(np.uint8),72,32767)
    contract=dict(schema_version=1,status='FROZEN_IMPLEMENTATION_PROFILE',sample_id='NPP+/cannyEdgeDetectorPython::cannyEdgeDetector.py',
      source=str(source.relative_to(ROOT)),original_source_sha256=digest(source),original_image_sha256=digest(image),
      implementation='rocm/ported/NPP+/cannyEdgeDetectorPython/cannyEdgeDetector.py',comparison_mode='ALGORITHM_VARIANT',
      algorithm=dict(stages='migration/rewrite/image-canny-stages-contract.json',strong='suppressed > high',weak='suppressed >= low AND a gradient-axis neighbour has equal suppressed magnitude and the same quantized direction',border='independently clamp neighbour x/y to image bounds; no boundary-self substitution',threshold_range=[0,32767],layout='C1 uint8 source with byte pitch; independently pitched output 0/255; padding untouched'),
      original=dict(resolutions=RESOLUTIONS,warmup=5,iterations=1000,low=72,high=256,preprocess='cv2 BGR resize -> Torch CHW -> torchvision RGB-to-gray applied to original BGR ordering'),
      required_runtime=['repeat-and-changed-input','two-streams','concurrent-instances','CPU-float32-and-float16-conversion','pitched-and-noncontiguous','invalid-shape-dtype-threshold-ABI-span-alias','full-original-file-profile','actual-GPU-trace','validator-positive-negative'],
      native_policy=dict(interior_IoU_min=.98,original_nonempty=True,outer_border='Full project CPU comparison remains exact; native outer differences reported under declared boundary semantics, never discarded from logs.',small_dimensions='Project extension; native may reject only with recorded NPP size diagnostic. Original8-resolution baseline must run successfully.'),cases=rows)
    write(e.path/'profile.json',contract);ref=e.finish('OBSERVED');contract['fixture_evidence']=ref;write(ROOT/'migration/rewrite/canny-plus-profile.json',contract)
    record('I1',f'NPP+完整入口合同与{len(rows)}组输入已冻结：8个原始尺寸、已有C1研究输入与新边界/阈值/随机holdout；原BGR->Torch灰度语义和1000循环保留。',[ref]);print(len(rows))
if __name__=='__main__':main()
