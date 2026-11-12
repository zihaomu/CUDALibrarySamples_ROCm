#!/usr/bin/env python3
"""Archive current six-entry JPEG harness text logs and hash every binary product."""
import json
import shutil

from experiment import ROOT, Experiment, digest, write
from image_progress import record

RUNS = ROOT / 'migration/reports/batches9_11-rocm.json'
VALIDATION = ROOT / 'migration/reports/batches9_11-validation.json'
REPORT = ROOT / 'migration/reports/image-progressive-harness-archive.json'


def main():
    runs = [r for r in json.loads(RUNS.read_text()) if r['batch'] == 'b10']
    if len(runs) != 6 or any(r['build_return_code'] != 0 or len(r['runs']) != 7 for r in runs):
        raise ValueError('current complete six-entry B10 run required')
    e = Experiment('I4', 'six-JPEG-entry-current-full-harness-logs-and-product-hashes',
                   'host-evidence-archive', sources=[__file__, RUNS, VALIDATION])
    text_files = {}; products = {}
    for row in runs:
        root = ROOT / row['evidence']
        if not root.is_dir():
            raise ValueError('missing raw harness directory: ' + str(root))
        prefix = row['source'].replace('/', '__')
        for source in root.rglob('*'):
            if not source.is_file():
                continue
            relative = source.relative_to(root)
            key = prefix + '/' + str(relative)
            if source.suffix in {'.json', '.log', '.csv', '.txt'}:
                target = e.path / 'harness' / key
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                text_files[key] = dict(bytes=source.stat().st_size, sha256=digest(source))
            elif source.suffix.lower() in {'.raw', '.bmp', '.jpg', '.bin'}:
                products[key] = dict(bytes=source.stat().st_size, sha256=digest(source),
                                     original_local_path=str(source.relative_to(ROOT)))
    checks = [dict(check='six-full-entry-text-logs-copied', passed=len(text_files) >= 100),
              dict(check='nonempty-binary-product-index', passed=len(products) >= 12),
              dict(check='all-copied-text-hashes-match-source',
                   passed=all(digest(e.path / 'harness' / key) == info['sha256']
                              for key, info in text_files.items()))]
    status = 'PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result = dict(status=status, source_report=str(RUNS.relative_to(ROOT)),
                  validation_report=str(VALIDATION.relative_to(ROOT)),
                  text_files=text_files, binary_products=products,
                  reconstruction='Rerun tools/migration/batches9_11_run.py b10 with the sealed source-tree and pinned image/fixtures; raw binary products remain local artifacts.',
                  checks=checks)
    write(e.path / 'inventory.json', result)
    result['evidence'] = e.finish('PASSED' if status == 'PASSED' else 'SELF_TEST_FAILED',
                                   dict(status=status, checks=checks))
    write(REPORT, dict(status=status, text_file_count=len(text_files),
                       binary_product_count=len(products), evidence=result['evidence'],
                       source_report=result['source_report'],
                       validation_report=result['validation_report']))
    record('I4', f'六JPEG入口当前完整harness归档 {len(text_files)} 个日志/JSON 与 '
           f'{len(products)} 个二进制产品SHA：{status}；大产品按固定命令重建。',
           [result['evidence']])
    print(status, len(text_files), len(products), result['evidence'])
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
