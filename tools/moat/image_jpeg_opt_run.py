#!/usr/bin/env python3
"""Independently decode optimized JPEGs and compare with frozen GPU FDCT baseline."""
import hashlib
import json
from PIL import Image, JpegImagePlugin
import numpy as np
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-jpeg-opt-huffman-profile.json'
BUILD = ROOT / 'migration/reports/image-jpeg-opt-huffman-build.json'
BASELINE = ROOT / 'migration/reports/image-jpeg-encoder-full-gpu-runs.json'
REPORT = ROOT / 'migration/reports/image-jpeg-opt-huffman-runs.json'


def dht_segments(data):
    if data[:2] != b'\xff\xd8':
        raise ValueError('JPEG SOI missing')
    segments = []
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xff:
            raise ValueError('invalid JPEG marker boundary')
        marker = data[pos + 1]
        if marker == 0xda:
            return segments
        size = (data[pos + 2] << 8) | data[pos + 3]
        if size < 2 or pos + 2 + size > len(data):
            raise ValueError('invalid JPEG marker length')
        if marker == 0xc4:
            segments.append(data[pos + 4:pos + 2 + size])
        pos += 2 + size
    raise ValueError('JPEG SOS missing')


def decode(path):
    with Image.open(path) as image:
        image.load()
        return (image.format, image.size, JpegImagePlugin.get_sampling(image),
                image.quantization, np.asarray(image.convert('RGB')).tobytes())


def main():
    profile = json.loads(PROFILE.read_text())
    build = json.loads(BUILD.read_text())
    baseline = {row['case']: row for row in json.loads(BASELINE.read_text())}
    binary = ROOT / build['binary']
    if profile['status'] != 'FROZEN' or build['status'] != 'BUILT' or \
            digest(binary) != build['binary_sha256'] or \
            any(digest(ROOT / p) != h for p, h in build['dependencies'].items()):
        raise ValueError('optimized JPEG source/build contract mismatch')
    results = []
    for item in profile['cases']:
        source = ROOT / item['path']
        prior = baseline[item['case']]
        prior_jpeg = ROOT / prior['evidence'].replace('migration/reports/evidence/rewrite',
                                                      'artifacts/rewrite') / 'output.jpg'
        if digest(source) != item['sha256'] or prior['status'] != 'PASSED' or \
                digest(prior_jpeg) != prior['jpeg_sha256']:
            raise ValueError('frozen JPEG input/baseline changed')
        e = Experiment('I5', 'optimized-Huffman-GPU-JPEG-' + item['case'], 'rocm-GPU',
                       case=item['case'], sources=[__file__, PROFILE, BUILD, BASELINE,
                                                  source, binary, prior_jpeg],
                       parent=build['experiment_id'])
        write(e.path / 'backend.observed.json', capture())
        output = e.path / 'output.jpg'
        rc = e.command([str(binary), str(source), str(item['width']), str(item['height']),
                        str(item['quality']), item['subsampling'], str(output)],
                       'encode-optimized-Huffman-with-GPU-entropy')
        checks = [dict(check='GPU-optimized-command-exit-zero', passed=rc == 0)]
        metrics = {}
        try:
            fmt, size, sampling, quant, rgb = decode(output)
            baseline_fmt, baseline_size, baseline_sampling, baseline_quant, baseline_rgb = decode(prior_jpeg)
            dht = dht_segments(output.read_bytes())
            baseline_dht = dht_segments(prior_jpeg.read_bytes())
            stdout = (e.path / 'logs/0001-encode-optimized-Huffman-with-GPU-entropy.stdout.log').read_text()
            metadata = json.loads(stdout.splitlines()[-1])
            metrics = dict(jpeg_sha256=digest(output), bytes=output.stat().st_size,
                           baseline_bytes=prior_jpeg.stat().st_size,
                           rgb_sha256=hashlib.sha256(rgb).hexdigest(),
                           dht_count=len(dht), dht_changed=dht != baseline_dht,
                           decoded_rgb_exact=rgb == baseline_rgb,
                           width=size[0], height=size[1], sampling=sampling,
                           gpu_metadata=metadata)
            checks.extend([
                dict(check='independent-libjpeg-JPEG-decode', passed=fmt == baseline_fmt == 'JPEG'),
                dict(check='geometry-sampling-quantization-exact',
                     passed=size == baseline_size == (item['width'], item['height']) and
                     sampling == baseline_sampling == (2 if item['subsampling'] == '420' else 0) and
                     quant == baseline_quant),
                dict(check='decoded-RGB-exact-vs-frozen-GPU-FDCT', passed=rgb == baseline_rgb),
                dict(check='optimized-DHT-differs-from-standard',
                     passed=len(dht) == 4 and (dht != baseline_dht if item['case'] != 'tiny-444' else True)),
                dict(check='GPU-histogram-and-entropy-no-CPU-entropy',
                     passed=metadata.get('gpu_huffman_histogram') is True and
                     metadata.get('gpu_entropy') is True and metadata.get('cpu_entropy') is False)])
        except Exception as error:
            metrics['error'] = repr(error)
            checks.append(dict(check='independent-cross-decode', passed=False, error=repr(error)))
        passed = all(check['passed'] for check in checks)
        result = dict(case=item['case'], status='PASSED' if passed else 'NUMERIC_MISMATCH',
                      return_code=rc, checks=checks, metrics=metrics,
                      output_sha256=digest(output) if output.exists() else None)
        write(e.path / 'comparison.json', result)
        result['evidence'] = e.finish('PASSED' if passed else 'NUMERIC_MISMATCH',
                                      dict(status=result['status'], checks=checks), metrics=metrics)
        results.append(result)
        write(REPORT, results)
        record('I5', f'优化 Huffman GPU 熵编码 {item["case"]}：{result["status"]}；独立解码/基线RGB/DHT核对。',
               [result['evidence']])
        print(item['case'], result['status'], metrics, flush=True)
        if not passed:
            return 1
    item = profile['cases'][0]
    source = ROOT / item['path']
    e = Experiment('I5', 'optimized-Huffman-truncated-RGB-rejection', 'rocm-GPU-negative',
                   sources=[__file__, PROFILE, BUILD, source, binary], parent=build['experiment_id'])
    write(e.path / 'backend.observed.json', capture())
    bad = e.path / 'truncated.rgb'; bad.write_bytes(source.read_bytes()[:-1])
    output = e.path / 'output.jpg'
    rc = e.command([str(binary), str(bad), str(item['width']), str(item['height']),
                    str(item['quality']), item['subsampling'], str(output)],
                   'reject-truncated-optimized-JPEG-input')
    rejected = rc != 0 and not output.exists()
    result = dict(case='truncated-RGB', status='PASSED' if rejected else 'FAILED',
                  return_code=rc, no_output=not output.exists(), input_sha256=digest(bad))
    result['evidence'] = e.finish('EXPECTED_REJECTION' if rejected else 'VALIDATOR_GAP',
                                  dict(status=result['status'], checks=[
                                      dict(check='truncated-input-rejected', passed=rejected)]))
    results.append(result)
    write(REPORT, results)
    record('I5', '优化 Huffman 截断 RGB 负例：' + result['status'] + '，必须拒绝且无输出。',
           [result['evidence']])
    return int(not rejected)


if __name__ == '__main__':
    raise SystemExit(main())
