#!/usr/bin/env python3
"""Seal I4 GPU progressive JPEG subset evidence for all six existing adapters."""
import json
from pathlib import Path

from audit import check as audit_check
from experiment import ROOT, Experiment, digest, git, write
from image_progress import record

REPORT = ROOT / 'migration/reports/image-progressive-subset-qualifications.json'


def latest(sample):
    directory = ROOT / 'migration/reports/evidence/rewrite/I4' / sample
    children = sorted(p for p in directory.iterdir() if p.is_dir())
    if not children:
        raise ValueError('missing completed regression: ' + sample)
    return str(children[-1].relative_to(ROOT))


def main():
    runs = {r['source']: r for r in json.loads(
        (ROOT / 'migration/reports/batches9_11-rocm.json').read_text()) if r['batch'] == 'b10'}
    validations = {r['source']: r for r in json.loads(
        (ROOT / 'migration/reports/batches9_11-validation.json').read_text()) if r['batch'] == 'b10'}
    profile = json.loads((ROOT / 'migration/rewrite/image-progressive-gpu-profile.json').read_text())
    prototype = json.loads((ROOT / 'migration/reports/image-progressive-runs.json').read_text())
    trace = json.loads((ROOT / 'migration/reports/image-progressive-trace.json').read_text())
    corpus = json.loads((ROOT / 'migration/reports/image-progressive-original-corpus.json').read_text())
    archive = json.loads((ROOT / 'migration/reports/image-progressive-harness-archive.json').read_text())
    refs = [latest('nvJPEG-isolated-backend-six-entry-regression'),
            latest('nvJPEG-isolated-backend-six-entry-CPU-CUDA'),
            trace['evidence'], corpus['evidence'], archive['evidence']]
    refs += [r['evidence'] for r in prototype]
    if any(audit_check(ROOT / ref) for ref in refs):
        raise ValueError('a referenced MOAT evidence seal is invalid')
    if not (len(runs) == len(validations) == 6 and len(prototype) == 2 and
            all(r['status'] == 'PASSED' for r in prototype) and
            trace['status'] == corpus['status'] == archive['status'] == 'PASSED' and
            archive['text_file_count'] >= 880 and archive['binary_product_count'] >= 511):
        raise ValueError('all six adapters and both original progressive inputs required')
    qualifications = []
    for source, run in runs.items():
        validation = validations[source]
        original = next(r for r in run['runs'] if r['case'] == 'original-corpus')
        case = json.loads((ROOT / original['evidence'] / 'case.json').read_text())
        product = {item['raw'].split('/')[-1].removesuffix('.rgbi.s1.raw'): item
                   for item in case['outputs']}
        progressive_names = {'cat.jpg', 'img9.jpg'}
        other_names = set(product) - progressive_names
        checks = [dict(check='all-seven-original-B10-cases-current-source',
                       passed=run['build_return_code'] == 0 and
                              validation['status'] == 'PASSED' and
                              validation['current_source_proof'] is True and
                              len(validation['cases']) == 7 and
                              all(c['status'] == 'PASSED' for c in validation['cases'])),
                  dict(check='all-seven-same-input-CUDA-math-comparisons',
                       passed=validation['cuda_comparison'] == 'PASSED' and
                              all(c['status'] == 'PASSED' for c in validation['cuda_cases'])),
                  dict(check='all-12-original-corpus-images', passed=len(product) == 12),
                  dict(check='two-progressive-GPU-pixels-and-no-CPU-pixel-fallback',
                       passed=all(product.get(name, {}).get('metadata', {}).get('gpu_software_decode') == 1 and
                                  product[name]['metadata'].get('cpu_fallback') == 0
                                  for name in progressive_names)),
                  dict(check='ten-baseline-rocJPEG-hardware-pixels',
                       passed=len(other_names) == 10 and
                              all(product[name]['metadata'].get('gpu_software_decode') == 0 and
                                  product[name]['metadata'].get('cpu_fallback') == 0 for name in other_names)),
                  dict(check='fixed-progressive-CPU-RGB-gates',
                       passed=all(r['max_abs'] <= profile['gates']['max_abs_per_channel'] and
                                  r['psnr_db'] >= profile['gates']['min_rgb_psnr_db'] for r in prototype)),
                  dict(check='actual-physical-GPU-IDCT-and-RGB-trace',
                       passed=trace['status'] == 'PASSED' and
                              trace['kernel_counts'].get('inverse_dct') == 3 and
                              trace['kernel_counts'].get('convert_rgb') == 1)]
        if not all(c['passed'] for c in checks):
            raise ValueError('progressive subset gate failed: ' + source)
        implementation = run['implementation']
        dependencies = dict(validation['dependencies'])
        dependencies[implementation] = digest(ROOT / implementation)
        dependencies['migration/rewrite/image-progressive-gpu-profile.json'] = digest(
            ROOT / 'migration/rewrite/image-progressive-gpu-profile.json')
        e = Experiment('I4', source, 'composite-subset-qualification',
            sources=[__file__, ROOT / implementation,
                     ROOT / 'migration/reports/batches9_11-rocm.json',
                     ROOT / 'migration/reports/batches9_11-validation.json',
                     ROOT / 'migration/reports/image-progressive-runs.json',
                     ROOT / 'migration/reports/image-progressive-trace.json',
                     ROOT / 'migration/reports/image-progressive-original-corpus.json',
                     ROOT / 'migration/reports/image-progressive-harness-archive.json',
                     ROOT / 'migration/rewrite/image-progressive-gpu-profile.json'])
        q = dict(kind='image-progressive-GPU-subset', status='PASSED',
                 contract_status='PARTIAL', sample_id=source.rsplit('/', 1)[0] +
                 '::' + source.rsplit('/', 1)[1], implementation=implementation,
                 implementation_sha256=digest(ROOT / implementation),
                 source_commit=git('rev-parse', 'HEAD').strip(),
                 case_count=8, case_ids=['batches9_11/' + r['case'] for r in run['runs']] +
                 ['I4/progressive-GPU-pixel-synthesis'],
                 checks=checks, dependencies=dependencies,
                 evidence_references=refs,
                 rocm_evidence=archive['evidence'] + '/harness/' + source.replace('/', '__'),
                 cuda_evidence=validation['cuda_evidence'],
                 comparison_mode='GPU_PROGRESSIVE_PROJECT_ALGORITHM',
                 remaining='native backend enum/pipeline or automatic scheduling, CPU JPEG encoding, and fixed-commit cold review vary by entrypoint')
        q['qualification_id'] = e.id
        write(e.path / 'qualification.json', {k: v for k, v in q.items()
                                                if k not in {'qualification_id', 'evidence'}})
        q['evidence'] = e.finish('PASSED', dict(status='PASSED', checks=checks))
        qualifications.append(q)
        write(REPORT, qualifications)
        record('I4', f'{source} 七组历史合同+两原始 progressive GPU像素/trace/current source '
               '复合子集证据封存；整例仍 PARTIAL，待剩余语义/冷检出复审。', [q['evidence']])
        print(source, 'SUBSET_PASSED', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
