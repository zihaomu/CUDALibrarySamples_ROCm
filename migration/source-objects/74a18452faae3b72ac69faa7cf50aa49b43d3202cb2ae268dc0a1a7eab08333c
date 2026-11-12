#!/usr/bin/env python3
"""Freeze I4 progressive JPEG GPU pixel-synthesis prototype inputs and gates."""
import json

from experiment import ROOT, Experiment, digest, write
from image_progress import record

INPUTS = ROOT / 'nvJPEG/nvJPEG-Decoder/input_images'
FILES = ('cat.jpg', 'img9.jpg')
PROFILE = ROOT / 'migration/rewrite/image-progressive-gpu-profile.json'


def main():
    if PROFILE.exists():
        raise ValueError('progressive prototype contract already frozen')
    paths = [INPUTS / name for name in FILES]
    e = Experiment('I4', 'two-original-progressive-JPEG-bitstreams',
                   'CPU-contract', sources=[__file__, *paths,
                   ROOT / 'rocm/ported/nvJPEG/nvJPEG-Decoder/nvjpegDecoder.cpp'])
    profile = dict(status='FROZEN', phase='I4', scope='Experimental GPU pixel synthesis; no sample qualification',
        inputs=[dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size,
                     sha256=digest(p)) for p in paths],
        algorithm='libjpeg-turbo progressive entropy and coefficient assembly on CPU; project HIP dequantization, 8x8 IDCT, chroma sampling and RGB conversion on AMD GPU',
        reference='separate libjpeg-turbo RGB decompression with do_fancy_upsampling=FALSE and JDCT_ISLOW',
        gates=dict(all_original_progressive_inputs=2, GPU_kernel_trace_required=True,
                   GPU_pixel_synthesis_required=True, CPU_pixel_fallback_forbidden=True,
                   output_bytes_exact_dimensions=True, max_abs_per_channel=4,
                   min_rgb_psnr_db=50.0, abnormal_or_empty_output_rejected=True),
        limitations='Entropy remains on CPU as in hybrid JPEG pipelines; this profile alone does not close native backend, ROI, multi-instance or sample CLI contracts.')
    write(e.path / 'profile.json', profile)
    profile['evidence'] = e.finish('OBSERVED', dict(status='FROZEN',
        checks=[dict(check='two-original-SOF2-progressive-inputs-hash-frozen', passed=True)]))
    write(PROFILE, profile)
    record('I4', '两张原始 SOF2 progressive JPEG 输入与 GPU IDCT/色彩路径固定；'
           '独立 libjpeg-turbo 非平滑 RGB 参考门槛 maxAbs≤4、PSNR≥50 dB，'
           'CPU 熵解码可用但 CPU 像素回退不计 GPU 支持。', [profile['evidence']])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
