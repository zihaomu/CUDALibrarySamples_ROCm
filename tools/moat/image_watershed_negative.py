#!/usr/bin/env python3
"""Reject missing original image without producing watershed products."""
import json
import shutil

from experiment import ROOT, Experiment, digest, write
from image_progress import record
from image_watershed_build import dependencies

PROFILE = ROOT / 'migration/rewrite/image-watershed-profile.json'
BUILD = ROOT / 'migration/reports/image-watershed-build.json'
REPORT = ROOT / 'migration/reports/image-watershed-negative.json'


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    rows = []
    for sample in profile['samples']:
        family = sample['sample_id'].split('/')[0]
        binary = ROOT / build['binaries'][family]['path']
        if digest(binary) != build['binaries'][family]['sha256']:
            raise ValueError('binary identity mismatch')
        e = Experiment('I3', sample['sample_id'], 'rocm-missing-input',
                       sources=[__file__, PROFILE, BUILD, *dependencies()],
                       parent=build['experiment_id'])
        images = e.path / 'images'; images.mkdir()
        work = e.path / 'work'; work.mkdir()
        missing = sample['inputs'][-1]['name']
        for image in sample['inputs'][:-1]:
            source = ROOT / family / 'watershedSegmentation/images' / image['name']
            shutil.copyfile(source, images / image['name'])
        rc = e.command([str(binary)], 'missing-last-original-image', cwd=work, timeout=120)
        error_log = (e.path / 'logs/0001-missing-last-original-image.stderr.log').read_text()
        all_products = set(sample['products'])
        produced = {p.name for p in images.iterdir() if p.name in all_products}
        expected_previous = {p for p in all_products if not p.endswith(missing)} if family == 'NPP' else {
            p for p in all_products if not p.startswith('Corn_')}
        checks = [dict(check='nonzero-exit-on-missing-input', passed=rc != 0),
                  dict(check='missing-file-diagnostic', passed=missing in error_log),
                  dict(check='no-product-for-missing-image',
                       passed=produced == expected_previous,
                       expected=sorted(expected_previous), observed=sorted(produced))]
        status = 'PASSED' if all(c['passed'] for c in checks) else 'FAILED'
        row = dict(family=family, status=status, return_code=rc,
                   missing=missing, products=sorted(produced), checks=checks)
        write(e.path / 'negative.json', row)
        row['evidence'] = e.finish('EXPECTED_REJECTION' if status == 'PASSED' else 'COMMAND_FAILED',
                                    dict(status=status, checks=checks))
        rows.append(row); write(REPORT, rows)
        record('I3', f'{family} watershed 缺失最后一张原图负向执行：'
               f'rc={rc}，诊断与无缺图产品检查 {status}。', [row['evidence']])
        print(family, status, flush=True)
    return int(any(r['status'] != 'PASSED' for r in rows))


if __name__ == '__main__':
    raise SystemExit(main())
