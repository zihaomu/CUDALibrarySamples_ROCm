#!/usr/bin/env python3
"""Compare isolated rounding candidate against unchanged CPU/native products."""
import argparse,json,hashlib
import numpy as np
from PIL import Image
from experiment import ROOT,Experiment,digest,write
from audit import check as audit_check
from image_completion_progress import record
from image_encoder_quality_reference import PROFILE,LOCK,identity,decode,baseline,quality_checks,metrics

def main(selected=None):
    names=['image-encoder-rounding-candidate-runs.json','image-encoder-quality-cpu.json','image-encoder-quality-native.json']
    reports=[ROOT/'migration/reports'/n for n in names];candidate,cpu,native=[json.loads(p.read_text()) for p in reports]
    p=json.loads(PROFILE.read_text());lock=json.loads(LOCK.read_text());expected={k:v for k,v in lock.items() if k!='evidence'}
    if identity()!=expected:raise ValueError('CPU identity drift')
    if selected and (len(selected)!=len(set(selected)) or not set(selected)<={r['case'] for r in candidate}):raise ValueError('selected cases must be unique and present')
    for number,group in enumerate([candidate,cpu,native]):
        count=len(group) if selected and number==0 else 80
        if not 0<count<=80 or len(group)!=count or [r['case'] for r in group]!=[c['id'] for c in p['cases'][:count]]:raise ValueError('complete matrix or explicitly selected frozen prefix required')
        for row in group:
            directory=ROOT/row['evidence']
            if audit_check(directory) or json.loads((directory/'result.json').read_text())!={k:v for k,v in row.items() if k!='evidence'}:raise ValueError('report not sealed')
    results=[]
    for case,a,c,n in zip(p['cases'],candidate,cpu,native):
        if selected and case['id'] not in selected:continue
        if a['status']!='PASSED' or n['status']!='PASSED' or any(not x['passed'] for x in c['checks'] if x['check'] in ['actual-CPU-reference-identity','complete-frozen-source-identity','geometry-sampling-DQT-baseline-exact']):raise ValueError('required execution/structure gate failed')
        item=next(i for i in p['inputs'] if i['id']==case['input']);paths=dict(amd=ROOT/a['products'][0]['path'],cpu=ROOT/c['evidence']/'cpu.jpg',native=ROOT/n['products'][0]['path'])
        for run in [a,n]:
            product=run['products'][0]
            if digest(ROOT/product['path'])!=product['sha256']:raise ValueError('product drift')
        e=Experiment('I5','encoder-ties-away-three-way-comparison','CPU-reference',case=case['id'],sources=[__file__,ROOT/'tools/moat/image_encoder_quality_reference.py',PROFILE,LOCK,*reports,ROOT/item['path'],*paths.values(),*[ROOT/name for name in lock['dependencies']]])
        checks=[];data={};decoded={}
        try:
            observed=identity();write(e.path/'CPU-loader-identity.json',observed);checks.append(dict(check='actual-CPU-loader',passed=observed==expected))
            with Image.open(ROOT/item['path']) as im:source=np.array(im.convert('RGB'))
            checks.append(dict(check='complete-source-RGB-identity',passed=hashlib.sha256(source.tobytes()).hexdigest()==item['rgb_sha256']))
            arrays={};structure={}
            for side,path in paths.items():arrays[side],structure[side]=decode(path);decoded[side]=hashlib.sha256(arrays[side].tobytes()).hexdigest()
            checks.append(dict(check='complete-geometry-DQT-sampling-SOF0-precision',passed=all(x.shape==source.shape for x in arrays.values()) and all(v==structure['cpu'] for v in structure.values()) and all(baseline(v['frame']) for v in structure.values())))
            for side in ['cpu','native']:
                tests,values=quality_checks(arrays['amd'],arrays[side],source,p['gates'],side);checks+=tests;data[side]=values
            data['source_metrics']={s:metrics(v,source) for s,v in arrays.items()}
        except Exception as error:checks.append(dict(check='validation-exception',passed=False,error=repr(error)))
        status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';row=dict(case=case['id'],status=status,checks=checks,metrics=data,decoded_sha256=decoded,evidence_references=[r['evidence'] for r in [a,c,n]],experiment_id=e.id)
        write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'NUMERIC_MISMATCH',dict(status=status,checks=checks));results.append(row);write(ROOT/'migration/reports/image-encoder-rounding-candidate-comparison.json',results)
        record('IMG-01','独立舍入候选三方比较 '+case['id']+'：'+status+'；使用原冻结质量预算和既有CPU/native产品，未签发生产资格。',[row['evidence']]);print(case['id'],status,flush=True)
    return int(not results or any(r['status']!='PASSED' for r in results))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--case',action='append');args=parser.parse_args();raise SystemExit(main(args.case))
