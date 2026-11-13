#!/usr/bin/env python3
"""Investigate label equivalences induced by neighbors of terminal minima."""
import json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical
from image_watershed_research import NATIVE,SIZES
from image_watershed_reference import native_output_dir

def model(image,variant):
    h,w=image.shape;indices=np.arange(h*w,dtype=np.int32).reshape(h,w);parent=indices.copy();best=image.copy();slices=[]
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if not (dy or dx):continue
            y0,y1=max(0,-dy),min(h,h-dy);x0,x1=max(0,-dx),min(w,w-dx)
            dst=np.s_[y0:y1,x0:x1];src=np.s_[y0+dy:y1+dy,x0+dx:x1+dx];slices.append((dst,src))
            take=image[src]<best[dst];best[dst][take]=image[src][take];parent[dst][take]=indices[src][take]
    seeds=parent==indices;roots=parent.ravel().copy()
    for _ in range(32):
        nxt=roots[roots]
        if np.array_equal(nxt,roots):break
        roots=nxt
    else:raise ValueError('cycle')
    roots=roots.reshape(image.shape);seg=image.ravel()[roots];u=[];v=[]
    for dst,src in slices:
        eligible=seeds[dst]&(seg[src]==image[dst])
        if variant=='initial-minimum':eligible &= best[src]==image[dst]
        elif variant=='original-value':eligible &= image[src]==image[dst]
        u.append(indices[dst][eligible]);v.append(roots[src][eligible])
    u=np.concatenate(u);v=np.concatenate(v);graph=coo_matrix((np.ones(len(u),np.uint8),(u,v)),shape=(h*w,h*w))
    _,cc=connected_components(graph,directed=False);return cc[roots],seg

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';r=json.loads(rp.read_text());raw=ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']/'outputs';inputs=[]
    for item in p['inputs']:
        shape=item['height'],item['width'];sp=raw/(item['id']+'-n8-m0-r0.segments');lp=sp.with_suffix('.labels')
        if any(digest(f)!=r['products'][f.name]['sha256'] for f in [sp,lp]):raise ValueError('native identity')
        inputs.append((item['id'],ROOT/item['path'],shape,sp,lp))
    for name,(w,h) in SIZES.items():
        family='NPP' if name!='Corn_614x461_8u_Gray.raw' else 'NPP+'
        folder=native_output_dir(family);source=ROOT/family/'watershedSegmentation/images'/name
        sn='Segmented_'+name if family=='NPP' else 'Corn_Segments_8Way_614x461_8u.raw';ln='Labels_'+name if family=='NPP' else 'Corn_CompressedSegmentLabels_8Way_614x461_32u.raw';inputs.append((name,source,(h,w),folder/sn,folder/ln))
    e=Experiment('I3','watershed-terminal-minimum-neighbor-label-graph','CPU-research',sources=[__file__,pp,rp,ROOT/'tools/moat/image_watershed_semantics_reference.py',ROOT/'tools/moat/image_watershed_reference.py',*[i[1] for i in inputs],*[ROOT/ref/'run.json' for ref in NATIVE.values()]])
    rows=[]
    for name,source,shape,sp,lp in inputs:
        a=np.fromfile(source,np.uint8).reshape(shape);ns=np.fromfile(sp,np.uint8).reshape(shape);nl=np.fromfile(lp,'<u4').reshape(shape);nc=canonical(nl)
        for variant in ['original-value','initial-minimum','final-minimum']:
            c,s=model(a,variant);cc=canonical(c);pairs=np.unique(np.stack([cc.ravel(),nc.ravel()],axis=1),axis=0)
            row=dict(case=name,variant=variant,segment_match=float(np.mean(s==ns)),partition_exact=bool(np.array_equal(cc,nc)),candidate_regions=int(np.unique(c).size),native_regions=int(np.unique(nl).size),candidate_basins_split_by_native=int(np.sum(np.bincount(pairs[:,0])>1)),native_basins_split_by_candidate=int(np.sum(np.bincount(pairs[:,1])>1)))
            rows.append(row);print(row,flush=True)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[r['evidence'],*NATIVE.values()]);write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-seed-graph-research.json',result)
    record('IMG-02','原生6大图灰度已与严格下降模型100%一致、差异仅为盆地合并；进一步冻结研究终点邻居的原值/初次最小值/最终最小值三类标签等价图并逐项比较。',[result['evidence']])

if __name__=='__main__':main()
