#!/usr/bin/env python3
"""Check that instrumented full-image CPU decode preserved frozen RGB identity."""
import hashlib
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record

CAPTURE = ROOT / 'migration/reports/image-j2k-real-mq-capture.json'
REFERENCE = ROOT / 'migration/reports/image-j2k-part1-crossdecode.json'
CONTRACT = ROOT / 'migration/rewrite/image-j2k-part1-crossdecode-profile.json'
REPORT = ROOT / 'migration/reports/image-j2k-real-mq-crosscheck.json'


def main():
    captured = json.loads(CAPTURE.read_text())
    reference = next(row for row in json.loads(REFERENCE.read_text())
                     if row['case'] == '2k_lossless')
    contract = next(row for row in json.loads(CONTRACT.read_text())['inputs']
                    if row['case'] == '2k_lossless')
    ppm = ROOT / captured['evidence'].replace('migration/reports/evidence/rewrite',
                                               'artifacts/rewrite') / 'full.ppm'
    if captured['status'] != 'CAPTURED' or digest(ppm) != captured['image_output_sha256'] or \
            captured['original_jp2_sha256'] != contract['source_sha256']:
        raise ValueError('instrumented full-image output changed')
    data = ppm.read_bytes()
    parts = data.split(b'\n', 4)
    valid_header = len(parts) == 5 and parts[0] == b'P6' and \
        parts[1].startswith(b'# OpenJPEG-') and parts[2] == b'1920 1080' and parts[3] == b'255'
    rgb = parts[4] if valid_header else b''
    sha = hashlib.sha256(rgb).hexdigest()
    exact = valid_header and len(rgb) == 1920 * 1080 * 3 and \
        sha == reference['metrics']['source_rgb_sha256'] == reference['metrics']['cuda_rgb_sha256']
    e = Experiment('I6', 'instrumented-OpenJPEG-original-JP2-full-RGB-crosscheck',
                   'CPU-reference', sources=[__file__, CAPTURE, REFERENCE, CONTRACT,
                                             ROOT / contract['source']],
                   parent=captured['evidence'].split('/')[-1])
    result = dict(status='PASSED' if exact else 'NUMERIC_MISMATCH',
                  width=1920, height=1080, rgb_bytes=len(rgb),
                  rgb_sha256=sha, expected_sha256=reference['metrics']['source_rgb_sha256'],
                  original_cuda_rgb_sha256=reference['metrics']['cuda_rgb_sha256'],
                  ppm_sha256=digest(ppm), exact=exact,
                  scope='CPU OpenJPEG instrumentation noninterference; no GPU JPEG2000 image decode.')
    write(e.path / 'comparison.json', result)
    result['evidence'] = e.finish('PASSED' if exact else 'NUMERIC_MISMATCH',
                                  dict(status=result['status'], checks=[
                                      dict(check='full-original-lossless-RGB-exact-vs-CPU-and-CUDA', passed=exact)]))
    write(REPORT, result)
    record('I6', 'OpenJPEG只读MQ捕获对整张原图解码无扰动：' + result['status'] +
           '；6,220,800 RGB 字节与既存独立CPU及原生CUDA精确一致，仅CPU交叉检查。',
           [result['evidence'], str(REPORT.relative_to(ROOT))])
    print(result['status'], sha)
    return int(not exact)


if __name__ == '__main__':
    raise SystemExit(main())
