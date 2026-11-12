#!/usr/bin/env python3
"""Qualify Flood Fill from sealed evidence."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from experiment import ROOT, Experiment, write, digest
from qualify_canny_plus import sealed, reviewed
from audit import check as audit
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

def build_command(r,command,frontend=False):
    """Bind the actual hipcc argv to the recorded source, device and output."""
    root=Path(command['cwd']);core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core')
    overlay=root/'build/rocm-sdk-overlay'
    common=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
            '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),
            '--offload-arch=gfx1201','-std=c++17','-O2']
    if frontend:
        backend=r['backend']
        library=root/backend['library']
        expected=[*common,'-D__HIP_PLATFORM_AMD__','-x','hip',
                  str(root/IMPLEMENTATION),'-L'+str(library.parent),'-limage_flood',
                  '-Wl,-rpath,'+str(library.parent),'-L'+str(core/'lib'),
                  '-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',
                  str(root/r['binary'])]
    else:
        expected=[*common,'-fPIC','-D__HIP_PLATFORM_AMD__','-x','hip','-shared',
                  str(root/'rocm/common/image/flood.hip'),
                  str(root/'rocm/common/image/connectivity.hip'),
                  '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),
                  '-lamdhip64','-o',str(root/r['library'])]
    return root.is_absolute() and command['argv']==expected

def cold_inventory(children):
    counts = {'contracts':1,'original-contracts':1,'runtime-contracts':1,
              'cli-contracts':1,'build':1,'all':1,'frontend-build':1,
              'originals':4,'runtime':1,'cli':18,'trace':1,
              'all-validation':1,'originals-validation':1,
              'runtime-validation':1,'cli-validation':1,'trace-validation':1}
    if (len(children)!=36 or {c['name'] for c in children}!=set(counts)
        or len({c['relative'] for c in children})!=36
        or len({c['report']['evidence'] for c in children})!=36):
        return False
    for name,count in counts.items():
        rows = [c for c in children if c['name']==name]
        if (len(rows)!=count or {c['index'] for c in rows}!=set(range(count))
            or any(c['relative']!=f'child-evidence/{name}/{c["index"]}' for c in rows)):
            return False
    original_rules=json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text())['workflows']
    cli_rules=json.loads((ROOT/'migration/rewrite/image-flood-cli-contract.json').read_text())['cases']
    return ({c['report']['case'] for c in children if c['name']=='originals'}=={r['case'] for r in original_rules}
            and {c['report']['case'] for c in children if c['name']=='cli'}=={r['case'] for r in cli_rules})

def cold_verify(r, build, source_deps, raw_override=None):
    """Check copied child archives and rerun independent CPU readers."""
    if (r['status']!='PASSED' or r['return_code']!=0 or not r['checks']
        or not all(c['passed'] for c in r['checks']) or not cold_inventory(r['children'])):
        return False
    parent=Path(raw_override) if raw_override else ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']
    groups={name:[c for c in r['children'] if c['name']==name]
            for name in {c['name'] for c in r['children']}}
    cb=groups['build'][0]['report'];fb=groups['frontend-build'][0]['report']
    if cb['dependencies']!=build['dependencies'] or cb['abi_version']!=1 or fb['backend']!=cb:
        return False
    members={name:'contracts.json' for name in
             ['contracts','original-contracts','runtime-contracts','cli-contracts']}
    members.update({'build':'build.json','frontend-build':'build.json',
                    'all':'run.json','runtime':'run.json','trace':'run.json',
                    'originals':'run.json','cli':'run.json'})
    members.update({name:'results.json' for name in
                    ['all-validation','originals-validation','runtime-validation',
                     'cli-validation','trace-validation']})
    backends={name:'CPU-contract' for name in
              ['contracts','original-contracts','runtime-contracts','cli-contracts']}
    backends.update({'build':'rocm-build','frontend-build':'rocm-build',
                     'all':'rocm-prototype','runtime':'rocm-runtime','trace':'rocm-trace',
                     'originals':'rocm-original','cli':'rocm-CLI'})
    backends.update({name:'CPU-reference' for name in
                     ['all-validation','originals-validation','runtime-validation',
                      'cli-validation','trace-validation']})
    for child in r['children']:
        name,report=child['name'],child['report'];path=parent/child['relative']
        seal=json.loads((path/'child-seal.json').read_text())['files']
        source=json.loads((path/'source.json').read_text())
        manifest=json.loads((path/'manifest.json').read_text())
        commands=json.loads((path/'commands.json').read_text()) if (path/'commands.json').exists() else []
        if (source['commit']!=r['source_commit']
            or not {'manifest.json','source.json','validation.json',members[name]}<=set(seal)
            or manifest['backend']!=backends[name]
            or manifest['experiment_id']!=Path(report['evidence']).name
            or report.get('experiment_id',manifest['experiment_id'])!=manifest['experiment_id']
            or json.loads((path/members[name]).read_text())!={k:v for k,v in report.items() if k!='evidence'}
            or any(not(path/file).is_file() or (path/file).stat().st_size!=v['bytes']
                   or digest(path/file)!=v['sha256'] for file,v in seal.items())
            or any(digest(ROOT/source['source_objects'][file])!=sha or digest(ROOT/file)!=sha
                   for file,sha in source['dependencies'].items())):
            return False
        if name in {'contracts','original-contracts','runtime-contracts','cli-contracts'}:
            if report['status']!='FROZEN' or manifest['experiment_outcome']!='OBSERVED' or commands:return False
        elif name in {'build','frontend-build','all','runtime','trace','originals','cli'}:
            rc=report.get('return_code',0)
            if len(commands)!=1 or commands[0]['return_code']!=rc or manifest['experiment_outcome']!=('EXPECTED_REJECTION' if rc else 'EXECUTED'):return False
        elif report['status']!='PASSED' or manifest['experiment_outcome']!='PASSED' or commands:
            return False
        if name in {'build','frontend-build'} and (commands[0]['cwd']!=r['clone']
            or not build_command(report,commands[0],frontend=name=='frontend-build')):
            return False
        if name in {'all','runtime','trace'} and (report['build']!=cb or manifest['parent_experiment_id']!=cb['experiment_id']):return False
        if name=='frontend-build' and manifest['parent_experiment_id']!=cb['experiment_id']:return False
        if name in {'originals','cli'} and (report['build']!=fb or manifest['parent_experiment_id']!=fb['experiment_id']):return False
        source_deps.update(source['dependencies'])
    if (digest(parent/groups['build'][0]['relative']/Path(cb['library']).name)!=cb['library_sha256']
        or digest(parent/groups['frontend-build'][0]['relative']/Path(fb['binary']).name)!=fb['binary_sha256']):
        return False
    def path_of(child):return parent/child['relative']
    def rebased(child):
        p=path_of(child);v=dict(child['report']);v['outputs']=str(p/'outputs');v['evidence']=str(p)
        return v,p
    actual=core.validate(*rebased(groups['all'][0]))
    expected=groups['all-validation'][0]['report']
    if {k:v for k,v in expected.items() if k!='evidence'}!=dict(status='PASSED',case_count=29,results=actual) or any(x['status']!='PASSED' for x in actual):return False
    actual=runtime.validate(*rebased(groups['runtime'][0]))
    expected=groups['runtime-validation'][0]['report']
    if actual!={k:v for k,v in expected.items() if k!='evidence'} or actual['status']!='PASSED':return False
    actual=trace.validate(*rebased(groups['trace'][0]))
    expected=groups['trace-validation'][0]['report']
    if actual!={k:v for k,v in expected.items() if k!='evidence'} or actual['status']!='PASSED':return False
    rules={x['case']:x for x in json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text())['workflows']}
    original_results=[]
    for child in groups['originals']:
        p=path_of(child);v=dict(child['report']);meta=json.loads((p/'manifest.json').read_text())
        old=Path(r['clone'])/meta['raw_artifact_dir']
        for field in ['inputs','outputs','audit']:
            v[field]=str(p/(Path(r['clone'])/v[field]).relative_to(old))
        v['evidence']=str(p)
        original_results.append(originals.validate_one(v,rules[v['case']],raw_override=p))
    expected=groups['originals-validation'][0]['report']
    summary=dict(status='PASSED',case_count=4,file_count=20,results=original_results)
    if summary!={k:v for k,v in expected.items() if k!='evidence'} or any(x['status']!='PASSED' for x in original_results):return False
    cli_rows=[];cli_raw={}
    for child in groups['cli']:
        p=path_of(child);v=dict(child['report']);meta=json.loads((p/'manifest.json').read_text())
        old=Path(r['clone'])/meta['raw_artifact_dir']
        for field in ['inputs','outputs','audit']:
            v[field]=str(p/(Path(r['clone'])/v[field]).relative_to(old))
        v['evidence']=str(p);cli_rows.append(v);cli_raw[v['case']]=p
    actual=cli.validate(cli_rows,raw_overrides=cli_raw)
    expected=groups['cli-validation'][0]['report']
    if actual!={k:v for k,v in expected.items() if k!='evidence'} or actual['status']!='PASSED':return False
    return True

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
                and commands(build)[0]['cwd']==str(ROOT)
                and build_command(build,commands(build)[0])
                and report(frontend,'build.json','rocm-build') and observed(frontend)
                and frontend['status']=='BUILT' and frontend['backend']==build
                and frontend['implementation']==IMPLEMENTATION and frontend['dependencies']==full
                and frontend['build_recipe_sha256']==digest(ROOT/'tools/moat/image_flood_frontend_build.py')
                and digest(ROOT/frontend['binary'])==frontend['binary_sha256']
                and len(commands(frontend))==1 and commands(frontend)[0]['return_code']==0
                and commands(frontend)[0]['cwd']==str(ROOT)
                and build_command(frontend,commands(frontend)[0],frontend=True))
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
        old_dir=ROOT/old['evidence'];old_build_dir=ROOT/old['build']['evidence']
        refs.update({old['evidence'],old['build']['evidence']})
        if audit(old_dir) or audit(old_build_dir):return False
        old_source=json.loads((old_dir/'source.json').read_text())
        old_build_source=json.loads((old_build_dir/'source.json').read_text())
        sources.update(old_source['source_objects'].values())
        sources.update(old_build_source['source_objects'].values())
        old_manifest=json.loads((old_dir/'manifest.json').read_text())
        new_dir,manifest,_=sealed(fixed['evidence'])
        old_command=json.loads((old_dir/'commands.json').read_text())
        new_command=json.loads((new_dir/'commands.json').read_text())
        if (not report(fixed,'results.json','rocm-contract-probe')
            or old['status']!='FAILED_CONTRACT'
            or old_manifest['experiment_outcome']!='CONTRACT_GAP_RECORDED'
            or manifest['experiment_outcome']!='PASSED'
            or json.loads((old_dir/'counterexample.json').read_text())!={k:v for k,v in old.items() if k!='evidence'}
            or fixed['status']!='PASSED' or fixed['build']!=build
            or fixed['historical_counterexample']!=old['evidence']
            or len(old_command)!=1 or len(new_command)!=1):return False
        # Both GPU processes execute the exact same Python descriptor reproducer;
        # only the fixed library/hash and output directory may change.
        a,c=old_command[0],new_command[0]
        if (a['return_code'] or c['return_code'] or a['argv'][:3]!=c['argv'][:3]
            or hashlib.sha256(a['argv'][2].encode()).hexdigest()!=fixed['reproducer_sha256']
            or a['argv'][3:5]!=[str(ROOT/old['build']['library']),old['build']['library_sha256']]
            or c['argv'][3:5]!=[str(ROOT/build['library']),build['library_sha256']]
            or old['build']['library_sha256']==build['library_sha256']
            or digest(ROOT/old['build']['library'])!=old['build']['library_sha256']):return False
        if (old_source['dependencies']['rocm/common/image/flood.hip']!=old['build']['dependencies']['rocm/common/image/flood.hip']
            or old_source['dependencies']['rocm/common/image/flood.hip']==build['dependencies']['rocm/common/image/flood.hip']):return False
        def bytes_and_observed(r,d):
            meta=json.loads((d/'manifest.json').read_text())
            raw=ROOT/meta['raw_artifact_dir']
            v=json.loads((raw/'outputs/observed.json').read_text())
            files={p.name:p.read_bytes() for p in (raw/'outputs').iterdir() if p.is_file()}
            if (v!=r['observed'] or set(files)!={'observed.json','input-before.bin',
                 'input-after.bin','output.bin','region.bin','workspace.bin'}
                or files['input-before.bin']!=bytes(v['input_before'])
                or files['input-after.bin']!=bytes(v['input_after'])):
                raise ValueError('actual old/new counterexample bytes')
            return v,files
        before,old_files=bytes_and_observed(old,old_dir)
        after,new_files=bytes_and_observed(fixed,new_dir)
        if any(fixed['files'][name]['bytes']!=len(data)
               or fixed['files'][name]['sha256']!=hashlib.sha256(data).hexdigest()
               for name,data in new_files.items()):return False
        for v,padding,rc in [(before,255,0),(after,197,1)]:
            d=v['descriptor']
            if (v['return_code']!=rc or v['expected_return_code']!=1
                or v['input_before']!=[31,41,51,197]
                or v['input_after']!=[31,41,51,padding]
                or v['padding_before']!=197 or v['padding_after']!=padding
                or d['width']!=1 or d['height']!=1 or d['input_pitch']!=4
                or d['output_pitch']!=3 or d['mask_pitch']!=1
                or d['mask']!=d['input']+3 or d['workspace_bytes']!=12):return False
        return (new_files['output.bin']==bytes([185])*3
                and new_files['region.bin']==bytes([167])*32
                and new_files['workspace.bin']==bytes([211])*12
                and len(old['checks'])==2 and not any(c['passed'] for c in old['checks'])
                and len(fixed['checks'])==4 and all(c['passed'] for c in fixed['checks']))
    gate('same-one-pixel-padding-counterexample-now-rejected',padding_fix)
    def cold():
        r = load('cold')
        return report(r,'cold.json','host-cold-replay') and cold_verify(r,build,sources)
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
