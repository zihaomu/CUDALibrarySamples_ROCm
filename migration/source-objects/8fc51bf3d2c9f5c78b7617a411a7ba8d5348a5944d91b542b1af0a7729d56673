#!/usr/bin/env python3
"""Verify image boundary semantics separately from opaque basin marker labels."""
import json
import numpy as np
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_watershed_semantics_reference import canonical
from image_watershed_research import NATIVE,SIZES
from image_watershed_reference import native_output_dir
from image_watershed_directed_labels_research import model

def edges(gray):
    b=np.zeros_like(gray,dtype=bool);b[1:]|=gray[1:]!=gray[:-1];b[:,1:]|=gray[:,1:]!=gray[:,:-1];return b

def main():
    pp=ROOT/'migration/rewrite/image-watershed-semantics-profile.json';p=json.loads(pp.read_text());rp=ROOT/'migration/reports/image-watershed-semantics-NPP.json';r=json.loads(rp.read_text());raw=ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']/'outputs';inputs=[]
    for item in p['inputs']:
        shape=item['height'],item['width'];sp=raw/(item['id']+'-n8-m0-r0.segments');lp=sp.with_suffix('.labels');bp=raw/(item['id']+'-n8-m4-r0.segments');cp=raw/(item['id']+'-n8-m3-r0.segments')
        if any(digest(f)!=r['products'][f.name]['sha256'] for f in [sp,lp,bp,cp]):raise ValueError('native identity')
        inputs.append((item['id'],ROOT/item['path'],shape,sp,lp,bp,cp))
    for name,(w,h) in SIZES.items():
        family='NPP' if name!='Corn_614x461_8u_Gray.raw' else 'NPP+'
        folder=native_output_dir(family);source=ROOT/family/'watershedSegmentation/images'/name
        sn='Segmented_'+name if family=='NPP' else 'Corn_Segments_8Way_614x461_8u.raw';ln='Labels_'+name if family=='NPP' else 'Corn_CompressedSegmentLabels_8Way_614x461_32u.raw'
        prefix='CT_skull' if name.startswith('CT_skull') else name.split('_')[0];plus=native_output_dir('NPP+');bn=plus/f'{prefix}_SegmentBoundaries_8Way_{w}x{h}_8u.raw';cn=plus/f'{prefix}_SegmentsWithContrastingBoundaries_8Way_{w}x{h}_8u.raw'
        inputs.append((name,source,(h,w),folder/sn,folder/ln,bn if bn.exists() else None,cn if cn.exists() else None))
    e=Experiment('I3','watershed-gray-boundaries-and-label-consistency','CPU-research',sources=[__file__,pp,rp,ROOT/'tools/moat/image_watershed_directed_labels_research.py',ROOT/'tools/moat/image_watershed_semantics_reference.py',ROOT/'tools/moat/image_watershed_reference.py',*[i[1] for i in inputs],*[ROOT/ref/'run.json' for ref in NATIVE.values()]])
    rows=[]
    for name,source,shape,sp,lp,bp,cp in inputs:
        a=np.fromfile(source,np.uint8).reshape(shape);ns=np.fromfile(sp,np.uint8).reshape(shape);nl=np.fromfile(lp,'<u4').reshape(shape);nc=canonical(nl);c,s,iterations=model(a,'final-minimum');cc=canonical(c)
        _,ci=np.unique(cc,return_inverse=True);_,ni=np.unique(nc,return_inverse=True);npairs=np.unique(np.stack([nc.ravel(),ns.ravel()],axis=1),axis=0);native_multigray=int(np.sum(np.bincount(npairs[:,0])>1))
        contour=edges(s);row=dict(case=name,segment_exact=bool(np.array_equal(s,ns)),native_regions_with_multiple_gray_values=native_multigray,partition_exact=bool(np.array_equal(cc,nc)),partition_local_edge_agreement=float(np.mean(edges(cc)==edges(nc))),label_pixel_agreement_by_majority=None)
        pairs,count=np.unique(np.stack([cc.ravel(),nc.ravel()],axis=1),axis=0,return_counts=True);largest=np.zeros(int(cc.max())+1,np.int64);np.maximum.at(largest,pairs[:,0],count);row['label_pixel_agreement_by_majority']=float(largest.sum()/a.size)
        if bp:
            b=np.fromfile(bp,np.uint8).reshape(shape);co=np.fromfile(cp,np.uint8).reshape(shape);row.update(boundary_exact=bool(np.array_equal(b,np.where(contour,0,255))),boundary_match=float(np.mean(b==np.where(contour,0,255))),contrast_exact=bool(np.array_equal(co,np.where(contour,np.where(s<128,255,0),s))))
        rows.append(row);print(row,flush=True)
    result=dict(status='OBSERVED',rows=rows,evidence_references=[r['evidence'],*NATIVE.values()]);write(e.path/'result.json',result);result['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-watershed-gray-boundary-research.json',result)
    record('IMG-02','原生边界观察显示采用分割灰度上/左比较、CONTRAST按128阈值取黑白；在18小输入及NPP+全部原图独立验证，同时统计有向标签模型的局部边界和逐盆地误差。',[result['evidence']])

if __name__=='__main__':main()
