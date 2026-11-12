#!/usr/bin/env python3
"""Build the HIP MQ arithmetic decoder against the frozen OpenJPEG vectors."""
import json
from pathlib import Path
from experiment import ROOT, Experiment, digest, write
from image_progress import record
from snapshot import capture

SOURCE = ROOT / 'rocm/probes/image/jpeg2000_mq_decode.hip'
HEADER = ROOT / 'rocm/backends/codec/jpeg2000/mq_decode.hpp'
STATES = ROOT / 'rocm/backends/codec/jpeg2000/mq_states.hpp'
LICENSE = ROOT / 'rocm/backends/codec/jpeg2000/OPENJPEG-LICENSE'
PROFILE = ROOT / 'migration/rewrite/image-j2k-mq-profile.json'
REPORT = ROOT / 'migration/reports/image-j2k-mq-build.json'


def main():
    profile = json.loads(PROFILE.read_text())
    if profile['status'] != 'FROZEN':
        raise ValueError('MQ test vectors not frozen')
    core = Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay = ROOT / 'build/rocm-sdk-overlay'
    deps = [SOURCE, HEADER, STATES, LICENSE, PROFILE]
    e = Experiment('I6', 'JPEG2000-HIP-MQ-arithmetic-decoder-build', 'rocm-build',
                   sources=[__file__, *deps], parent=profile['evidence'].split('/')[-1])
    write(e.path / 'backend.observed.json', capture())
    binary = e.path / 'probe'
    command = ['hipcc', '--rocm-path=' + str(overlay), '--hip-path=' + str(overlay),
               '--rocm-device-lib-path=' + str(core / 'lib/llvm/amdgcn/bitcode'),
               '--offload-arch=gfx1201', '-std=c++17', '-O2', '-D__HIP_PLATFORM_AMD__',
               '-x', 'hip', str(SOURCE), '-o', str(binary),
               '-I' + str(core / 'include'), '-L' + str(core / 'lib'),
               '-Wl,-rpath,' + str(core / 'lib'), '-lamdhip64']
    rc = e.command(command, 'build-HIP-MQ-decoder', timeout=300)
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
    record('I6', 'JPEG2000 孤立 MQ 算术解码 HIP 编译：' + result['status'] +
           '；尚未接入真实 JP2 码块。', [result['evidence']])
    print(result['status'], result['evidence'])
    return int(rc != 0)


if __name__ == '__main__':
    raise SystemExit(main())
