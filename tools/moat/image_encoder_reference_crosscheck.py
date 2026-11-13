#!/usr/bin/env python3
"""Observe whether the two independent encoders satisfy each other's tile gate."""
import json
import numpy as np
from experiment import ROOT,Experiment,write
from audit import check as audit_check
from image_completion_progress import record

def main():
    names=[('development','image-encoder-quality-profile.json','image-encoder-quality-cpu.json'),
           ('heldout','image-encoder-quality-holdout-v2-profile.json','image-encoder-quality-heldout-cpu.json')]
    sources=[__file__,ROOT/'tools/moat/image_encoder_quality_reference.py',ROOT/'tools/moat/image_encoder_quality_holdout_reference.py']
    groups=[]
    for label,profile,report in names:
        pp=ROOT/'migration/rewrite'/profile;rp=ROOT/'migration/reports'/report;sources+=[pp,rp]
        p=json.loads(pp.read_text());rows=json.loads(rp.read_text())
        if [r['case'] for r in rows]!=[c['id'] for c in p['cases']]:raise ValueError('incomplete reference matrix')
        for r in rows:
            proof=ROOT/r['evidence']
            if audit_check(proof) or json.loads((proof/'result.json').read_text())!={k:v for k,v in r.items() if k!='evidence'}:raise ValueError('reference report differs from seal')
        groups.append((label,p,rows))
    e=Experiment('I5','encoder-independent-reference-tile-crosscheck','CPU-reference',sources=sources);observations=[];checks=[]
    for label,p,rows in groups:
        for r in rows:
            cpu=np.array(r['metrics']['cpu']['reference_tile_mse']);native=np.array(r['metrics']['native']['reference_tile_mse']);g=p['gates']
            if cpu.shape!=native.shape or cpu.ndim!=2 or cpu.shape[1]!=3:raise ValueError('tile geometry mismatch')
            item=dict(matrix=label,case=r['case'],directions={})
            for name,a,b in [('CPU_vs_native',cpu,native),('native_vs_CPU',native,cpu)]:
                positions=np.argwhere(a>b*g['source_tile_mse_factor']+g['source_tile_mse_floor'])
                item['directions'][name]=dict(passes_frozen_local_gate=len(positions)==0,failing_channel_tiles=len(positions),
                    failures=[dict(tile=int(i),channel=int(c),candidate_mse=float(a[i,c]),reference_mse=float(b[i,c])) for i,c in positions])
            observations.append(item)
        checks.append(dict(check=label+'-all80-reference-cases',passed=len(rows)==80))
    summary={label:{direction:sum(not r['directions'][direction]['passes_frozen_local_gate'] for r in observations if r['matrix']==label)
        for direction in ['CPU_vs_native','native_vs_CPU']} for label,_,_ in groups}
    row=dict(status='OBSERVED',checks=checks,summary=summary,observations=observations,
        scope='Tests the two independent encoder outputs against the existing empirical tile-quality gate. No threshold or support-status change; does not establish JPEG conformance or mathematical equivalence.')
    write(e.path/'result.json',row);row['evidence']=e.finish('OBSERVED',dict(status='OBSERVED',checks=checks));write(ROOT/'migration/reports/image-encoder-reference-crosscheck.json',row)
    record('IMG-01','独立CPU与native参考互相套用原局部门槛的诊断完成：'+json.dumps(summary,separators=(',',':'))+'；仅观察，尚未修改合同/支持结论。',[row['evidence']]);print(summary)

if __name__=='__main__':main()
