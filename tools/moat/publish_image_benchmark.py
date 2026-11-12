#!/usr/bin/env python3
"""Publish the complete NPP benchmark only after its composite proof is in Git."""
import json
from experiment import ROOT,write,digest
from qualify_image_benchmark import SAMPLE,IMPLEMENTATION,COMPARISON,collect,expected_dependencies,load
from selected_proofs import inspect,anchored_seal,publication

def main():
    q=json.loads((ROOT/'migration/reports/image-benchmark-qualification.json').read_text())
    review=json.loads((ROOT/'migration/reports/image-benchmark-review.json').read_text())
    catalog=json.loads((ROOT/'migration/samples.yaml').read_text())
    sample=next(s for s in catalog['samples'] if s['id']==SAMPLE)
    checks,refs,build,profile=collect(review)
    proof=ROOT/q['evidence'];manifest=json.loads((proof/'manifest.json').read_text())
    frozen=json.loads((proof/'qualification.json').read_text())
    if (not anchored_seal(proof,publication(proof),qualification=True)
      or q['sample_id']!=SAMPLE or q['kind']!='image-benchmark-full' or q['status']!='PASSED'
      or q['implementation']!=IMPLEMENTATION or q['implementation_sha256']!=digest(ROOT/IMPLEMENTATION)
      or q['source_commit']!=review['source_commit']
      or q['comparison_mode']!=COMPARISON
      or q['dependencies']!=expected_dependencies(build)
      or q['checks']!=checks or not all(c['passed'] for c in checks)
      or set(q['evidence_references'])!=refs
      or q['case_ids']!=[c['case'] for c in profile['cases']] or q['case_count']!=6
      or q['rocm_evidence']!=next(r['evidence'] for r in load('runs') if r['case']=='original-default')
      or q['cuda_evidence']!=json.loads((ROOT/'migration/reports/image-I3-benchmark-native.json').read_text())['evidence']
      or q['environment']!=build['evidence']+'/backend.observed.json'
      or q['devices']!=json.loads((ROOT/build['evidence']/'backend.observed.json').read_text())['devices']
      or manifest['backend']!='composite-qualification' or manifest['sample_id']!=SAMPLE
      or manifest['experiment_outcome']!='PASSED' or manifest['experiment_id']!=q['qualification_id']
      or {k:v for k,v in q.items() if k not in {'qualification_id','evidence'}}!=frozen):
        raise ValueError('unanchored, altered, or incomplete benchmark qualification')
    if inspect(dict(sample,implementation=IMPLEMENTATION,selected_validation=q))['status']!='PASSED':
        raise ValueError('selected proof is not publication-ready')
    required=['image-benchmark/'+case for case in q['case_ids']]+[
       'image-benchmark/matched-OpenCV4.12-and-four-HIP-build',
       'image-benchmark/all-four-independent-CPU-and-printed-metrics',
       'image-benchmark/original-5090-and-algorithm-variants',
       'image-benchmark/eighteen-device-contracts',
       'image-benchmark/real-four-operation-trace',
       'image-benchmark/nineteen-reader-counterexamples',
       'image-benchmark/nineteen-child-fixed-commit-cold-replay',
       'image-benchmark/three-independent-reviews']
    sample.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',
       implementation=IMPLEMENTATION,selected_validation=q,
       required_cases=required,passed_cases=required,
       actual_library='Project HIP Gaussian/Canny/resize/RGB gray plus pinned OpenCV 4.12 CPU benchmark',
       backend_library='project HIP image benchmark',equivalence=COMPARISON,
       reason='完整四算子C++原例、6 CLI、独立CPU全量产品/四行OpenCV统计、5090原生同输入与同构建OpenCV对照、18设备合同、真实GPU trace、19项反例及19子证据固定提交冷检出、三份独立复审通过。Gaussian/Canny为明确项目算法变体；NPP原生未输出像素，不宣称NPP逐像素等价；计时仅观察。',
       cuda_baseline='PASSED',cuda_comparison='OBSERVED',
       cuda_comparison_mode=COMPARISON,
       cuda_comparison_reason='5090原生与ROCm同输入/4096×2048/20×5/OpenCV4.12。NPP不输出产品像素；Gaussian原生vsOpenCV均差1.70、项目0.00（原始尺寸），Canny计数同546308但掩码不保证相同。',
       benchmark='OBSERVED_NOT_QUALIFIED',active_batch='I3',
       retry_condition='四算子数学政策、共享HIP核、CPU oracle、OpenCV版本/动态库、CLI或实验门改变需重新资格。',
       next_step='I3两个watershed完整入口、I4–I9 JPEG/JPEG2000 队列。',
       reproduce='python3 tools/moat/image_benchmark_contracts.py\npython3 tools/moat/image_benchmark_deps.py\npython3 tools/moat/image_benchmark_build.py\npython3 tools/moat/image_benchmark_run.py\nbuild/image-cpu-venv/bin/python tools/moat/image_benchmark_reference.py\npython3 tools/moat/image_benchmark_native_comparison.py\npython3 tools/moat/image_benchmark_runtime.py\npython3 tools/moat/image_benchmark_trace.py\npython3 tools/moat/image_benchmark_cold.py\npython3 tools/moat/qualify_image_benchmark.py')
    for ref in ['migration/reports/image-benchmark.md',q['evidence'],*q['evidence_references']]:
      if ref not in sample['evidence']:sample['evidence'].append(ref)
    if not any(a.get('qualification_id')==q['qualification_id'] for a in sample['attempts']):sample['attempts'].append(q)
    write(ROOT/'migration/samples.yaml',catalog)
    print('Published complete NPP OpenCV benchmark')

if __name__=='__main__':main()
