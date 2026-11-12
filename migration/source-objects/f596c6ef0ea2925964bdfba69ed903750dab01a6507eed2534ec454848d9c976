#!/usr/bin/env python3
"""Build the pinned private OpenJPEG static reference library for MQ experiments."""
import json
import subprocess
from experiment import ROOT, Experiment, digest, write
from image_progress import record

PROFILE = ROOT / 'migration/rewrite/image-j2k-openjpeg-reference-lock.json'
SOURCE = ROOT / 'build/openjpeg-v2.5.4'
OUTPUT = ROOT / 'build/openjpeg-v2.5.4-static'
REPORT = ROOT / 'migration/reports/image-j2k-openjpeg-build.json'


def main():
    profile = json.loads(PROFILE.read_text())
    actual = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    if profile['status'] != 'PINNED' or actual != profile['commit'] or any(
            digest(SOURCE / n) != sha for n, sha in profile['files'].items()):
        raise ValueError('pinned OpenJPEG reference changed')
    e = Experiment('I6', 'pinned-OpenJPEG-static-MQ-CPU-oracle-build', 'host-build',
                   sources=[__file__, PROFILE, SOURCE / 'LICENSE',
                            SOURCE / 'src/lib/openjp2/mqc.c',
                            SOURCE / 'src/lib/openjp2/mqc.h'],
                   parent=profile['evidence'].split('/')[-1])
    rc = e.command(['cmake', '-S', str(SOURCE), '-B', str(OUTPUT),
                    '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=OFF',
                    '-DBUILD_CODEC=OFF', '-DBUILD_TESTING=OFF'],
                   'configure-private-OpenJPEG-static', timeout=300)
    if rc == 0:
        rc = e.command(['cmake', '--build', str(OUTPUT), '--parallel', '4'],
                       'build-private-OpenJPEG-static', timeout=300)
    libraries = list(OUTPUT.rglob('libopenjp2.a'))
    status = 'BUILT' if rc == 0 and len(libraries) == 1 else 'BUILD_ERROR'
    result = dict(status=status, return_code=rc,
                  library=str(libraries[0].relative_to(ROOT)) if len(libraries) == 1 else None,
                  library_sha256=digest(libraries[0]) if len(libraries) == 1 else None,
                  source_commit=profile['commit'], experiment_id=e.id)
    write(e.path / 'build.json', result)
    result['evidence'] = e.finish('EXECUTED' if status == 'BUILT' else 'BUILD_ERROR',
                                  dict(status=status, checks=[
                                      dict(check='pinned-CPU-reference-build', passed=status == 'BUILT')]))
    write(REPORT, result)
    record('I6', '固定 OpenJPEG 2.5.4 CPU 静态参考库构建：'+status+'；作为MQ独立oracle，不计GPU codec。',
           [result['evidence']])
    print(status, result['evidence'])
    return int(status != 'BUILT')


if __name__ == '__main__':
    raise SystemExit(main())
