#!/usr/bin/env python3
"""Exercise all twelve original JPEG files through the actual decoder entrypoint."""
import json
from pathlib import Path

from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

CORPUS = ROOT / 'nvJPEG/nvJPEG-Decoder/input_images'
BUILD = ROOT / 'migration/reports/image-progressive-integration.json'
PROFILE = ROOT / 'migration/rewrite/image-progressive-gpu-profile.json'
REPORT = ROOT / 'migration/reports/image-progressive-original-corpus.json'


def main():
    build = json.loads(BUILD.read_text())
    if build['status'] != 'BUILT' or any(
            digest(ROOT / name) != sha for name, sha in build['dependencies'].items()):
        raise ValueError('current integrated decoder build required')
    profile = json.loads(PROFILE.read_text())
    prototypes = {r['input']: r for r in json.loads(
        (ROOT / 'migration/reports/image-progressive-runs.json').read_text())}
    files = sorted(p for p in CORPUS.iterdir() if p.is_file())
    e = Experiment('I4', 'actual-nvJPEG-decoder-twelve-original-JPEG-files',
                   'rocm-original', sources=[__file__, BUILD, PROFILE, *files,
                   ROOT / 'rocm/common/image/jpeg_decoder_v2.hpp',
                   ROOT / 'rocm/common/image/progressive_jpeg.hpp'],
                   parent=build['experiment_id'])
    write(e.path / 'backend.observed.json', capture())
    output = e.path / 'outputs'; output.mkdir()
    rc = e.command([str(ROOT / build['binary']), '-i', str(CORPUS),
                    '-fmt', 'rgbi', '-b', '3', '-o', str(output)],
                   'all-twelve-original-JPEG-files', timeout=300)
    names = {p.name for p in files}
    products = {}
    for name in sorted(names):
        raw = output / (name + '.rgbi.s1.raw')
        meta = Path(str(raw) + '.json')
        if raw.is_file() and meta.is_file():
            products[name] = dict(bytes=raw.stat().st_size, sha256=digest(raw),
                                  metadata=json.loads(meta.read_text()))
    checks = [dict(check='original-entry-exit-zero', passed=rc == 0),
              dict(check='all-twelve-original-JPEG-products',
                   passed=len(files) == len(products) == 12),
              dict(check='all-progressive-pixels-from-GPU-no-CPU-fallback',
                   passed=all(name in products and
                              products[name]['metadata'].get('gpu_software_decode') == 1 and
                              products[name]['metadata'].get('cpu_fallback') == 0
                              for name in prototypes)),
              dict(check='both-progressive-pixels-equal-standalone-HIP-prototype',
                   passed=all(name in products and
                              products[name]['sha256'] == proto['gpu_sha256']
                              for name, proto in prototypes.items())),
              dict(check='all-baseline-decoded-by-rocJPEG-hardware',
                   passed=all(products.get(name, {}).get('metadata', {}).get('gpu_software_decode') == 0 and
                              products.get(name, {}).get('metadata', {}).get('cpu_fallback') == 0
                              for name in names - set(prototypes)))]
    status = 'PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result = dict(status=status, return_code=rc, products=products,
                  checks=checks, experiment_id=e.id, build_evidence=build['evidence'])
    write(e.path / 'corpus.json', result)
    result['evidence'] = e.finish('PASSED' if status == 'PASSED' else 'RUNTIME_ERROR',
                                   dict(status=status, checks=checks))
    write(REPORT, result)
    record('I4', f'nvJPEG-Decoder 原始12图完整C++入口：{len(products)}/12产品，'
           f'2 progressive GPU像素/10 rocJPEG硬件分路检查 {status}；'
           '原例全部CLI/backend与独立CPU/CUDA整例资格待验。', [result['evidence']])
    print(status, len(products), '/', len(files))
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
