#!/usr/bin/env python3
"""Qualify Flood Fill from sealed evidence."""
import argparse, json, subprocess
from experiment import ROOT, Experiment, write, digest
from qualify_canny_plus import sealed, reviewed
from image_flood_build import dependencies
from image_flood_inputs import load_case
import image_flood_reference as core
import image_flood_original_reference as originals
import image_flood_runtime_reference as runtime
import image_flood_cli as cli
import image_flood_trace as trace
import image_flood_native_reference as native

SAMPLE = 'NPP+/floodFill::floodFillVariousRegionTypesNPPPlus.cpp'
IMPLEMENTATION = 'rocm/ported/NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp'
COMPARISON = 'ALGORITHM_VARIANT_EXACT_PROJECT_FIXED_SEED_8_CONNECTED'
IMAGE = 'sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03'

def load(name):
    return json.loads((ROOT/f'migration/reports/image-flood-{name}.json').read_text())

def native_run():
    return next(r for r in json.loads((ROOT/'migration/reports/image-I3-native-originals.json').read_text())
                if r['source'] == 'NPP+/floodFill/floodFillVariousRegionTypesNPPPlus.cpp')

def collect(review=None):
    spec = json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text())
    build, frontend = load('build'), load('frontend-build')
    refs, sources, checks = set(), {str(p.relative_to(ROOT)) for p in dependencies()}, []
    def gate(name, fn):
        try:
            ok = bool(fn())
        except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration,
                AssertionError, subprocess.CalledProcessError):
            ok = False
        checks.append(dict(check=name, passed=ok))
        return ok
    def report(r, member, backend=None):
        refs.add(r['evidence'])
        directory, manifest, source = sealed(r['evidence'])
        sources.update(source['dependencies'])
        return ((backend is None or manifest['backend'] == backend)
                and manifest['experiment_id'] == r.get('experiment_id', manifest['experiment_id'])
                and json.loads((directory/member).read_text()) ==
                {k:v for k,v in r.items() if k != 'evidence'})
    def observed(r, physical={1}):
        o = json.loads((ROOT/r['evidence']/'backend.observed.json').read_text())
        return (o['image_id'] == IMAGE and o['rocm_release'] == '10.1.0'
                and {d['physical_id'] for d in o['devices']} == physical)
    def commands(r):
        return json.loads((ROOT/r['evidence']/'commands.json').read_text())

    def frozen():
        profiles = [('contracts','image-flood-profile.json',29),
                    ('original-contracts','image-flood-original-contract.json',4),
                    ('runtime-contracts','image-flood-runtime-contract.json',72),
                    ('cli-contracts','image-flood-cli-contract.json',18)]
        for name, filename, count in profiles:
            r = load(name)
            directory, _, _ = sealed(r['evidence'])
            profile = json.loads((ROOT/'migration/rewrite'/filename).read_text())
            if (not report(r,'contracts.json','CPU-contract') or r['status']!='FROZEN'
                or profile['status']!='FROZEN'
                or json.loads((directory/'profile.json').read_text())!=profile
                or r.get('case_count', r.get('workflows'))!=count):
                return False
        return (spec['sample_id']==SAMPLE and spec['case_count']==len(spec['cases'])==29
                and len({c['case'] for c in spec['cases']})==29
                and len(spec['original_case_ids'])==spec['original_product_count']==5
                and digest(ROOT/spec['original_source'])==spec['original_source_sha256'])
    gate('four-frozen-input-workflow-runtime-CLI-contracts', frozen)
    def fixtures():
        for c in spec['cases']:
            load_case(c)
            if c['original'] and digest(ROOT/c['original']['source'])!=c['original']['sha256']:
                return False
        original = json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text())
        return (len(original['workflows'])==4 and original['required_output_count']==5
                and all((ROOT/c['path']).stat().st_size==c['bytes']
                        and digest(ROOT/c['path'])==c['sha256']
                        for rows in original['datasets'].values() for c in rows))
    gate('all-frozen-full-RGB-fixture-and-source-image-bytes', fixtures)
    def builds():
        deps = {str(p.relative_to(ROOT)):digest(p) for p in dependencies()}
        full = dict(deps, **{n:digest(ROOT/n) for n in
                              [IMPLEMENTATION,'rocm/common/image/flood_sample.hpp']})
        return (report(build,'build.json','rocm-build') and observed(build)
                and build['status']=='BUILT' and build['abi_version']==1
                and build['dependencies']==deps
                and build['build_recipe_sha256']==digest(ROOT/'tools/moat/image_flood_build.py')
                and digest(ROOT/build['library'])==build['library_sha256']
                and len(commands(build))==1 and commands(build)[0]['return_code']==0
                and report(frontend,'build.json','rocm-build') and observed(frontend)
                and frontend['status']=='BUILT' and frontend['backend']==build
                and frontend['implementation']==IMPLEMENTATION and frontend['dependencies']==full
                and frontend['build_recipe_sha256']==digest(ROOT/'tools/moat/image_flood_frontend_build.py')
                and digest(ROOT/frontend['binary'])==frontend['binary_sha256']
                and len(commands(frontend))==1 and commands(frontend)[0]['return_code']==0)
    gate('current-GPU-ABI-and-complete-C++-build', builds)
    def gpu(name, backend, worker, physical):
        r = load(name)
        cs = commands(r)
        return (report(r,'run.json',backend) and observed(r,physical)
                and r['return_code']==0 and r['build']==build and len(cs)==1
                and cs[0]['return_code']==0
                and str(ROOT/'tools/moat'/worker) in cs[0]['argv']
                and str(ROOT/build['library']) in cs[0]['argv']
                and build['library_sha256'] in cs[0]['argv']
                and cs[0]['argv'][cs[0]['argv'].index('--output')+1]==str(ROOT/r['outputs']))
    for name, backend, worker, physical in [
        ('all','rocm-prototype','image_flood_worker.py',{1}),
        ('runtime','rocm-runtime','image_flood_runtime.py',{0,1}),
        ('trace','rocm-trace','image_flood_worker.py',{1}),
    ]:
        gate(name+'/actual-current-GPU-process',
             lambda name=name,backend=backend,worker=worker,physical=physical:
             gpu(name,backend,worker,physical))
    validators = [
        ('all',lambda:core.validate(load('all')),29),
        ('originals',lambda:originals.validate(load('originals')),4),
        ('runtime',lambda:runtime.validate(load('runtime')),72),
        ('cli',lambda:cli.validate(load('cli')),18),
        ('trace',lambda:trace.validate(load('trace')),30),
        ('native',lambda:native.validate(native_run()),5),
    ]
    for name, fn, count in validators:
        def cpu(name=name,fn=fn,count=count):
            r = load(name+'-validation')
            actual = fn()
            if isinstance(actual,list):
                rows = actual
                actual = dict(status='PASSED' if all(x['status']=='PASSED' for x in rows)
                              else 'FAILED',case_count=len(rows),results=rows)
                if name=='originals':
                    actual['file_count']=sum(x['file_count'] for x in rows)
            return (report(r,'results.json','CPU-reference') and r['status']=='PASSED'
                    and r['case_count']==count
                    and {k:v for k,v in r.items() if k!='evidence'}==actual)
        gate(name+'/independently-recomputed-complete-results',cpu)
    def process_matrix(name,count):
        rows = load(name)
        if len(rows)!=count:
            return False
        for r in rows:
            cs = commands(r)
            if (not report(r,'run.json','rocm-original' if name=='originals' else 'rocm-CLI')
                or not observed(r) or r['build']!=frontend or len(cs)!=1
                or cs[0]['return_code']!=r['return_code']
                or cs[0]['argv'][0]!=str(ROOT/frontend['binary'])):
                return False
        return True
    gate('four-complete-original-C++-processes',lambda:process_matrix('originals',4))
    gate('eighteen-actual-CLI-processes',lambda:process_matrix('cli',18))
    def native_process():
        r = native_run()
        return (report(r,'run.json','cuda-original') and r['status']=='EXECUTED'
                and r['return_code']==r['build_return_code']==r['collection_return_code']==0
                and len(commands(r))==6 and all(c['return_code']==0 for c in commands(r)))
    gate('unmodified-native-CUDA-original-and-device-receipts',native_process)
    def mutations(name,filename):
        r = load(name)
        names = json.loads((ROOT/'migration/rewrite'/filename).read_text())
        return (report(r,'checks.json','CPU-validator-test') and r['status']=='PASSED'
                and r['case_count']==len(r['checks'])==len(names)==30
                and len({c['check'] for c in r['checks']})==30
                and {c['check'] for c in r['checks']}==set(names)
                and all(c['passed'] for c in r['checks']))
    gate('thirty-core-acceptance-reader-checks',
         lambda:mutations('checks','image-flood-validator-cases.json'))
    gate('thirty-runtime-CLI-original-reader-checks',
         lambda:mutations('runtime-checks','image-flood-runtime-validator-cases-v2.json'))
    def padding_fix():
        old, fixed = load('legacy-padding-failure'), load('padding-fix-validation')
        return (report(fixed,'results.json','rocm-contract-probe')
                and fixed['status']=='PASSED'
                and fixed['historical_counterexample']==old['evidence']
                and all(c['passed'] for c in fixed['checks']))
    gate('same-one-pixel-padding-counterexample-now-rejected',padding_fix)
    def cold():
        r = load('cold')
        counts = {'contracts':1,'original-contracts':1,'runtime-contracts':1,
                  'cli-contracts':1,'build':1,'all':1,'frontend-build':1,
                  'originals':4,'runtime':1,'cli':18,'trace':1,
                  'all-validation':1,'originals-validation':1,
                  'runtime-validation':1,'cli-validation':1,'trace-validation':1}
        if (not report(r,'cold.json','host-cold-replay') or r['status']!='PASSED'
            or r['return_code'] or len(r['children'])!=36
            or not all(c['passed'] for c in r['checks'])
            or any(len([c for c in r['children'] if c['name']==name])!=count
                   for name,count in counts.items())):
            return False
        manifest = json.loads((ROOT/r['evidence']/'manifest.json').read_text())
        raw = ROOT/manifest['raw_artifact_dir']
        for child in r['children']:
            path = raw/child['relative']
            members = json.loads((path/'child-seal.json').read_text())['files']
            source = json.loads((path/'source.json').read_text())
            if (source['commit']!=r['source_commit']
                or any(not(path/name).is_file()
                       or (path/name).stat().st_size!=value['bytes']
                       or digest(path/name)!=value['sha256']
                       for name,value in members.items())
                or any(digest(ROOT/source['source_objects'][name])!=sha
                       or digest(ROOT/name)!=sha
                       for name,sha in source['dependencies'].items())):
                return False
            sources.update(source['dependencies'])
        cold_build = next(c['report'] for c in r['children'] if c['name']=='build')
        return cold_build['dependencies']==build['dependencies'] and cold_build['abi_version']==1
    gate('thirty-six-sealed-child-clean-checkout',cold)
    sources.update({'tools/moat/qualify_image_flood.py', 'tools/moat/publish_image_flood.py',
                    'tools/moat/qualify_canny_plus.py', 'tools/moat/qualify_first.py',
                    'tools/moat/selected_proofs.py', 'tools/moat/audit.py',
                    'tools/moat/snapshot.py', 'tools/migration/device_guard.py',
                    'migration/environments/project.lock.json',
                    'migration/rewrite/image-acceptance-policy.json'})
    gate('three-independent-exact-source-and-proof-reviews',
         lambda: reviewed(review, sorted(sources), refs))
    return checks, refs, sorted(sources), build, spec

def metadata():
    r = load('all')
    return dict(rocm_evidence=r['evidence'], cuda_evidence=native_run()['evidence'],
                environment=r['evidence']+'/backend.observed.json',
                devices=json.loads((ROOT/r['evidence']/'backend.observed.json').read_text())['devices'])

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    review = load('review') if (ROOT/'migration/reports/image-flood-review.json').exists() else None
    checks, refs, sources, build, spec = collect(review)
    status = 'PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    print(status, [c['check'] for c in checks if not c['passed']], flush=True)
    if a.dry_run or status != 'PASSED':
        return int(status != 'PASSED')
    q = dict(sample_id=SAMPLE, kind='image-flood-full', status=status,
             implementation=IMPLEMENTATION, implementation_sha256=digest(ROOT/IMPLEMENTATION),
             dependencies=load('frontend-build')['dependencies'],
             case_ids=[c['case'] for c in spec['cases']], case_count=29,
             comparison_mode=COMPARISON, checks=checks,
             evidence_references=sorted(refs), source_commit=review['source_commit'],
             scope='Complete five-mode/two-image/five-product C++ entry; independently exact fixed-seed eight-connected GPU flood fill. Native NPP+ differences documented. Linux/gfx1201/ROCm10.1; no vendor ABI/performance/wave64/Windows claim.',
             **metadata())
    e = Experiment('I3', SAMPLE, 'composite-qualification', sources=[ROOT/n for n in sources])
    write(e.path/'qualification.json', q)
    q.update(qualification_id=e.id,
             evidence=e.finish('PASSED', dict(status=status, checks=checks)))
    write(ROOT/'migration/reports/image-flood-qualification.json', q)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
