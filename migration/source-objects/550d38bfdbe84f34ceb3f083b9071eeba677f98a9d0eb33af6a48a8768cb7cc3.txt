#!/usr/bin/env python3
"""Observe actual GPU color planes against exact rational color mathematics."""
import hashlib,json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def rational_plane(rgb,channel,sampling):
    scale=sampling if channel else 1
    h,w=rgb.shape[:2]
    # Independent whole-array integer reference: sum RGB first, then one rounding.
    padded=np.pad(rgb.astype(np.int64),((0,(-h)%scale),(0,(-w)%scale),(0,0)),mode='edge')
    sums=padded.reshape((h+scale-1)//scale,scale,(w+scale-1)//scale,scale,3).sum((1,3))
    weights=[[299000,587000,114000],[-168736,-331264,500000],[500000,-418688,-81312]][channel]
    denominator=1000000*scale*scale
    numerator=(sums*np.array(weights)).sum(-1)+(128*denominator if channel else 0)
    quotient,remainder=np.divmod(numerator,denominator)
    rounded=quotient+((2*remainder>denominator)|((2*remainder==denominator)&(quotient%2!=0)))
    return np.clip(rounded,0,255).astype(np.uint8)

def main():
    from snapshot import capture
    bp=ROOT/'migration/reports/image-encoder-wide-build.json';b=json.loads(bp.read_text())
    profile=ROOT/'migration/rewrite/image-encoder-quality-holdout-v2-profile.json';p=json.loads(profile.read_text())
    if digest(ROOT/b['binary'])!=b['binary_sha256'] or any(digest(ROOT/n)!=v for n,v in b['dependencies'].items()):raise ValueError('stale GPU wide probe')
    rows=[]
    for name in ['heldout-gradient','heldout-color-edges','heldout-natural-img9']:
        item=next(i for i in p['inputs'] if i['id']==name);source=ROOT/item['path']
        e=Experiment('I5','encoder-GPU-color-rational-diagnosis','rocm-probe',case=name,sources=[__file__,bp,profile,source,*[ROOT/n for n in b['dependencies']]])
        write(e.path/'backend.observed.json',capture())
        with Image.open(source) as im:rgb=np.array(im.convert('RGB'))
        raw=e.path/'source.rgb';rgb.tofile(raw);out=e.path/'arrays'
        rc=e.command([str(ROOT/b['binary']),str(raw),str(item['width']),str(item['height']),'2','1',str(out)],'actual-GPU-color-planes')
        checks=[dict(check='GPU-command',passed=rc==0),dict(check='frozen-input',passed=digest(source)==item['sha256'] and hashlib.sha256(rgb.tobytes()).hexdigest()==item['rgb_sha256'])];observations=[]
        try:
            for c in range(3):
                expected=rational_plane(rgb,c,2);actual=np.fromfile(out/f'color{c}-wide.bin',dtype=np.uint8).reshape(expected.shape)
                positions=np.argwhere(actual!=expected);difference=actual.astype(np.int64)-expected
                observations.append(dict(channel=c,pixels=actual.size,different=int(len(positions)),max_abs=int(np.abs(difference).max()),
                    GPU_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),rational_sha256=hashlib.sha256(expected.tobytes()).hexdigest(),
                    first_positions=[dict(y=int(y),x=int(x),GPU=int(actual[y,x]),rational=int(expected[y,x])) for y,x in positions[:100]]))
        except Exception as error:checks.append(dict(check='diagnostic-exception',passed=False,error=repr(error)))
        status='OBSERVED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(case=name,status=status,checks=checks,observations=observations,scope='Actual GPU planes versus exact decimal-coefficient model; diagnostic only, no gate or production change.')
        write(e.path/'result.json',row);row['evidence']=e.finish('OBSERVED' if status=='OBSERVED' else 'PROBE_FAILED',dict(status=status,checks=checks));rows.append(row)
        write(ROOT/'migration/reports/image-encoder-color-diagnosis.json',rows)
        record('IMG-01','GPU颜色平面与独立有理数模型 '+name+'：'+status+'；记录FMA/舍入位置，尚未修改生产算法。',[row['evidence']]);print(name,[(o['channel'],o['different'],o['max_abs']) for o in observations],flush=True)

if __name__=='__main__':main()
