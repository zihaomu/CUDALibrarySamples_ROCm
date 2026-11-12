#!/usr/bin/env python3
"""Issue a composite qualification for the complete four-operation benchmark."""
import argparse,collections,csv,json,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from audit import check as audit
from image_benchmark_build import dependencies
from image_benchmark_reference import validate as cpu_validate
from image_benchmark_native_comparison import parse as parse_benchmark,native_execution_ok
from qualify_first import review_identity
from image_benchmark_cold import FILES as COLD_FILES

SAMPLE='NPP/opencvBenchmark::opencvBenchmark.cpp'
IMPLEMENTATION='rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp'
COMPARISON='DOCUMENTED_IMAGE_ALGORITHM_VARIANTS'
REPORTS={'contracts':'image-benchmark-contracts.json','deps':'image-I3-rocm-OpenCV.json',
 'build':'image-benchmark-build.json','runs':'image-benchmark-runs.json',
 'validation':'image-benchmark-validation.json','native':'image-benchmark-native-comparison.json',
 'runtime':'image-benchmark-runtime.json','trace':'image-benchmark-trace.json',
 'negative':'image-benchmark-negative.json','cold':'image-benchmark-cold.json'}
MEMBERS={'contracts':'contracts.json','deps':'results.json','build':'build.json',
 'runs':'run.json','validation':'results.json','native':'comparison.json',
 'runtime':'runtime.json','trace':'trace-result.json','negative':'negative.json','cold':'cold.json'}
BACKENDS={'contracts':'CPU-contract','deps':'rocm-setup','build':'rocm-build',
 'runs':'rocm-original','validation':'CPU-reference','native':'CPU-comparison',
 'runtime':'rocm-runtime','trace':'rocm-trace','negative':'CPU-negative','cold':'host-cold-replay'}

def expected_dependencies(build):
    deps=dict(build['dependencies'])
    for name in ['migration/rewrite/image-benchmark-profile.json',
       'tools/moat/image_benchmark_reference.py','tools/moat/image_benchmark_native_comparison.py',
       'tools/moat/image_benchmark_identity.py','tools/moat/image_benchmark_cold.py',
       'tools/moat/qualify_image_benchmark.py']:
      deps[name]=digest(ROOT/name)
    return deps

def load(kind):return json.loads((ROOT/'migration/reports'/REPORTS[kind]).read_text())
def proof(row,kind):
    ref=row['evidence'];path=ROOT/ref
    if audit(path):return False
    manifest=json.loads((path/'manifest.json').read_text())
    source=json.loads((path/'source.json').read_text())['dependencies']
    if any(not (ROOT/name).is_file() or digest(ROOT/name)!=sha for name,sha in source.items()):return False
    stored=json.loads((path/MEMBERS[kind]).read_text())
    return (manifest['backend']==BACKENDS[kind] and manifest['experiment_id']==path.name
       and stored=={k:v for k,v in row.items() if k!='evidence'})

def reviews_ok(review,cold,refs):
    if review.get('verdict')!='APPROVED' or review.get('source_commit')!=cold['source_commit']:return False
    reviewers=review.get('reviewers',[])
    if (len(reviewers)!=3 or {r['scope'] for r in reviewers}!={'original-contract','evidence-closure','HIP-algorithm'}
       or any(r['verdict']!='APPROVED' for r in reviewers)
       or len({r['reviewer_id'] for r in reviewers})!=3):return False
    commit=review['source_commit']
    if subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,capture_output=True).returncode:return False
    if not review_identity(review):return False
    if review.get('proof_seals')!={ref:digest(ROOT/ref/'sealed.json') for ref in refs}:return False
    try:
      if any(digest_bytes(subprocess.check_output(['git','show',commit+':'+ref+'/sealed.json'],cwd=ROOT,stderr=subprocess.DEVNULL))!=sha
             for ref,sha in review['proof_seals'].items()):return False
    except (OSError,subprocess.CalledProcessError):return False
    source_names=[str(p.relative_to(ROOT)) for p in dependencies() if 'image-I3-rocm-OpenCV.json' not in str(p)]
    source_names += ['migration/rewrite/image-benchmark-profile.json',
       'tools/moat/image_benchmark_runtime.cpp','tools/moat/qualify_image_benchmark.py',
       'tools/moat/publish_image_benchmark.py']
    source_names += [str(p.relative_to(ROOT)) for p in (ROOT/'tools/moat').glob('image_benchmark_*.py')]
    try:return all(digest(ROOT/name)==digest_bytes(subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT,stderr=subprocess.DEVNULL)) for name in set(source_names))
    except (OSError,subprocess.CalledProcessError):return False

def digest_bytes(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()

def runtime_recompute(runtime,build):
    path=ROOT/runtime['evidence'];manifest=json.loads((path/'manifest.json').read_text())
    raw=ROOT/manifest['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text())
    expected=['resolve-real-image-libraries','compile-runtime-contracts','run-actual-device-contracts']
    if ([c['phase'] for c in commands]!=expected or any(c['return_code'] for c in commands)
        or manifest['parent_experiment_id']!=build['experiment_id']):return False
    rows=[line.split('|') for line in (raw/commands[-1]['stdout']).read_text().splitlines()]
    names=['normal','changed-to-zero','restored','default-stream',
           'invalid-rejected-and-output-preserved','destroyed-stream-rejected']
    expected_rows=[[op,name,'1'] for op in ['gauss','resize','color'] for name in names]
    observed=json.loads((raw/'backend.observed.json').read_text())['devices']
    loaded=json.loads((raw/'loaded-libraries.json').read_text())
    return (rows==runtime['rows']==expected_rows and runtime['return_code']==0
        and len(observed)==1 and observed[0]['physical_id']==1
        and loaded['status']=='PASSED' and all(c['passed'] for c in loaded['checks']))

def native_recompute(comparison,default_run,profile):
    native=json.loads((ROOT/'migration/reports/image-I3-benchmark-native.json').read_text())
    nproof=ROOT/native['evidence'];nmanifest=json.loads((nproof/'manifest.json').read_text())
    ncommands=json.loads((nproof/'commands.json').read_text())
    nlogs=list((nproof/'logs').glob('*actual-4096x2048*stdout.log'))
    if not native_execution_ok(native,nmanifest,ncommands,nproof,nlogs):return False
    rproof=ROOT/default_run['evidence'];rmanifest=json.loads((rproof/'manifest.json').read_text())
    raw=ROOT/rmanifest['raw_artifact_dir'];rcommands=json.loads((raw/'commands.json').read_text())
    actual=[c for c in rcommands if c['phase']=='actual-four-operation-original-CLI']
    if len(actual)!=1 or actual[0]['return_code']!=0:return False
    original=nlogs[0].read_text();amd=(raw/actual[0]['stdout']).read_text()
    first=json.loads(original.splitlines()[0]);loader=json.loads((raw/'loaded-libraries.json').read_text())
    dep=json.loads((ROOT/'migration/reports/image-I3-rocm-OpenCV.json').read_text())
    receipt=json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text())['receipt']['files']
    cuda=parse_benchmark(original);amd_parsed=parse_benchmark(amd)
    cuda['size']=list(cuda['size']);amd_parsed['size']=list(amd_parsed['size'])
    return (comparison['status']=='PASSED' and comparison['native_evidence']==native['evidence']
      and comparison['rocm_evidence']==default_run['evidence']
      and comparison['cuda']==cuda and comparison['rocm']==amd_parsed
      and first['source_sha256']==digest(ROOT/native['source'])==profile['source_sha256']
      and first['input_sha256']==profile['image_sha256']
      and first['OpenCV_source']['commit']==dep['source']['commit']
      and loader['status']=='PASSED' and all(c['passed'] for c in loader['checks'])
      and any('libopencv_core' in name and meta['sha256']==receipt['lib/libopencv_core.so.4.12.0']['sha256']
              for name,meta in first['libraries'].items())
      and any('libopencv_imgproc' in name and meta['sha256']==receipt['lib/libopencv_imgproc.so.4.12.0']['sha256']
              for name,meta in first['libraries'].items())
      and comparison['cuda']['size']==comparison['rocm']['size']==[4096,2048,20,5]
      and comparison['cuda']['edges']=={'label':'NPP','gpu':546308,'opencv':324128}
      and comparison['rocm']['edges']=={'label':'ROCm','gpu':546308,'opencv':324128})

def cpu_recompute(profile,runs,valid):
    cases=profile['cases'];case_ids={c['case'] for c in cases}
    gpu={r['case']:r for r in runs};cpu={r['case']:r for r in valid}
    if len(gpu)!=len(cases) or len(cpu)!=len(cases) or set(gpu)!=case_ids or set(cpu)!=case_ids:return False
    for case in cases:
      row=cpu[case['case']];run=gpu[case['case']]
      directory=ROOT/row['evidence'];manifest=json.loads((directory/'manifest.json').read_text())
      recomputed=cpu_validate(case,run,profile)
      if (manifest['parent_experiment_id']!=Path(run['evidence']).name
        or row['status']!='PASSED' or row['checks']!=recomputed['checks']
        or row.get('metrics')!=recomputed.get('metrics') or recomputed['status']!='PASSED'):
        return False
    return True

def trace_recompute(trace,build,small_run):
    path=ROOT/trace['evidence'];manifest=json.loads((path/'manifest.json').read_text())
    raw=ROOT/manifest['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text())
    if ([c['phase'] for c in commands]!=['resolve-real-image-libraries','profile-complete-four-operation-C++-entry']
      or any(c['return_code'] for c in commands) or manifest['parent_experiment_id']!=build['experiment_id']):return False
    observed=json.loads((raw/'backend.observed.json').read_text())['devices']
    if len(observed)!=1 or observed[0]['physical_id']!=1:return False
    if ({p.name:digest(p) for p in (raw/'outputs').iterdir() if p.is_file()}
       !={name:x['sha256'] for name,x in small_run['products'].items()}):return False
    traces=list((raw/'trace').rglob('*kernel_trace.csv'));agents=list((raw/'trace').rglob('*agent_info.csv'))
    if len(traces)!=1 or len(agents)!=1:return False
    lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())}
    names=['gauss5','sobel','suppress','local_threshold','resize_half','rgb_gray'];counts=collections.Counter()
    for row in csv.DictReader(traces[0].open()):
      hits=[key for key in names if key in row['Kernel_Name']]
      if not hits:continue
      for key in hits:counts[key]+=1
      node=lookup[row['Agent_Id'].split()[-1]];loc=int(node['Location_Id'])
      bdf=f"{int(node['Domain']):04x}:{loc>>8:02x}:{(loc>>3)&31:02x}.{loc&7}"
      if (bdf!=observed[0]['pci_bdf'] or int(row['End_Timestamp'])<=int(row['Start_Timestamp'])
        or int(row['Grid_Size_X'])<=0):return False
    loaded=json.loads((raw/'loaded-libraries.json').read_text())
    return (dict(counts)==trace['counts'] and all(counts[name]>=1 for name in names)
      and trace['return_code']==0 and loaded['status']=='PASSED' and all(c['passed'] for c in loaded['checks']))

def cold_recompute(cold,profile,runs,valid):
    if cold['status']!='PASSED' or cold['return_code']!=0 or any(not c['passed'] for c in cold['checks']):return False
    path=ROOT/cold['evidence'];outer=json.loads((path/'manifest.json').read_text());raw=ROOT/outer['raw_artifact_dir']
    clone=Path(cold['clone'])
    if (clone.name!='src' or clone.parent.parent!=ROOT.parent
      or not clone.parent.name.startswith('image-benchmark-cold-')
      or outer['backend']!='host-cold-replay' or outer['experiment_outcome']!='PASSED'):return False
    commands=json.loads((raw/'commands.json').read_text())
    phases=['fresh-checkout','fixed-commit']+['cold-'+name for name in
      ['image_benchmark_contracts','image_benchmark_deps','bootstrap_sdk','image_benchmark_build',
       'image_benchmark_run','image_benchmark_reference','image_benchmark_native_comparison',
       'image_benchmark_runtime','image_benchmark_trace','image_benchmark_negative']]
    if (len(commands)!=len(phases) or [c['phase'] for c in commands]!=phases
       or any(c['return_code'] for c in commands)
       or commands[0]['argv']!=['git','clone','--shared','--quiet',str(ROOT),str(clone)]
       or commands[1]['argv']!=['git','checkout','--quiet',cold['source_commit']]
       or any(c['cwd']!=str(clone) for c in commands[1:])):return False
    expected={'contracts':1,'deps':1,'build':1,'runs':6,'validation':6,'native-comparison':1,
      'runtime':1,'trace':1,'negative':1}
    children=cold['children']
    if (len(children)!=19 or collections.Counter(c['kind'] for c in children)!=expected
       or len({(c['kind'],c['index']) for c in children})!=19
       or len({c['evidence'] for c in children})!=19
       or len({c['raw'] for c in children})!=19):return False
    for kind,count in expected.items():
      if {c['index'] for c in children if c['kind']==kind}!=set(range(count)):return False
    by={kind:[c for c in children if c['kind']==kind] for kind in expected}
    outcomes={'contracts':'OBSERVED','deps':'PASSED','build':'EXECUTED','validation':'PASSED',
      'native-comparison':'PASSED','runtime':'PASSED','trace':'PASSED','negative':'PASSED'}
    def child_report(child):
      typ='native' if child['kind']=='native-comparison' else child['kind']
      report=json.loads((raw/child['raw']/MEMBERS[typ]).read_text());report['evidence']=child['evidence']
      return report
    cold_build=child_report(by['build'][0])['experiment_id'];case_ids={c['case'] for c in profile['cases']}
    run_cases={child_report(c)['case']:c for c in by['runs']}
    validation_cases={child_report(c)['case']:c for c in by['validation']}
    if set(run_cases)!=case_ids or set(validation_cases)!=case_ids:return False
    for child in children:
      kind=child['kind'];index=child['index'];report=child_report(child)
      if child['raw']!=f'child-evidence/{kind}/{index}':return False
      folder=raw/child['raw'];seal=json.loads((folder/'child-seal.json').read_text())['files']
      actual={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and p.name!='child-seal.json'}
      if set(seal)!=actual:return False
      if any((folder/name).stat().st_size!=meta['bytes'] or digest(folder/name)!=meta['sha256'] for name,meta in seal.items()):return False
      manifest=json.loads((folder/'manifest.json').read_text());source=json.loads((folder/'source.json').read_text())
      typ='native' if kind=='native-comparison' else kind
      aggregate=json.loads((clone/'migration/reports'/COLD_FILES[kind]).read_text())
      aggregate=aggregate[index] if isinstance(aggregate,list) else aggregate
      if (source['commit']!=cold['source_commit'] or manifest['experiment_id']!=Path(child['evidence']).name
        or report['evidence']!=child['evidence'] or manifest['backend']!=BACKENDS[typ]
        or aggregate!=report):return False
      expected_outcome=outcomes.get(kind,'EXPECTED_REJECTION' if next(
        (c['expected_return_code'] for c in profile['cases'] if c['case']==report.get('case')),0) else 'EXECUTED')
      if manifest['experiment_outcome']!=expected_outcome:return False
      if kind in {'runs','runtime','trace'}:
        observed=json.loads((folder/'backend.observed.json').read_text())['devices']
        if len(observed)!=1 or observed[0]['physical_id']!=1:return False
      if kind=='runs':
        current=next(r for r in runs if r['case']==report['case'])
        if (manifest['case_id']!=report['case'] or manifest['parent_experiment_id']!=cold_build
          or report['products']!=current['products']):return False
        for name,meta in report['products'].items():
          product=folder/'outputs'/name
          if not product.is_file() or product.stat().st_size!=meta['bytes'] or digest(product)!=meta['sha256']:return False
      if kind=='validation':
        current=next(r for r in valid if r['case']==report['case'])
        if (manifest['case_id']!=report['case'] or manifest['parent_experiment_id']!=Path(run_cases[report['case']]['evidence']).name
          or report['checks']!=current['checks']):return False
        if report.get('metrics')!=current.get('metrics'):return False
      if kind in {'runtime','trace'} and manifest['parent_experiment_id']!=cold_build:return False
      if report['status'] not in {'READY','FROZEN','BUILT','EXECUTED','PASSED'}:return False
    return True

def collect(review):
    p=json.loads((ROOT/'migration/rewrite/image-benchmark-profile.json').read_text())
    data={kind:load(kind) for kind in REPORTS};build=data['build'];runs=data['runs'];valid=data['validation'];cold=data['cold']
    checks=[];refs=set()
    def gate(name,value):checks.append(dict(check=name,passed=bool(value)))
    def evidence(kind,rows):
      good=True
      for row in rows:
        refs.add(row['evidence'])
        try:good=proof(row,kind) and good
        except (OSError,KeyError,ValueError,TypeError):good=False
      return good
    gate('frozen-original-six-CLI-and-mathematics',p['status']=='FROZEN' and p['sample_id']==SAMPLE
       and p['case_count']==len(p['cases'])==6 and len({c['case'] for c in p['cases']})==6
       and p['semantic_policy']['gaussian']['project_max_abs']==0
       and p['semantic_policy']['gaussian']['opencv'].endswith('REFLECT_101')
       and p['semantic_policy']['performance'].endswith('no cross-device speedup claim')
       and digest(ROOT/p['source'])==p['source_sha256'] and digest(ROOT/p['image'])==p['image_sha256'])
    gate('sealed-contract',evidence('contracts',[data['contracts']]) and data['contracts']['status']=='FROZEN')
    gate('pinned-native-matched-OpenCV-dependency',evidence('deps',[data['deps']])
       and data['deps']['status']=='READY' and data['deps']['files_checked']==200
       and all(c['passed'] for c in data['deps']['checks']))
    gate('current-four-operation-GPU-build',evidence('build',[build]) and build['status']=='BUILT'
       and set(build['dependencies'])=={str(path.relative_to(ROOT)) for path in dependencies()}
       and all(digest(ROOT/name)==sha for name,sha in build['dependencies'].items())
       and digest(ROOT/build['binary'])==build['binary_sha256']
       and digest(ROOT/build['library'])==build['library_sha256']
       and build['build_recipe_sha256']==digest(ROOT/'tools/moat/image_benchmark_build.py'))
    case_ids=[c['case'] for c in p['cases']];by_case={r['case']:r for r in runs}
    gate('six-unique-actual-GPU-CLI-and-loaded-libraries',len(runs)==len(by_case)==6
       and set(by_case)==set(case_ids) and evidence('runs',runs)
       and all(r['status']=='EXECUTED' and all(c['passed'] for c in r['checks'])
       and json.loads((ROOT/r['evidence']/'loaded-libraries.json').read_text())['status']=='PASSED'
       for r in runs))
    gate('six-independent-full-products-and-error-diagnostics',
         cpu_recompute(p,runs,valid) and evidence('validation',valid))
    native=data['native'];native_ref=json.loads((ROOT/'migration/reports/image-I3-benchmark-native.json').read_text())['evidence']
    opencv_ref=json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text())['evidence']
    refs.update([native_ref,opencv_ref])
    gate('real-unmodified-5090-four-operation-comparison',evidence('native',[native])
       and not audit(ROOT/native_ref) and not audit(ROOT/opencv_ref)
       and native['status']=='PASSED' and all(c['passed'] for c in native['checks'])
       and native_recompute(native,by_case['original-default'],p))
    runtime=data['runtime']
    gate('eighteen-actual-device-memory-and-stream-contracts',evidence('runtime',[runtime])
       and runtime['status']=='PASSED' and len(runtime['rows'])==18 and all(r[2]=='1' for r in runtime['rows'])
       and all(c['passed'] for c in runtime['checks']) and runtime_recompute(runtime,build))
    trace=data['trace']
    gate('four-GPU-operation-and-Canny-real-kernel-trace',evidence('trace',[trace])
       and trace['status']=='PASSED' and all(trace['counts'].get(n,0)>=1 for n in
          ['gauss5','sobel','suppress','local_threshold','resize_half','rgb_gray'])
       and all(c['passed'] for c in trace['checks']) and trace_recompute(trace,build,by_case['small']))
    negative=data['negative']
    gate('nineteen-native-CLI-and-closure-counterexamples',evidence('negative',[negative])
       and negative['status']=='PASSED' and negative['case_count']==len(negative['checks'])==19
       and all(c['passed'] for c in negative['checks']))
    expected={'contracts':1,'deps':1,'build':1,'runs':6,'validation':6,'native-comparison':1,
       'runtime':1,'trace':1,'negative':1}
    gate('fixed-commit-clean-ten-job-nineteen-child-replay',evidence('cold',[cold])
       and cold['status']=='PASSED' and cold['return_code']==0
       and len(cold['children'])==19
       and collections.Counter(c['kind'] for c in cold['children'])==expected
       and all(c['passed'] for c in cold['checks'])
       and cold_recompute(cold,p,runs,valid)
       and review is not None and cold['source_commit']==review['source_commit'])
    gate('three-independent-fixed-source-reviews',reviews_ok(review,cold,refs) if review else False)
    return checks,refs,build,p

def main():
    a=argparse.ArgumentParser();a.add_argument('--dry-run',action='store_true');args=a.parse_args()
    report=ROOT/'migration/reports/image-benchmark-review.json'
    review=json.loads(report.read_text()) if report.exists() else None
    checks,refs,build,p=collect(review)
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    print(status,[c['check'] for c in checks if not c['passed']],flush=True)
    if args.dry_run or status!='PASSED':return int(status!='PASSED')
    deps=expected_dependencies(build)
    q=dict(sample_id=SAMPLE,kind='image-benchmark-full',status=status,
       implementation=IMPLEMENTATION,implementation_sha256=digest(ROOT/IMPLEMENTATION),
       dependencies=deps,case_ids=[c['case'] for c in p['cases']],case_count=6,
       comparison_mode=COMPARISON,checks=checks,evidence_references=sorted(refs),
       source_commit=review['source_commit'],
       rocm_evidence=next(r for r in load('runs') if r['case']=='original-default')['evidence'],
       cuda_evidence=json.loads((ROOT/'migration/reports/image-I3-benchmark-native.json').read_text())['evidence'],
       environment=build['evidence']+'/backend.observed.json',
       devices=json.loads((ROOT/build['evidence']/'backend.observed.json').read_text())['devices'],
       scope='Four original NPP/OpenCV benchmark operations, six valid/error CLI cases, full independent CPU outputs, 18 real device contracts, actual kernel trace, matched OpenCV 4.12 loaded libraries, original 5090 statistics and documented Gaussian/Canny variants. Linux/gfx1201/ROCm10.1 only; no NPP pixel-exact or cross-device performance claim.')
    sources=[ROOT/name for name in deps if (ROOT/name).is_file()]
    sources += [Path(__file__),report,ROOT/'migration/reports/image-benchmark-cold.json',
       ROOT/'migration/reports/image-benchmark-negative.json']
    e=Experiment('I3',SAMPLE,'composite-qualification',sources=sources)
    write(e.path/'qualification.json',q)
    q.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status=status,checks=checks)))
    write(ROOT/'migration/reports/image-benchmark-qualification.json',q)
    return 0

if __name__=='__main__':raise SystemExit(main())
