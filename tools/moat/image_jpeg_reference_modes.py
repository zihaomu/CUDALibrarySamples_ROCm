#!/usr/bin/env python3
"""Source-backed CPU reconstruction-mode amendment with fresh held-out inputs."""
import argparse,json,hashlib,re
from pathlib import Path
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record
from image_encoder_large import compare_decoders

PROFILE=ROOT/'migration/rewrite/image-jpeg-reference-modes-profile.json'
BUILD=ROOT/'migration/reports/image-jpeg-ycbcr-reference-build.json'
SOURCE=ROOT/'rocm/probes/image/jpeg_cpu_ycbcr.cpp'

def triangle(ycc):
    """RGB601 after quarter-sample separable triangle, edge-clamped in chroma."""
    h,w,_=ycc.shape;y=np.arange(h);x=np.arange(w);cy=y//2;cx=x//2
    low=ycc[::2,::2,1:].astype(np.int32);ny=np.clip(cy+np.where(y%2,1,-1),0,low.shape[0]-1);nx=np.clip(cx+np.where(x%2,1,-1),0,low.shape[1]-1)
    vertical=3*low[cy[:,None],cx[None,:]]+low[ny[:,None],cx[None,:]]
    neighbor=3*low[cy[:,None],nx[None,:]]+low[ny[:,None],nx[None,:]]
    chroma=((3*vertical+neighbor+8)//16).astype(np.float64)-128
    Y=ycc[:,:,0].astype(np.float64);Cb=chroma[:,:,0];Cr=chroma[:,:,1]
    rgb=np.stack([Y+1.402*Cr,Y-0.344136*Cb-0.714136*Cr,Y+1.772*Cb],axis=-1)
    return np.clip(np.floor(rgb+0.5),0,255).astype(np.uint8)

def freeze():
    if PROFILE.exists():raise ValueError('reference-mode amendment already frozen')
    folder=ROOT/'migration/fixtures/image-jpeg-reference-modes';folder.mkdir(parents=True,exist_ok=True);cases=[]
    for i,(w,h,q) in enumerate([(1,257,80),(2,513,100),(3,31,1),(4,65500,80),(5,129,80),(17,131,100)]):
        rgb=np.random.default_rng(21351+i).integers(0,256,(h,w,3),dtype=np.uint8);path=folder/f'{w}x{h}-q{q}.jpg'
        Image.fromarray(rgb).save(path,format='JPEG',quality=q,subsampling=2)
        cases.append(dict(id=path.stem,path=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size,width=w,height=h,quality=q,seed=21351+i,source_rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
    sources=[__file__,ROOT/'tools/moat/image_encoder_large.py',ROOT/'migration/rewrite/image-encoder-large-profile.json',
        ROOT/'build/deps/libjpeg-turbo/src/jdsample.c',ROOT/'build/deps/libjpeg-turbo/src/jmorecfg.h',
        ROOT/'build/deps/stb-reference-9600522de539/stb_image.h',*[ROOT/c['path'] for c in cases]]
    e=Experiment('I5','JPEG-CPU-reconstruction-mode-amendment','CPU-contract',sources=sources)
    value=dict(status='FROZEN',amends='migration/rewrite/image-encoder-large-profile.json',cases=cases,
        diagnosis='libjpeg-turbo h2v2 selects fancy only when downsampled_width>2; stb still applies vertical triangle when chroma width1. Original 1x65500-420 Pillow comparison failed at maxAbs82 and remains FAILED under its original protocol.',
        normalization='Independent libjpeg ISLOW nearest-upsampled YCbCr -> recover chroma samples at even row/column -> explicit separable quarter-sample triangle with edge clamps -> RGB601 float64 rounding. Entropy and IDCT stay independent from stb.',
        scope='Reference decoder mode only. No production encoding/output changes. This amendment does not waive numeric gates or full native encoder equivalence.',
        gates=dict(max_abs=4,channel_rmse=1,channel_p99_abs=2,psnr_db=48,channel_global_ssim=0.995),
        application='After all six fresh held-out decoder inputs pass, apply the same frozen reconstruction to the historical skinny420 product and use a new scoped validation receipt. Keep original experiments/profiles immutable.')
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','源码确认CPU上采样模式差异，冻结独立参考修订和6个新seed保留输入（宽1/2/3/4/5/17、Q1/80/100）；保留原maxAbs82失败，统一三角重建且维持原4/1/2/48/.995门槛。',[str(PROFILE.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

def build():
    jpeg=ROOT/'build/cpu-codecs';deps={str(p.relative_to(ROOT)):digest(p) for p in [SOURCE,PROFILE,jpeg/'include/jpeglib.h',jpeg/'lib/libjpeg.so.62.4.0']}
    e=Experiment('I5','independent-libjpeg-YCbCr-reference-build','CPU-build',sources=[__file__,*[ROOT/n for n in deps]]);binary=e.path/'ycbcr-reference'
    rc=e.command(['c++','-std=c++17','-O2','-I'+str(jpeg/'include'),str(SOURCE),'-o',str(binary),'-L'+str(jpeg/'lib'),'-Wl,-rpath,'+str(jpeg/'lib'),'-ljpeg','-ldl'],'build-raw-YCbCr-reference')
    row=dict(status='BUILT' if rc==0 else 'BUILD_ERROR',binary=str(binary.relative_to(ROOT)),binary_sha256=digest(binary) if binary.exists() else None,dependencies=deps,experiment_id=e.id)
    write(e.path/'build.json',row);row['evidence']=e.finish('EXECUTED' if rc==0 else 'BUILD_ERROR');write(BUILD,row)
    record('IMG-01','独立libjpeg原生YCbCr参考构建：'+row['status']+'；保留正常尺寸限制，后续只统一重建语义。',[row['evidence']]);print(row['status']);return int(rc!=0)

def current():
    reports=[BUILD,ROOT/'migration/reports/image-stb-reference-build.json'];builds=[json.loads(p.read_text()) for p in reports]
    for b in builds:
        if b['status']!='BUILT' or digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=sha for n,sha in b['dependencies'].items()):raise ValueError('stale independent CPU reference')
    return reports,builds

def loaded_library_check(e,command,build):
    loaded=re.findall(r'^JPEG_LIBRARY=(.+)$',(e.path/command['stderr']).read_text(),re.M)
    expected=ROOT/'build/cpu-codecs/lib/libjpeg.so.62.4.0'
    return dict(check='actual-loaded-libjpeg-matches-bound-path-and-SHA',passed=len(loaded)==1 and
        Path(loaded[0]).resolve()==expected.resolve() and digest(loaded[0])==build['dependencies'][str(expected.relative_to(ROOT))],
        observed=loaded,expected_path=str(expected),expected_sha256=build['dependencies'][str(expected.relative_to(ROOT))])

def run():
    reports,builds=current();raw_build,stb_build=builds;p=json.loads(PROFILE.read_text());rows=[]
    for c in p['cases']:
        source=ROOT/c['path']
        if digest(source)!=c['sha256']:raise ValueError('new holdout bytes changed')
        e=Experiment('I5','JPEG-CPU-reconstruction-heldout','CPU-reference',case=c['id'],sources=[__file__,ROOT/'tools/moat/image_encoder_large.py',PROFILE,*reports,source,*[ROOT/n for b in builds for n in b['dependencies']]])
        ycc=e.path/'libjpeg.ycc';stb=e.path/'stb.rgb';rc=e.command([str(ROOT/raw_build['binary']),str(source),str(ycc)],'independent-libjpeg-YCbCr');sc=e.command([str(ROOT/stb_build['binary']),str(source),str(stb)],'independent-stb-RGB')
        checks=[dict(check='both-independent-decode-commands',passed=rc==sc==0),loaded_library_check(e,e.commands[0],raw_build)];metrics={}
        try:
            shape=(c['height'],c['width'],3);expected_bytes=np.prod(shape).item()
            checks.append(dict(check='complete-buffer-lengths',passed=ycc.stat().st_size==stb.stat().st_size==expected_bytes))
            reference=triangle(np.fromfile(ycc,dtype=np.uint8).reshape(shape));reference.tofile(e.path/'normalized-reference.rgb')
            actual=np.fromfile(stb,dtype=np.uint8).reshape(shape);metrics,good=compare_decoders(actual,reference)
            checks.append(dict(check='unchanged-frozen-pixel-gates',passed=good))
        except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if all(x['passed'] for x in checks) else 'FAILED';row=dict(case=c['id'],status=status,checks=checks,metrics=metrics,experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(ROOT/'migration/reports/image-jpeg-reference-modes-heldout.json',rows)
        record('IMG-01','CPU重建模式新保留输入 '+c['id']+'：'+status+'；独立熵/IDCT和统一重建，门槛未放宽。',[row['evidence']]);print(c['id'],status,metrics,flush=True)
    return int(any(r['status']!='PASSED' for r in rows))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','build','run']);args=parser.parse_args();raise SystemExit(globals()[args.action]())
