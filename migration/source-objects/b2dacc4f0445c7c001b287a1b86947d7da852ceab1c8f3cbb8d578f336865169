#!/usr/bin/env python3
"""Investigate native strict descent with independent plateau component labeling."""
import json
import numpy as np
from scipy.ndimage import label
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical

def model(image,connectivity,seed_only):
    h,w=image.shape;indices=np.arange(h*w,dtype=np.int32).reshape(h,w);parent=indices.copy();best=image.copy()
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if not (dx or dy) or connectivity==4 and dx and dy:continue
            y0,y1=max(0,-dy),min(h,h-dy);x0,x1=max(0,-dx),min(w,w-dx)
            target=(slice(y0,y1),slice(x0,x1));neighbor=(slice(y0+dy,y1+dy),slice(x0+dx,x1+dx))
            v=image[neighbor];j=indices[neighbor];b=best[target];p=parent[target];original=image[target]
            choose=(v<b)|((v==b)&(v<original)&(j<p));b[choose]=v[choose];p[choose]=j[choose]
    seeds=parent==indices;roots=parent.ravel().copy()
    for _ in range(32):
        following=roots[roots]
        if np.array_equal(roots,following):break
        roots=following
    else:raise ValueError('strict descent did not converge')
    eligible=seeds if seed_only else np.ones_like(seeds);components=np.zeros_like(parent);offset=0
    structure=np.ones((3,3),bool) if connectivity==8 else np.array([[0,1,0],[1,1,1],[0,1,0]],bool)
    for value in np.unique(image[eligible]):
        mask=(image==value)&eligible;labels,count=label(mask,structure);components[mask]=labels[mask]+offset;offset+=count
    result=components.ravel()[roots].reshape(image.shape)
    if np.any(result==0):raise ValueError('terminal root lacks a plateau label')
    return result,image.ravel()[roots].reshape(image.shape)

def main():
    profile=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(profile.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';r=json.loads(rp.read_text());proof=ROOT/r['evidence'];raw=ROOT/json.loads((proof/'manifest.json').read_text())['raw_artifact_dir']/'outputs'
    e=Experiment('I3','watershed-strict-descent-plateau-component-models','CPU-research',sources=[__file__,profile,rp,ROOT/'tools/moat/image_watershed_semantics_reference.py',*[ROOT/i['path'] for i in p['inputs']]])
    rows=[]
    for item in p['inputs']:
        image=np.fromfile(ROOT/item['path'],np.uint8).reshape(item['height'],item['width'])
        for norm in [4,8]:
            key=item['id']+f'-n{norm}-m0-r0';sp=raw/(key+'.segments');lp=raw/(key+'.labels')
            if any(digest(path)!=r['products'][path.name]['sha256'] for path in [sp,lp]):raise ValueError('native raw drift')
            native_seg=np.fromfile(sp,np.uint8).reshape(image.shape);native_labels=np.fromfile(lp,'<u4').reshape(image.shape)
            for seed_only in [False,True]:
                labels,seg=model(image,norm,seed_only)
                row=dict(case=item['id'],connectivity=norm,plateau_mode='local-minimum-pixels-only' if seed_only else 'all-original-equal-pixels',segment_match=float(np.mean(seg==native_seg)),partition_exact=bool(np.array_equal(canonical(labels),canonical(native_labels))),regions=int(np.unique(labels).size),native_regions=int(np.unique(native_labels).size));rows.append(row);print(row,flush=True)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[r['evidence']],hypothesis='Native outputs suggest strict downhill links do not drain interior plateau pixels. Compare two independent equal-value component definitions; this is development investigation, not an accepted watershed contract.')
    write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-strict-descent-research.json',result)
    record('IMG-02','严格下降/平台连通两个CPU模型已对18输入×2邻域作72次原生比较；依据实际输出检验平台内部是否保持独立区域，不沿用旧浸没假设，也不提前签发算法变体资格。',[result['evidence']])

if __name__=='__main__':main()
