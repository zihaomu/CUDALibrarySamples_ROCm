#!/usr/bin/env python3
"""Run both complete watershed entrypoints on their original image sets."""
import json
import shutil

from experiment import ROOT, Experiment, digest, write
from image_progress import record
from image_watershed_build import dependencies
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-watershed-profile.json'
BUILD = ROOT / 'migration/reports/image-watershed-build.json'
REPORT = ROOT / 'migration/reports/image-watershed-runs.json'


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    if profile['status'] != 'FROZEN' or build['status'] != 'BUILT':
        raise ValueError('a frozen contract and complete HIP build are required')
    if any(digest(ROOT / name) != sha for name, sha in build['dependencies'].items()):
        raise ValueError('build dependency changed; rebuild before execution')
    rows = []
    for sample in profile['samples']:
        family = sample['sample_id'].split('/')[0]
        binary = build['binaries'][family]
        if digest(ROOT / binary['path']) != binary['sha256']:
            raise ValueError('HIP binary hash changed')
        e = Experiment('I3', sample['sample_id'], 'rocm-original-full-images',
            sources=[__file__, PROFILE, BUILD, *dependencies(),
                     *[ROOT / family / 'watershedSegmentation/images' / image['name']
                       for image in sample['inputs']]], parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        images = e.path / 'images'
        images.mkdir()
        for image in sample['inputs']:
            source = ROOT / family / 'watershedSegmentation/images' / image['name']
            if digest(source) != image['sha256'] or source.stat().st_size != image['bytes']:
                raise ValueError('frozen original input changed: ' + str(source))
            shutil.copyfile(source, images / image['name'])
        work = e.path / 'work'
        work.mkdir()
        rc = e.command([str(ROOT / binary['path'])], 'full-original-entrypoint',
                       cwd=work, timeout=300)
        observed = {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size}
                    for p in images.iterdir() if p.name not in
                    {image['name'] for image in sample['inputs']}}
        expected = sample['products']
        checks = [dict(check='entrypoint-exit-zero', passed=rc == 0),
                  dict(check='all-original-product-names',
                       passed=set(observed) == set(expected),
                       expected=sorted(expected), observed=sorted(observed)),
                  dict(check='all-original-product-sizes',
                       passed=set(observed) == set(expected) and
                       all(observed[name]['bytes'] == expected[name]['bytes']
                           for name in expected))]
        status = 'EXECUTED' if all(c['passed'] for c in checks) else 'RUNTIME_ERROR'
        row = dict(sample_id=sample['sample_id'], family=family,
                   status=status, return_code=rc, experiment_id=e.id,
                   build_evidence=build['evidence'], outputs=observed,
                   output_dir=str(images.relative_to(ROOT)), checks=checks)
        write(e.path / 'run.json', row)
        row['evidence'] = e.finish(status, dict(status=status, checks=checks))
        rows.append(row)
        write(REPORT, rows)
        record('I3', f'{family} watershed 原始完整入口在 AMD GPU 上运行：'
               f'{len(observed)}/{len(expected)} 产品，rc={rc}，状态 {status}；'
               '逐字节 CPU 数值验收待完成。', [row['evidence']])
        print(family, status, len(observed), '/', len(expected), flush=True)
    return int(any(row['status'] != 'EXECUTED' for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
