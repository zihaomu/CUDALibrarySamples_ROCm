#!/usr/bin/env python3
"""Test whether native marker aliases originate in clamped neighborhood coordinates."""
import json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical
from image_watershed_research import NATIVE,SIZES
from image_watershed_reference import native_output_dir
from image_watershed_directed_labels_research import model

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';r=json.loads(rp.read_text());raw=ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']/'outputs';inputs=[]
    for item in p['inputs']:
        shape=item['height'],item['width'];sp=raw/(item['id']+'-n8-m0-r0.segments');lp=sp.with_suffix('.labels')
        if any(digest(f)!=r['products'][f.name]['sha256'] for f in [sp,lp]):raise ValueError('native identity')
        inputs.append((item['id'],ROOT/item['path'],shape,lp,False))
    for name,(w,h) in SIZES.items():
        family='NPP' if name!='Corn_614x461_8u_Gray.raw' else 'NPP+'
        folder=native_output_dir(family);source=ROOT/family/'watershedSegmentation/images'/name
        ln='Labels_'+name if family=='NPP' else 'Corn_CompressedSegmentLabels_8Way_614x461_32u.raw';inputs.append((name,source,(h,w),folder/ln,family=='NPP+'))
    e=Experiment('I3','watershed-marker-coordinate-origin-hypothesis','CPU-research',sources=[__file__,pp,rp,ROOT/'tools/moat/image_watershed_directed_labels_research.py',ROOT/'tools/moat/image_watershed_semantics_reference.py',ROOT/'tools/moat/image_watershed_reference.py',*[i[1] for i in inputs],*[ROOT/ref/'run.json' for ref in NATIVE.values()]])
    rows=[]
    for name,source,shape,lp,compact in inputs:
        a=np.fromfile(source,np.uint8).reshape(shape);nl=np.fromfile(lp,'<u4').reshape(shape);nc=canonical(nl);c,s,_=model(a,'final-minimum');h,w=shape
        variants={'root':c,'minus-one':np.maximum(c-1,0),'top-left-clamped':np.maximum(c//w-1,0)*w+np.maximum(c%w-1,0),'top-left-linear-clamped':np.maximum(c-w-1,0)}
        for variant,label in variants.items():
            cc=canonical(label);row=dict(case=name,variant=variant,partition_exact=bool(np.array_equal(cc,nc)),candidate_regions=int(np.unique(label).size),native_regions=int(np.unique(nl).size),raw_label_match=None if compact else float(np.mean(label==nl)))
            if not compact:
                delta=nl.astype(np.int64)-label;values,count=np.unique(delta,return_counts=True);selected=np.argsort(count)[-8:][::-1];row['common_label_deltas']=[dict(delta=int(values[k]),pixels=int(count[k])) for k in selected]
            rows.append(row);print(row,flush=True)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[r['evidence'],*NATIVE.values()]);write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-label-origin-research.json',result)
    record('IMG-02','单行原生marker比下降根索引小1，进一步独立测试邻域左上角坐标/边缘钳位对标签编号及跨灰度别名的解释；保留原始标签差值分布。',[result['evidence']])

if __name__=='__main__':main()
