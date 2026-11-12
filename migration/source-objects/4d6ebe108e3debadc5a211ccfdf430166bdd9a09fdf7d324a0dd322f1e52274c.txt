#!/usr/bin/env python3
"""Build isolated optimized-Huffman full-GPU entropy JPEG prototype."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

PROFILE = ROOT / 'migration/rewrite/image-jpeg-opt-huffman-profile.json'
REPORT = ROOT / 'migration/reports/image-jpeg-opt-huffman-build.json'


def main():
    profile = json.loads(PROFILE.read_text())
    if profile['status'] != 'FROZEN':
        raise ValueError('optimized-Huffman contract required')
    core = Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay = ROOT / 'build/rocm-sdk-overlay'
    jpeg = ROOT / 'build/cpu-codecs'
    headers = [ROOT / 'rocm/common/image' / name for name in
               ('jpeg_opt_full_gpu.hpp', 'jpeg_optimal_huffman.hpp',
                'jpeg_full_gpu.hpp', 'jpeg_entropy_gpu.hpp', 'jpeg_encoder_gpu.hpp')]
    source = ROOT / 'rocm/probes/image/jpeg_opt_full_gpu.hip'
    deps = [source, *headers, PROFILE, jpeg / 'include/jpeglib.h',
            jpeg / 'lib/libjpeg.so.62.4.0']
    e = Experiment('I5', 'GPU-optimized-Huffman-JPEG-build', 'rocm-build',
                   sources=[__file__, *deps], parent=profile['evidence'].split('/')[-1])
    write(e.path / 'backend.observed.json', capture())
    binary = e.path / 'probe'
    command = ['hipcc', '--rocm-path=' + str(overlay), '--hip-path=' + str(overlay),
               '--rocm-device-lib-path=' + str(core / 'lib/llvm/amdgcn/bitcode'),
               '--offload-arch=gfx1201', '-std=c++17', '-O2', '-D__HIP_PLATFORM_AMD__',
               '-I' + str(jpeg / 'include'), '-I' + str(headers[0].parent),
               '-x', 'hip', str(source), '-o', str(binary),
               '-L' + str(core / 'lib'), '-L' + str(jpeg / 'lib'),
               '-Wl,-rpath,' + str(core / 'lib'), '-Wl,-rpath,' + str(jpeg / 'lib'),
               '-lamdhip64', '-ljpeg']
    rc = e.command(command, 'compile-optimized-Huffman-GPU-JPEG', timeout=300)
    result = dict(status='BUILT' if rc == 0 else 'BUILD_ERROR', return_code=rc,
                  binary=str(binary.relative_to(ROOT)) if rc == 0 else None,
                  binary_sha256=digest(binary) if rc == 0 else None,
                  dependencies={str(p.relative_to(ROOT)): digest(p) for p in deps},
                  experiment_id=e.id)
    write(e.path / 'build.json', result)
    result['evidence'] = e.finish('EXECUTED' if rc == 0 else 'BUILD_ERROR',
                                  dict(status=result['status'], checks=[
                                      dict(check='HIP-optimized-Huffman-build', passed=rc == 0)]))
    write(REPORT, result)
    record('I5', '优化 Huffman GPU 直方图与 GPU 熵编码孤立原型编译：' + result['status'] +
           '；尚未进入原始多实例入口。', [result['evidence']])
    print(result['status'], result['evidence'])
    return int(rc != 0)


if __name__ == '__main__':
    raise SystemExit(main())
