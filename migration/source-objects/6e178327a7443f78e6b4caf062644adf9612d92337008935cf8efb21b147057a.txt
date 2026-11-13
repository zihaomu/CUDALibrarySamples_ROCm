#!/usr/bin/env python3
"""Derive boundary predicates from independent native mode observations."""
import json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical

def offsets(labels):
    h,w=labels.shape;result=[]
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if not (dy or dx):continue
            mask=np.zeros((h,w),bool);y0,y1=max(0,-dy),min(h,h-dy);x0,x1=max(0,-dx),min(w,w-dx)
            mask[y0:y1,x0:x1]=labels[y0:y1,x0:x1]!=labels[y0+dy:y1+dy,x0+dx:x1+dx];result.append(mask)
    return result

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';r=json.loads(rp.read_text());raw=ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']/'outputs'
    e=Experiment('I3','watershed-native-boundary-mode-predicates','CPU-research',sources=[__file__,pp,rp]);rows=[];totals=np.zeros(256,np.int64);pixel_count=0
    for item in p['inputs']:
        shape=item['height'],item['width'];outputs=[]
        for mode in range(5):
            f=raw/(item['id']+f'-n8-m{mode}-r0.segments')
            if digest(f)!=r['products'][f.name]['sha256']:raise ValueError('native identity')
            outputs.append(np.fromfile(f,np.uint8).reshape(shape))
        f=raw/(item['id']+'-n8-m0-r0.labels')
        if digest(f)!=r['products'][f.name]['sha256']:raise ValueError('label identity')
        labels=np.fromfile(f,'<u4').reshape(shape);seg,black,white,contrast,only=outputs;edge=black!=white;pixel_count+=seg.size;neighbors=offsets(labels)
        agreements=[]
        for subset in range(256):
            mask=np.zeros(shape,bool)
            for k in range(8):
                if subset>>k&1:mask|=neighbors[k]
            equal=np.sum(mask==edge);totals[subset]+=equal;agreements.append(int(equal))
        row=dict(case=item['id'],pixels=seg.size,edge_count=int(edge.sum()),black_rule_exact=bool(np.array_equal(black,np.where(edge,0,seg))),white_rule_exact=bool(np.array_equal(white,np.where(edge,255,seg))),only_black_on_white=bool(np.array_equal(only,np.where(edge,0,255))),only_white_on_black=bool(np.array_equal(only,np.where(edge,255,0))),contrast_invert=bool(np.array_equal(contrast,np.where(edge,255-seg,seg))),contrast_xor128=bool(np.array_equal(contrast,np.where(edge,seg^128,seg))),contrast_threshold=bool(np.array_equal(contrast,np.where(edge,np.where(seg<128,255,0),seg))),best_direction_masks=[k for k,x in enumerate(agreements) if x==max(agreements)],best_direction_agreement=max(agreements)/seg.size,contrast_pairs=sorted(set(zip(seg[edge].tolist(),contrast[edge].tolist()))))
        rows.append(row);print(row,flush=True)
    result=dict(status='OBSERVED',rows=rows,aggregate_best_masks=[int(k) for k in np.flatnonzero(totals==totals.max())],aggregate_best_match=float(totals.max()/pixel_count),evidence_references=[r['evidence']]);write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-boundary-research.json',result)
    record('IMG-02','五种原生边界输出分离验证：由BLACK/WHITE模式提取真实边界，枚举8邻域方向谓词，分别核查ONLY极性和CONTRAST灰度映射。',[result['evidence']])

if __name__=='__main__':main()
