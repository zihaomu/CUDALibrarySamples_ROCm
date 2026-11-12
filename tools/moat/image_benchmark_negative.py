#!/usr/bin/env python3
"""Check that benchmark qualification readers reject known false positives."""
import copy,json
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_benchmark_reference import validate
from image_benchmark_native_comparison import native_execution_ok
from image_benchmark_cold import same_build_source_hashes
from image_benchmark_build import dependencies

def main():
    native=json.loads((ROOT/'migration/reports/image-I3-benchmark-native.json').read_text())
    proof=ROOT/native['evidence'];manifest=json.loads((proof/'manifest.json').read_text())
    commands=json.loads((proof/'commands.json').read_text())
    logs=list((proof/'logs').glob('*actual-4096x2048*stdout.log'))
    runs=json.loads((ROOT/'migration/reports/image-benchmark-runs.json').read_text())
    profile=json.loads((ROOT/'migration/rewrite/image-benchmark-profile.json').read_text())
    cases={c['case']:c for c in profile['cases']}
    e=Experiment('I3','OpenCV-benchmark-sealed-reader-counterexamples','CPU-negative',
       sources=[__file__,ROOT/'tools/moat/image_benchmark_reference.py',
         ROOT/'tools/moat/image_benchmark_native_comparison.py',
         ROOT/'tools/moat/image_benchmark_cold.py',
         ROOT/'migration/reports/image-I3-benchmark-native.json',
         ROOT/'migration/reports/image-benchmark-runs.json',
         ROOT/'migration/rewrite/image-benchmark-profile.json'])
    checks=[]
    checks.append(dict(check='actual-native-baseline-accepted',passed=native_execution_ok(native,manifest,commands,proof,logs)))
    for field,bad in [('status','FAILED'),('build_return_code',1),('return_code',137),('collection_return_code',1)]:
      changed=dict(native);changed[field]=bad
      checks.append(dict(check='reject-native-'+field,passed=not native_execution_ok(changed,manifest,commands,proof,logs)))
    changed=copy.deepcopy(commands);changed[4]['return_code']=137
    checks.append(dict(check='reject-native-actual-command-failure',
      passed=not native_execution_ok(native,manifest,changed,proof,logs)))
    missing=cases['missing-input'];invalid=next(r for r in runs if r['case']=='invalid-dimensions')
    swapped=validate(missing,invalid,profile)
    checks.append(dict(check='reject-mismatched-error-CLI-and-diagnostic',passed=swapped['status']=='FAILED'
      and any(not c['passed'] for c in swapped['checks'])))
    expected={str(path.relative_to(ROOT)):digest(path) for path in dependencies()}
    checks.append(dict(check='accept-complete-fixed-dependency-set',passed=same_build_source_hashes(expected,ROOT)))
    changed=dict(expected);changed.pop(next(name for name in changed if name.endswith('benchmark.hip')))
    checks.append(dict(check='reject-trimmed-build-dependency-set',passed=not same_build_source_hashes(changed,ROOT)))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,checks=checks,case_count=len(checks))
    write(e.path/'negative.json',result)
    result['evidence']=e.finish(status if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-benchmark-negative.json',result)
    record('I3','benchmark原生失败伪成功/错误CLI互换/裁剪源码依赖共'+str(len(checks))+'项正反证据：'+status+'。',[result['evidence']])
    print(status,[(c['check'],c['passed']) for c in checks]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
