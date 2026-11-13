#!/usr/bin/env python3
"""Exercise strict entropy and local mathematical rejection gates."""
import json
import numpy as np
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from image_encoder_math_oracle import color,coefficient_checks,precision_check
from image_jpeg_baseline_entropy_reference import decode

def main():
    profile=ROOT/'migration/rewrite/image-encoder-math-variant-v2-profile.json'
    report=ROOT/'migration/reports/image-encoder-math-native.json';rows=json.loads(report.read_text())
    if len(rows)!=80 or any(r['status']!='PASSED' for r in rows):raise ValueError('native fresh matrix required')
    paths=[ROOT/r['products'][0]['path'] for r in rows]
    e=Experiment('I5','encoder-math-validator-negative-controls','CPU-negative',sources=[__file__,profile,report,ROOT/'tools/moat/image_encoder_math_oracle.py',ROOT/'tools/moat/image_jpeg_baseline_entropy_reference.py',*paths])
    checks=[];observations=[]
    try:
        precision=precision_check();checks.append(dict(check='80-digit-reference',**precision))
        for row,path in zip(rows,paths):
            parsed=decode(path.read_bytes());checks.append(dict(check='strict-native-positive-'+row['case'],passed=bool(parsed['blocks'])))
        data=paths[0].read_bytes()
        negatives={'missing-EOI':data[:-2],'trailing-byte':data+b'\0','truncated-entropy':data[:-20]+b'\xff\xd9',
                   'extra-entropy-byte':data[:-2]+b'\0'+data[-2:],'unexpected-marker':data[:-2]+b'\xff\x01'+data[-2:],
                   'truncated-marker':data[:5],'missing-SOI':data[2:]}
        for name,damaged in negatives.items():
            try:decode(damaged);rejected=False;message='accepted'
            except (ValueError,KeyError,IndexError) as error:rejected=True;message=str(error)
            checks.append(dict(check=name,passed=rejected));observations.append(dict(case=name,reason=message))
        rgb=np.array([[[255,255,0],[0,0,255],[255,0,0],[128,128,128]]],dtype=np.uint8)
        expected=[[226,29,76,128],[0,255,85,128],[149,107,255,128]]
        for c in range(3):checks.append(dict(check='known-rational-primary-'+str(c),passed=color(rgb,c,1).tolist()==[expected[c]]))
        plane=np.full((8,8),128,dtype=np.uint8);coeff=np.zeros((1,1,8,8),dtype=np.int16);quant=np.ones((8,8),dtype=np.int64)
        checks.append(dict(check='zero-block-positive',passed=coefficient_checks(plane,coeff,quant,.01)['passed']))
        for name,index in [('DC',(0,0)),('AC',(3,5))]:
            altered=coeff.copy();altered[0,0,index[0],index[1]]=1
            checks.append(dict(check='single-wrong-'+name+'-rejected',passed=not coefficient_checks(plane,altered,quant,.01)['passed']))
        altered=plane.copy();altered[0,0]=255
        checks.append(dict(check='single-local-pixel-change-rejected',passed=not coefficient_checks(altered,coeff,quant,.01)['passed']))
    except Exception as error:checks.append(dict(check='control-exception',passed=False,error=repr(error)))
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks,observations=observations,scope='Strict parser reference validation and local arithmetic controls, not candidate qualification.')
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-math-controls.json',row)
    record('IMG-01','数学/完整entropy验证器正反检查：'+status+'；80个native合法产品、截断/尾部/marker、局部像素和DC/AC损坏。',[row['evidence']]);print(status,[(c['check'],c.get('error')) for c in checks if not c['passed']]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
