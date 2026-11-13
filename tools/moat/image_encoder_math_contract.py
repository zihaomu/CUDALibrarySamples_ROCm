#!/usr/bin/env python3
"""Freeze an explicit mathematical JPEG transform contract and new inputs."""
import hashlib,json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

PROFILE=ROOT/'migration/rewrite/image-encoder-math-variant-profile.json'

def main():
    if PROFILE.exists():raise ValueError('mathematical contract already frozen')
    parent=ROOT/'migration/rewrite/image-encoder-quality-profile.json'
    cross=ROOT/'migration/reports/image-encoder-reference-crosscheck.json'
    diagnosis=ROOT/'migration/reports/image-encoder-color-diagnosis.json'
    original=ROOT/'nvJPEG/nvJPEG-Decoder/input_images/img5.jpg'
    y,x=np.indices((271,773),dtype=np.uint32)
    gradient=np.stack([x*255//772,y*255//270,(2*x+y)*255//1814],axis=-1).astype(np.uint8)
    noise=np.random.default_rng(97531).integers(0,256,(277,389,3),dtype=np.uint8)
    y,x=np.indices((135,131));palette=np.array([[255,255,0],[0,0,255],[255,0,0],[0,255,0],[0,255,255],[255,0,255],[255,255,255],[0,0,0]],dtype=np.uint8)
    edges=palette[(x//7+3*(y//9))%8]
    with Image.open(original) as im:natural=np.array(im.convert('RGB'))
    inputs=[];folder=ROOT/'migration/fixtures/image-encoder-math-variant';folder.mkdir(parents=True,exist_ok=True)
    for name,rgb in [('math-gradient',gradient),('math-noise',noise),('math-edges',edges),('math-natural-img5',natural)]:
        path=folder/(name+'.bmp');Image.fromarray(rgb).save(path)
        inputs.append(dict(id=name,path=str(path.relative_to(ROOT)),sha256=digest(path),bytes=path.stat().st_size,width=rgb.shape[1],height=rgb.shape[0],rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest()))
    gates=json.loads(parent.read_text())['gates']
    value=dict(status='FROZEN',acceptance='ALGORITHM_VARIANT',inputs=inputs,
        cases=[dict(id=f"{i['id']}-q{q}-s{s}-opt{o}",input=i['id'],quality=q,sampling=s,optimized=bool(o)) for i in inputs for q in [1,50,80,95,100] for s in [1,2] for o in [0,1]],
        gates=gates,reference_natural=dict(path=str(original.relative_to(ROOT)),sha256=digest(original)),
        mathematics=dict(color_coefficients=[[299000,587000,114000],[-168736,-331264,500000],[500000,-418688,-81312]],denominator=1000000,
            color='Replicate input at right/bottom odd boundaries; sum RGB over scale x scale, apply exact rational coefficients, add chroma 128, nearest-even once, clip to [0,255]. Y scale 1; Cb/Cr requested sampling 1 or 2.',
            transform='Replicate component edges to complete 8x8 blocks. Standard orthonormal DCT-II of samples minus 128. DC is exactly sum/8. Quantization nearest integer, exact DC halves away from zero.',
            coefficient_gate='Every emitted coefficient and every GPU probe coefficient must agree exactly; every color byte must equal independent integer model. Every DC must match independent integer nearest/ties-away reference. Every AC must satisfy abs(coefficient*quant - independent float64 DCT) <= quant/2 + absolute_DCT_error_budget.',
            absolute_DCT_error_budget=.01,scope='Project mathematical approximation budget, not ISO/T.83 certification. Float64 oracle error must be cross-checked on adversarial blocks with higher precision.'),
        required=['All 80 original-entry products, exact geometry/sampling/DQT/SOF0/8bit/3 components.',
                  'Every component/pixel/block/frequency checked; no missing, duplicate, truncated, reordered or stale products accepted.',
                  'Keep original whole-image per-channel MSE factor/floor and global SSIM against both independent CPU and native CUDA.',
                  'Standard/optimized decoded pixels identical, Q100 vs Q1 control, malformed proof/plane/coefficient negative checks.',
                  'Final entropy extracted independently from complete JPEG must equal probe coefficients, with edge block geometry independently derived.',
                  'New candidate on these fresh inputs and both historical matrices; historical failed rows remain immutable.'],
        amendment=dict(previous_profile=str(parent.relative_to(ROOT)),previous_sha256=digest(parent),
            replaced_gate='Every 32x32 source tile MSE relative to a different encoder: retain all measurements as diagnostics; use complete local mathematical transform/entropy checks as acceptance.',
            reason='Independent CPU and CUDA references themselves fail the old tile rule: development CPU/native 2/0 cases, retained CPU/native 4/2. Different color rounding and downsampling cross coarse quantization boundaries. A vendor-relative local lossy-error ratio is not an independent transform specification.',
            evidence=[str(cross.relative_to(ROOT)),str(diagnosis.relative_to(ROOT))],
            preserved_failures=['Production development 78/80','Exact-DC isolated candidate fresh retained 74/80'],
            no_waiver='All whole-image quality, format, execution, CLI and resource contracts remain required. Any mathematical gate failure remains FAILED; no automatic sample promotion.'),
        standards_context=[dict(url='https://www.w3.org/Graphics/JPEG/itu-t81.pdf',use='A.3.4 nearest quantization and section 4 color interpretation scope; does not by itself validate this implementation.'),
                           dict(url='https://www.iso.org/standard/20689.html',use='Formal Part 2 compliance is separate and is not claimed.')])
    e=Experiment('I5','encoder-mathematical-variant-contract','CPU-contract',sources=[__file__,parent,cross,diagnosis,original,*[ROOT/i['path'] for i in inputs]])
    write(e.path/'profile.json',value);value['evidence']=e.finish('OBSERVED');write(PROFILE,value)
    record('IMG-01','冻结新80项ALGORITHM_VARIANT数学合同：精确有理数颜色、全块独立DCT/码流系数验证；保留全图CPU/native门槛，原局部比值改诊断且旧失败不改写。候选与新保留集尚未执行。',[str(PROFILE.relative_to(ROOT)),value['evidence']]);print(value['evidence'])

if __name__=='__main__':main()
