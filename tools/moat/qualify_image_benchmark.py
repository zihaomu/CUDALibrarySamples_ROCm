#!/usr/bin/env python3
"""Issue a composite qualification for the complete four-operation benchmark."""
import argparse,collections,json,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest,git
from audit import check as audit
from image_benchmark_build import dependencies

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

def reviews_ok(review,cold):
    if review.get('verdict')!='APPROVED' or review.get('source_commit')!=cold['source_commit']:return False
    reviewers=review.get('reviewers',[])
    if (len(reviewers)!=3 or {r['scope'] for r in reviewers}!={'original-contract','evidence-closure','HIP-algorithm'}
       or any(r['verdict']!='APPROVED' for r in reviewers)
       or len({r['reviewer_id'] for r in reviewers})!=3):return False
    commit=review['source_commit']
    if subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,capture_output=True).returncode:return False
    source_names=[str(p.relative_to(ROOT)) for p in dependencies() if 'image-I3-rocm-OpenCV.json' not in str(p)]
    source_names += ['migration/rewrite/image-benchmark-profile.json',
       'tools/moat/image_benchmark_identity.py','tools/moat/image_benchmark_run.py',
       'tools/moat/image_benchmark_reference.py','tools/moat/image_benchmark_native_comparison.py',
       'tools/moat/image_benchmark_runtime.cpp','tools/moat/image_benchmark_runtime.py',
       'tools/moat/image_benchmark_trace.py','tools/moat/image_benchmark_cold.py',
       'tools/moat/image_benchmark_negative.py','tools/moat/qualify_image_benchmark.py',
       'tools/moat/publish_image_benchmark.py']
    try:return all(digest(ROOT/name)==digest_bytes(subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT,stderr=subprocess.DEVNULL)) for name in set(source_names))
    except (OSError,subprocess.CalledProcessError):return False

def digest_bytes(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()

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
    gate('six-independent-full-products-and-error-diagnostics',len(valid)==6
       and {r['case'] for r in valid}==set(case_ids) and evidence('validation',valid)
       and all(r['status']=='PASSED' and r['checks'] and all(c['passed'] for c in r['checks'])
       for r in valid))
    native=data['native'];refs.add(json.loads((ROOT/'migration/reports/image-I3-benchmark-native.json').read_text())['evidence'])
    refs.add(json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text())['evidence'])
    gate('real-unmodified-5090-four-operation-comparison',evidence('native',[native])
       and native['status']=='PASSED' and all(c['passed'] for c in native['checks'])
       and native['rocm_evidence']==by_case['original-default']['evidence'])
    runtime=data['runtime']
    gate('eighteen-actual-device-memory-and-stream-contracts',evidence('runtime',[runtime])
       and runtime['status']=='PASSED' and len(runtime['rows'])==18 and all(r[2]=='1' for r in runtime['rows'])
       and all(c['passed'] for c in runtime['checks']))
    trace=data['trace']
    gate('four-GPU-operation-and-Canny-real-kernel-trace',evidence('trace',[trace])
       and trace['status']=='PASSED' and all(trace['counts'].get(n,0)>=1 for n in
          ['gauss5','sobel','suppress','local_threshold','resize_half','rgb_gray'])
       and all(c['passed'] for c in trace['checks']))
    negative=data['negative']
    gate('nine-native-CLI-and-closure-counterexamples',evidence('negative',[negative])
       and negative['status']=='PASSED' and negative['case_count']==len(negative['checks'])==9
       and all(c['passed'] for c in negative['checks']))
    expected={'contracts':1,'deps':1,'build':1,'runs':6,'validation':6,'native-comparison':1,
       'runtime':1,'trace':1,'negative':1}
    gate('fixed-commit-clean-ten-job-nineteen-child-replay',evidence('cold',[cold])
       and cold['status']=='PASSED' and cold['return_code']==0
       and len(cold['children'])==19
       and collections.Counter(c['kind'] for c in cold['children'])==expected
       and all(c['passed'] for c in cold['checks'])
       and cold['source_commit']==review.get('source_commit') if review else False)
    # Check every copied full child against its own seal, including files omitted from Git's compact archive.
    childgood=True
    if cold['status']=='PASSED':
      manifest=json.loads((ROOT/cold['evidence']/'manifest.json').read_text())
      full=ROOT/manifest['raw_artifact_dir']
      for child in cold['children']:
        path=full/child['raw'];seal=json.loads((path/'child-seal.json').read_text())['files']
        if any(not (path/name).is_file() or (path/name).stat().st_size!=v['bytes']
          or digest(path/name)!=v['sha256'] for name,v in seal.items()):childgood=False;break
    gate('nineteen-complete-cold-child-seals',childgood)
    gate('three-independent-fixed-source-reviews',reviews_ok(review,cold) if review else False)
    return checks,refs,build,p

def main():
    a=argparse.ArgumentParser();a.add_argument('--dry-run',action='store_true');args=a.parse_args()
    report=ROOT/'migration/reports/image-benchmark-review.json'
    review=json.loads(report.read_text()) if report.exists() else None
    checks,refs,build,p=collect(review)
    status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED'
    print(status,[c['check'] for c in checks if not c['passed']],flush=True)
    if args.dry_run or status!='PASSED':return int(status!='PASSED')
    deps=dict(build['dependencies']);deps.update({
      'migration/rewrite/image-benchmark-profile.json':digest(ROOT/'migration/rewrite/image-benchmark-profile.json'),
      'tools/moat/image_benchmark_reference.py':digest(ROOT/'tools/moat/image_benchmark_reference.py'),
      'tools/moat/image_benchmark_native_comparison.py':digest(ROOT/'tools/moat/image_benchmark_native_comparison.py'),
      'tools/moat/image_benchmark_identity.py':digest(ROOT/'tools/moat/image_benchmark_identity.py'),
      'tools/moat/image_benchmark_cold.py':digest(ROOT/'tools/moat/image_benchmark_cold.py')})
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
