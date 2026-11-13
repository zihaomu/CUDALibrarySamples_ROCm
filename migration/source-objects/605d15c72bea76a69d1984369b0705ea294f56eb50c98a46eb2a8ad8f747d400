#!/usr/bin/env python3
"""Execute the same isolated transform on every distinct fresh input/Q/sampling."""
import argparse,hashlib,json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from image_completion_progress import record

def main():
    from snapshot import capture
    profile=PROFILE;p=json.loads(profile.read_text())
    bp=ROOT/'migration/reports/image-encoder-math-candidate-build.json';b=json.loads(bp.read_text());probe=b['probe']
    if digest(ROOT/probe['binary'])!=probe['binary_sha256'] or any(digest(ROOT/n)!=h for n,h in b['dependencies'].items()):raise ValueError('stale candidate probe')
    rows=[]
    for case in p['cases']:
        if case['optimized']:continue
        item=next(i for i in p['inputs'] if i['id']==case['input']);source=ROOT/item['path']
        e=Experiment('I5','encoder-historical-mathematical-arrays','rocm-probe',case=case['id'],sources=[__file__,profile,bp,source,*[ROOT/n for n in b['dependencies']]])
        write(e.path/'backend.observed.json',capture());checks=[];products=[]
        try:
            with Image.open(source) as im:rgb=np.array(im.convert('RGB'))
            if digest(source)!=item['sha256'] or hashlib.sha256(rgb.tobytes()).hexdigest()!=item['rgb_sha256']:raise ValueError('input drift')
            raw=e.path/'source.rgb';rgb.tofile(raw);out=e.path/'arrays'
            rc=e.command([str(ROOT/probe['binary']),str(raw),str(item['width']),str(item['height']),str(case['sampling']),str(case['quality']),str(out)],'same-candidate-GPU-transform',timeout=300)
            checks.append(dict(check='actual-GPU-command',passed=rc==0))
            for channel in range(3):
                s=case['sampling'] if channel else 1;w=(item['width']+s-1)//s;h=(item['height']+s-1)//s
                for kind,length in [('color',w*h),('coeff',((w+7)//8)*((h+7)//8)*64*2)]:
                    path=out/f'{kind}{channel}-wide.bin'
                    checks.append(dict(check=f'complete-{kind}-{channel}',passed=path.stat().st_size==length))
                    products.append(dict(kind=kind,channel=channel,path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=digest(path)))
        except Exception as error:checks.append(dict(check='probe-exception',passed=False,error=repr(error)))
        status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';row=dict(case=case['id'],status=status,checks=checks,products=products,binary_sha256=probe['binary_sha256'],input=item,experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));rows.append(row);write(REPORT,rows)
        record('IMG-01','数学候选完整GPU平面/系数 '+case['id']+'：'+status+'；独立CPU数学及最终JPEG系数另验。',[row['evidence']]);print(case['id'],status,flush=True)
        if status!='PASSED':return 1
    return 0

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('matrix',choices=['development','heldout']);a=parser.parse_args()
    PROFILE=ROOT/('migration/rewrite/image-encoder-quality-profile.json' if a.matrix=='development' else 'migration/rewrite/image-encoder-quality-holdout-v2-profile.json')
    REPORT=ROOT/f'migration/reports/image-encoder-math-history-{a.matrix}-probe.json'
    raise SystemExit(main())
