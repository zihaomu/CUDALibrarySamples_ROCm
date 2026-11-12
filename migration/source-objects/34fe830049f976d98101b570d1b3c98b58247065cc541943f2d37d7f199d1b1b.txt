#!/usr/bin/env python3
"""Publish current GPU progressive JPEG evidence while retaining PARTIAL scope."""
import json

from experiment import ROOT, digest, write
from image_progress import record
from selected_proofs import anchored_seal, publication

QUALIFICATIONS = ROOT / 'migration/reports/image-progressive-subset-qualifications.json'
CATALOG = ROOT / 'migration/samples.yaml'


def missing(source):
    work = ['I4/fixed-commit-cold-replay-and-independent-review']
    if 'MultipleInstances' in source:
        work.append('I4/original-automatic-multiple-instance-scheduling')
    if 'Backend-ROI' in source:
        work.append('I4/original-backend-enums-and-decoupled-pipeline')
    if 'Image-Resize' in source:
        work.append('I5/GPU-JPEG-reencoding-and-metadata')
    return work


def main():
    qualifiers = json.loads(QUALIFICATIONS.read_text())
    catalog = json.loads(CATALOG.read_text())
    if len(qualifiers) != 6:
        raise ValueError('all six current JPEG adapters required')
    for q in qualifiers:
        proof = ROOT / q['evidence']
        frozen = json.loads((proof / 'qualification.json').read_text())
        sample = next(s for s in catalog['samples'] if s['id'] == q['sample_id'])
        if (not anchored_seal(proof, publication(proof), qualification=True) or
            q['kind'] != 'image-progressive-GPU-subset' or
            q['status'] != 'PASSED' or q['contract_status'] != 'PARTIAL' or
            q['case_count'] != 8 or len(q['case_ids']) != 8 or
            not all(c['passed'] for c in q['checks']) or
            q['implementation'] != sample['implementation'] or
            q['implementation_sha256'] != digest(ROOT / q['implementation']) or
            any(digest(ROOT / name) != sha for name, sha in q['dependencies'].items()) or
            {k: v for k, v in q.items() if k not in {'qualification_id', 'evidence'}} != frozen or
            not (ROOT / q['rocm_evidence']).is_dir() or
            not all(anchored_seal(ROOT / ref, publication(ROOT / ref))
                    for ref in q['evidence_references'])):
            raise ValueError('incomplete or unanchored progressive subset: ' + q['sample_id'])
        remaining = missing(sample['source'])
        passed = q['case_ids']
        route = ('rocJPEG hardware baseline + project HIP progressive IDCT/chroma/RGB; '
                 'libjpeg-turbo CPU entropy assembly')
        if 'Image-Resize' in sample['source']:
            route += ' + current CPU JPEG encode'
        sample.update(status='PARTIAL', level='L4',
            reason_code='VALIDATED_I4_PROGRESSIVE_SUBSET',
            actual_library=route,
            backend_library='rocJPEG + project HIP image decoder + libjpeg-turbo entropy',
            equivalence='HYBRID_CPU_GPU',
            selected_validation=q,
            required_cases=passed + remaining,
            passed_cases=passed,
            reason='七组原登记流程与同输入 CUDA 数学对照重新通过；12 原始 JPEG 中 10 张 rocJPEG 硬件解码、'
                   '2 张 progressive 使用 CPU 熵装配 + AMD GPU IDCT/色度/RGB，独立 CPU maxAbs≤3、'
                   'PSNR≥60.76 dB，真实 GPU kernel trace 已验。当前仍缺：' +
                   '、'.join(remaining) + '。',
            cuda_comparison='PASSED',
            cuda_comparison_mode='GPU_PROGRESSIVE_PROJECT_ALGORITHM',
            cuda_comparison_reason='既有七组同输入 CUDA 数学对照通过；progressive 采用项目 HIP 与 CPU 熵装配，'
                                   '不声称 nvJPEG 私有 backend/流水线 ABI 一致。',
            active_batch='I4',
            retry_condition='完成 ' + '、'.join(remaining) + ' 后重做固定提交资格；'
                            'progressive灰度/采样变体及错误流仍需增补输入合同。',
            next_step='I4 冷检出/独立复审与 backend/多实例；I5 GPU JPEG encoder；I6–I8 JPEG2000。',
            reproduce='HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh '
                      'python3 tools/moat/image_progressive_build.py\n'
                      'HIP_VISIBLE_DEVICES=2 /home/zihaomu/zihaomu_workspace/rocm10-launch.sh '
                      'python3 tools/migration/batches9_11_run.py b10\n'
                      'build/image-cpu-venv/bin/python tools/migration/batches9_11_validate.py b10\n'
                      'python3 tools/moat/qualify_image_progressive_subset.py')
        if not any(a.get('qualification_id') == q['qualification_id'] for a in sample['attempts']):
            sample['attempts'].append(q)
        for ref in [q['evidence'], q['rocm_evidence'],
                    'migration/reports/image-progressive.md',
                    'migration/reports/image-progressive-harness-archive.json',
                    'migration/reports/image-progressive-original-corpus.json',
                    'migration/reports/image-progressive-runs.json',
                    'migration/reports/image-progressive-trace.json']:
            if ref not in sample['evidence']:
                sample['evidence'].append(ref)
    write(CATALOG, catalog)
    report = dict(status='PUBLISHED_PARTIAL', sample_count=len(qualifiers),
        scope='Current eight-case numerical subset only; no complete nvJPEG sample promoted',
        sample_ids=[q['sample_id'] for q in qualifiers],
        evidence='migration/reports/image-progressive-subset-qualifications.json')
    write(ROOT / 'migration/reports/image-progressive-publication.json', report)
    record('I4', '六个 nvJPEG 入口新 progressive GPU 子集证据已按 Git 封印绑定到逐例主表；'
           '仍全部 PARTIAL，旧 CPU 回退原因改为各入口真实剩余缺口。',
           ['migration/reports/image-progressive-publication.json'])
    print('Published six current PARTIAL JPEG subsets')


if __name__ == '__main__':
    main()
