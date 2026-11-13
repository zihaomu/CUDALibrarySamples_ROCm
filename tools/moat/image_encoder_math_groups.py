#!/usr/bin/env python3
"""Cross-mode quality consistency and quantitative validator controls."""
import json
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from image_encoder_math_reference import PROFILE,REPORT,decode,quality_checks,frame_identity,baseline

def main():
    p=json.loads(PROFILE.read_text());rows=json.loads(REPORT.read_text());lookup={r['case']:r for r in rows}
    if [r['case'] for r in rows]!=[c['id'] for c in p['cases']] or len(rows)!=80:raise ValueError('complete matrix required')
    checks=[]
    e=Experiment('I5','encoder-mathematical-mode-groups','CPU-negative',sources=[__file__,ROOT/'tools/moat/image_encoder_math_reference.py',PROFILE,REPORT,*[ROOT/i['path'] for i in p['inputs']]])
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
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    row=dict(status=status,checks=checks,evidence_references=[r['evidence'] for r in rows],scope='40 lossless Huffman pairs and 16 quality-control comparisons. Separate mathematical/strict entropy controls required; no sample promotion.')
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-math-groups.json',row)
    record('IMG-01','编码Huffman无损一致及Q1→Q100质量控制：'+status+'；各case三方数值结论继续独立保留。',[row['evidence']]);print(status)
    return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
