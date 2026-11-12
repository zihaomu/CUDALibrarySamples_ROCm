#!/usr/bin/env python3
"""Build the frozen I5 HIP JPEG forward-transform prototype."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-jpeg-encoder-gpu-profile.json'
HEADER = ROOT / 'rocm/common/image/jpeg_encoder_gpu.hpp'
SOURCE = ROOT / 'rocm/probes/image/jpeg_encoder_gpu.hip'
REPORT = ROOT / 'migration/reports/image-jpeg-encoder-build.json'


def main():
    profile = json.loads(PROFILE.read_text())
    if profile['status'] != 'FROZEN':
        raise ValueError('frozen I5 profile required')
    core = Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay = ROOT / 'build/rocm-sdk-overlay'
    jpeg = ROOT / 'build/cpu-codecs'
    dependencies = [SOURCE, HEADER, PROFILE, jpeg / 'include/jpeglib.h',
                    jpeg / 'lib/libjpeg.so.62.4.0']
    if not all(p.is_file() for p in dependencies):
        raise ValueError('prototype build dependency missing')
    e = Experiment('I5', 'GPU-JPEG-FDCT-quantizer-build', 'rocm-build',
                   sources=[__file__, *dependencies], parent=Path(profile['evidence']).name)
    write(e.path / 'backend.observed.json', capture())
    binary = e.path / 'jpeg_encoder_gpu'
    cmd = ['hipcc', '--rocm-path=' + str(overlay), '--hip-path=' + str(overlay),
           '--rocm-device-lib-path=' + str(core / 'lib/llvm/amdgcn/bitcode'),
           '--offload-arch=gfx1201', '-std=c++17', '-O2', '-D__HIP_PLATFORM_AMD__',
           '-I' + str(jpeg / 'include'), '-I' + str(HEADER.parent), '-x', 'hip', str(SOURCE),
           '-L' + str(core / 'lib'), '-L' + str(jpeg / 'lib'),
           '-Wl,-rpath,' + str(core / 'lib'), '-Wl,-rpath,' + str(jpeg / 'lib'),
           '-lamdhip64', '-ljpeg', '-o', str(binary)]
    rc = e.command(cmd, 'build-I5-HIP-JPEG-encoder', timeout=300)
    result = dict(status='BUILT' if rc == 0 else 'BUILD_ERROR', return_code=rc,
                  experiment_id=e.id, binary=str(binary.relative_to(ROOT)) if rc == 0 else None,
                  binary_sha256=digest(binary) if rc == 0 else None,
                  dependencies={str(p.relative_to(ROOT)): digest(p) for p in dependencies})
    write(e.path / 'build.json', result)
    result['evidence'] = e.finish('EXECUTED' if rc == 0 else 'BUILD_ERROR',
        dict(status=result['status'], checks=[dict(check='HIP-source-build', passed=rc == 0)]))
    write(REPORT, result)
    record('I5', 'GPU JPEG 前向色彩/FDCT/量化原型构建：' + result['status'] +
           '；独立跨解码和 GPU trace 尚待验证。', [result['evidence']])
    print(result['status'], result['evidence'])
    return int(rc != 0)


if __name__ == '__main__':
    raise SystemExit(main())
