#!/usr/bin/env python3
"""Freeze isolated GPU entropy plus optimized Huffman table stage for I5."""
import json
from experiment import ROOT, Experiment, digest, write
from image_progress import record

SOURCE = ROOT / 'migration/rewrite/image-jpeg-encoder-full-gpu-profile.json'
PROFILE = ROOT / 'migration/rewrite/image-jpeg-opt-huffman-profile.json'


def main():
    if PROFILE.exists():
        raise ValueError('optimized JPEG contract already frozen')
    base = json.loads(SOURCE.read_text())
    if base['status'] != 'FROZEN' or len(base['inputs']) != 4:
        raise ValueError('four baseline JPEG RGB cases required')
    cases = [dict(case=row['case'], path=row['path'], sha256=row['sha256'],
                  width=row['width'], height=row['height'], quality=row['quality'],
                  subsampling=row['subsampling']) for row in base['inputs']]
    if any(digest(ROOT / row['path']) != row['sha256'] for row in cases):
        raise ValueError('JPEG input changed')
    e = Experiment('I5', 'optimized-Huffman-GPU-entropy-stage-contract',
                   'CPU-contract', sources=[__file__, SOURCE, *[ROOT / c['path'] for c in cases]],
                   parent=base['evidence'].split('/')[-1])
    profile = dict(status='FROZEN', phase='I5', cases=cases,
                   gates=dict(valid_JPEG_all_four=True, independent_full_RGB_decode=True,
                              quantization_and_sampling_equal_baseline=True,
                              DHT_differs_from_standard_for_nonconstant_cases=True,
                              GPU_symbol_histogram=True, GPU_entropy_pack_stuff=True,
                              physical_GPU1_trace=True, corrupted_input_rejected=True),
                   policy='CPU may construct canonical length-limited optimized Huffman tables from GPU symbol histograms; MCU coefficients and entropy emission remain on HIP GPU.',
                   scope='Isolated optimized baseline JPEG component, not original multi-instance entrypoint qualification or progressive JPEG.')
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('PASSED', dict(status='FROZEN', checks=[
        dict(check='four-existing-input-hashes', passed=len(cases) == 4)]))
    write(PROFILE, profile)
    record('I5', '优化 Huffman GPU 熵编码阶段先冻结4组原 RGB/采样/质量及DHT、独立解码和真实GPU门槛；未改原入口资格。',
           [profile['evidence'], str(PROFILE.relative_to(ROOT))])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
