#!/usr/bin/env python3
"""Observe GPU planes and exact DC mathematics at the two differing blocks."""
import hashlib,json,math
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def main():
    from snapshot import capture
    bp=ROOT/'migration/reports/image-encoder-wide-build.json';b=json.loads(bp.read_text());profile=ROOT/'migration/rewrite/image-encoder-quality-profile.json'
    item=next(i for i in json.loads(profile.read_text())['inputs'] if i['id']=='gradient');source=ROOT/item['path']
    if digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale wide probe')
    e=Experiment('I5','encoder-Q1-DC-normalization-diagnosis','rocm-probe',sources=[__file__,profile,source,bp,*[ROOT/n for n in b['dependencies']]])
    write(e.path/'backend.observed.json',capture())
    with Image.open(source) as im:rgb=np.array(im.convert('RGB'))
    raw=e.path/'source.rgb';rgb.tofile(raw);out=e.path/'arrays'
    rc=e.command([str(ROOT/b['binary']),str(raw),str(item['width']),str(item['height']),'2','1',str(out)],'GPU-original-and-wide-planes-coefficients')
    checks=[dict(check='command',passed=rc==0),dict(check='frozen-RGB',passed=hashlib.sha256(rgb.tobytes()).hexdigest()==item['rgb_sha256'])];observations=[]
    try:
        for channel,x,y in [(0,29,25),(1,12,0)]:
            s=2 if channel else 1;w=(item['width']+s-1)//s;h=(item['height']+s-1)//s
            plane=np.fromfile(out/f'color{channel}-wide.bin',dtype=np.uint8).reshape(h,w);padded=np.pad(plane,((0,(-h)%8),(0,(-w)%8)),mode='edge')
            total=int(padded[y*8:y*8+8,x*8:x*8+8].astype(np.int64).sum())-8192
            exact=total/8/255;sqrt_half=np.float32(0.7071067811865475);normalizer=np.float32(np.float32(sqrt_half*sqrt_half)*np.float32(.25));scaled=np.float32(np.float32(total)*normalizer/np.float32(255))
            coeff=np.fromfile(out/f'coeff{channel}-wide.bin',dtype='<i2').reshape((h+7)//8,(w+7)//8,64)
            observations.append(dict(channel=channel,block_x=x,block_y=y,plane_sum_centered=total,exact_dc_normalizer=.125,float32_sqrt_product_normalizer=float(normalizer),
                exact_scaled_DC=exact,float32_scaled_DC=float(scaled),GPU_quantized_DC=int(coeff[y,x,0]),exact_nearest_ties_away=int(math.copysign(math.floor(abs(exact)+.5),exact))))
    except Exception as error:checks.append(dict(check='inspection-exception',passed=False,error=repr(error)))
    status='OBSERVED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,observations=observations,scope='Diagnosis only, no changed production algorithm or acceptance budget.')
    write(e.path/'result.json',row);row['evidence']=e.finish('OBSERVED' if status=='OBSERVED' else 'PROBE_FAILED',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-DC-diagnosis.json',row)
    record('IMG-01','GPU颜色平面/DC数学诊断：'+status+'；记录精确1/8与float sqrt乘积的量化边界差异，未改变生产算法或门槛。',[row['evidence']]);print(status,observations)

if __name__=='__main__':main()
