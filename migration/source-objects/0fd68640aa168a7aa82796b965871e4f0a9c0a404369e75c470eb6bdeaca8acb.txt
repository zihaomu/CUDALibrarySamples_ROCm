#!/usr/bin/env python3
"""Publish the Flood Fill entry after Git anchoring its complete qualification."""
import json
from experiment import ROOT,write,digest
from qualify_image_flood import collect,load,SAMPLE,IMPLEMENTATION,COMPARISON,metadata
from qualify_canny_plus import sealed
from selected_proofs import inspect

def validate(q,sample,review,closure=None):
    checks,refs,sources,build,spec=closure if closure is not None else collect(review)
    directory,manifest,_=sealed(q['evidence'])
    frozen=json.loads((directory/'qualification.json').read_text())
    if (sample['id']!=SAMPLE or q['sample_id']!=SAMPLE
        or manifest['backend']!='composite-qualification'
        or manifest['sample_id']!=SAMPLE
        or manifest['experiment_id']!=q['qualification_id']
        or manifest['experiment_outcome']!='PASSED'
        or q['kind']!='image-flood-full'
        or q['implementation']!=IMPLEMENTATION
        or q['implementation_sha256']!=digest(ROOT/IMPLEMENTATION)
        or q['source_commit']!=review['source_commit']):
        raise ValueError('Flood Fill qualification identity')
    if (q['status']!='PASSED' or q['checks']!=checks
        or not checks or not all(c['passed'] for c in checks)
        or q['dependencies']!=load('frontend-build')['dependencies']
        or set(q['evidence_references'])!=refs
        or any(q.get(k)!=v for k,v in frozen.items())
        or set(q)!=set(frozen)|{'qualification_id','evidence'}
        or q['case_ids']!=[c['case'] for c in spec['cases']]
        or q['case_count']!=29 or q['comparison_mode']!=COMPARISON
        or any(q.get(k)!=v for k,v in metadata().items())):
        raise ValueError('incomplete or altered Flood Fill proof')
    result=inspect(dict(sample,implementation=IMPLEMENTATION,selected_validation=q))
    if result['status']!='PASSED':
        raise ValueError(str(result['errors']))

def main():
    q=load('qualification')
    review=load('review')
    catalog=json.loads((ROOT/'migration/samples.yaml').read_text())
    sample=next(s for s in catalog['samples'] if s['id']==SAMPLE)
    validate(q,sample,review)
    required=['image-flood/'+case for case in q['case_ids']]+[
        'image-flood/four-original-workflows-twenty-RGB-products',
        'image-flood/seventy-two-runtime-memory-and-stream-cases',
        'image-flood/eighteen-CLI-and-error-cases',
        'image-flood/full-real-GPU-trace',
        'image-flood/independent-CPU-and-native-comparison',
        'image-flood/sixty-acceptance-reader-checks',
        'image-flood/sixteen-archive-provenance-and-publication-reader-checks',
        'image-flood/exact-padding-counterexample-fixed',
        'image-flood/thirty-six-child-cold-checkout',
        'image-flood/independent-review']
    sample.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',
                  implementation=IMPLEMENTATION,selected_validation=q,
                  required_cases=required,passed_cases=required,
                  actual_library='Project HIP fixed-seed RGB flood fill and shared GPU connectivity',
                  backend_library='project HIP image flood fill',equivalence=COMPARISON,
                  reason='完整五模式/两原图/五RGB产品C++入口；29全量输入、4流程20RGB、72运行合同、18CLI、60基础验收器与16资格门反例、真实GPU trace、36子记录冷检出及独立复审通过。项目固定seed八连通/内边界与原生NPP+的分区和元数据差异单列；项目GPU对独立CPU逐字节精确。',
                  cuda_baseline='PASSED',
                  cuda_baseline_reason='5090上未修改NPP+原始源码和两输入五产品完整执行；实际二进制、库与GPU收据封存。',
                  cuda_comparison='OBSERVED',
                  cuda_comparison_mode='DOCUMENTED_FIXED_SEED_ALGORITHM_VARIANT',
                  cuda_comparison_reason='五原始产品与当前NPP+逐像素/region字段差异完整记录；不声称vendor逐字节一致。',
                  benchmark='NOT_QUALIFIED',active_batch='I3',
                  retry_condition='修改连接、边界、输入布局、元数据或接口须重签合同与复验。',
                  next_step='继续I3两类watershed、Hough和OpenCV benchmark，然后I4–I9。',
                  reproduce='python3 tools/moat/image_flood_contracts.py\npython3 tools/moat/image_flood_build.py\npython3 tools/moat/image_flood_run.py\npython3 tools/moat/image_flood_frontend_build.py\npython3 tools/moat/image_flood_originals.py\npython3 tools/moat/image_flood_runtime.py')
    for ref in ['migration/reports/image-flood.md',q['evidence'],*q['evidence_references']]:
        if ref not in sample['evidence']:
            sample['evidence'].append(ref)
    if not any(a.get('qualification_id')==q['qualification_id'] for a in sample['attempts']):
        sample['attempts'].append(q)
    write(ROOT/'migration/samples.yaml',catalog)
    print('Published complete NPP+ Flood Fill')

if __name__=='__main__':
    main()
