#!/usr/bin/env python3
"""Freeze fresh image inputs after selecting the exact-DC correction policy."""
import hashlib,json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def main():
    dest=ROOT/'migration/rewrite/image-encoder-quality-holdout-v2-profile.json'
    if dest.exists():raise ValueError('retained quality inputs already frozen')
    parent=ROOT/'migration/rewrite/image-encoder-quality-profile.json';p=json.loads(parent.read_text());p.pop('evidence',None)
    folder=ROOT/'migration/fixtures/image-encoder-quality-holdout';folder.mkdir(parents=True,exist_ok=True)
    y,x=np.indices((263,529),dtype=np.uint32);gradient=np.stack([x*255//528,y*255//262,(x+y)*255//790],axis=-1).astype(np.uint8)
    noise=np.random.default_rng(37123).integers(0,256,(269,523,3),dtype=np.uint8)
    y,x=np.indices((127,129));palette=np.array([[255,0,255],[0,0,0],[0,255,0],[255,255,255],[255,0,0],[0,255,255],[0,0,255],[255,255,0]],dtype=np.uint8)
    edges=palette[(x//11+y//13+3)%8]
    original=ROOT/'nvJPEG/nvJPEG-Decoder/input_images/img9.jpg'
    with Image.open(original) as im:natural=np.array(im.convert('RGB'))
    inputs=[]
    for name,rgb in [('heldout-gradient',gradient),('heldout-noise',noise),('heldout-color-edges',edges),('heldout-natural-img9',natural)]:
        path=folder/(name+'.bmp');Image.fromarray(rgb).save(path)
        inputs.append(dict(id=name,path=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size,width=rgb.shape[1],height=rgb.shape[0],rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
    p.update(inputs=inputs,cases=[dict(id=f"{i['id']}-q{q}-s{s}-opt{o}",input=i['id'],quality=q,sampling=s,optimized=bool(o)) for i in inputs for q in [1,50,80,95,100] for s in [1,2] for o in [0,1]],
        scope='Fresh 80-case retained matrix after selecting exact DC 1/8 plus ties-away policy; independent input dimensions/seed/palette/natural image. Same original quality gates; no retuning from retained results.',
        parent_profile=str(parent.relative_to(ROOT)),parent_profile_sha256=digest(parent),
        reference_natural=dict(path=str(original.relative_to(ROOT)),sha256=digest(original)),
        candidate_policy='Exact DC normalizer 1/8 and nearest half ties away from zero. No quality budget changes.')
    previous=ROOT/'migration/rewrite/image-encoder-quality-holdout-profile.json'
    old=json.loads(previous.read_text())
    if old['inputs']!=inputs or old['cases']!=p['cases'] or old['gates']!=p['gates']:raise ValueError('metadata amendment changed frozen inputs or gates')
    p['references'].update(source_natural=str(original.relative_to(ROOT)),source_natural_sha256=digest(original))
    p['metadata_amendment']=dict(previous_profile=str(previous.relative_to(ROOT)),previous_sha256=digest(previous),reason='Correct inherited references.source_natural from parent cat to actual fresh img9. Input bytes, case IDs, source RGB hashes and numerical gates unchanged; no retained numeric results observed.')
    e=Experiment('I5','encoder-fresh-quality-heldout-contract','CPU-contract',sources=[__file__,parent,previous,original,*[ROOT/i['path'] for i in inputs]])
    write(e.path/'profile.json',p);p['evidence']=e.finish('OBSERVED');write(dest,p)
    record('IMG-01','新80项保留合同v2更正继承的自然图出处字段为实际img9；与首版逐字段验证输入/模式/数值门槛完全相同，旧合同保留，尚无保留集数值结果。',[str(dest.relative_to(ROOT)),p['evidence']]);print(p['evidence'])

if __name__=='__main__':main()
