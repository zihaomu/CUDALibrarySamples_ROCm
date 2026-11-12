#!/usr/bin/env python3
"""Freeze the three bundled JP2 inputs and real CUDA output identities before CPU decoding."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record

NATIVE = ROOT / 'migration/reports/image-I0-native-JPEG2000-originals.json'
PROFILE = ROOT / 'migration/rewrite/image-j2k-part1-crossdecode-profile.json'
SOURCES = ROOT / 'nvJPEG2000/nvJPEG2000-Decoder/images'


def main():
    if PROFILE.exists():
        raise ValueError('I6 JP2 crossdecode profile already frozen')
    native = json.loads(NATIVE.read_text())
    if native['status'] != 'EXECUTED':
        raise ValueError('actual native CUDA baseline required')
    raw = ROOT / 'artifacts' / Path(native['evidence']).relative_to('migration/reports/evidence')
    rows = []
    for kind, name in [('2k_image_lossless', '2k_lossless'),
                       ('2k_image_lossy', '2k_lossy'),
                       ('4k_image_lossy', '4k_lossy')]:
        source = SOURCES / kind / (name + '.jp2')
        output_rel = 'outputs/decode/' + name + '.bmp'
        cuda = raw / output_rel
        expected_sha = native['outputs'][output_rel]['sha256']
        if digest(cuda) != expected_sha:
            raise ValueError('native CUDA output identity drift')
        rows.append(dict(case=name, source=str(source.relative_to(ROOT)),
                         source_sha256=digest(source), native_output=str(cuda.relative_to(ROOT)),
                         native_output_sha256=expected_sha,
                         reversible=name.endswith('lossless')))
    e = Experiment('I6', 'three-original-JP2-native-and-CPU-crossdecode-contract',
                   'CPU-contract', sources=[__file__, NATIVE, *[ROOT/r['source'] for r in rows]])
    profile = dict(status='FROZEN', phase='I6', inputs=rows,
                   cpu_library='Pillow linked to libopenjp2 (actual loaded version recorded in run)',
                   scope='Observe independent Part 1 decoder difference against original native CUDA outputs; no AMD GPU codec inferred.',
                   gates=dict(all_three_files_decodable=True, exact_geometry=True,
                              lossless_RGB_exact_or_report_mismatch=True,
                              lossy_full_pixel_differences_reported=True))
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('OBSERVED', dict(status='FROZEN', checks=[
        dict(check='three-input-and-native-output-SHA256-pairs', passed=len(rows) == 3)]))
    write(PROFILE, profile)
    record('I6', '三张原始 JP2 和 CUDA 原入口 BMP 输出 SHA 已在 CPU OpenJPEG 跨解码前冻结；仅参考基线，AMD 完整解码尚未支持。',
           [profile['evidence']])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
