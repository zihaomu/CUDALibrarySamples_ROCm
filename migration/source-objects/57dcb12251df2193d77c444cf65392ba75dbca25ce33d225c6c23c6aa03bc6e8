#!/usr/bin/env python3
"""Build the frozen isolated HIP inverse 5/3 and RCT component probe."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

SOURCE = ROOT / 'rocm/probes/image/jpeg2000_reversible53.hip'
HEADER = ROOT / 'rocm/backends/codec/jpeg2000/reversible53.hpp'
PROFILE = ROOT / 'migration/rewrite/image-j2k-i53-rct-profile.json'
REPORT = ROOT / 'migration/reports/image-j2k-i53-build.json'


def main():
    profile = json.loads(PROFILE.read_text())
    if profile['status'] != 'FROZEN':
        raise ValueError('I6 transform contract must be frozen')
    core = Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay = ROOT / 'build/rocm-sdk-overlay'
    deps = [SOURCE, HEADER, PROFILE]
    e = Experiment('I6', 'JPEG2000-GPU-inverse-5-3-RCT-component-build', 'rocm-build',
                   sources=[__file__, *deps], parent=profile['evidence'].split('/')[-1])
    write(e.path / 'backend.observed.json', capture())
    binary = e.path / 'probe'
    command = ['hipcc', '--rocm-path=' + str(overlay), '--hip-path=' + str(overlay),
               '--rocm-device-lib-path=' + str(core / 'lib/llvm/amdgcn/bitcode'),
               '--offload-arch=gfx1201', '-std=c++17', '-O2', '-D__HIP_PLATFORM_AMD__',
               '-x', 'hip', str(SOURCE), '-o', str(binary),
               '-I' + str(core / 'include'), '-L' + str(core / 'lib'),
               '-Wl,-rpath,' + str(core / 'lib'), '-lamdhip64']
    rc = e.command(command, 'build-GPU-inverse-53-RCT', timeout=300)
    result = dict(status='BUILT' if rc == 0 else 'BUILD_ERROR', return_code=rc,
                  binary=str(binary.relative_to(ROOT)) if rc == 0 else None,
                  binary_sha256=digest(binary) if rc == 0 else None,
                  dependencies={str(p.relative_to(ROOT)): digest(p) for p in deps},
                  experiment_id=e.id)
    write(e.path / 'build.json', result)
    result['evidence'] = e.finish('EXECUTED' if rc == 0 else 'BUILD_ERROR',
                                  dict(status=result['status'], checks=[
                                      dict(check='actual-HIP-build', passed=rc == 0)]))
    write(REPORT, result)
    record('I6', 'JPEG2000 独立 GPU inverse 5/3+RCT 构建：' + result['status'] +
           '；仍未包含 JP2/J2K packet/MQ/原入口。', [result['evidence']])
    print(result['status'], result['evidence'])
    return int(rc != 0)


if __name__ == '__main__':
    raise SystemExit(main())
