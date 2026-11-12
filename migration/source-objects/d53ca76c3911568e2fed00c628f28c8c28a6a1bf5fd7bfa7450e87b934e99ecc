#!/usr/bin/env python3
"""Replay the complete Flood Fill entry from a fixed clean Git checkout."""
import json
import os
import shutil
import tempfile
from pathlib import Path

from experiment import ROOT, Experiment, write, digest, git
from image_flood_build import dependencies
from image_progress import record

GROUPS = [
    'contracts', 'original-contracts', 'runtime-contracts', 'cli-contracts',
    'build', 'all', 'frontend-build', 'originals', 'runtime', 'cli', 'trace',
    'all-validation', 'originals-validation', 'runtime-validation',
    'cli-validation', 'trace-validation',
]

def main():
    commit = git('rev-parse', 'HEAD').strip()
    sources = [__file__, *dependencies(), ROOT/'tools/migration/bootstrap_sdk.py',
               *sorted((ROOT/'tools/moat').glob('image_flood_*.py')),
               *sorted((ROOT/'migration/rewrite').glob('image-flood-*.json'))]
    e = Experiment('I3', 'FloodFill-clean-checkout-complete-RGB-runtime-CLI-trace',
                   'host-cold-replay', sources=sources)
    clone = Path(tempfile.mkdtemp(prefix='image-flood-cold-', dir=ROOT.parent))/'src'
    children, checks = [], []
    rc = e.command(['git', 'clone', '--shared', '--quiet', str(ROOT), str(clone)],
                   'fresh-fixed-checkout', timeout=300)
    try:
        if not rc:
            rc = e.command(['git', 'checkout', '--quiet', commit], 'fixed-commit', cwd=clone)
        checks.append(dict(check='no-preexisting-build-or-library-cache',
                           passed=not (clone/'build').exists()))
        cpu = str(ROOT/'build/image-cpu-venv/bin/python')
        contracts = ['image_flood_contracts.py', 'image_flood_original_contracts.py',
                     'image_flood_runtime_contracts.py']
        for name in contracts:
            if rc:
                break
            rc = e.command([cpu, str(clone/'tools/moat'/name)], 'freeze-'+name,
                           cwd=clone, timeout=400)
        if not rc:
            rc = e.command([cpu, str(clone/'tools/moat/image_flood_cli.py'), '--freeze'],
                           'freeze-full-CLI', cwd=clone, timeout=400)
        frozen = ['image-flood-profile.json', 'image-flood-original-contract.json',
                  'image-flood-runtime-contract.json', 'image-flood-cli-contract.json']
        checks.append(dict(check='same-four-fixed-profiles-and-input-identities',
                           passed=not rc and all(digest(clone/'migration/rewrite'/name) ==
                                                 digest(ROOT/'migration/rewrite'/name)
                                                 for name in frozen)))
        jobs = ['tools/migration/bootstrap_sdk.py', 'tools/moat/image_flood_build.py',
                'tools/moat/image_flood_run.py', 'tools/moat/image_flood_frontend_build.py',
                'tools/moat/image_flood_originals.py', 'tools/moat/image_flood_runtime.py',
                'tools/moat/image_flood_cli.py', 'tools/moat/image_flood_trace.py']
        for name in jobs:
            if rc:
                break
            both = name.endswith('image_flood_runtime.py')
            env = dict(os.environ, HIP_VISIBLE_DEVICES='0,2' if both else '2')
            mask = ['ROCR_VISIBLE_DEVICES=2,3', 'HIP_VISIBLE_DEVICES=0,1'] if both else [
                'ROCR_VISIBLE_DEVICES=3', 'HIP_VISIBLE_DEVICES=0']
            rc = e.command(['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh',
                            'env', *mask, 'python3', str(clone/name)],
                           'fresh-'+Path(name).stem, cwd=clone, env=env, timeout=1200)
        checks.append(dict(check='fresh-backend-29-inputs-four-workflows-72-runtime-18-CLI-and-trace',
                           passed=rc == 0))
        validators = [
            ('all', 'image_flood_reference.py'),
            ('originals', 'image_flood_original_reference.py'),
            ('runtime', 'image_flood_runtime_reference.py'),
            ('cli', 'image_flood_cli.py'),
            ('trace', 'image_flood_trace.py'),
        ]
        for key, script in validators:
            if rc:
                break
            argv = [cpu, str(clone/'tools/moat'/script)]
            if key in {'cli', 'trace'}:
                argv.append('--check')
            rc = e.command(argv, 'independent-CPU-'+key, cwd=clone, timeout=1200)
        checks.append(dict(check='independent-all-pixels-all-original-files-runtime-CLI-and-trace',
                           passed=rc == 0))
        for name in GROUPS:
            p = clone/'migration/reports'/('image-flood-'+name+'.json')
            if not p.exists():
                continue
            v = json.loads(p.read_text())
            rows = v if isinstance(v, list) else [v]
            for index, row in enumerate(rows):
                if 'evidence' not in row:
                    continue
                meta = json.loads((clone/row['evidence']/'manifest.json').read_text())
                raw = clone/meta['raw_artifact_dir']
                if not raw.is_dir() or not (raw/'sealed.json').is_file():
                    raise ValueError('complete sealed child archive')
                dest = e.path/'child-evidence'/name/str(index)
                shutil.copytree(raw, dest)
                (dest/'sealed.json').rename(dest/'child-seal.json')
                source = json.loads((dest/'source.json').read_text())
                for object_name in source['source_objects'].values():
                    src, dst = clone/object_name, ROOT/object_name
                    if dst.exists():
                        if digest(src) != digest(dst):
                            raise ValueError('source object collision')
                    else:
                        shutil.copyfile(src, dst)
                children.append(dict(name=name, index=index,
                                     relative=str(dest.relative_to(e.path)), report=row))
        checks.append(dict(check='all-thirty-six-sealed-child-records',
                           passed=len(children) == 36))
        builds = [c['report'] for c in children if c['name']=='build']
        checks.append(dict(check='same-current-HIP-dependencies-and-ABI',
                           passed=len(builds)==1 and builds[0]['abi_version']==1 and
                           builds[0]['dependencies']=={
                               str(p.relative_to(ROOT)): digest(p) for p in dependencies()}))
    except Exception as error:
        checks.append(dict(check='cold-replay-finished-with-complete-evidence',
                           passed=False, error=repr(error)))
        rc = rc or 1
    checks.append(dict(check='final-return-code', passed=rc == 0))
    status = 'PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    v = dict(status=status, return_code=rc, source_commit=commit,
             clone=str(clone), checks=checks, children=children)
    write(e.path/'cold.json', v)
    v['evidence'] = e.finish('PASSED' if status=='PASSED' else 'SELF_TEST_FAILED',
                             dict(status=status, checks=checks))
    write(ROOT/'migration/reports/image-flood-cold.json', v)
    record('I3', 'flood固定Git检出重建四合同、HIP/C++、29完整RGB、四原例、72运行、18CLI、GPU trace及五CPU验收与36封存子记录：'+status,
           [v['evidence']])
    print(status, v['evidence'])
    return int(status != 'PASSED')

if __name__=='__main__':
    raise SystemExit(main())
