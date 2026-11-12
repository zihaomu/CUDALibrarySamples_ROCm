#!/usr/bin/env python3
"""Freeze and replay one original JP2 codeblock's real MQ segment on HIP GPU."""
import csv
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

CAPTURE = ROOT / 'migration/reports/image-j2k-real-mq-capture.json'
CONTRACT = ROOT / 'migration/rewrite/image-j2k-real-mq-profile.json'
BUILD = ROOT / 'migration/reports/image-j2k-mq-build.json'
VECTOR = ROOT / 'migration/rewrite/image-j2k-real-mq-vector.json'
REPORT = ROOT / 'migration/reports/image-j2k-real-mq-replay.json'


def main():
    captured = json.loads(CAPTURE.read_text())
    contract = json.loads(CONTRACT.read_text())
    build = json.loads(BUILD.read_text())
    if captured['status'] != 'CAPTURED' or contract['status'] != 'FROZEN' or \
            captured['original_jp2_sha256'] != contract['original_jp2_sha256'] or \
            build['status'] != 'BUILT':
        raise ValueError('real-MQ capture/build contract mismatch')
    files = {key: ROOT / captured['files'][key]['path'] for key in ('mq', 'pairs', 'meta')}
    if any(digest(path) != captured['files'][key]['sha256'] for key, path in files.items()):
        raise ValueError('real MQ captured source changed')
    pairs = files['pairs'].read_bytes()
    if len(pairs) != 2 * captured['symbols']:
        raise ValueError('real MQ capture length mismatch')
    context = files['pairs'].with_suffix('.ctx')
    expected = files['pairs'].with_suffix('.bits')
    context.write_bytes(pairs[::2]); expected.write_bytes(pairs[1::2])
    if VECTOR.exists():
        old = json.loads(VECTOR.read_text())
        if old['context_sha256'] != digest(context) or old['bits_sha256'] != digest(expected):
            raise ValueError('frozen real-MQ vector changed')
        vector = old
    else:
        e = Experiment('I6', 'original-JP2-first-real-MQ-vector-freeze', 'CPU-contract',
                       sources=[__file__, CONTRACT, CAPTURE, *files.values()],
                       parent=captured['evidence'].split('/')[-1])
        vector = dict(status='FROZEN', symbols=captured['symbols'],
                      segment_bytes=files['mq'].stat().st_size,
                      mq=str(files['mq'].relative_to(ROOT)),
                      mq_sha256=digest(files['mq']),
                      context=str(context.relative_to(ROOT)),
                      context_sha256=digest(context),
                      bits=str(expected.relative_to(ROOT)),
                      bits_sha256=digest(expected),
                      meta=str(files['meta'].relative_to(ROOT)),
                      meta_sha256=digest(files['meta']),
                      source_capture=captured['evidence'],
                      scope='Original JP2, one 64x64 MQ segment, 19 passes; context schedule from CPU OpenJPEG, not GPU EBCOT generation.')
        write(e.path / 'vector.json', vector)
        vector['evidence'] = e.finish('PASSED', dict(status='FROZEN', checks=[
            dict(check='all-contexts-in-range', passed=max(context.read_bytes()) < 19),
            dict(check='all-symbols-binary', passed=max(expected.read_bytes()) < 2),
            dict(check='source-capture-hash', passed=digest(files['mq']) == captured['files']['mq']['sha256'])]))
        write(VECTOR, vector)
        record('I6', f'原始JP2首个真实64x64码块MQ段{vector["segment_bytes"]}字节、{vector["symbols"]}个context/bit先冻结SHA；CPU上下文供重放，非GPU EBCOT。',
               [vector['evidence'], str(VECTOR.relative_to(ROOT))])

    binary = ROOT / build['binary']
    if digest(binary) != build['binary_sha256']:
        raise ValueError('HIP MQ binary changed')
    e = Experiment('I6', 'original-JP2-first-MQ-segment-HIP-full-bit-replay',
                   'rocm-GPU', sources=[__file__, VECTOR, BUILD, binary,
                                        files['mq'], context, expected],
                   parent=vector['evidence'].split('/')[-1])
    observed = capture()
    write(e.path / 'backend.observed.json', observed)
    output = e.path / 'out.bits'
    rc = e.command([str(binary), str(files['mq']), str(context), str(output)],
                   'decode-real-original-JP2-MQ-segment-on-GPU', timeout=300)
    exact = rc == 0 and output.is_file() and digest(output) == vector['bits_sha256']
    result = dict(status='PASSED' if exact else 'NUMERIC_MISMATCH',
                  symbols=vector['symbols'], segment_bytes=vector['segment_bytes'],
                  expected_sha256=vector['bits_sha256'],
                  output_sha256=digest(output) if output.is_file() else None,
                  return_code=rc)
    write(e.path / 'replay-result.json', result)
    result['evidence'] = e.finish('PASSED' if exact else 'NUMERIC_MISMATCH',
                                  dict(status=result['status'], checks=[
                                      dict(check='real-JP2-MQ-all-bits-exact', passed=exact)]))
    write(REPORT, result)
    record('I6', f'真实JP2码块 MQ HIP 重放{vector["symbols"]} bit：{result["status"]}；CPU生成context，尚非GPU整图解码。',
           [result['evidence'], str(REPORT.relative_to(ROOT))])
    print(result['status'], result['symbols'], result['evidence'])
    return int(not exact)


if __name__ == '__main__':
    raise SystemExit(main())
