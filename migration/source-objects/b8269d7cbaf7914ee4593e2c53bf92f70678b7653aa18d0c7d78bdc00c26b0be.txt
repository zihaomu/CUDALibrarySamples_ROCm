#!/usr/bin/env python3
"""Freeze original JP2 main-header parsing and malformed-input matrix."""
import json
from experiment import ROOT, Experiment, write
from image_progress import record

SOURCE = ROOT / 'migration/rewrite/image-j2k-part1-crossdecode-profile.json'
CPU = ROOT / 'migration/reports/image-j2k-part1-crossdecode.json'
PROFILE = ROOT / 'migration/rewrite/image-j2k-container-profile.json'


def main():
    if PROFILE.exists():
        raise ValueError('I6 JP2 parser profile already frozen')
    sources = json.loads(SOURCE.read_text())['inputs']
    cpu = {r['case']: r for r in json.loads(CPU.read_text())}
    inputs = [dict(case=r['case'], source=r['source'], sha256=r['source_sha256'],
                   width=cpu[r['case']]['metrics']['width'],
                   height=cpu[r['case']]['metrics']['height'],
                   components=3, reversible=r['reversible']) for r in sources]
    cases = [r['case'] + '-jp2' for r in inputs] + [
        '2k_lossless-raw-j2k', 'invalid-signature', 'invalid-box-length',
        'truncated-main-header', 'zero-components', 'changed-SIZ-width']
    e = Experiment('I6', 'original-JP2-J2K-container-parser-contract', 'CPU-contract',
                   sources=[__file__, SOURCE, CPU, *[ROOT/r['source'] for r in inputs]])
    profile = dict(status='FROZEN', phase='I6', inputs=inputs, cases=cases,
                   gates=dict(all_three_original_JP2_headers=True,
                              independent_CPU_geometry=True, raw_J2K_SOC_SIZ_COD=True,
                              four_malformed_inputs_rejected_without_result=True,
                              changed_SIZ_changes_reported_width=True),
                   scope='CPU container/marker metadata only. No packet/tier1 or GPU JPEG2000 decode is inferred.')
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('OBSERVED', dict(status='FROZEN', checks=[
        dict(check='nine-predeclared-main-header-cases', passed=len(cases) == 9)]))
    write(PROFILE, profile)
    record('I6', '原始 JP2/J2K 容器与主头解析 9 组合同先冻结：3真实JP2、1原始codestream、4损坏、1变更重放；只算CPU描述阶段。',
           [profile['evidence']])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
