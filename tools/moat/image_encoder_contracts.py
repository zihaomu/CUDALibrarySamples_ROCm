#!/usr/bin/env python3
"""Freeze an I5 GPU JPEG forward-transform prototype contract before execution."""
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record

PROFILE = ROOT / 'migration/rewrite/image-jpeg-encoder-gpu-profile.json'
FIXTURES = ROOT / 'migration/fixtures/image-jpeg-encoder'


def pixels(width, height, variant):
    output = bytearray()
    for y in range(height):
        for x in range(width):
            if variant == 'smooth':
                output.extend(((x * 5 + y * 2) % 256,
                               (x * 2 + y * 7) % 256,
                               (x * 3 + y * 3) % 256))
            elif variant == 'checker':
                output.extend(((x // 4 % 2) * 175 + 30,
                               (y // 4 % 2) * 175 + 30,
                               ((x + y) // 4 % 2) * 175 + 30))
            else:
                output.extend((0, 0, 0))
    return bytes(output)


def main():
    if PROFILE.exists():
        raise ValueError('I5 prototype contract already frozen')
    FIXTURES.mkdir(parents=True, exist_ok=True)
    cases = [('odd-420', 33, 29, 'smooth', 75, '420'),
             ('odd-444', 13, 11, 'smooth', 90, '444'),
             ('mcu-boundary', 64, 40, 'checker', 75, '420'),
             ('tiny-444', 1, 1, 'black', 75, '444')]
    inputs = []
    for name, width, height, variant, quality, sampling in cases:
        path = FIXTURES / (name + '.rgb')
        path.write_bytes(pixels(width, height, variant))
        inputs.append(dict(case=name, path=str(path.relative_to(ROOT)), sha256=digest(path),
                           width=width, height=height, variant=variant, quality=quality,
                           subsampling=sampling))
    e = Experiment('I5', 'GPU-JPEG-forward-transform-contract', 'CPU-contract',
                   sources=[__file__, *[ROOT / x['path'] for x in inputs]])
    profile = dict(status='FROZEN', phase='I5',
        scope='GPU RGB-to-YCbCr, chroma downsample, FDCT and quantization prototype; entropy assembly remains CPU and does not qualify a sample',
        inputs=inputs,
        gates=dict(all_cases=4, actual_GPU_trace_required=True, independently_decodable=True,
                   dimensions_exact=True, subsampling_exact=True, quantization_tables_exact=True,
                   decoded_psnr_vs_source_min_db={'smooth': 26.0, 'checker': 12.0, 'black': 60.0},
                   malformed_input_rejected=True),
        limitations='No GPU entropy/Huffman, metadata/progressive re-encoding, multi-instance scheduling or source-sample integration yet.')
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('OBSERVED', dict(status='FROZEN', checks=[
        dict(check='four-predeclared-inputs-and-gates', passed=True)]))
    write(PROFILE, profile)
    record('I5', 'GPU JPEG encoder 四组输入、420/444、奇数/MCU边界、质量与独立跨解码门槛已先冻结；'
           '当前仅计划 FDCT/量化 GPU 原型，CPU entropy 不计整例支持。', [profile['evidence']], state='IN_PROGRESS')
    print(profile['evidence'])


if __name__ == '__main__':
    main()
