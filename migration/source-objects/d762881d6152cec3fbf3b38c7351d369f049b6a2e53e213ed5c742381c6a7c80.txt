#!/usr/bin/env python3
"""Cross-mode quality consistency and quantitative validator controls."""
import json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from image_encoder_quality_holdout_reference import PROFILE,REPORT,decode,quality_checks,frame_identity,baseline

def main():
    p=json.loads(PROFILE.read_text());rows=json.loads(REPORT.read_text());lookup={r['case']:r for r in rows}
    if [r['case'] for r in rows]!=[c['id'] for c in p['cases']] or len(rows)!=80:raise ValueError('complete matrix required')
    checks=[]
    e=Experiment('I5','encoder-fresh-quality-mode-groups-and-controls','CPU-negative',sources=[__file__,ROOT/'tools/moat/image_encoder_quality_holdout_reference.py',PROFILE,REPORT,*[ROOT/i['path'] for i in p['inputs']]])
    for item in p['inputs']:
        for sampling in [1,2]:
            for q in [1,50,80,95,100]:
                a=lookup[f"{item['id']}-q{q}-s{sampling}-opt0"];b=lookup[f"{item['id']}-q{q}-s{sampling}-opt1"]
                checks.append(dict(check=f"{item['id']}-q{q}-s{sampling}-Huffman-lossless",passed=set(a['decoded_sha256'])=={'amd','cpu','native'} and a['decoded_sha256']==b['decoded_sha256']))
            for opt in [0,1]:
                low=lookup[f"{item['id']}-q1-s{sampling}-opt{opt}"];high=lookup[f"{item['id']}-q100-s{sampling}-opt{opt}"]
                try:good=all(np.all(np.array(high['metrics']['source_metrics'][s]['channel_mse'])<=np.array(low['metrics']['source_metrics'][s]['channel_mse'])+1e-12) for s in ['amd','cpu','native'])
                except KeyError:good=False
                checks.append(dict(check=f"{item['id']}-s{sampling}-opt{opt}-quality-control",passed=bool(good)))
        row=lookup[f"{item['id']}-q100-s1-opt0"];jpeg=ROOT/row['evidence']/'cpu.jpg';reference,_=decode(jpeg)
        data=jpeg.read_bytes();offset=data.index(b'\xff\xc0');sof1=bytearray(data);sof1[offset+1]=0xc1
        precision=bytearray(data);precision[offset+4]=12
        checks.append(dict(check=item['id']+'-baseline-SOF0-positive',passed=baseline(frame_identity(data))))
        checks.append(dict(check=item['id']+'-SOF1-rejected',passed=not baseline(frame_identity(sof1))))
        checks.append(dict(check=item['id']+'-precision12-rejected',passed=not baseline(frame_identity(precision))))
        with Image.open(ROOT/item['path']) as im:source=np.array(im.convert('RGB'))
        variants={'positive':reference.copy(),'rounding':np.clip(reference.astype(np.int16)+1,0,255).astype(np.uint8),
            'zero':np.zeros_like(reference),'wrong-channels':reference[:,:,[2,1,0]].copy(),'local':reference.copy()}
        variants['local'][:8,:8]^=255
        for name,actual in variants.items():
            accepted=all(c['passed'] for c in quality_checks(actual,reference,source,p['gates'],name)[0])
            checks.append(dict(check=item['id']+'-validator-'+name,passed=accepted==(name in ['positive','rounding'])))
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    row=dict(status=status,checks=checks,evidence_references=[r['evidence'] for r in rows],scope='Mode consistency and validator controls; does not override individual failed quality cases.')
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-quality-heldout-groups.json',row)
    record('IMG-01','编码Huffman无损一致、Q1→Q100质量控制及误差门槛正反检查：'+status+'；各case三方数值结论继续独立保留。',[row['evidence']]);print(status)
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
