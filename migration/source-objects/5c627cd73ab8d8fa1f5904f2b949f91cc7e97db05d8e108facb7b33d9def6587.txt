#!/usr/bin/env python3
"""Measure transient cellular label propagation with fixed strict descent links."""
import json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical
from image_watershed_research import NATIVE,SIZES
from image_watershed_reference import native_output_dir

def model(image,initial):
    h,w=image.shape;indices=np.arange(h*w,dtype=np.int32).reshape(h,w);parent=indices.copy();best=image.copy();slices=[]
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if not (dy or dx):continue
            y0,y1=max(0,-dy),min(h,h-dy);x0,x1=max(0,-dx),min(w,w-dx)
            dst=np.s_[y0:y1,x0:x1];src=np.s_[y0+dy:y1+dy,x0+dx:x1+dx];slices.append((dst,src))
            take=image[src]<best[dst];best[dst][take]=image[src][take];parent[dst][take]=indices[src][take]
    seeds=parent==indices;u=[];v=[]
    for dst,src in slices:
        eligible=seeds[dst];u.append(indices[dst][eligible]);v.append(indices[src][eligible])
    u=np.concatenate(u);v=np.concatenate(v);parent=parent.ravel();ii=indices.ravel();g=np.maximum(ii//w-1,0)*w+np.maximum(ii%w-1,0)
    gray=(best if initial[0] else image).ravel().copy();c=g[parent].copy() if initial[1] else g.copy()
    for iteration in range(2000):
        ng=gray[parent];nc=c[parent];mask=gray[v]==gray[u];np.minimum.at(nc,u[mask],c[v[mask]])
        if np.array_equal(ng,gray) and np.array_equal(nc,c):break
        gray,c=ng,nc
    else:raise ValueError('cell convergence')
    return c.reshape(image.shape),gray.reshape(image.shape),iteration

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';r=json.loads(rp.read_text());raw=ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']/'outputs';inputs=[]
    for item in p['inputs']:
        shape=item['height'],item['width'];sp=raw/(item['id']+'-n8-m0-r0.segments');lp=sp.with_suffix('.labels')
        if any(digest(f)!=r['products'][f.name]['sha256'] for f in [sp,lp]):raise ValueError('native identity')
        inputs.append((item['id'],ROOT/item['path'],shape,sp,lp,False))
    for name,(w,h) in SIZES.items():
        family='NPP' if name!='Corn_614x461_8u_Gray.raw' else 'NPP+'
        folder=native_output_dir(family);source=ROOT/family/'watershedSegmentation/images'/name
        sn='Segmented_'+name if family=='NPP' else 'Corn_Segments_8Way_614x461_8u.raw';ln='Labels_'+name if family=='NPP' else 'Corn_CompressedSegmentLabels_8Way_614x461_32u.raw';inputs.append((name,source,(h,w),folder/sn,folder/ln,family=='NPP+'))
    e=Experiment('I3','watershed-transient-cell-label-propagation','CPU-research',sources=[__file__,pp,rp,ROOT/'tools/moat/image_watershed_semantics_reference.py',ROOT/'tools/moat/image_watershed_reference.py',*[i[1] for i in inputs],*[ROOT/ref/'run.json' for ref in NATIVE.values()]])
    rows=[]
    for name,source,shape,sp,lp,compact in inputs:
        a=np.fromfile(source,np.uint8).reshape(shape);ns=np.fromfile(sp,np.uint8).reshape(shape);nl=np.fromfile(lp,'<u4').reshape(shape);nc=canonical(nl)
        for initial in [(0,0),(1,0),(0,1),(1,1)]:
            c,s,iterations=model(a,initial);cc=canonical(c)
            row=dict(case=name,initial=list(initial),iterations=iterations,segment_match=float(np.mean(s==ns)),partition_exact=bool(np.array_equal(cc,nc)),candidate_regions=int(np.unique(c).size),native_regions=int(np.unique(nl).size),raw_label_match=None if compact else float(np.mean(c==nl)))
            rows.append(row);print(row,flush=True)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[r['evidence'],*NATIVE.values()]);write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-cell-labels-research.json',result)
    record('IMG-02','独立同步细胞更新模型检查中间高度对marker最小编号的影响；18小输入/6原图及四种初始化分别封存，继续区分稳定灰度与瞬态标签传播。',[result['evidence']])

if __name__=='__main__':main()
