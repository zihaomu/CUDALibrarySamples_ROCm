#!/usr/bin/env python3
"""Freeze original multi-instance encoder BMP/CLI execution cases before rewriting."""
from pathlib import Path
from PIL import Image
from experiment import ROOT, Experiment, digest, write
from image_progress import record

PROFILE = ROOT / 'migration/rewrite/image-jpeg-encoder-instances-profile.json'
FIXTURES = ROOT / 'migration/fixtures/image-jpeg-encoder-instances'


def main():
    if PROFILE.exists():
        raise ValueError('multi-instance encoder contract already frozen')
    FIXTURES.mkdir(parents=True, exist_ok=True)
    specs = [('img1.bmp', 17, 19, 1), ('img2.bmp', 32, 24, 2),
             ('img10.bmp', 63, 47, 3)]
    rows = []
    for name, width, height, seed in specs:
        data = bytes((x * (7 + seed) + y * (3 + seed) + c * 67) % 256
                     for y in range(height) for x in range(width) for c in range(3))
        path = FIXTURES / name
        Image.frombytes('RGB', (width, height), data).save(path, format='BMP')
        rows.append(dict(path=str(path.relative_to(ROOT)), sha256=digest(path),
                         width=width, height=height, source_rgb_sha256=__import__('hashlib').sha256(data).hexdigest()))
    e = Experiment('I5', 'original-multiple-instance-encoder-BMP-contract',
                   'CPU-contract', sources=[__file__,
                     ROOT / 'nvJPEG/nvJPEG-Encoder-MultipleInstances/nvJPEGEncMultipleInstances.cpp',
                     *[ROOT / x['path'] for x in rows]])
    profile = dict(status='FROZEN', phase='I5', inputs=rows,
        required_cases=['recursive-BMP-natural-order-3-images',
                        'repeat-n-7-two-threads-two-states-unique-outputs',
                        'quality-75-420-and-quality-90-444',
                        'optimized-Huffman-flag', 'hardware-backend-explicit-unavailable',
                        'missing-dir-and-invalid-CLI-rejection',
                        'real-multiple-HIP-streams-and-changed-input-replay'],
        gates=dict(independent_decode_all_outputs=True, output_name_ids_exact=True,
                   quantization_quality_and_sampling_exact=True,
                   multiple_stream_ids_required=True, changed_input_changes_output=True,
                   cpu_entropy_explicitly_reported=True),
        limitation='CPU Huffman entropy and header assembly remain partial; no AMD hardware JPEG encoder capability is claimed.')
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('OBSERVED', dict(status='FROZEN', checks=[
        dict(check='three-source-BMP-hashes-and-seven-contract-cases-frozen', passed=True)]))
    write(PROFILE, profile)
    record('I5', '原始 nvJPEG 多实例编码器三张 BMP、自然排序、n=7 重复、两线程/状态、'
           'Q75/90、420/444、优化 Huffman、硬件拒绝、真实多stream与改输入重放合同先冻结。',
           [profile['evidence']])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
