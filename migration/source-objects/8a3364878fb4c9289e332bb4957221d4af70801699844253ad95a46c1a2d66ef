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
    evidence_commit=review.get('evidence_commit','')
    if (not evidence_commit or subprocess.run(['git','merge-base','--is-ancestor',commit,evidence_commit],cwd=ROOT,capture_output=True).returncode
      or subprocess.run(['git','merge-base','--is-ancestor',evidence_commit,'HEAD'],cwd=ROOT,capture_output=True).returncode):return False
    if not review_identity(review):return False
    if review.get('proof_seals')!={ref:digest(ROOT/ref/'sealed.json') for ref in refs}:return False
    try:
      if any(digest_bytes(subprocess.check_output(['git','show',evidence_commit+':'+ref+'/sealed.json'],cwd=ROOT,stderr=subprocess.DEVNULL))!=sha
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

NATIVE_ALL_ARGV_SHA256='ef11935b499f86441a876a8fd6a6272657a05b9800e8885d7e2ec9e5f65a81e3'
NATIVE_ORIGINAL_ROOT=Path('/home/zihaomu/zihaomu_workspace/cuda_libraray_sample_workspace_migra/CUDALibrarySamples_ROCm')

def native_recipe_ok(commands):
    if len(commands)!=6:return False
    argv=[c['argv'] for c in commands]
    return (digest_bytes(json.dumps(argv,sort_keys=True,separators=(',',':')).encode())==NATIVE_ALL_ARGV_SHA256
      and all(c['cwd']==str(NATIVE_ORIGINAL_ROOT) and c.get('environment_changes',{})=={} for c in commands))

def build_recompute(build,raw_override=None,project_root=ROOT):
    path=Path(raw_override) if raw_override else project_root/build['evidence']
    manifest=json.loads((path/'manifest.json').read_text())
    raw=path if raw_override else project_root/manifest['raw_artifact_dir']
    logical=project_root/manifest['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text())
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=project_root/'build/rocm-sdk-overlay'
    opencv=project_root/build['opencv_prefix']
    flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
      '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201',
      '-std=c++17','-O2','-ffp-contract=off','-D__HIP_PLATFORM_AMD__']
    shared=[str(project_root/'rocm/common/image'/n) for n in ['canny_stages.hip','canny.hip','benchmark.hip']]
    recipe=[[*flags,'-fPIC','-x','hip','-shared',*shared,
      '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(logical/'libimage_benchmark.so')],
      [*flags,'-x','hip','-I'+str(opencv/'include/opencv4'),str(project_root/IMPLEMENTATION),
       '-L'+str(logical),'-limage_benchmark','-Wl,-rpath,'+str(logical),
       '-L'+str(opencv/'lib'),'-Wl,-rpath,'+str(opencv/'lib'),
       '-lopencv_imgproc','-lopencv_core','-L'+str(core/'lib'),
       '-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(logical/'opencvBenchmark')]]
    return (build['status']=='BUILT' and manifest['backend']=='rocm-build'
      and len(commands)==2 and all(c['argv']==argv and c['cwd']==str(project_root)
          and c['return_code']==0 and c.get('environment_changes',{})=={}
          for c,argv in zip(commands,recipe))
      and digest(raw/'libimage_benchmark.so')==build['library_sha256']
      and digest(raw/'opencvBenchmark')==build['binary_sha256'])

def runtime_recompute(runtime,build,raw_override=None,project_root=ROOT):
    path=Path(raw_override) if raw_override else project_root/runtime['evidence']
    manifest=json.loads((path/'manifest.json').read_text())
    raw=path if raw_override else project_root/manifest['raw_artifact_dir']
    logical=project_root/manifest['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text())
    expected=['resolve-real-image-libraries','compile-runtime-contracts','run-actual-device-contracts']
    if ([c['phase'] for c in commands]!=expected or any(c['return_code'] for c in commands)
        or manifest['parent_experiment_id']!=build['experiment_id']):return False
    core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');overlay=project_root/'build/rocm-sdk-overlay'
    lib=project_root/build['library'];binary=project_root/build['binary']
    flags=['hipcc','--rocm-path='+str(overlay),'--hip-path='+str(overlay),
      '--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201',
      '-std=c++17','-O2','-D__HIP_PLATFORM_AMD__']
    recipe=[['ldd',str(binary)],
      [*flags,'-x','hip',str(project_root/'tools/moat/image_benchmark_runtime.cpp'),
       '-L'+str(lib.parent),'-limage_benchmark','-Wl,-rpath,'+str(lib.parent),
       '-L'+str(core/'lib'),'-Wl,-rpath,'+str(core/'lib'),'-lamdhip64','-o',str(logical/'runtime')],
      [str(logical/'runtime')]]
    if any(c['argv']!=argv or c['cwd']!=str(project_root)
       or c.get('environment_changes',{})!={} for c,argv in zip(commands,recipe)):return False
    rows=[line.split('|') for line in (raw/commands[-1]['stdout']).read_text().splitlines()]
    names=['normal','changed-to-zero','restored','default-stream',
           'invalid-rejected-and-output-preserved','destroyed-stream-rejected']
    expected_rows=[[op,name,'1'] for op in ['gauss','resize','color'] for name in names]
    observed=json.loads((raw/'backend.observed.json').read_text())['devices']
    loaded=json.loads((raw/'loaded-libraries.json').read_text())
    return (rows==runtime['rows']==expected_rows and runtime['return_code']==0
        and len(observed)==1 and observed[0]['physical_id']==1
        and loaded['status']=='PASSED' and all(c['passed'] for c in loaded['checks']))

def native_recompute(comparison,default_run,profile,run_raw_override=None,project_root=ROOT,build_override=None):
    native=json.loads((ROOT/'migration/reports/image-I3-benchmark-native.json').read_text())
    nproof=ROOT/native['evidence'];nmanifest=json.loads((nproof/'manifest.json').read_text())
    ncommands=json.loads((nproof/'commands.json').read_text())
    nlogs=list((nproof/'logs').glob('*actual-4096x2048*stdout.log'))
    if not native_execution_ok(native,nmanifest,ncommands,nproof,nlogs) or not native_recipe_ok(ncommands):return False
    rproof=Path(run_raw_override) if run_raw_override else project_root/default_run['evidence']
    rmanifest=json.loads((rproof/'manifest.json').read_text())
    raw=rproof if run_raw_override else project_root/rmanifest['raw_artifact_dir']
    rcommands=json.loads((raw/'commands.json').read_text())
    actual=[c for c in rcommands if c['phase']=='actual-four-operation-original-CLI']
    build=build_override if build_override is not None else json.loads((ROOT/'migration/reports/image-benchmark-build.json').read_text())
    binary=project_root/build['binary'];logical=project_root/rmanifest['raw_artifact_dir']
    if (len(rcommands)!=2 or len(actual)!=1 or actual[0]['return_code']!=0
      or rcommands[0]['phase']!='resolve-real-image-libraries'
      or rcommands[0]['argv']!=['ldd',str(binary)]
      or actual[0]['argv']!=[str(binary),*default_run['arguments']]
      or actual[0]['cwd']!=str(logical/'outputs')
      or any(c.get('environment_changes',{})!={} for c in rcommands)):return False
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

def trace_recompute(trace,build,small_run,raw_override=None,project_root=ROOT):
    path=Path(raw_override) if raw_override else project_root/trace['evidence']
    manifest=json.loads((path/'manifest.json').read_text())
    raw=path if raw_override else project_root/manifest['raw_artifact_dir']
    logical=project_root/manifest['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text())
    if ([c['phase'] for c in commands]!=['resolve-real-image-libraries','profile-complete-four-operation-C++-entry']
      or any(c['return_code'] for c in commands) or manifest['parent_experiment_id']!=build['experiment_id']):return False
    binary=project_root/build['binary'];source=project_root/'NPP/opencvBenchmark/images/CircuitBoard_2048x1024_8u.raw'
    expected=[['ldd',str(binary)],
      ['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(logical/'trace'),
       '--',str(binary),'-i',str(source),'-w','128','-h','96','-n','1']]
    if (any(c['argv']!=argv or c['cwd']!=(str(project_root) if i==0 else str(logical/'outputs'))
       or c.get('environment_changes',{})!={} for i,(c,argv) in enumerate(zip(commands,expected)))):return False
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

def cold_structure_ok(cold):
    expected={'contracts':1,'deps':1,'build':1,'runs':6,'validation':6,'native-comparison':1,
      'runtime':1,'trace':1,'negative':1}
    children=cold['children']
    return (len(children)==19 and collections.Counter(c['kind'] for c in children)==expected
       and len({(c['kind'],c['index']) for c in children})==19
       and len({c['evidence'] for c in children})==19
       and len({c['raw'] for c in children})==19
       and all({c['index'] for c in children if c['kind']==kind}==set(range(count)) for kind,count in expected.items()))

def cold_recipe_ok(commands,clone,commit):
    phases=['fresh-checkout','fixed-commit']+['cold-'+name for name in
      ['image_benchmark_contracts','image_benchmark_deps','bootstrap_sdk','image_benchmark_build',
       'image_benchmark_run','image_benchmark_reference','image_benchmark_native_comparison',
       'image_benchmark_runtime','image_benchmark_trace','image_benchmark_negative']]
    if (len(commands)!=len(phases) or [c['phase'] for c in commands]!=phases
       or any(c['return_code'] for c in commands)
       or commands[0]['argv']!=['git','clone','--shared','--quiet',str(ROOT),str(clone)]
       or commands[0]['cwd']!=str(ROOT)
       or commands[1]['argv']!=['git','checkout','--quiet',commit]
       or any(c['cwd']!=str(clone) for c in commands[1:])):return False
    jobs=[('tools/moat/image_benchmark_contracts.py','cpu'),
      ('tools/moat/image_benchmark_deps.py','host'),('tools/migration/bootstrap_sdk.py','gpu'),
      ('tools/moat/image_benchmark_build.py','gpu'),('tools/moat/image_benchmark_run.py','gpu'),
      ('tools/moat/image_benchmark_reference.py','cpu'),
      ('tools/moat/image_benchmark_native_comparison.py','cpu'),
      ('tools/moat/image_benchmark_runtime.py','gpu'),('tools/moat/image_benchmark_trace.py','gpu'),
      ('tools/moat/image_benchmark_negative.py','cpu')]
    cpu=str(ROOT/'build/image-cpu-venv/bin/python')
    for command,(name,kind) in zip(commands[2:],jobs):
      script=str(clone/name)
      argv=([cpu,script] if kind=='cpu' else ['python3',script] if kind=='host' else
        ['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh','env','ROCR_VISIBLE_DEVICES=3',
         'HIP_VISIBLE_DEVICES=0','python3',script])
      env={'HIP_VISIBLE_DEVICES':'2'} if kind=='gpu' else {}
      if command['argv']!=argv or command.get('environment_changes',{})!=env:return False
    return True

COLD_SOURCE_KEYS={
 'contracts': '''tools/moat/image_benchmark_contracts.py NPP/opencvBenchmark/opencvBenchmark.cpp NPP/opencvBenchmark/images/CircuitBoard_2048x1024_8u.raw tools/moat/experiment.py''',
 'deps': '''tools/moat/image_benchmark_deps.py migration/reports/image-I3-native-OpenCV.json tools/moat/experiment.py''',
 'runs': '''tools/moat/image_benchmark_run.py tools/moat/image_benchmark_identity.py migration/reports/image-I3-native-OpenCV.json migration/rewrite/image-benchmark-profile.json migration/reports/image-benchmark-build.json NPP/opencvBenchmark/images/CircuitBoard_2048x1024_8u.raw tools/moat/experiment.py''',
 'validation': '''tools/moat/image_benchmark_reference.py migration/rewrite/image-benchmark-profile.json migration/reports/image-benchmark-runs.json tools/moat/image_canny_stages_reference.py tools/moat/image_canny_local_research.py tools/moat/experiment.py''',
 'native-comparison': '''tools/moat/image_benchmark_native_comparison.py migration/reports/image-I3-benchmark-native.json migration/reports/image-benchmark-runs.json migration/reports/image-benchmark-validation.json migration/rewrite/image-benchmark-profile.json migration/reports/image-I3-rocm-OpenCV.json NPP/opencvBenchmark/opencvBenchmark.cpp tools/moat/experiment.py''',
 'negative': '''tools/moat/image_benchmark_negative.py tools/moat/image_benchmark_reference.py tools/moat/qualify_image_benchmark.py tools/moat/image_benchmark_native_comparison.py tools/moat/image_benchmark_cold.py migration/reports/image-I3-benchmark-native.json migration/reports/image-I3-rocm-OpenCV.json migration/reports/image-benchmark-build.json migration/reports/image-benchmark-runs.json migration/reports/image-benchmark-validation.json migration/reports/image-benchmark-native-comparison.json migration/reports/image-benchmark-runtime.json migration/reports/image-benchmark-trace.json migration/rewrite/image-benchmark-profile.json tools/moat/experiment.py''',
}
_COLD_IMAGE_SOURCES={
 'rocm/ported/NPP/opencvBenchmark/opencvBenchmark.cpp',
 'NPP/opencvBenchmark/opencvBenchmark.cpp',
 'NPP/opencvBenchmark/images/CircuitBoard_2048x1024_8u.raw',
 'migration/reports/image-I3-rocm-OpenCV.json',
 'migration/reports/image-I3-native-OpenCV.json',
 'rocm/common/image/benchmark.h','rocm/common/image/benchmark.hip',
 'rocm/common/image/canny.h','rocm/common/image/canny.hip',
 'rocm/common/image/canny_stages.h','rocm/common/image/canny_stages.hip',
 'tools/moat/experiment.py',
}
COLD_SOURCE_KEYS['build']=' '.join(sorted(_COLD_IMAGE_SOURCES|{'tools/moat/image_benchmark_build.py'}))
COLD_SOURCE_KEYS['runtime']=' '.join(sorted(_COLD_IMAGE_SOURCES|{
 'tools/moat/image_benchmark_runtime.py','tools/moat/image_benchmark_runtime.cpp',
 'tools/moat/image_benchmark_identity.py'}))
COLD_SOURCE_KEYS['trace']=' '.join(sorted(_COLD_IMAGE_SOURCES|{
 'tools/moat/image_benchmark_trace.py','tools/moat/image_benchmark_identity.py'}))

def cold_source_ok(source,kind,report,generated,commit):
    dependencies=source['dependencies'];objects=source['source_objects']
    if set(dependencies)!=set(COLD_SOURCE_KEYS[kind].split()) or set(dependencies)!=set(objects):return False
    for name,sha in dependencies.items():
      object_name=objects[name]
      if (object_name!='migration/source-objects/'+sha
        or not (ROOT/object_name).is_file() or digest(ROOT/object_name)!=sha):return False
      if name in generated:
        if json.loads((ROOT/object_name).read_text())!=generated[name]:return False
      else:
        try:
          actual=digest_bytes(subprocess.check_output(
            ['git','show',commit+':'+name],cwd=ROOT,stderr=subprocess.DEVNULL))
        except (OSError,subprocess.CalledProcessError):return False
        if sha!=actual:return False
    if kind=='build' and dependencies!=report['dependencies']|{
      'tools/moat/image_benchmark_build.py':dependencies['tools/moat/image_benchmark_build.py'],
      'tools/moat/experiment.py':dependencies['tools/moat/experiment.py']}:return False
    return True

def cold_run_ok(folder,manifest,report,case,build,project_root,profile):
    logical=project_root/manifest['raw_artifact_dir'];binary=project_root/build['binary']
    commands=json.loads((folder/'commands.json').read_text())
    expected_argv=[['ldd',str(binary)],[str(binary),*case['arguments']]]
    expected_cwd=[str(project_root),str(logical/'outputs')]
    loaded=json.loads((folder/'loaded-libraries.json').read_text())
    native_receipt=json.loads((ROOT/'migration/reports/image-I3-native-OpenCV.json').read_text())['receipt']['files']
    loaded_checks={x['check']:x for x in loaded['checks']}
    if (len(commands)!=2 or [x['phase'] for x in commands]!=[
      'resolve-real-image-libraries','actual-four-operation-original-CLI']
      or any(x['argv']!=argv or x['cwd']!=cwd or x.get('environment_changes',{})!={}
             for x,argv,cwd in zip(commands,expected_argv,expected_cwd))
      or commands[0]['return_code']!=0 or commands[1]['return_code']!=case['expected_return_code']
      or report['return_code']!=case['expected_return_code']
      or report['arguments']!=case['arguments'] or report['build_evidence']!=build['evidence']
      or digest(folder/'images'/Path(profile['image']).name)!=profile['image_sha256']
      or not (folder/commands[1]['stdout']).read_text().startswith(case['stdout_starts'])
      or not (folder/commands[1]['stderr']).read_text().startswith(case['stderr_starts'])
      or loaded['status']!='PASSED' or loaded['binary']!=str(binary)
      or loaded['library']!=str(project_root/build['library'])
      or loaded['opencv_prefix']!=str(project_root/build['opencv_prefix'])
      or loaded_checks['actual-loaded-libimage_benchmark.so']['sha256']!=build['library_sha256']
      or loaded_checks['actual-loaded-libopencv_core.so.412']['sha256']!=native_receipt['lib/libopencv_core.so.412']['sha256']
      or loaded_checks['actual-loaded-libopencv_imgproc.so.412']['sha256']!=native_receipt['lib/libopencv_imgproc.so.412']['sha256']):return False
    return True

def cold_recompute(cold,profile,runs,valid):
    if (cold['status']!='PASSED' or cold['return_code']!=0 or any(not c['passed'] for c in cold['checks'])
      or not cold_structure_ok(cold)):return False
    path=ROOT/cold['evidence'];outer=json.loads((path/'manifest.json').read_text());raw=ROOT/outer['raw_artifact_dir']
    clone=Path(cold['clone'])
    if (clone.name!='src' or clone.parent.parent!=ROOT.parent
      or not clone.parent.name.startswith('image-benchmark-cold-')
      or outer['backend']!='host-cold-replay' or outer['experiment_outcome']!='PASSED'):return False
    commands=json.loads((raw/'commands.json').read_text())
    if not cold_recipe_ok(commands,clone,cold['source_commit']):return False
    expected={'contracts':1,'deps':1,'build':1,'runs':6,'validation':6,'native-comparison':1,
      'runtime':1,'trace':1,'negative':1}
    children=cold['children']
    by={kind:[c for c in children if c['kind']==kind] for kind in expected}
    outcomes={'contracts':'OBSERVED','deps':'PASSED','build':'EXECUTED','validation':'PASSED',
      'native-comparison':'PASSED','runtime':'PASSED','trace':'PASSED','negative':'PASSED'}
    def child_report(child):
      typ='native' if child['kind']=='native-comparison' else child['kind']
      report=json.loads((raw/child['raw']/MEMBERS[typ]).read_text());report['evidence']=child['evidence']
      return report
    cold_build_row=child_report(by['build'][0]);cold_build=cold_build_row['experiment_id']
    generated={
      'migration/reports/image-I3-rocm-OpenCV.json':child_report(by['deps'][0]),
      'migration/reports/image-benchmark-build.json':cold_build_row,
      'migration/reports/image-benchmark-runs.json':[child_report(c) for c in by['runs']],
      'migration/reports/image-benchmark-validation.json':[child_report(c) for c in by['validation']],
      'migration/reports/image-benchmark-native-comparison.json':child_report(by['native-comparison'][0]),
      'migration/reports/image-benchmark-runtime.json':child_report(by['runtime'][0]),
      'migration/reports/image-benchmark-trace.json':child_report(by['trace'][0]),
    }
    case_ids={c['case'] for c in profile['cases']}
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
      if not cold_source_ok(source,kind,report,generated,cold['source_commit']):return False
      if (source['commit']!=cold['source_commit'] or manifest['experiment_id']!=Path(child['evidence']).name
        or report['evidence']!=child['evidence'] or manifest['backend']!=BACKENDS[typ]
        or report['status']!={'contracts':'FROZEN','deps':'READY','build':'BUILT','runs':'EXECUTED',
           'validation':'PASSED','native-comparison':'PASSED','runtime':'PASSED','trace':'PASSED',
           'negative':'PASSED'}[kind]
        or any(not check['passed'] for check in report.get('checks',[]))):return False
      expected_outcome=outcomes.get(kind,'EXPECTED_REJECTION' if next(
        (c['expected_return_code'] for c in profile['cases'] if c['case']==report.get('case')),0) else 'EXECUTED')
      if manifest['experiment_outcome']!=expected_outcome:return False
      if kind in {'runs','runtime','trace'}:
        observed=json.loads((folder/'backend.observed.json').read_text())['devices']
        if len(observed)!=1 or observed[0]['physical_id']!=1:return False
      if kind=='runs':
        current=next(r for r in runs if r['case']==report['case'])
        case=next(c for c in profile['cases'] if c['case']==report['case'])
        if not cold_run_ok(folder,manifest,report,case,cold_build_row,clone,profile):return False
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
      if kind=='contracts' and json.loads((folder/'profile.json').read_text())!=profile:return False
    if not build_recompute(cold_build_row,raw/by['build'][0]['raw'],clone):return False
    runtime_child=by['runtime'][0];runtime_row=child_report(runtime_child)
    if not runtime_recompute(runtime_row,cold_build_row,raw/runtime_child['raw'],clone):return False
    trace_child=by['trace'][0];trace_row=child_report(trace_child)
    if not trace_recompute(trace_row,cold_build_row,child_report(run_cases['small']),
       raw/trace_child['raw'],clone):return False
    native_child=by['native-comparison'][0];native_row=child_report(native_child)
    if not native_recompute(native_row,child_report(run_cases['original-default']),profile,
       raw/run_cases['original-default']['raw'],clone,cold_build_row):return False
    negative_row=child_report(by['negative'][0])
    current_negative=json.loads((ROOT/'migration/reports/image-benchmark-negative.json').read_text())
    if (negative_row['status']!='PASSED' or negative_row['case_count']!=31
      or negative_row['checks']!=current_negative['checks']):return False
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
       and build['build_recipe_sha256']==digest(ROOT/'tools/moat/image_benchmark_build.py')
       and build_recompute(build))
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
    gate('thirty-one-native-CLI-and-closure-counterexamples',evidence('negative',[negative])
       and negative['status']=='PASSED' and negative['case_count']==len(negative['checks'])==31
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
