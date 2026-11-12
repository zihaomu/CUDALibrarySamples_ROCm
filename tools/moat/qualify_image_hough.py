#!/usr/bin/env python3
"""Qualify the complete Hough original entry from current sealed GPU/CPU evidence."""
import argparse,collections,json,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from qualify_canny_plus import sealed,reviewed
from image_hough_reference import validate
from image_hough_build import dependencies

SAMPLE='NPP/houghLines::houghLines.cpp'
IMPLEMENTATION='rocm/ported/NPP/houghLines/houghLines.cpp'
COMPARISON='DOCUMENTED_HOUGH_ACCUMULATOR_VARIANT'

def load(name):return json.loads((ROOT/f'migration/reports/image-hough-{name}.json').read_text())
def profile():return json.loads((ROOT/'migration/rewrite/image-hough-profile.json').read_text())

def cold_verify(cold):
    expected={'contracts':1,'build':1,'runs':14,'validation':14,'options-run':5,
              'options-validation':5,'runtime':1,'runtime-validation':1,'trace':1}
    children=cold['children']
    if (cold['status']!='PASSED' or cold['return_code']!=0 or len(children)!=43
        or collections.Counter(c['name'] for c in children)!=expected
        or len({c['relative'] for c in children})!=43
        or len({c['report']['evidence'] for c in children})!=43
        or not all(c['passed'] for c in cold['checks'])):return False
    parent=ROOT/json.loads((ROOT/cold['evidence']/'manifest.json').read_text())['raw_artifact_dir']
    for name,count in expected.items():
        if {c['index'] for c in children if c['name']==name}!=set(range(count)):return False
    for child in children:
        path=parent/child['relative']
        if child['relative']!=f"child-evidence/{child['name']}/{child['index']}":return False
        seal=json.loads((path/'child-seal.json').read_text())['files']
        if not {'manifest.json','source.json','validation.json'}<=set(seal):return False
        if set(seal)!={str(p.relative_to(path)) for p in path.rglob('*') if p.is_file() and p.name!='child-seal.json'}:return False
        if any((path/name).stat().st_size!=meta['bytes'] or digest(path/name)!=meta['sha256'] for name,meta in seal.items()):return False
        manifest=json.loads((path/'manifest.json').read_text());source=json.loads((path/'source.json').read_text())
        if manifest['experiment_id']!=Path(child['report']['evidence']).name or source['commit']!=cold['source_commit']:return False
        if any(not (ROOT/obj).is_file() or digest(ROOT/obj)!=sha
               for n,sha in source['dependencies'].items()
               for obj in [source['source_objects'][n]]):return False
        member='contracts.json' if child['name']=='contracts' else 'build.json' if child['name']=='build' else 'run.json' if child['name'] in {'runs','options-run'} else 'results.json' if child['name'] in {'validation','runtime-validation'} else 'runtime.json' if child['name']=='runtime' else 'trace-result.json' if child['name']=='trace' else None
        if member and json.loads((path/member).read_text())!={k:v for k,v in child['report'].items() if k!='evidence'}:return False
        if child['name']=='options-validation':
            v=json.loads((path/'validation.json').read_text())
            if v['status']!='PASSED' or v['checks']!=child['report']['checks']:return False
    return True

def collect(review=None):
    p=profile();contract=load('contracts');build=load('build');runs=load('runs');cpu=load('validation')
    options=load('options');runtime=load('runtime');runtime_cpu=load('runtime-validation')
    trace=load('trace');native=load('native-comparison');cold=load('cold')
    refs=set();sources={str(x.relative_to(ROOT)) for x in dependencies()};checks=[]
    def gate(name,fn):
        try:ok=bool(fn())
        except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration,AssertionError,subprocess.CalledProcessError):ok=False
        checks.append(dict(check=name,passed=ok));return ok
    def record(r,member,backend=None):
        refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies'])
        return ((backend is None or m['backend']==backend)
                and json.loads((d/member).read_text())=={k:v for k,v in r.items() if k!='evidence'})
    def physical(r):
        observed=json.loads((ROOT/r['evidence']/'backend.observed.json').read_text())
        return {d['physical_id'] for d in observed['devices']}=={1}
    def frozen():
        cases=p['cases'];names={c['case'] for c in cases}
        return (record(contract,'contracts.json','CPU-contract') and contract['status']=='FROZEN'
                and p['status']=='FROZEN' and p['sample_id']==SAMPLE
                and p['source_sha256']==digest(ROOT/p['source'])
                and p['case_count']==len(cases)==len(names)==14
                and sum(c['kind']=='valid' for c in cases)==7
                and all((ROOT/c['input']).stat().st_size==c['bytes'] and digest(ROOT/c['input'])==c['sha256']
                        for c in cases if 'input' in c))
    gate('frozen-fourteen-complete-CLI-and-RAW-contract',frozen)
    def built():
        return (record(build,'build.json','rocm-build') and physical(build)
                and build['status']=='BUILT' and build['return_code']==0
                and digest(ROOT/build['binary'])==build['binary_sha256']
                and digest(ROOT/build['library'])==build['library_sha256']
                and build['dependencies']=={str(x.relative_to(ROOT)):digest(x) for x in dependencies()}
                and build['build_recipe_sha256']==digest(ROOT/'tools/moat/image_hough_build.py')
                and len(json.loads((ROOT/build['evidence']/'commands.json').read_text()))==2)
    gate('current-compiled-shared-Canny-and-Hough-GPU-binary',built)
    cases={c['case']:c for c in p['cases']}
    def original_workflows():
        if len(runs)!=14 or {r['case'] for r in runs}!=set(cases):return False
        for r in runs:
            c=cases[r['case']];args=c['arguments'].copy()
            if '-i' in args:args[args.index('-i')+1]=str(ROOT/args[args.index('-i')+1])
            commands=json.loads((ROOT/r['evidence']/'commands.json').read_text())
            if (not record(r,'run.json','rocm-original') or not physical(r) or r['status']!='EXECUTED'
                or r['build']!=build['evidence'] or r['return_code']!=c['expected_return_code']
                or len(commands)!=1 or commands[0]['argv']!=[str(ROOT/build['binary']),*args]
                or commands[0]['return_code']!=r['return_code']):return False
            if c['kind']=='valid':
                raw=ROOT/json.loads((ROOT/r['evidence']/'manifest.json').read_text())['raw_artifact_dir']
                for file,key in [('hough_result.ppm','ppm'),('hough_lines.csv','lines')]:
                    f=raw/'outputs'/file
                    if not f.is_file() or digest(f)!=r[key+'_sha256'] or f.stat().st_size!=r[key+'_bytes']:return False
            elif r['ppm_sha256'] is not None or r['lines_sha256'] is not None:return False
        return True
    gate('fourteen-actual-complete-original-CLI-and-products',original_workflows)
    def cpu_cases():
        if len(cpu)!=14 or {r['case'] for r in cpu}!=set(cases):return False
        by={r['case']:r for r in runs}
        for v in cpu:
            if (not record(v,'results.json','CPU-reference') or v['status']!='PASSED'
                or not all(c['passed'] for c in v['checks'])
                or json.loads(json.dumps(validate(cases[v['case']],by[v['case']])))!={k:x for k,x in v.items() if k!='evidence'}):return False
        return True
    gate('fourteen-complete-line-list-CSV-PPM-independent-CPU-recomputations',cpu_cases)
    def valid_options():
        if len(options)!=5 or len({x['case']['case'] for x in options})!=5:return False
        for x in options:
            c,r,v=x['case'],x['run'],x['validation']
            if (not record(r,'run.json','rocm-original') or not physical(r)
                or r['status']!='EXECUTED' or r['return_code']!=0
                or v['status']!='PASSED' or not all(ch['passed'] for ch in v['checks'])
                or json.loads(json.dumps(validate(c,r)))!={k:y for k,y in v.items() if k!='evidence'}):return False
            refs.add(v['evidence']);d,m,src=sealed(v['evidence']);sources.update(src['dependencies'])
            if m['backend']!='CPU-reference' or json.loads((d/'validation.json').read_text())!=dict(status='PASSED',checks=v['checks']):return False
        return True
    gate('five-valid-nondefault-parameter-and-1196-peak-complete-products',valid_options)
    def runtime_gate():
        return (record(runtime,'runtime.json','rocm-runtime') and physical(runtime)
                and runtime['status']=='PASSED' and runtime['case_count']==11
                and len(runtime['checks'])>=7 and all(c['passed'] for c in runtime['checks'])
                and record(runtime_cpu,'results.json','CPU-reference')
                and runtime_cpu['status']=='PASSED' and all(c['passed'] for c in runtime_cpu['checks']))
    gate('eleven-real-device-runtime-and-all-peaks-independent-CPU',runtime_gate)
    def trace_gate():
        return (record(trace,'trace-result.json','rocm-trace') and physical(trace)
                and trace['status']=='PASSED' and trace['return_code']==0
                and all(trace['counts'].get(k)==1 for k in ['sobel','suppress','local_threshold','cast_votes','extract_peaks'])
                and all(c['passed'] for c in trace['checks']))
    gate('five-actual-Canny-and-Hough-GPU-dispatches-on-physical-one',trace_gate)
    def native_gate():
        original=next(r for r in json.loads((ROOT/'migration/reports/image-I3-native-originals.json').read_text())
                      if r['source']=='NPP/houghLines/houghLines.cpp')
        return (record(native,'comparison.json','CPU-reference') and native['status']=='PASSED'
                and original['return_code']==original['build_return_code']==original['collection_return_code']==0
                and native['native_evidence']==original['evidence']
                and native['native_line_count']==native['project_line_count']==10
                and native['differing_RGB_pixels']==10627
                and abs(native['red_line_IoU']-0.2394618192227868)<1e-12)
    gate('unmodified-native-5090-complete-PPM-and-declared-variant',native_gate)
    def cold_gate():
        refs.add(cold['evidence']);d,m,src=sealed(cold['evidence']);sources.update(src['dependencies'])
        return m['backend']=='host-cold-replay' and json.loads((d/'cold.json').read_text())=={k:v for k,v in cold.items() if k!='evidence'} and cold_verify(cold)
    gate('forty-three-sealed-child-clean-checkout-replay',cold_gate)
    def mutations():
        r=load('qualification-checks')
        names=json.loads((ROOT/'migration/rewrite/image-hough-qualification-checks.json').read_text())
        return (record(r,'checks.json','CPU-validator-test') and r['status']=='PASSED'
                and r['case_count']==len(r['checks'])==len(names)==11
                and [c['check'] for c in r['checks']]==names
                and all(c['passed'] for c in r['checks']))
    gate('eleven-real-qualification-and-archive-mutation-checks',mutations)
    sources.update({'tools/moat/qualify_image_hough.py','tools/moat/publish_image_hough.py',
                    'tools/moat/image_hough_qualification_checks.py',
                    'tools/moat/qualify_canny_plus.py','tools/moat/qualify_first.py',
                    'tools/moat/selected_proofs.py','tools/moat/audit.py',
                    'migration/environments/project.lock.json',
                    'migration/rewrite/image-acceptance-policy.json'})
    gate('three-independent-fixed-source-and-proof-reviews',lambda:reviewed(review,sorted(sources),refs))
    return checks,refs,sorted(sources),build,p

def main():
    args=argparse.ArgumentParser();args.add_argument('--dry-run',action='store_true');a=args.parse_args()
    review=load('review') if (ROOT/'migration/reports/image-hough-review.json').exists() else None
    checks,refs,sources,build,p=collect(review)
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    print(status,[c['check'] for c in checks if not c['passed']],flush=True)
    if a.dry_run or status!='PASSED':return int(status!='PASSED')
    q=dict(sample_id=SAMPLE,kind='image-hough-full',status=status,
           implementation=IMPLEMENTATION,implementation_sha256=digest(ROOT/IMPLEMENTATION),
           dependencies=build['dependencies'],case_ids=[c['case'] for c in p['cases']]+[x['case']['case'] for x in load('options')],
           case_count=19,comparison_mode=COMPARISON,checks=checks,
           evidence_references=sorted(refs),source_commit=review['source_commit'],
           rocm_evidence=next(r for r in load('runs') if r['case']=='synthetic-default')['evidence'],
           cuda_evidence=load('native-comparison')['native_evidence'],
           environment=build['evidence']+'/backend.observed.json',
           devices=json.loads((ROOT/build['evidence']/'backend.observed.json').read_text())['devices'],
           scope='Complete synthetic/RAW C++ Hough entry, nineteen valid/error/parameter CLI cases, eleven memory/stream contracts, GPU Canny/vote/peak dispatch, exact independent CPU project outputs and documented native differences. Linux/gfx1201/ROCm10.1 only; no vendor-exact or performance claim.')
    e=Experiment('I3',SAMPLE,'composite-qualification',sources=[ROOT/n for n in sources])
    write(e.path/'qualification.json',q)
    q.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status=status,checks=checks)))
    write(ROOT/'migration/reports/image-hough-qualification.json',q)
    return 0

if __name__=='__main__':raise SystemExit(main())
