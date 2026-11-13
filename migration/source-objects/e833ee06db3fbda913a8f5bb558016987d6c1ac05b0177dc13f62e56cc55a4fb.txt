#!/usr/bin/env python3
"""Freeze the complete watershed algorithm variant and unseen input corpus."""
import json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def main():
    target=ROOT/'migration/rewrite/image-watershed-completion-contract.json'
    if target.exists():raise ValueError('contract already frozen')
    folder=ROOT/'migration/fixtures/image-watershed-completion';folder.mkdir(parents=True,exist_ok=True)
    y,x=np.indices((65,67));flat=np.full((65,67),190,np.uint8);samples={}
    for value in [0,127,128,255]:samples['constant-'+str(value)]=np.full((65,67),value,np.uint8)
    samples['pixel-127']=np.array([[127]],np.uint8)
    row=np.array([[255,128,128,127,127,0,0,127,128,255,255,190,190,190,63,64,64,127,127,128,128,129,0,255,0,128,127,129,255]],np.uint8)
    samples.update({'single-row':row,'single-column':row.T,'ramp-x':(x*3).astype(np.uint8),'ramp-y':(y*3).astype(np.uint8),'ramp-diagonal':(x+y).astype(np.uint8),'two-basins':np.minimum((x-13)**2+(y-25)**2,(x-49)**2+(y-37)**2).clip(0,255).astype(np.uint8),'saddle':np.abs((x-33)*(y-32)).clip(0,255).astype(np.uint8),'stairs':((x//7+y//9)*11).astype(np.uint8),'checker':(((x+y)%2)*255).astype(np.uint8),'diagonal-minima':np.where(x==y,0,190).astype(np.uint8)})
    separate=flat.copy();separate[8:20,8:20]=0;separate[41:53,45:57]=0;samples['disconnected-equal-minima']=separate
    bridge=flat.copy();bridge[8:20,8:20]=0;bridge[8:20,45:57]=0;bridge[13,20:45]=0;samples['one-pixel-bridge']=bridge
    diagonal=flat.copy();diagonal[8:20,8:20]=0;diagonal[20:32,20:32]=0;samples['diagonal-only-bridge']=diagonal
    snake=np.full((129,131),255,np.uint8)
    for k,yy in enumerate(range(1,128,4)):
        snake[yy,1:130]=0
        if yy+4<128:snake[yy:yy+5,129 if k%2==0 else 1]=0
    samples['long-serpentine-plateau']=snake
    outlets=flat.copy()
    for yy,xx,value in [(0,33,0),(64,33,63),(32,0,127),(32,66,128)]:outlets[yy,xx]=value
    samples['plateau-four-outlets']=outlets
    samples['threshold-quadrants']=np.where(y<32,np.where(x<33,127,128),np.where(x<33,0,255)).astype(np.uint8)
    border=np.full((65,67),128,np.uint8);border[1:-1,1:-1]=np.random.default_rng(917301).integers(0,256,(63,65),dtype=np.uint8);samples['one-pixel-border']=border
    for levels in [2,4,8,16,64,256]:
        for repetition in [0,1]:
            seed=918001+levels*19+repetition;z=np.random.default_rng(seed).integers(0,levels,(65+2*repetition,67+4*repetition));samples[f'noise-{levels}-{seed}']=(z*255//(levels-1)).astype(np.uint8)
    natural=[]
    for name in ['cat_baseline.jpg','img4.jpg']:
        source=ROOT/'nvJPEG/nvJPEG-Decoder/input_images'/name
        with Image.open(source) as im:array=np.asarray(im.convert('L').resize((257,193),Image.Resampling.BILINEAR)).copy()
        samples['natural-'+name.replace('.','-')]=array;natural.append(dict(path=str(source.relative_to(ROOT)),sha256=digest(source),recipe='Pillow convert L, bilinear resize 257x193; final raw bytes are the oracle input'))
    if len(samples)!=36:raise ValueError('heldout inventory')
    rows=[]
    for name,array in samples.items():
        path=folder/('heldout-'+name+'.raw');path.write_bytes(array.tobytes());rows.append(dict(id='heldout-'+name,split='heldout',width=array.shape[1],height=array.shape[0],path=str(path.relative_to(ROOT)),bytes=array.nbytes,sha256=digest(path)))
    previous=json.loads((ROOT/'migration/rewrite/image-watershed-semantics-profile.json').read_text())
    for item in previous['inputs']:
        path=folder/('development-'+item['id']+'.raw');path.write_bytes((ROOT/item['path']).read_bytes());rows.append(dict(item,id='development-'+item['id'],split='development',path=str(path.relative_to(ROOT)),sha256=digest(path)))
    sizes={'CT_skull_512x512_8u_Gray.raw':(512,512),'Rocks_512x512_8u_Gray.raw':(512,512),'Lena_512x512_8u_Gray.raw':(512,512),'coins_500x383_8u_Gray.raw':(500,383),'coins_overlay_500x569_8u_Gray.raw':(500,569),'Corn_614x461_8u_Gray.raw':(614,461)}
    for name,(w,h) in sizes.items():
        family='NPP+' if name.startswith('Corn') else 'NPP';source=ROOT/family/'watershedSegmentation/images'/name;path=folder/('original-'+name);path.write_bytes(source.read_bytes());rows.append(dict(id=path.stem,split='original',width=w,height=h,path=str(path.relative_to(ROOT)),bytes=w*h,sha256=digest(path),original_path=str(source.relative_to(ROOT))))
    (folder/'cases.txt').write_text(''.join(f'{i["id"]} {i["width"]} {i["height"]}\n' for i in rows))
    e=Experiment('I3','watershed-complete-variant-and-heldout-contract','CPU-contract',sources=[__file__,ROOT/'migration/reports/image-completion-IMG-02.md',ROOT/'rocm/common/image/watershed_v2.hpp',ROOT/'tools/moat/image_watershed_graph_reference.py',*[ROOT/i['path'] for i in rows],*[ROOT/i['path'] for i in natural]])
    contract=dict(status='FROZEN',algorithm_id='strict-descent-directed-terminal-reachability-v1',inputs=rows,natural_sources=natural,
      original_samples=['NPP/watershedSegmentation::watershedSegmentation.cpp','NPP+/watershedSegmentation::watershedSegmentationNPPPlus.cpp'],original_input_uses=8,original_products=22,
      specification=dict(neighborhood='8-connected in-bounds neighbors',descent='Select the strictly smaller minimum original intensity; equal lower candidates use row-major order. No equal-height descent. Follow fixed links to terminal root.',graph='Vertices are terminal roots. For root r and each neighboring pixel p, add directed edge r -> root(p) iff their final descent intensities agree. Self reachability is included.',marker='uint32 minimum original row-major root index among all forward-reachable roots, assigned back to every pixel with that descent root. Zero is a valid label; no truncation before fixed point.',compact='Distinct marker IDs sorted ascending, mapped bijectively to uint32 [0, region_count).',image_boundary='Compare final gray with valid upper and left pixels, OR the differences; no artificial outside border.',image_modes=dict(NONE='final gray',BLACK='0 on image boundary else gray',WHITE='255 on image boundary else gray',ONLY='0 on image boundary else 255',CONTRAST='on image boundary choose 255 if gray<128 else 0; elsewhere gray'),optional_marker='Marker and compact output pointers may both be null for image-only modes.',layouts=['compact','padded ROI','input aliases segment output'],cpu_oracle='height-ordered descent, strongly connected component condensation, reverse topological DAG minimum; no reuse of GPU relaxation'),
      acceptance=dict(classification='ALGORITHM_VARIANT for marker partition; EXACT for tested native image outputs',CPU='Every output element/extent exact including compact label ordering; every region 8-connected and constant gray; labels satisfy directed reachability minimum.',native_image='All five image modes EXACT on all 18 development, 36 heldout and 6 original inputs for NPP and NPP+; repeats must agree.',native_markers='Diagnostic only: full contingency table, deterministic one-to-one matching with unmatched IoU=0, macro/small-region/area-weighted IoU, splits/merges and each horizontal/vertical/diagonal adjacency edge. Do not claim native partition equivalence or only an ID renumbering.',runtime='Original 8 uses/22 products, missing/truncated/IO and invalid views, null marker, actual GPU trace and changed-input replay, cold build and independent review required.'),
      negative_controls=['one-label-image','merge-distinct-regions','split-one-region','drop-small-region','reuse-label-on-disconnected-regions','nonbijective-compact','OR-mask-hides-horizontal-vs-vertical-edges','alter-one-gray-pixel','alter-one-boundary-pixel','missing-product','trailing-bytes','wrong-native-product-SHA','missing-seal','unconverged-marker-result'],
      review=dict(decision='Contract direction approved; not sample qualification',reviewer='/root/image_evidence_review',required_corrections=['Rename prior OR boundary mask metric; report actual adjacency edges separately.','Explicitly disclose partition changes, including region counts; no opaque-ID-only claim.','Freeze reachability and compact numbering, null marker behavior, one-to-one regional diagnostics and meaningful negative cases.']),scope='Only two original watershed examples on locked Linux/gfx1201/ROCm10.1; no SDK-wide or other-platform claim. Earlier failures remain immutable.')
    write(e.path/'contract.json',contract);contract['evidence']=e.finish('OBSERVED');write(target,contract)
    record('IMG-02','独立复审接受marker图算法变体并要求明确分区变化；现冻结36个新保留输入、18开发输入、6原图及完整合同：native五种图像模式EXACT、CPU图论marker EXACT，逐区/逐边vendor差异诊断与14类反向检查。',[contract['evidence']]);print('FROZEN',len(rows),contract['evidence'])

if __name__=='__main__':main()
