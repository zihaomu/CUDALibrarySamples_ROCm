#!/usr/bin/env python3
"""Freeze exact-valued 8-connected components and original CCL workflows."""
import json,re,shutil
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record
SIZES=[('lena',512,512),('CT_skull',512,512),('PCB_METAL',509,335),('PCB2',1024,683),('PCB',1280,720)]
def main():
 originals=[];sources=[Path(__file__)]
 for family in ['NPP','NPP+']:
  d=ROOT/family/'batchedLabelMarkersAndCompression';source=d/('batchedLabelMarkersAndCompression.cpp' if family=='NPP' else 'batchedLabelMarkersAndCompressionNPPPlus.cpp');sources.extend([source,d/'batchedLabelMarkersAndCompression.h'])
  for stem,w,h in SIZES:
   p=d/'images'/(stem+f'_{w}x{h}_8u.raw');a=np.fromfile(p,np.uint8);assert len(a)==w*h
   originals.append(dict(case=('npp-' if family=='NPP' else 'plus-')+stem,source=str(p.relative_to(ROOT)),width=w,height=h,values=len(np.unique(a)),sha256=digest(p),bytes=p.stat().st_size))
 e=Experiment('I2','CCL-frozen-contracts-and-golden-audit','CPU-contract',sources=sources);fixtures=ROOT/'build/image-ccl-fixtures';fixtures.mkdir(parents=True,exist_ok=True);cases=[]
 def add(name,a,original=None):
  h,w=a.shape;pitch=w+7;data=np.full((h,pitch),193,np.uint8);data[:,:w]=a;d=fixtures/name;d.mkdir(exist_ok=True);data.tofile(d/'input.bin');cfg=dict(case=name,width=w,height=h,pitch=pitch,connectivity=8,all_values_including_zero=True);write(d/'config.json',cfg);write(d/'manifest.json',dict(files={n:dict(bytes=(d/n).stat().st_size,sha256=digest(d/n)) for n in ['input.bin','config.json']}));cases.append(dict(**cfg,fixture=str(d.relative_to(ROOT)),manifest_sha256=digest(d/'manifest.json'),original=original))
 for x in originals:add(x['case'],np.fromfile(ROOT/x['source'],np.uint8).reshape(x['height'],x['width']),x)
 add('three-by-three-stale-root',np.array([[0,2,0],[0,2,0],[1,0,1]],np.uint8))
 for name,h,w in [('one-pixel',1,1),('single-row',1,521),('single-column',519,1),('scan-255',3,85),('scan-256',2,128),('scan-257',1,257),('scan-recursive',513,515)]:
  yy,xx=np.indices((h,w));add(name,((xx%2)+2*(yy%2)).astype(np.uint8))
 for value in [0,1,255]:add('constant-'+str(value),np.full((19,33),value,np.uint8))
 for seed,h,w in [(847,17,31),(83827,61,79),(654981,123,257)]:add('noise-'+str(seed),np.random.default_rng(seed).integers(0,11,(h,w),dtype=np.uint8))
 a=np.zeros((65,67),np.uint8);np.fill_diagonal(a,1);add('diagonal-touch',a)
 a=np.zeros((67,71),np.uint8);a[0,:]=1;a[-1,:]=1;a[:,0]=1;a[:,-1]=1;a[30:37,30:37]=2;add('frame-hole-and-island',a)
 a=np.zeros((73,521),np.uint8);a[::2,:]=1;a[1::4,-1]=1;a[3::4,0]=1;add('long-serpentine-component',a)
 golden=[]
 for family in ['NPP','NPP+']:
  d=ROOT/family/'batchedLabelMarkersAndCompression/images'
  for stem,w,h in SIZES:
   a=np.fromfile(d/(stem+f'_{w}x{h}_8u.raw'),np.uint8).reshape(h,w)
   for p in sorted(d.glob(('Lena' if stem=='lena' else stem)+f'*{w}x{h}_32u.raw')):
    b=np.fromfile(p,'<u4').reshape(h,w);bad=0
    for dy,dx in [(0,1),(1,0),(1,1),(1,-1)]:
     s=(slice(0,h-dy),slice(max(0,-dx),w-max(0,dx)));t=(slice(dy,h),slice(max(0,dx),w-max(0,-dx)));bad+=int(np.count_nonzero((a[s]==a[t])&(b[s]!=b[t])))
    golden.append(dict(file=str(p.relative_to(ROOT)),sha256=digest(p),labels=len(np.unique(b)),equal_adjacent_split_pairs=bad,conformance='FAILED' if bad else 'NECESSARY_CHECK_ONLY'))
 profile=dict(schema_version=1,algorithm='equal-byte-value eight-connected maximal components; every pixel including zero belongs to one component',raw_labels='minimum row-major pixel index + 1',compact_labels='consecutive 1..K ordered by minimum row-major pixel index',comparison_mode='EXACT_PARTITION_AFTER_BIJECTIVE_LABEL_MAP',cases=cases,originals=originals,original_sources={str(p.relative_to(ROOT)):digest(p) for p in sources[1:]},original_branches=dict(NPP='individual labels/compact and heterogeneous batch labels/compact: 20 files',NPP_plus_default='individual labels/compact and heterogeneous batch labels: 15 files',NPP_plus_CUDA11U1='adds batch compression: 20 files'),CLI=dict(default_batch=5,valid_batch_counts=[1,2,3,4,5],original_partial_batch_bug='Original later batch loops hardcode 5 after allocating only -b images. Project consistently processes requested 1..5 and rejects invalid counts before GPU initialization.',errors=['missing-b','zero','negative','above-five','noninteger','duplicate','unknown-option','missing-input','truncated-input','unwritable-output','no-GPU']),GPU='all pixel initialization, equality union/find, prefix-scan compaction and final labels on GPU; CPU may read scalar convergence flag and final component count',runtime=['nondefault-stream','changed-input','repeat','independent-concurrent-instances','pitched-input-and-output-padding','heterogeneous-batch-and-tail','undersized-device-buffers','overlap-and-device-identity','no-host-image-compute'],sources=['https://docs.nvidia.com/cuda/nppplus/image_filtering_functions.html','https://docs.nvidia.com/cuda/archive/11.8.0/npp/group__image__filter__label__markers.html'],native_policy='Vendor label numbers arbitrary; zero can be a real component. Report actual split/merge defects against independent CPU, rather than reproducing them or accepting an invalid partition.')
 write(ROOT/'migration/rewrite/image-ccl-profile.json',profile);write(e.path/'profile.json',profile);write(e.path/'golden-audit.json',golden);ref=e.finish('OBSERVED');write(ROOT/'migration/reports/image-ccl-contracts.json',dict(status='FROZEN',cases=len(cases),original_inputs=len(originals),historical_golden_files=len(golden),historical_golden_failures=sum(x['conformance']=='FAILED' for x in golden),evidence=ref));record('I2',f'冻结CCL {len(cases)}组输入、两原始入口/完整条件分支、1..5实际batch及错误合同；{len(golden)}个历史golden全部出现同值相邻分裂，作为实测旧文件缺陷保留，当前SDK另测，不复制错误分区。',[ref],state='IN_PROGRESS');print(len(cases),ref)
if __name__=='__main__':main()
