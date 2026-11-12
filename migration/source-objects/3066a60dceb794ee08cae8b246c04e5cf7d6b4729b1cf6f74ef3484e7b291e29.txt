#!/usr/bin/env python3
"""Freeze independent one-level JPEG2000 reversible 5/3 + RCT component data."""
import json
import struct
from PIL import Image
from experiment import ROOT, Experiment, digest, write
from image_progress import record

SOURCE = ROOT / 'nvJPEG2000/nvJPEG2000-Encoder/images/TestImage640x480.bmp'
FIXTURES = ROOT / 'migration/fixtures/image-j2k-i53-rct'
PROFILE = ROOT / 'migration/rewrite/image-j2k-i53-rct-profile.json'
CASES = [('singleton', 1, 1), ('odd-small', 13, 11),
         ('even-grid', 16, 16), ('tile-edge', 17, 19), ('odd-wide', 33, 29)]


def forward_line(values):
    low = list(values[::2]); high = list(values[1::2])
    if not high:
        return low
    high = [v - (low[i] + low[min(i + 1, len(low) - 1)]) // 2
            for i, v in enumerate(high)]
    low = [v + ((high[max(i - 1, 0)] + high[min(i, len(high) - 1)] + 2) // 4)
           for i, v in enumerate(low)]
    return low + high


def forward_plane(plane, width, height):
    horizontal = [forward_line(plane[y * width:(y + 1) * width])
                  for y in range(height)]
    columns = [forward_line([horizontal[y][x] for y in range(height)])
               for x in range(width)]
    return [columns[x][y] for y in range(height) for x in range(width)]


def inverse_line(values):
    n = len(values); low_count = (n + 1) // 2
    low = list(values[:low_count]); high = list(values[low_count:])
    if not high:
        return low
    low = [v - ((high[max(i - 1, 0)] + high[min(i, len(high) - 1)] + 2) // 4)
           for i, v in enumerate(low)]
    high = [v + (low[i] + low[min(i + 1, len(low) - 1)]) // 2
            for i, v in enumerate(high)]
    return [low[i // 2] if i % 2 == 0 else high[i // 2] for i in range(n)]


def inverse_plane(coefficients, width, height):
    cols = [inverse_line([coefficients[y * width + x] for y in range(height)])
            for x in range(width)]
    rows = [[cols[x][y] for x in range(width)] for y in range(height)]
    return [v for row in rows for v in inverse_line(row)]


def main():
    if PROFILE.exists():
        raise ValueError('I6 transform contract already frozen')
    source_sha = digest(SOURCE)
    image = Image.open(SOURCE).convert('RGB')
    if image.size[0] < 33 or image.size[1] < 29:
        raise ValueError('original BMP too small')
    e = Experiment('I6', 'JPEG2000-reversible-5-3-RCT-first-GPU-stage-contract',
                   'CPU-contract', sources=[__file__, SOURCE])
    fixtures = []
    for name, width, height in CASES:
        rgb = image.crop((0, 0, width, height)).tobytes()
        pixels = [rgb[i:i + 3] for i in range(0, len(rgb), 3)]
        y = [(int(r) + 2 * int(g) + int(b)) // 4 for r, g, b in pixels]
        cb = [int(b) - int(g) for r, g, b in pixels]
        cr = [int(r) - int(g) for r, g, b in pixels]
        coefficients = sum((forward_plane(p, width, height) for p in (y, cb, cr)), [])
        reconstructed = [inverse_plane(coefficients[c * width * height:(c + 1) * width * height],
                                       width, height) for c in range(3)]
        out = bytearray()
        for yy, cc, rr in zip(*reconstructed):
            g = yy - (cc + rr) // 4
            out.extend((rr + g, g, cc + g))
        if bytes(out) != rgb:
            raise ValueError('independent 5/3 and RCT roundtrip failed: ' + name)
        folder = FIXTURES / name; folder.mkdir(parents=True, exist_ok=True)
        coeff = folder / 'coefficients.i32'; expected = folder / 'expected.rgb'
        coeff.write_bytes(struct.pack('<' + str(len(coefficients)) + 'i', *coefficients))
        expected.write_bytes(rgb)
        fixtures.append(dict(case=name, width=width, height=height, components=3,
                             coefficients=str(coeff.relative_to(ROOT)),
                             coefficients_sha256=digest(coeff),
                             expected_rgb=str(expected.relative_to(ROOT)),
                             expected_rgb_sha256=digest(expected),
                             coefficient_min=min(coefficients), coefficient_max=max(coefficients)))
    profile = dict(status='FROZEN', phase='I6', source=str(SOURCE.relative_to(ROOT)),
                   source_sha256=source_sha, fixtures=fixtures,
                   representation='one-level planar LL/HL/LH/HH packed rows, signed int32; Y/Cb/Cr reversible color transform',
                   gates=dict(exact_all_RGB_bytes=True, actual_HIP_GPU_kernels=True,
                              physical_GPU1=True, changed_coefficient_replay=True,
                              negative_dimensions_and_truncated_payload=True),
                   scope='Isolated transform stage only. No JP2/J2K parser, MQ/EBCOT, packet or original entrypoint support is inferred.',
                   references=['https://www.itu.int/rec/T-REC-T.800-202407-I/en',
                               'https://github.com/uclouvain/openjpeg/blob/master/src/lib/openjp2/dwt.c'])
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('OBSERVED', dict(status='FROZEN', checks=[
        dict(check='five-prior-input-coefficient-and-RGB-hashes', passed=len(fixtures) == 5)]))
    write(PROFILE, profile)
    record('I6', 'JPEG2000 可逆 5/3+RCT 纵向 GPU 阶段先冻结5组原图裁剪、系数和精确 RGB oracle；仅变换组件，不宣称完整码流/整例。',
           [profile['evidence']])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
