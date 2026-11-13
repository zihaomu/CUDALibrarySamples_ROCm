#!/usr/bin/env python3
"""Test whether labels join regional minima in the initial neighborhood minimum image."""
import json
import numpy as np
from scipy.ndimage import label,minimum_filter
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical
from image_watershed_research import NATIVE,SIZES
from image_watershed_reference import native_output_dir

def model(image,erosions):
    h,w=image.shape;indices=np.arange(h*w,dtype=np.int32).reshape(h,w);parent=indices.copy();best=image.copy()
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if not (dy or dx):continue
            y0,y1=max(0,-dy),min(h,h-dy);x0,x1=max(0,-dx),min(w,w-dx)
            dst=np.s_[y0:y1,x0:x1];src=np.s_[y0+dy:y1+dy,x0+dx:x1+dx]
            take=image[src]<best[dst];best[dst][take]=image[src][take];parent[dst][take]=indices[src][take]
    roots=parent.ravel().copy()
    for _ in range(32):
        nxt=roots[roots]
        if np.array_equal(nxt,roots):break
        roots=nxt
    else:raise ValueError('cycle')
    local=image.copy()
    for _ in range(erosions):local=minimum_filter(local,size=3,mode='nearest')
    c=np.zeros_like(parent);offset=0
    for value in np.unique(local):
        mask=local==value;cc,n=label(mask,np.ones((3,3)));c[mask]=cc[mask]+offset;offset+=n
    return c.ravel()[roots].reshape(image.shape),image.ravel()[roots].reshape(image.shape)

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';r=json.loads(rp.read_text());raw=ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']/'outputs'
    inputs=[]
    for item in p['inputs']:
        shape=item['height'],item['width'];sp=raw/(item['id']+'-n8-m0-r0.segments');lp=sp.with_suffix('.labels')
        if any(digest(f)!=r['products'][f.name]['sha256'] for f in [sp,lp]):raise ValueError('native identity')
        inputs.append((item['id'],ROOT/item['path'],shape,sp,lp))
    for name,(w,h) in SIZES.items():
        family='NPP' if name!='Corn_614x461_8u_Gray.raw' else 'NPP+'
        folder=native_output_dir(family);source=ROOT/family/'watershedSegmentation/images'/name
        sn='Segmented_'+name if family=='NPP' else 'Corn_Segments_8Way_614x461_8u.raw'
        ln='Labels_'+name if family=='NPP' else 'Corn_CompressedSegmentLabels_8Way_614x461_32u.raw'
        inputs.append((name,source,(h,w),folder/sn,folder/ln))
    e=Experiment('I3','watershed-one-step-neighborhood-minimum-label-model','CPU-research',sources=[__file__,pp,rp,ROOT/'tools/moat/image_watershed_semantics_reference.py',ROOT/'tools/moat/image_watershed_reference.py',*[i[1] for i in inputs],*[ROOT/ref/'run.json' for ref in NATIVE.values()]])
    rows=[]
    for name,source,shape,sp,lp in inputs:
        a=np.fromfile(source,np.uint8).reshape(shape);ns=np.fromfile(sp,np.uint8).reshape(shape);nl=np.fromfile(lp,'<u4').reshape(shape);nc=canonical(nl)
        for steps in [1,2]:
            c,s=model(a,steps);cc=canonical(c);pairs=np.unique(np.stack([cc.ravel(),nc.ravel()],axis=1),axis=0)
            row=dict(case=name,erosions=steps,segment_match=float(np.mean(s==ns)),partition_exact=bool(np.array_equal(cc,nc)),candidate_regions=int(np.unique(c).size),native_regions=int(np.unique(nl).size),candidate_basins_split_by_native=int(np.sum(np.bincount(pairs[:,0])>1)),native_basins_split_by_candidate=int(np.sum(np.bincount(pairs[:,1])>1)))
            rows.append(row);print(row,flush=True)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[r['evidence'],*NATIVE.values()]);write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-eroded-labels-research.json',result)
    record('IMG-02','在严格下降灰度模型外，独立检验邻域最小值图上的区域标签合并；18小输入/6原图、一次及两次邻域运算分别测量，不以研究模型预记支持。',[result['evidence']])

if __name__=='__main__':main()
