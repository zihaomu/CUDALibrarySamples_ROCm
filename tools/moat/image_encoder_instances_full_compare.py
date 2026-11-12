#!/usr/bin/env python3
"""Compare 13 old baseline products exactly and document 3 CPU-to-GPU opt changes."""
import json
import numpy as np
from PIL import Image, JpegImagePlugin
from experiment import ROOT, Experiment, digest, write
from image_progress import record

PROFILE = ROOT / 'migration/rewrite/image-jpeg-encoder-instances-full-gpu-profile.json'
OPT_PROFILE = ROOT / 'migration/rewrite/image-jpeg-encoder-instances-opt-profile.json'
RUNS = ROOT / 'migration/reports/image-jpeg-encoder-instances-runs.json'
REPORT = ROOT / 'migration/reports/image-jpeg-encoder-instances-full-comparison.json'


def main():
    profile = json.loads(PROFILE.read_text())
    opt_profile = json.loads(OPT_PROFILE.read_text())
    runs = {r['case']: r for r in json.loads(RUNS.read_text())}
    if profile['status'] != 'FROZEN' or opt_profile['status'] != 'FROZEN' or not all(r['status'] == 'PASSED' for r in runs.values()):
        raise ValueError('frozen contract and successful current runs required')
    e = Experiment('I5', 'multi-instance-sixteen-JPEG-prior-vs-full-GPU-decode',
                   'CPU-reference', sources=[__file__, PROFILE, OPT_PROFILE, RUNS],
                   parent=profile['evidence'].split('/')[-1])
    rows = []
    for old in profile['prior_products']:
        previous = ROOT / old['path']
        current = ROOT / runs[old['case']]['evidence'] / 'outputs' / old['file']
        if digest(previous) != old['sha256'] or not current.is_file():
            raise ValueError('prior product identity or current output missing')
        with Image.open(previous) as image:
            image.load(); a = np.asarray(image.convert('RGB'))
            geometry = image.size; sampling = JpegImagePlugin.get_sampling(image)
            quant = image.quantization
        with Image.open(current) as image:
            image.load(); b = np.asarray(image.convert('RGB'))
            same_header = (image.size == geometry and
                           JpegImagePlugin.get_sampling(image) == sampling and
                           image.quantization == quant)
        rows.append(dict(case=old['case'], file=old['file'],
                         previous_sha256=old['sha256'], current_sha256=digest(current),
                         exact_decoded_rgb=a.shape == b.shape and np.array_equal(a, b),
                         mean_absolute_rgb_delta=float(np.mean(np.abs(a.astype(np.int16)-b.astype(np.int16)))),
                         header_sampling_quant_match=same_header,
                         decoded_rgb_bytes=int(a.size)))
    checks = [dict(check='all-sixteen-frozen-products', passed=len(rows) == 16),
              dict(check='thirteen-baseline-independent-decoded-RGB-exact',
                   passed=sum(r['case']!='optimized-444' for r in rows)==13 and
                   all(r['exact_decoded_rgb'] for r in rows if r['case']!='optimized-444')),
              dict(check='three-optimized-products-validated-against-same-GPU-FDCT-plain',
                   passed=sum(r['case']=='optimized-444' for r in rows)==3 and
                   all(any(c['check']=='optimized-RGB-exact-vs-same-GPU-FDCT-plain-'+str(i) and c['passed']
                           for c in runs['optimized-444']['checks']) for i in range(3))),
              dict(check='geometry-sampling-quantization-exact',
                   passed=all(r['header_sampling_quant_match'] for r in rows))]
    status = 'PASSED' if all(c['passed'] for c in checks) else 'NUMERIC_MISMATCH'
    result = dict(status=status, checks=checks, products=rows,
                  total_decoded_rgb_bytes=sum(r['decoded_rgb_bytes'] for r in rows),
                  experiment_id=e.id)
    write(e.path / 'comparison.json', result)
    result['evidence'] = e.finish(status, dict(status=status, checks=checks))
    write(REPORT, result)
    record('I5', '原始多实例编码16件 JPEG 独立解码：13 baseline 旧 RGB 精确，3 优化输出按同源GPU FDCT plain精确；旧CPU优化结果差值逐件记录，尺寸/采样/量化均核对：' + status + '。', [result['evidence']])
    print(status, len(rows), result['total_decoded_rgb_bytes'])
    return int(status != 'PASSED')


if __name__ == '__main__':
    raise SystemExit(main())
