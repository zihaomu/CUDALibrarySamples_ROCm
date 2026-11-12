#!/usr/bin/env python3
"""Freeze all 68 original resize JPEG products for GPU vs prior encoder comparison."""
import json
from pathlib import Path
from experiment import ROOT,Experiment,digest,write
from image_progress import record
PROFILE=ROOT/'migration/rewrite/image-jpeg-encoder-full-gpu-products-profile.json'
def main():
 if PROFILE.exists():raise ValueError('full GPU product comparison profile already frozen')
 old=json.loads((ROOT/'migration/reports/image-jpeg-encoder-integration.json').read_text())
 new=json.loads((ROOT/'migration/reports/image-jpeg-encoder-full-gpu-integration.json').read_text())
 pairs=[]
 for a,b in zip(old,new):
  if a['source']!=b['source'] or a['status']!='PASSED_SUBSET' or b['status']!='PASSED_SUBSET':raise ValueError('paired entry mismatch')
  left=ROOT/a['evidence'];right=ROOT/b['evidence']
  x={str(p.relative_to(left)):p for p in left.rglob('*.jpg')};y={str(p.relative_to(right)):p for p in right.rglob('*.jpg')}
  if set(x)!=set(y):raise ValueError('product names changed')
  for name in sorted(x):pairs.append(dict(source=a['source'],product=name,
   old=str(x[name].relative_to(ROOT)),old_sha256=digest(x[name]),
   gpu=str(y[name].relative_to(ROOT)),gpu_sha256=digest(y[name])))
 if len(pairs)!=68:raise ValueError('expected all 68 JPEG products')
 e=Experiment('I5','all-68-resize-JPEG-products-compare-contract','CPU-contract',
  sources=[__file__,ROOT/'migration/reports/image-jpeg-encoder-integration.json',
           ROOT/'migration/reports/image-jpeg-encoder-full-gpu-integration.json'])
 profile=dict(status='FROZEN',phase='I5',products=pairs,
  gates=dict(exact_product_names_and_count=68,independent_Pillow_decode=True,
             exact_all_RGB_pixels_vs_prior_GPU_FDCT_CPU_entropy=True,
             GPU_full_encode_metadata_and_no_CPU_entropy=True),
  limitation='Prior encoder is a numerical reference for the same HIP FDCT, not an NVIDIA native output oracle.')
 write(e.path/'profile.json',profile);profile['evidence']=e.finish('OBSERVED',dict(status='FROZEN',checks=[dict(check='68-paired-JPEG-sha256-predeclared',passed=True)]))
 write(PROFILE,profile)
 record('I5','两个 resize 原入口合计68件 JPEG 产品、旧 GPU FDCT+CPU entropy 与新全 GPU entropy 输出及 SHA 已先冻结，独立全像素解码比对待跑。',[profile['evidence']])
 print(profile['evidence'])
if __name__=='__main__':main()
