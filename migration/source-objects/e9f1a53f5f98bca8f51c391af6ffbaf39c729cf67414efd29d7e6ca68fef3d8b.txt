#!/usr/bin/env python3
"""Reject subset promotion, duplicate samples and substituted platform measurements."""
import copy,json
from experiment import ROOT,Experiment,write
from image_completion_progress import record
from qualify_image_encoder_completion import SAMPLE,publication_shapes,performance_valid,read

def main():
    e=Experiment('I5','encoder-complete-publication-negative-controls','CPU-negative',sources=[__file__,ROOT/'tools/moat/qualify_image_encoder_completion.py',ROOT/'migration/reports/image-encoder-instances-v2-qualification.json',*[ROOT/f'migration/reports/image-encoder-performance-v2-{s}.json' for s in ['amd','native']]])
    good=[dict(sample_id=SAMPLE,kind='image-JPEG-full-GPU-async-original-entry',contract_status='COMPLETE')]+[dict(sample_id=s,kind='image-JPEG-mathematical-baseline-resize-subset',contract_status='PARTIAL') for s in ['nvJPEG/Image-Resize::imageResize.cpp','nvJPEG/Image-Resize-WaterMark::imageResizeWatermark.cpp']]
    checks=[dict(check='declared-unique-publication-shapes-accepted',passed=publication_shapes(good))]
    for name in ['old-48-case-subset','duplicate-ID','wrong-resize-contract','wrong-encoder-kind']:
        rows=copy.deepcopy(good)
        if name=='old-48-case-subset':rows[0]=read('image-encoder-instances-v2-qualification.json')
        elif name=='duplicate-ID':rows[-1]=rows[1]
        elif name=='wrong-resize-contract':rows[1]['contract_status']='COMPLETE'
        else:rows[0]['kind']='image-JPEG-multiple-instances-async-GPU-subset'
        checks.append(dict(check='reject-'+name,passed=not publication_shapes(rows)))
    perf={s:read('image-encoder-performance-v2-'+s+'.json') for s in ['amd','native']};ids=[r['case'] for r in perf['amd']];binaries={s:rows[0]['binary_sha256'] for s,rows in perf.items()}
    checks.append(dict(check='actual-two-platform-performance-accepted',passed=performance_valid(perf,ids,binaries)))
    for name in ['AMD-records-in-native-slot','wrong-native-binary','duplicate-performance-case']:
        changed=copy.deepcopy(perf)
        if name=='AMD-records-in-native-slot':changed['native']=changed['amd']
        elif name=='wrong-native-binary':changed['native'][0]['binary_sha256']=binaries['amd']
        else:changed['native'][-1]=changed['native'][0]
        checks.append(dict(check='reject-'+name,passed=not performance_valid(changed,ids,binaries)))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED';row=dict(status=status,checks=checks)
    write(e.path/'result.json',row);row['evidence']=e.finish('PASSED' if status=='PASSED' else 'VALIDATOR_GAP',dict(status=status,checks=checks));write(ROOT/'migration/reports/image-encoder-completion-controls.json',row)
    record('IMG-01','完整资格发布反向检查：'+status+'；旧48项PARTIAL、重复ID/错误合同、跨平台替换/错二进制/重复性能case均拒绝。',[row['evidence']]);print(status);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
