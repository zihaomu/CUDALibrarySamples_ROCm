#!/usr/bin/env python3
"""Check that benchmark qualification readers reject known false positives."""
import copy,json,re,shutil,subprocess,tempfile
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_benchmark_reference import validate
from image_benchmark_native_comparison import native_execution_ok
from image_benchmark_cold import same_build_source_hashes
from image_benchmark_build import dependencies
from qualify_image_benchmark import cpu_recompute,runtime_recompute,trace_recompute,native_recompute,cold_structure_ok,cold_recipe_ok,native_recipe_ok,cold_source_ok,cold_run_ok,loaded_recompute

def fake_loader(folder):
    commands=json.loads((folder/'commands.json').read_text())
    path=folder/next(c['stdout'] for c in commands if c['phase']=='resolve-real-image-libraries')
    original=path.read_text();changed,count=re.subn(r'(libopencv_core\.so\.412\s*=>\s*)\S+',
      r'\1/tmp/fake-opencv.so',original,count=1)
    if count!=1:raise ValueError('real OpenCV loader line required')
    path.write_text(changed)
    return path,original

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
         ROOT/'tools/moat/qualify_image_benchmark.py',
         ROOT/'tools/moat/image_benchmark_native_comparison.py',
         ROOT/'tools/moat/image_benchmark_cold.py',
         ROOT/'migration/reports/image-I3-benchmark-native.json',
         ROOT/'migration/reports/image-benchmark-runs.json',
         ROOT/'migration/reports/image-benchmark-validation.json',
         ROOT/'migration/reports/image-benchmark-native-comparison.json',
         ROOT/'migration/reports/image-benchmark-runtime.json',
         ROOT/'migration/reports/image-benchmark-trace.json',
         ROOT/'migration/reports/image-benchmark-build.json',
         ROOT/'migration/reports/image-I3-rocm-OpenCV.json',
         ROOT/'migration/rewrite/image-benchmark-profile.json'])
    checks=[]
    checks.append(dict(check='actual-native-baseline-accepted',passed=native_execution_ok(native,manifest,commands,proof,logs)))
    for field,bad in [('status','FAILED'),('build_return_code',1),('return_code',137),('collection_return_code',1)]:
      changed=dict(native);changed[field]=bad
      checks.append(dict(check='reject-native-'+field,passed=not native_execution_ok(changed,manifest,commands,proof,logs)))
    changed=copy.deepcopy(commands);changed[4]['return_code']=137
    checks.append(dict(check='reject-native-actual-command-failure',
      passed=not native_execution_ok(native,manifest,changed,proof,logs)))
    checks.append(dict(check='actual-native-execution-recipe',passed=native_recipe_ok(commands)))
    changed=copy.deepcopy(commands);changed[4]['argv']=['echo','replayed-stdout']
    checks.append(dict(check='reject-native-echo-replay',passed=not native_recipe_ok(changed)))
    changed=copy.deepcopy(commands);changed[3]['argv']=['ssh','nvidia-5090x2','true']
    checks.append(dict(check='reject-native-compile-replaced-with-true',passed=not native_recipe_ok(changed)))
    missing=cases['missing-input'];invalid=next(r for r in runs if r['case']=='invalid-dimensions')
    swapped=validate(missing,invalid,profile)
    checks.append(dict(check='reject-mismatched-error-CLI-and-diagnostic',passed=swapped['status']=='FAILED'
      and any(not c['passed'] for c in swapped['checks'])))
    expected={str(path.relative_to(ROOT)):digest(path) for path in dependencies()}
    checks.append(dict(check='accept-complete-fixed-dependency-set',passed=same_build_source_hashes(expected,ROOT)))
    changed=dict(expected);changed.pop(next(name for name in changed if name.endswith('benchmark.hip')))
    checks.append(dict(check='reject-trimmed-build-dependency-set',passed=not same_build_source_hashes(changed,ROOT)))
    validations=json.loads((ROOT/'migration/reports/image-benchmark-validation.json').read_text())
    checks.append(dict(check='accept-current-full-CPU-recomputation',passed=cpu_recompute(profile,runs,validations)))
    bad=copy.deepcopy(validations);next(r for r in bad if r['case']=='small')['metrics']['gauss.raw']['project']['max_abs']=255
    checks.append(dict(check='reject-forged-sealed-CPU-metrics',passed=not cpu_recompute(profile,runs,bad)))
    build=json.loads((ROOT/'migration/reports/image-benchmark-build.json').read_text())
    build_source=json.loads((ROOT/build['evidence']/'source.json').read_text())
    dep=json.loads((ROOT/'migration/reports/image-I3-rocm-OpenCV.json').read_text())
    generated={'migration/reports/image-I3-rocm-OpenCV.json':dep}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    checks.append(dict(check='accept-fixed-build-source-and-generated-dependency',
      passed=cold_source_ok(build_source,'build',build,generated,commit)))
    bad=copy.deepcopy(build_source);key='rocm/common/image/benchmark.hip'
    bad['dependencies']['rocm/common/image/benchmark.xip']=bad['dependencies'].pop(key)
    bad['source_objects']['rocm/common/image/benchmark.xip']=bad['source_objects'].pop(key)
    checks.append(dict(check='reject-nonexistent-cold-build-dependency-name',
      passed=not cold_source_ok(bad,'build',build,generated,commit)))
    bad=copy.deepcopy(build_source);other='rocm/common/image/canny.hip'
    bad['dependencies'][key]=bad['dependencies'][other]
    bad['source_objects'][key]=bad['source_objects'][other]
    checks.append(dict(check='reject-cold-build-dependency-wrong-CAS',
      passed=not cold_source_ok(bad,'build',build,generated,commit)))
    small=next(r for r in runs if r['case']=='small');small_case=cases['small']
    small_folder=ROOT/small['evidence'];small_manifest=json.loads((small_folder/'manifest.json').read_text())
    checks.append(dict(check='accept-actual-cold-run-command-recipe',
      passed=cold_run_ok(small_folder,small_manifest,small,small_case,build,ROOT,profile)))
    with tempfile.TemporaryDirectory(prefix='benchmark-cold-run-negative-') as temporary:
      copied=Path(temporary)/'run';shutil.copytree(small_folder,copied)
      loader_file,loader_original=fake_loader(copied)
      checks.append(dict(check='reject-main-run-forged-ldd-stdout',passed=not loaded_recompute(copied,build)))
      checks.append(dict(check='reject-cold-run-forged-ldd-stdout',
        passed=not cold_run_ok(copied,small_manifest,small,small_case,build,ROOT,profile)))
      loader_file.write_text(loader_original)
      command_file=copied/'commands.json';bad_commands=json.loads(command_file.read_text())
      bad_commands[-1]['argv'][0]=bad_commands[-1]['argv'][0]+'X';write(command_file,bad_commands)
      checks.append(dict(check='reject-cold-run-nonexistent-binary-command',
        passed=not cold_run_ok(copied,small_manifest,small,small_case,build,ROOT,profile)))
    runtime=json.loads((ROOT/'migration/reports/image-benchmark-runtime.json').read_text())
    checks.append(dict(check='accept-actual-runtime-stdout',passed=runtime_recompute(runtime,build)))
    bad=copy.deepcopy(runtime);bad['rows'][0][2]='0'
    checks.append(dict(check='reject-forged-runtime-rows',passed=not runtime_recompute(bad,build)))
    runtime_manifest=json.loads((ROOT/runtime['evidence']/'manifest.json').read_text())
    with tempfile.TemporaryDirectory(prefix='benchmark-runtime-command-negative-') as temporary:
      copied=Path(temporary)/'runtime';shutil.copytree(ROOT/runtime_manifest['raw_artifact_dir'],copied)
      loader_file,loader_original=fake_loader(copied)
      checks.append(dict(check='reject-runtime-forged-ldd-stdout',
        passed=not runtime_recompute(runtime,build,copied)))
      loader_file.write_text(loader_original)
      command_file=copied/'commands.json';bad_commands=json.loads(command_file.read_text())
      bad_commands[-1]['argv']=['echo','fabricated-runtime'];write(command_file,bad_commands)
      checks.append(dict(check='reject-runtime-echo-replay',
        passed=not runtime_recompute(runtime,build,copied)))
    trace=json.loads((ROOT/'migration/reports/image-benchmark-trace.json').read_text())
    small=next(r for r in runs if r['case']=='small')
    checks.append(dict(check='accept-actual-trace-CSV-and-PCI',passed=trace_recompute(trace,build,small)))
    bad=copy.deepcopy(trace);bad['counts']['gauss5']+=1
    checks.append(dict(check='reject-forged-trace-count',passed=not trace_recompute(bad,build,small)))
    trace_manifest=json.loads((ROOT/trace['evidence']/'manifest.json').read_text())
    with tempfile.TemporaryDirectory(prefix='benchmark-trace-command-negative-') as temporary:
      copied=Path(temporary)/'trace';shutil.copytree(ROOT/trace_manifest['raw_artifact_dir'],copied)
      loader_file,loader_original=fake_loader(copied)
      checks.append(dict(check='reject-trace-forged-ldd-stdout',
        passed=not trace_recompute(trace,build,small,copied)))
      loader_file.write_text(loader_original)
      command_file=copied/'commands.json';bad_commands=json.loads(command_file.read_text())
      bad_commands[-1]['argv']=['echo','fabricated-trace'];write(command_file,bad_commands)
      checks.append(dict(check='reject-trace-echo-replay',
        passed=not trace_recompute(trace,build,small,copied)))
    comparison=json.loads((ROOT/'migration/reports/image-benchmark-native-comparison.json').read_text())
    default=next(r for r in runs if r['case']=='original-default')
    checks.append(dict(check='accept-native-stdout-recomputation',passed=native_recompute(comparison,default,profile)))
    bad=copy.deepcopy(comparison);bad['cuda']['rows']['Gaussian 5x5']['opencv_mean_abs']=0.0
    checks.append(dict(check='reject-forged-native-statistics',passed=not native_recompute(bad,default,profile)))
    groups={'contracts':1,'deps':1,'build':1,'runs':6,'validation':6,
            'native-comparison':1,'runtime':1,'trace':1,'negative':1}
    synthetic={'children':[dict(kind=kind,index=i,evidence=f'fixture/{kind}/{i}',raw=f'child-evidence/{kind}/{i}')
                           for kind,count in groups.items() for i in range(count)]}
    checks.append(dict(check='accept-complete-cold-child-identity-matrix',passed=cold_structure_ok(synthetic)))
    bad=copy.deepcopy(synthetic);children=[c for c in bad['children'] if c['kind']=='runs']
    children[1]['evidence']=children[0]['evidence'];children[1]['raw']=children[0]['raw']
    checks.append(dict(check='reject-duplicated-cold-child',passed=not cold_structure_ok(bad)))
    clone=ROOT.parent/'image-benchmark-cold-fixture/src';commit='fixture-source-commit'
    recipe=[dict(phase='fresh-checkout',argv=['git','clone','--shared','--quiet',str(ROOT),str(clone)],
                 cwd=str(ROOT),return_code=0),
            dict(phase='fixed-commit',argv=['git','checkout','--quiet',commit],cwd=str(clone),return_code=0)]
    jobs=[('image_benchmark_contracts','cpu'),('image_benchmark_deps','host'),('bootstrap_sdk','gpu'),
          ('image_benchmark_build','gpu'),('image_benchmark_run','gpu'),('image_benchmark_reference','cpu'),
          ('image_benchmark_native_comparison','cpu'),('image_benchmark_runtime','gpu'),
          ('image_benchmark_trace','gpu'),('image_benchmark_negative','cpu')]
    for name,kind in jobs:
      file=('tools/migration/' if name=='bootstrap_sdk' else 'tools/moat/')+name+'.py'
      script=str(clone/file)
      argv=([str(ROOT/'build/image-cpu-venv/bin/python'),script] if kind=='cpu'
            else ['python3',script] if kind=='host'
            else ['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh','env',
                  'ROCR_VISIBLE_DEVICES=3','HIP_VISIBLE_DEVICES=0','python3',script])
      item=dict(phase='cold-'+name,argv=argv,cwd=str(clone),return_code=0)
      if kind=='gpu':item['environment_changes']={'HIP_VISIBLE_DEVICES':'2'}
      recipe.append(item)
    checks.append(dict(check='accept-exact-ten-job-cold-recipe',passed=cold_recipe_ok(recipe,clone,commit)))
    bad=copy.deepcopy(recipe);bad[5]['argv']=['/bin/true']
    checks.append(dict(check='reject-cold-build-replaced-with-true',passed=not cold_recipe_ok(bad,clone,commit)))
    status='PASSED' if all(c['passed'] for c in checks) else 'FAILED'
    result=dict(status=status,checks=checks,case_count=len(checks))
    write(e.path/'negative.json',result)
    result['evidence']=e.finish(status if status=='PASSED' else 'SELF_TEST_FAILED',dict(status=status,checks=checks))
    write(ROOT/'migration/reports/image-benchmark-negative.json',result)
    record('I3','benchmark原生/错误CLI/依赖及CPU/runtime/trace/cold配对篡改共'+str(len(checks))+'项正反证据：'+status+'。',[result['evidence']])
    print(status,[(c['check'],c['passed']) for c in checks]);return int(status!='PASSED')

if __name__=='__main__':raise SystemExit(main())
