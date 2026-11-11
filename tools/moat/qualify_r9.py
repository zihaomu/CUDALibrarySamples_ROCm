#!/usr/bin/env python3
"""Issue scoped qualifications only from complete, immutable R9 proofs."""
import argparse,json,subprocess,functools,struct
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from audit import check as audit
from qualification_common import fixture
from helper_reference import validate as helper_cpu
from crc_benchmark_reference import validate as crc_cpu

TRUSTED_COMMIT=None

def load(name):return json.loads((ROOT/'migration/reports'/name).read_text())
@functools.lru_cache(maxsize=None)
def sealed(path,required=()):
 directory=ROOT/path;seal=json.loads((directory/'sealed.json').read_text())['files']
 if TRUSTED_COMMIT and (directory/'sealed.json').read_bytes()!=subprocess.check_output(['git','show',TRUSTED_COMMIT+':'+str(Path(path)/'sealed.json')],cwd=ROOT):raise ValueError('seal differs from reviewed commit '+path)
 if not set(['source.json','manifest.json','validation.json',*required])<=set(seal) or audit(directory):raise ValueError('evidence seal/mandatory members '+str(path))
 return directory,json.loads((directory/'manifest.json').read_text()),json.loads((directory/'source.json').read_text())
def current(path,names):
 directory,meta,source=sealed(path)
 for name in names:
  if source['dependencies'].get(name)!=digest(ROOT/name):raise ValueError('stale evidence dependency '+name)
 return directory,meta
def review_ok(review,sources):
 if review.get('verdict')!='APPROVED' or not review.get('reviewers') or any(r.get('verdict')!='APPROVED' for r in review['reviewers']):return False
 commit=review['source_commit']
 for name in sources:
  try:data=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT,stderr=subprocess.DEVNULL)
  except subprocess.CalledProcessError:return False
  import hashlib
  if hashlib.sha256(data).hexdigest()!=digest(ROOT/name):return False
 return True

def helpers(profile,review):
 global TRUSTED_COMMIT
 TRUSTED_COMMIT=review['source_commit']
 build=load('rewrite-R9-helper-build.json');native=load('rewrite-R9-helper-native-build.json');rocm=load('rewrite-R9-helper-rocm.json');cuda=load('rewrite-R9-helper-cuda.json');negative=load('rewrite-R9-helper-negative.json');runtime=load('rewrite-R9-helper-runtime.json');originals=load('rewrite-R9-helper-originals.json');checks=[];refs=set()
 def gate(name,fn):
  try:ok=bool(fn())
  except (OSError,ValueError,KeyError,TypeError,StopIteration,AssertionError,subprocess.CalledProcessError):ok=False
  checks.append(dict(check=name,passed=ok));return ok
 expected={str(p.relative_to(ROOT)) for p in (ROOT/'rocm/adapters/helpers').glob('*')}|{p['implementation'] for p in json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers']}
 sources=sorted(expected|{'tools/moat/build_helpers.py','tools/moat/run_helpers.py','tools/moat/cuda_helpers.py','tools/moat/cuda_helper_originals.py','tools/moat/helper_reference.py','tools/moat/helper_fixtures.py','tools/moat/helper_negative.py','tools/moat/helper_runtime.py','tools/moat/qualify_r9.py','migration/rewrite/helpers-benchmark.json'})
 gate('frozen-independent-source-review',lambda:review_ok(review,sources));gate('nonempty-five-case-contract',lambda:len(profile['cases'])==5 and len(set(profile['cases']))==5)
 def build_ok():
  directory,meta,_=sealed(build['evidence'],('build-result.json','compiled-dependencies.json'));record=json.loads((directory/'build-result.json').read_text())
  return meta['experiment_id']==build['experiment_id'] and record=={k:v for k,v in build.items() if k!='evidence'} and build['status']=='BUILT' and set(build['dependencies'])==expected and all(digest(ROOT/n)==h for n,h in build['dependencies'].items()) and build['build_recipe_sha256']==digest(ROOT/'tools/moat/build_helpers.py') and digest(ROOT/build['shared_library'])==build['shared_library_sha256']
 gate('sealed-complete-current-build-and-library',build_ok);refs.add(build['evidence']);gate('original-source-identity',lambda:digest(ROOT/profile['source'])==profile['original_sha256'])
 binary=next(b for b in build['binaries'] if b['sample_id']==profile['sample_id']);gate('actual-language-binary',lambda:digest(ROOT/binary['binary'])==binary['binary_sha256'] and digest(ROOT/profile['implementation'])==binary['implementation_sha256'])
 def native_build_ok():
  d,m,_=sealed(native['evidence'],('build-result.json','sdk-identity.json','binary-identities.json'));record=json.loads((d/'build-result.json').read_text());sdk=json.loads((d/'sdk-identity.json').read_text());return record=={k:v for k,v in native.items() if k!='evidence'} and sdk['library']['sha256']==native['library_sha256'] and set(native['binary_sha256'])=={'dense_matrix_helpers','sparse_matrix_helpers','batch_sparse_matrix_helpers'}
 gate('sealed-native-cuDSS-build',native_build_ok);refs.add(native['evidence'])
 for case in profile['cases']:
  root=ROOT/'tests/fixtures/rewrite-helpers'/profile['language']/profile['kind']/case;mh=digest(root/'manifest.json');comparison=profile['sample_id']+'/'+case+'/'+mh
  for backend,rows in [('rocm',rocm),('cuda',cuda)]:
   matches=[r for r in rows if r['sample_id']==profile['sample_id'] and r['case']==case]
   gate(backend+'/'+case+'/unique-required-entry',lambda:len(matches)==1)
   if len(matches)!=1:continue
   r=matches[0];refs.add(r['evidence'])
   def case_ok():
    d,m,_=sealed(r['evidence'],('case-result.json',));record=json.loads((d/'case-result.json').read_text());raw=ROOT/m['raw_artifact_dir'];commands=json.loads((d/'commands.json').read_text());v=json.loads((d/'validation.json').read_text());data=fixture(raw/'inputs',mh,kind='matrix-helpers');proof=helper_cpu(raw/'inputs',raw/'outputs');source=json.loads((d/'source.json').read_text())['dependencies']
    if record!={k:v for k,v in r.items() if k!='evidence'} or m['experiment_id']!=r['experiment_id'] or m['sample_id']!=profile['sample_id'] or m['case_id']!=case or m['comparison_id']!=comparison or m['experiment_outcome']!='PASSED' or r['status']!='PASSED' or r['return_code']!=0 or r['input_manifest_sha256']!=mh or not proof['checks'] or proof!=v or proof['checks']!=r['checks']:return False
    if (ROOT/r['output']).resolve()!=(raw/'outputs').resolve() or (ROOT/r['input_snapshot']).resolve()!=(raw/'inputs').resolve() or source.get('tools/moat/helper_reference.py')!=digest(ROOT/'tools/moat/helper_reference.py') or source.get('tools/moat/'+('run_helpers.py' if backend=='rocm' else 'cuda_helpers.py'))!=digest(ROOT/'tools/moat'/('run_helpers.py' if backend=='rocm' else 'cuda_helpers.py')):return False
    if backend=='rocm':
     c=commands[0];observed=json.loads((d/'backend.observed.json').read_text());return r['build']==build and m['parent_experiment_id']==build['experiment_id'] and c['argv']==[str(ROOT/binary['binary'])] and c['environment_changes']['REWRITE_INPUT']==str(raw/'inputs') and c['environment_changes']['REWRITE_OUTPUT']==str(raw/'outputs') and observed['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and observed['rocm_release']=='10.1.0' and bool(observed['devices']) and all(x['physical_id']!=3 for x in observed['devices'])
    ident=json.loads((raw/'outputs/native-binary.json').read_text());return r['build']==native and m['parent_experiment_id']==native['experiment_id'] and ident==dict(path=native['remote']+'/'+profile['kind'],sha256=native['binary_sha256'][profile['kind']]) and any(c['phase']=='real-native-helper-entry' and ident['sha256'] in c['argv'][-1] and str(native['remote']+'/inputs/'+profile['language']+'/'+profile['kind']+'/'+case) in c['argv'][-1] for c in commands)
   gate(backend+'/'+case+'/sealed-current-input-output-CPU-and-command',case_ok)
 faults=[r for r in negative['checks'] if r['sample_id']==profile['sample_id']];required_faults={'metadata','device-bytes','lifetime'}|({'shape-alias'} if profile['kind']=='batch_sparse_matrix_helpers' else set())
 gate('complete-distinct-targeted-faults',lambda:len(faults)==len(required_faults) and {r['fault'] for r in faults}==required_faults)
 for r in faults:
  def fault_ok(r=r):
   d,m=current(r['evidence'],['tools/moat/helper_reference.py','tools/moat/helper_negative.py']);v=json.loads((d/'rejection.json').read_text());parent=next(x for x in rocm if x['sample_id']==profile['sample_id'] and x['case']=='original');return r['passed'] and bool(r['rejected_checks']) and r['rejected_checks']==v['rejected_checks'] and v['status']=='PASSED' and m['sample_id']==profile['sample_id'] and m['case_id']==r['fault'] and m['parent_experiment_id']==parent['experiment_id'] and m['comparison_id']==parent['comparison_id']
  refs.add(r['evidence']);gate('fault/'+r['fault'],fault_ok)
 matches=[r for r in runtime['entries'] if r['sample_id']==profile['sample_id']]
 def invalid_entry_ok():
  if len(matches)!=1:return False
  r=matches[0];d,m=current(r['evidence'],['tools/moat/helper_runtime.py']);cs=json.loads((d/'commands.json').read_text());return r['passed'] and r['return_code']!=0 and m['sample_id']==profile['sample_id'] and m['parent_experiment_id']==build['experiment_id'] and m['experiment_outcome']=='EXPECTED_REJECTION' and len(cs)==1 and cs[0]['argv']==[str(ROOT/binary['binary'])] and cs[0]['return_code']==r['return_code'] and 'profile' in (d/cs[0]['stderr']).read_text().lower()
 gate('actual-language-invalid-entry',invalid_entry_ok);refs.update(r['evidence'] for r in matches)
 def abi_ok():
  r=runtime['ABI'];d,m=current(r['evidence'],['tools/moat/helper_runtime.py']);v=json.loads((d/'ABI-checks.json').read_text());return runtime['status']=='PASSED' and len(r['checks'])>=22 and r['checks']==v['checks'] and v==json.loads((d/'validation.json').read_text()) and all(c['passed'] for c in r['checks']) and m['sample_id']=='matrix-helper-ABI-negative' and m['parent_experiment_id']==build['experiment_id'] and m['experiment_outcome']=='PASSED'
 refs.add(runtime['ABI']['evidence']);gate('actual-C-ABI-and-lifetime-tests',abi_ok)
 if profile['language']=='cpp':
  rs=[r for r in originals['originals'] if r['sample_id']==profile['sample_id']];gate('unmodified-native-original',lambda:len(rs)==1 and rs[0]['status']=='PASSED' and rs[0]['original_sha256']==profile['original_sha256'] and current(rs[0]['evidence'],[profile['source'],'tools/moat/cuda_helper_originals.py']));refs.update(r['evidence'] for r in rs)
 else:refs.add(originals['Fortran_toolchain_evidence']);gate('explicit-original-Fortran-toolchain-inventory',lambda:bool(sealed(originals['Fortran_toolchain_evidence'])))
 return checks,refs,sources,build

def crc_benchmark(review):
 global TRUSTED_COMMIT
 TRUSTED_COMMIT=review['source_commit']
 build=load('rewrite-R9-crc-benchmark-build.json');native=load('rewrite-R9-crc-benchmark-native-build.json');runs=load('rewrite-R9-crc-benchmark-rocm.json');natives=load('rewrite-R9-crc-benchmark-cuda.json');aux=load('rewrite-R9-crc-benchmark-checks.json');trace=load('rewrite-R9-crc-benchmark-trace.json');cases=json.loads((ROOT/'migration/rewrite/crc-benchmark-cases.json').read_text());checks=[];refs=set()
 def gate(name,fn):
  try:ok=bool(fn())
  except (OSError,ValueError,KeyError,TypeError,StopIteration,AssertionError,subprocess.CalledProcessError):ok=False
  checks.append(dict(check=name,passed=ok));return ok
 names=['build_crc_benchmark','run_crc_benchmark','cuda_crc_benchmark','crc_benchmark_fixtures','crc_benchmark_reference','crc_benchmark_checks','profile_crc_benchmark','prepare_crc_benchmark','qualify_r9']
 sources=sorted(set(build['dependencies'])|{'tools/moat/'+n+'.py' for n in names}|{'migration/rewrite/crc-benchmark-cases.json','migration/rewrite/helpers-benchmark.json','rocm/probes/crc_benchmark_lengths.cpp','nvCOMP/benchmarks/benchmark_crc32.cpp'})
 gate('frozen-independent-source-review',lambda:review_ok(review,sources));gate('exact-five-case-contract',lambda:{c['case'] for c in cases}=={'original-auto','storage-small','complete-small','changed-input','repeat'} and len(cases)==5 and set(runs)==set(natives)=={c['case'] for c in cases})
 def build_ok():
  d,m,_=sealed(build['evidence'],('build-result.json','compiled-dependencies.json'));return json.loads((d/'build-result.json').read_text())=={k:v for k,v in build.items() if k!='evidence'} and build['status']=='BUILT' and digest(ROOT/build['binary'])==build['binary_sha256'] and all(digest(ROOT/n)==h for n,h in build['dependencies'].items()) and set(build['dependencies'])=={'rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp','rocm/backends/codec/crc_benchmark_compat.hpp','rocm/backends/codec/crc_benchmark_observe.hpp'} and build['build_recipe_sha256']==digest(ROOT/'tools/moat/build_crc_benchmark.py')
 gate('complete-current-compiled-build',build_ok);refs.add(build['evidence'])
 def native_build_ok():
  d,m,_=current(native['evidence'],['tools/moat/cuda_crc_benchmark.py','tools/moat/prepare_crc_benchmark.py','tools/moat/crc_benchmark_reference.py','rocm/backends/codec/crc_benchmark_observe.hpp','nvCOMP/benchmarks/benchmark_crc32.cpp']);return json.loads((d/'build-result.json').read_text())=={k:v for k,v in native.items() if k!='evidence'} and json.loads((d/'binary-identities.json').read_text())=={k:native[k] for k in ['binary_sha256','linked_libraries']} and any('nvcomp' in n for n in native['linked_libraries']) and any('curand' in n for n in native['linked_libraries'])
 gate('native-original-harness-sdk-and-actual-loader-identities',native_build_ok);refs.add(native['evidence'])
 for case in cases:
  name=case['case'];mh=digest(ROOT/'tests/fixtures/rewrite-crc-benchmark'/name/'manifest.json')
  for backend,rows,b in [('rocm',runs,build),('cuda',natives,native)]:
   r=rows[name];refs.add(r['evidence'])
   def case_ok(r=r,backend=backend,b=b,case=case,mh=mh):
    runner='run_crc_benchmark.py' if backend=='rocm' else 'cuda_crc_benchmark.py';d,m=current(r['evidence'],['tools/moat/'+runner,'tools/moat/crc_benchmark_reference.py']);raw=ROOT/m['raw_artifact_dir'];v=json.loads((d/'validation.json').read_text());cs=json.loads((d/'commands.json').read_text());f=fixture(raw/'inputs',mh,kind='crc32-benchmark')
    if json.loads((raw/'inputs/case.json').read_text())!=case or json.loads((d/'case-result.json').read_text())!={k:v for k,v in r.items() if k!='evidence'} or m['experiment_id']!=r['experiment_id'] or m['sample_id']!='nvCOMP/benchmarks::benchmark_crc32.cpp' or m['case_id']!=case['case'] or m['comparison_id']!='crc32-benchmark/'+case['case']+'/'+mh or m['parent_experiment_id']!=b['experiment_id'] or m['experiment_outcome']!='PASSED' or r['status']!='PASSED' or r['return_code'] or r['cpu_return_code'] or r['input_manifest_sha256']!=mh or r['build']!=b or r['validation']!=v or v['status']!='PASSED' or not v['checks'] or not all(c['passed'] for c in v['checks']):return False
    if (ROOT/r['output']).resolve()!=(raw/'outputs').resolve() or (ROOT/r['input_snapshot']).resolve()!=(raw/'inputs').resolve():return False
    out=raw/'outputs'
    if backend=='rocm':
     observed=json.loads((d/'backend.observed.json').read_text());cmd=cs[0];cpu=cs[1];return crc_cpu(out,case)==v and cmd['argv']==[str(ROOT/build['binary'])]+case['argv'] and cmd['environment_changes']['REWRITE_OUTPUT']==str(out) and cmd['cwd']==str(out) and cpu['phase']=='independent-zlib-grid-CSV-validation' and cpu['return_code']==0 and observed['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and observed['rocm_release']=='10.1.0' and bool(observed['devices']) and all(x['physical_id']!=3 for x in observed['devices'])
    remote=r['remote_output'];receipt=json.loads((out/'remote-payload-manifest.json').read_text());process=json.loads((out/'native-process.json').read_text());report=json.loads((out/'cpu-validation.json').read_text())
    if receipt['root']!=remote or receipt['files']['input.bin']['bytes']!=v['storage'] or process!=dict(return_code=0,binary_sha256=native['binary_sha256']) or report!=v or r['collection_return_code'] or r['manifest_return_code']:return False
    for n,identity in receipt['files'].items():
     p=out/n
     if n=='input.bin' and not case['storage']:continue
     if not p.is_file() or p.stat().st_size!=identity['bytes'] or digest(p)!=identity['sha256']:return False
    if not any(c['phase']=='original-native-benchmark-CLI' and native['binary_sha256'] in c['argv'][-1] and remote in c['argv'][-1] and native['remote']+'/native' in c['argv'][-1] and c['return_code']==0 for c in cs) or not any(c['phase']=='independent-remote-zlib-and-grid' and native['remote']+'/reference.py' in c['argv'][-1] and remote in c['argv'][-1] and c['return_code']==0 for c in cs):return False
    if case['storage']:return crc_cpu(out,case,'cuda')==v
    # The 16 GiB native input remains on the CUDA host; its independent CPU
    # command, input hash/length and every returned checksum are sealed here.
    if v['storage']!=1<<34 or v['rows']!=6 or v['columns']!=6 or v['valid_cells']!=26 or v['skipped_cells']!=10 or len(v['cells'])!=26:return False
    return all((out/('cell_'+str(c['size'])+'_'+str(c['count'])+'_final.bin')).read_bytes()==struct.pack('<'+str(c['count'])+'I',*c['crcs']) for c in v['cells'])
   gate(backend+'/'+name+'/sealed-current-command-input-and-independent-CPU',case_ok)
 for backend,rows in [('rocm',runs),('cuda',natives)]:
  gate(backend+'/changed-input-exercises-distinct-checksums',lambda rows=rows:rows['storage-small']['validation']['cells']!=rows['changed-input']['validation']['cells'])
 for case in cases:
  if case['storage']:gate(case['case']+'/identical-three-way-bytes-and-checksums',lambda case=case:runs[case['case']]['validation']['cells']==natives[case['case']]['validation']['cells'])
 required={'CRC-value','candidate-value','CSV-negative-infinity','CSV-skipped-active','timing-zero','selected-not-minimum','missing-cell'}
 gate('complete-seven-fault-set',lambda:len(aux['negative'])==7 and {r['fault'] for r in aux['negative']}==required)
 for r in aux['negative']:
  refs.add(r['evidence'])
  def fault_ok(r=r):
   d,m=current(r['evidence'],['tools/moat/crc_benchmark_checks.py','tools/moat/crc_benchmark_reference.py']);v=json.loads((d/'validation.json').read_text());return r['passed'] and m['case_id']==r['fault'] and m['experiment_outcome']=='PASSED' and v==json.loads((d/'rejection.json').read_text()) and v['status']=='PASSED' and bool(v['reason']) and all(c['passed'] for c in v['checks'])
  gate('fault/'+r['fault'],fault_ok)
 required_cli={'help','unknown','missing-output','missing-storage','not-power-two','empty-table','over-capacity','unwritable-CSV'}
 gate('complete-eight-CLI-cases',lambda:len(aux['runtime'])==8 and {r['case'] for r in aux['runtime']}==required_cli)
 for r in aux['runtime']:
  refs.add(r['evidence'])
  def runtime_ok(r=r):
   d,m=current(r['evidence'],['tools/moat/crc_benchmark_checks.py',*build['dependencies']]);cs=json.loads((d/'commands.json').read_text());return r['passed'] and m['case_id']==r['case'] and m['parent_experiment_id']==build['experiment_id'] and len(cs)==1 and cs[0]['argv']==[str(ROOT/build['binary'])]+r['argv'] and cs[0]['return_code']==r['return_code'] and (r['return_code']==0 if r['case']=='help' else r['return_code']!=0)
  gate('actual-CLI/'+r['case'],runtime_ok)
 refs.add(aux['boundary']['evidence'])
 def boundary_ok():
  d,m=current(aux['boundary']['evidence'],['tools/moat/crc_benchmark_checks.py','rocm/probes/crc_benchmark_lengths.cpp',*build['dependencies']]);v=json.loads((d/'validation.json').read_text());return v=={k:v for k,v in aux['boundary'].items() if k!='evidence'} and v['status']=='PASSED' and len(v['checks'])==6 and all(c['passed'] for c in v['checks']) and any('4294967296' in c['check'] for c in v['checks']) and m['parent_experiment_id']==build['experiment_id']
 gate('actual-GPU-64bit-length-versus-independent-libz',boundary_ok)
 refs.add(trace['evidence'])
 def trace_ok():
  d,m=current(trace['evidence'],['tools/moat/profile_crc_benchmark.py','tools/moat/crc_benchmark_reference.py',*build['dependencies']]);summary=json.loads((d/'kernel-summary.json').read_text());v=json.loads((d/'validation.json').read_text());return {**summary,**v}=={k:v for k,v in trace.items() if k!='evidence'} and v['status']=='PASSED' and all(c['passed'] for c in v['checks']) and summary['binary_sha256']==build['binary_sha256'] and summary['segment_dispatches']==summary['expected_segment_dispatches']==12 and summary['combine_dispatches']==summary['expected_combine_dispatches']>0 and m['parent_experiment_id']==build['experiment_id']
 gate('raw-GPU-trace-proves-full-search-and-final-replay',trace_ok)
 return checks,refs,sources,build


def qualify_crc(review,dry_run):
 checks,refs,sources,build=crc_benchmark(review);status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';case_ids=[c['case'] for c in json.loads((ROOT/'migration/rewrite/crc-benchmark-cases.json').read_text())];implementation='rocm/ported/nvCOMP/benchmarks/benchmark_crc32.cpp'
 row=dict(sample_id='nvCOMP/benchmarks::benchmark_crc32.cpp',kind='crc32-benchmark',status=status,checks=checks,implementation=implementation,implementation_sha256=digest(ROOT/implementation),dependencies=build['dependencies'],case_count=5,case_ids=case_ids,evidence_references=sorted(refs),source_commit=review['source_commit'],scope='Original benchmark auto-storage/CLI/CSV/grid and IEEE CRC32 with full GPU search and recomputation. Default backend RNG streams checked independently; four bounded cases use identical bytes. 64-bit length probe is not a full 32 GiB benchmark scan. No cross-device performance claim.')
 print('CRC benchmark',status,[c['check'] for c in checks if not c['passed']],flush=True)
 if not dry_run:
  if status=='PASSED':
   e=Experiment('R9',row['sample_id'],'composite-qualification',sources=[ROOT/n for n in sources]);write(e.path/'qualification.json',row);row.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status='PASSED',checks=checks)));run=load('rewrite-R9-crc-benchmark-rocm.json')['original-auto'];d=ROOT/run['evidence'];row.update(rocm_evidence=run['evidence'],cuda_evidence=load('rewrite-R9-crc-benchmark-cuda.json')['original-auto']['evidence'],environment=str((d/'backend.observed.json').relative_to(ROOT)),devices=json.loads((d/'backend.observed.json').read_text())['devices'])
  write(ROOT/'migration/reports/rewrite-R9-crc-benchmark-qualification.json',dict(status=status,qualifications=[row]))
 return int(status!='PASSED')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--only',choices=['helpers','crc'],default='helpers');parser.add_argument('--dry-run',action='store_true');a=parser.parse_args();spec=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text());review=load('rewrite-R9-'+('helper' if a.only=='helpers' else 'crc-benchmark')+'-review.json');rows=[]
 if a.only=='crc':return qualify_crc(review,a.dry_run)
 for p in spec['helpers']:
  checks,refs,sources,build=helpers(p,review);status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';row=dict(sample_id=p['sample_id'],kind='matrix-helper/'+p['language']+'/'+p['kind'],status=status,checks=checks,implementation=p['implementation'],implementation_sha256=digest(ROOT/p['implementation']),dependencies=build['dependencies'],case_count=len(p['cases']),case_ids=p['cases'],evidence_references=sorted(refs),source_commit=review['source_commit'],scope='Original helper metadata/borrowed pointer/data mutation/lifecycle and actual source-language caller, plus registered variants. Host descriptor objects backed by real HIP storage; no GPU sparse-solver claim. NVIDIA Fortran compiler remains a separate unavailable baseline.')
  print(p['language'],p['kind'],status,[c['check'] for c in checks if not c['passed']],flush=True)
  if not a.dry_run and status=='PASSED':
   e=Experiment('R9',p['sample_id'],'composite-qualification',sources=[ROOT/n for n in sources]);write(e.path/'qualification.json',row);row.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status='PASSED',checks=checks)));run=next(r for r in load('rewrite-R9-helper-rocm.json') if r['sample_id']==p['sample_id']);d=ROOT/run['evidence'];row.update(rocm_evidence=run['evidence'],cuda_evidence=next(r['evidence'] for r in load('rewrite-R9-helper-cuda.json') if r['sample_id']==p['sample_id']),environment=str((d/'backend.observed.json').relative_to(ROOT)),devices=json.loads((d/'backend.observed.json').read_text())['devices'])
  rows.append(row)
 if not a.dry_run:write(ROOT/'migration/reports/rewrite-R9-helper-qualification.json',dict(status='PASSED' if all(r['status']=='PASSED' for r in rows) else 'FAILED',qualifications=rows))
 return int(any(r['status']!='PASSED' for r in rows))
if __name__=='__main__':raise SystemExit(main())
