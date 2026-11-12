#!/usr/bin/env python3
"""Seal the I5 GPU transform subset for the two current resize adapters."""
import json
from pathlib import Path
from audit import check as audit_check
from experiment import ROOT, Experiment, digest, git, write
from image_progress import record

REPORT = ROOT / 'migration/reports/image-jpeg-encoder-subset-qualifications.json'


def load(name):
    return json.loads((ROOT / 'migration/reports' / name).read_text())


def sealed(ref):
    if audit_check(ROOT / ref):
        raise ValueError('unsealed or invalid evidence: ' + ref)


def main():
    profile = json.loads((ROOT / 'migration/rewrite/image-jpeg-encoder-gpu-profile.json').read_text())
    builds = load('image-jpeg-encoder-build.json')
    runs = load('image-jpeg-encoder-runs.json')
    trace = load('image-jpeg-encoder-trace.json')
    negatives = load('image-jpeg-encoder-negative.json')
    integration = load('image-jpeg-encoder-integration.json')
    cuda = {x['source']: x for x in load('batches9_11-validation.json') if x['batch'] == 'b10'}
    references = [builds['evidence'], trace['evidence']]
    references += [x['evidence'] for x in runs + negatives]
    if len(runs) != profile['gates']['all_cases'] or len(negatives) != 4 or len(integration) != 2:
        raise ValueError('complete I5 prototype and resize integration required')
    for ref in references + [x['evidence'] for x in integration]:
        sealed(ref)
    if (builds['status'] != 'BUILT' or trace['status'] != 'PASSED' or
        any(x['status'] != 'PASSED' for x in runs) or
        any(x['status'] != 'EXPECTED_REJECTION' for x in negatives) or
        any(x['status'] != 'PASSED_SUBSET' for x in integration)):
        raise ValueError('I5 subset gates not satisfied')
    qualifications = []
    for row in integration:
        source = row['source']
        frontend = ROOT / 'rocm/ported' / source
        current_deps = {str(frontend.relative_to(ROOT)): digest(frontend),
                        **row['dependencies']}
        old = cuda[source]
        checks = [dict(check='four-predeclared-GPU-encoder-inputs-and-independent-cross-decode',
                       passed=len(runs) == 4 and all(x['status'] == 'PASSED' for x in runs)),
                  dict(check='real-physical-GPU-forward-color-FDCT-quant-trace',
                       passed=trace['status'] == 'PASSED' and
                              trace['counts'] == {'rgb_to_plane': 3,
                                                  'forward_dct_quantize': 3}),
                  dict(check='four-malformed-input-rejections',
                       passed=len(negatives) == 4 and
                              all(x['status'] == 'EXPECTED_REJECTION' for x in negatives)),
                  dict(check='seven-original-CLI-case-groups-and-independent-CPU-validation',
                       passed=len(row['cases']) == 7 and all(x['return_code'] == 0 and
                            x['status'] == 'PASSED' for x in row['cases'])),
                  dict(check='all-produced-postprocess-JPEG-uses-GPU-FDCT',
                       passed=sum(x['encoded_products'] for x in row['cases']) >= 33 and
                              all(x['encoder_claims'] for x in row['cases'])),
                  dict(check='same-input-CUDA-math-comparison',
                       passed=old['cuda_comparison'] == 'PASSED' and
                              all(x['status'] == 'PASSED' for x in old['cuda_cases'])),
                  dict(check='current-source-and-compiled-header-closure',
                       passed=all(digest(ROOT / name) == sha for name, sha in
                                  current_deps.items()))]
        if not all(x['passed'] for x in checks):
            raise ValueError('I5 subset failed for ' + source)
        sample_id = source.rsplit('/', 1)[0] + '::' + source.rsplit('/', 1)[1]
        refs = references + [row['evidence']]
        e = Experiment('I5', sample_id, 'composite-subset-qualification',
                       sources=[__file__, frontend,
                                ROOT / 'migration/reports/image-jpeg-encoder-integration.json',
                                ROOT / 'migration/reports/image-jpeg-encoder-runs.json',
                                ROOT / 'migration/reports/image-jpeg-encoder-trace.json',
                                ROOT / 'migration/reports/image-jpeg-encoder-negative.json',
                                ROOT / 'migration/rewrite/image-jpeg-encoder-gpu-profile.json'])
        devices = json.loads((ROOT / row['evidence'] / 'backend.observed.json').read_text())['devices']
        q = dict(kind='image-JPEG-GPU-forward-transform-subset', status='PASSED',
                 contract_status='PARTIAL', sample_id=sample_id,
                 implementation=str(frontend.relative_to(ROOT)),
                 implementation_sha256=digest(frontend),
                 source_commit=git('rev-parse', 'HEAD').strip(),
                 case_count=9,
                 case_ids=['batches9_11/' + x['case'] for x in row['cases']] +
                          ['I4/progressive-GPU-pixel-synthesis',
                           'I5/GPU-JPEG-forward-transform-and-cross-decode'],
                 checks=checks, devices=devices, dependencies=current_deps,
                 evidence_references=refs,
                 rocm_evidence=row['evidence'], cuda_evidence=old['cuda_evidence'],
                 comparison_mode='HYBRID_GPU_FORWARD_TRANSFORM_CPU_ENTROPY',
                 remaining='GPU entropy/Huffman and bitstream packing; encoding-mode/table/APP-COM preservation; fixed-commit cold review')
        q['qualification_id'] = e.id
        write(e.path / 'qualification.json', {k: v for k, v in q.items()
                                               if k not in {'qualification_id', 'evidence'}})
        q['evidence'] = e.finish('PASSED', dict(status='PASSED', checks=checks))
        qualifications.append(q)
        write(REPORT, qualifications)
        record('I5', source+' 七组完整入口+GPU JPEG 前向变换与CPU熵编码子集资格封存；'
               '待GPU entropy、模式/metadata与冷检出，整例仍 PARTIAL。', [q['evidence']])
        print(source, 'SUBSET_PASSED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
