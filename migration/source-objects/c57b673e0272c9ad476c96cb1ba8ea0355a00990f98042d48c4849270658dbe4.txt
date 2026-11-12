#!/usr/bin/env python3
"""Publish the Hough entry only after sealed qualification enters Git."""
import json
from experiment import ROOT,write,digest
from qualify_image_hough import collect,load,SAMPLE,IMPLEMENTATION,COMPARISON
from qualify_canny_plus import sealed
from selected_proofs import inspect

def validate(q,sample,review,closure=None):
    checks,refs,sources,build,p=closure if closure is not None else collect(review)
    directory,manifest,_=sealed(q['evidence']);frozen=json.loads((directory/'qualification.json').read_text())
    if (sample['id']!=SAMPLE or q['sample_id']!=SAMPLE or q['kind']!='image-hough-full'
        or manifest['backend']!='composite-qualification' or manifest['sample_id']!=SAMPLE
        or manifest['experiment_id']!=q['qualification_id'] or manifest['experiment_outcome']!='PASSED'
        or q['implementation']!=IMPLEMENTATION or q['implementation_sha256']!=digest(ROOT/IMPLEMENTATION)
        or q['source_commit']!=review['source_commit']):raise ValueError('Hough qualification identity')
    ids=[c['case'] for c in p['cases']]+[x['case']['case'] for x in load('options')]
    if (q['status']!='PASSED' or q['checks']!=checks or not all(c['passed'] for c in checks)
        or set(q['evidence_references'])!=refs or q['dependencies']!=build['dependencies']
        or q['case_ids']!=ids or q['case_count']!=len(ids)==19
        or q['comparison_mode']!=COMPARISON or any(q.get(k)!=v for k,v in frozen.items())
        or set(q)!=set(frozen)|{'qualification_id','evidence'}):
        raise ValueError('altered or incomplete Hough proof')
    result=inspect(dict(sample,implementation=IMPLEMENTATION,selected_validation=q))
    if result['status']!='PASSED':raise ValueError(str(result['errors']))

def main():
    q=load('qualification');review=load('review')
    catalog=json.loads((ROOT/'migration/samples.yaml').read_text())
    sample=next(s for s in catalog['samples'] if s['id']==SAMPLE)
    validate(q,sample,review)
    required=['image-hough/'+case for case in q['case_ids']]+[
        'image-hough/eleven-runtime-contracts-and-independent-peaks',
        'image-hough/complete-native-PPM-and-declared-differences',
        'image-hough/five-real-GPU-kernel-dispatches',
        'image-hough/forty-three-child-cold-replay',
        'image-hough/three-independent-fixed-source-reviews']
    sample.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',
                  implementation=IMPLEMENTATION,selected_validation=q,
                  required_cases=required,passed_cases=required,
                  actual_library='Project HIP C1 Canny plus GPU Hough votes and peak extraction',
                  backend_library='project HIP image Hough',equivalence=COMPARISON,
                  reason='完整C++原例、19输入/有效参数/错误CLI及逐字节PPM和完整诊断线表、11运行合同、真实GPU Sobel/NMS/threshold/votes/peaks、43子记录干净检出与三范围独立复审通过。项目CPU逐线/逐峰/全PPM精确；当前NPP原生默认PPM差10627 RGB像素，五条真值各被双方两条线覆盖。',
                  cuda_baseline='PASSED',cuda_comparison='OBSERVED',
                  cuda_comparison_mode=COMPARISON,
                  cuda_comparison_reason='当前5090原生与项目默认各10条线；部分rho偏1像素，red IoU0.23946。固定算法变体，不声称NPP逐位兼容。',
                  benchmark='NOT_QUALIFIED',active_batch='I3',
                  retry_condition='Canny/投票/峰/排序/布局或输入解析改变须重新资格与受影响入口回归。',
                  next_step='I3两种watershed与OpenCV benchmark，然后I4–I9。',
                  reproduce='python3 tools/moat/image_hough_contracts.py\npython3 tools/moat/image_hough_build.py\npython3 tools/moat/image_hough_run.py\nbuild/image-cpu-venv/bin/python tools/moat/image_hough_reference.py\npython3 tools/moat/image_hough_options.py\npython3 tools/moat/image_hough_runtime.py\npython3 tools/moat/image_hough_trace.py')
    for ref in ['migration/reports/image-hough.md',q['evidence'],*q['evidence_references']]:
        if ref not in sample['evidence']:sample['evidence'].append(ref)
    if not any(a.get('qualification_id')==q['qualification_id'] for a in sample['attempts']):sample['attempts'].append(q)
    write(ROOT/'migration/samples.yaml',catalog)
    print('Published complete NPP Hough Lines')

if __name__=='__main__':main()
