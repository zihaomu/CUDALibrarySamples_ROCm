#!/usr/bin/env python3
"""Pin the private OpenJPEG reference checkout before MQ/codeblock experiments."""
import json
import subprocess
from experiment import ROOT, Experiment, digest, write
from image_progress import record

CHECKOUT = ROOT / 'build/openjpeg-v2.5.4'
PROFILE = ROOT / 'migration/rewrite/image-j2k-openjpeg-reference-lock.json'
COMMIT = '6c4a29b00211eb0430fa0e5e890f1ce5c80f409f'
FILES = ['LICENSE', 'src/lib/openjp2/mqc.c', 'src/lib/openjp2/mqc.h',
         'src/lib/openjp2/mqc_inl.h', 'src/lib/openjp2/t1.c',
         'src/lib/openjp2/t1_luts.h', 'src/lib/openjp2/dwt.c']


def main():
    if PROFILE.exists():
        raise ValueError('OpenJPEG reference already pinned')
    observed = subprocess.check_output(['git', '-C', str(CHECKOUT), 'rev-parse', 'HEAD'],
                                       text=True).strip()
    if observed != COMMIT or subprocess.check_output(
            ['git', '-C', str(CHECKOUT), 'status', '--porcelain'], text=True).strip():
        raise ValueError('OpenJPEG reference revision or tree differs')
    paths = [CHECKOUT / p for p in FILES]
    if '2-clauses' not in paths[0].read_text() or not all(p.is_file() for p in paths):
        raise ValueError('OpenJPEG source/license missing')
    e = Experiment('I6', 'OpenJPEG-2.5.4-MQ-and-tier1-reference-lock',
                   'host-source-lock', sources=[__file__, *paths])
    profile = dict(status='PINNED',phase='I6',repository='https://github.com/uclouvain/openjpeg',
                   release='v2.5.4',commit=COMMIT,license='BSD-2-Clause',
                   license_sha256=digest(paths[0]),
                   files={name:digest(CHECKOUT / name) for name in FILES},
                   scope='Private independent CPU oracle and research reference only; OpenJPEG CPU decode does not qualify GPU JPEG2000 codec.')
    write(e.path / 'reference-lock.json', profile)
    profile['evidence'] = e.finish('OBSERVED', dict(status='PINNED', checks=[
        dict(check='official-release-commit-and-clean-tree', passed=True),
        dict(check='BSD-two-clause-license-identity', passed=True)]))
    write(PROFILE, profile)
    record('I6', 'OpenJPEG v2.5.4 官方参考源码固定commit '+COMMIT[:12]+'、BSD-2-Clause许可与MQ/tier1/DWT源码SHA；仅独立CPU oracle，不计GPU支持。',
           [profile['evidence']])
    print(profile['evidence'])


if __name__ == '__main__':
    main()
