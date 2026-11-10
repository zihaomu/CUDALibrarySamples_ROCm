#!/usr/bin/env python3
import argparse,fcntl,json
from experiment import ROOT,Experiment,write,digest,git
import qualify_first as review_gate
from qualification_common import read,evidence,fixture,guarded,file_run
review_gate.REVIEW_PATHS += ['migration/rewrite','tests/fixtures/rewrite-extensions']
def load(name):return read(ROOT/'migration/reports'/name)
def collect():
 p=next(p for p in read(ROOT/'migration/rewrite/extensions.json')['profiles'] if p['kind']=='crc32');p=dict(p,fixture_root='tests/fixtures/rewrite-extensions/crc32');b=load('rewrite-extension-builds.json')['crc32'];checks=[];refs=[]
 def gate(name,value):checks.append(dict(check=name,passed=bool(value)))
 def proof(path,**kw):refs.append(path);return guarded(lambda: bool(evidence(path,**kw)))
 review=load('rewrite-R4-review.json');gate('current-independent-review',review.get('verdict')=='APPROVED' and review_gate.review_identity(review));required={'original','changed-values','chunk-boundary','multi-file','empty-with-data','repeat','empty-only'};gate('complete-unique-case-contract',set(p['cases'])==required and len(p['cases'])==len(required))
 sample=next(s for s in read(ROOT/'migration/samples.yaml')['samples'] if s['id']==p['sample_id']);gate('unchanged-original-source',digest(ROOT/p['source'])==sample['source_sha256']);gate('current-compiled-dependencies',all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items()));gate('current-build-recipe',b['build_recipe_sha256']==digest(ROOT/'tools/moat/build_extensions.py'));gate('current-binary',digest(ROOT/b['binary'])==b['binary_sha256']);gate('sealed-build',proof(b['evidence'],outcome='EXECUTED'))
 records={backend:load(f'rewrite-crc32-{backend}.json') for backend in ['rocm','cuda']};values={backend:load(f'rewrite-crc32-{backend}-validation.json') for backend in records}
 for case in p['cases']:
  frozen=fixture(ROOT/p['fixture_root']/case,kind='crc32',case=case);mh=digest(ROOT/p['fixture_root']/case/'manifest.json');comp='crc32/'+case+'/'+mh
  gate(case+'/expected-input-outcome',frozen['expected_run_outcome']==('ZERO_CHUNKS_REJECTED' if case=='empty-only' else 'SUCCESS'))
  for backend in records:
   r=records[backend][case];tag='rocm' if backend=='rocm' else 'cuda-native';gate(case+'/'+backend+'/frozen-run-identity',guarded(file_run,r,p,case,tag));directory=ROOT/r['evidence'];commands=read(directory/'commands.json');meta=read(directory/'manifest.json')
   if backend=='rocm':
    command=next(c for c in commands if c['phase']=='original-file-CLI');raw=ROOT/meta['raw_artifact_dir'];gate(case+'/actual-build-and-CLI',r['build']==b and command['argv']==[str(ROOT/b['binary'])]+frozen['argv'] and command['cwd']==str(raw/'inputs') and command['return_code']==r['return_code']);observed=read(directory/'backend.observed.json');gate(case+'/locked-GPU',observed['rocm_release']=='10.1.0' and observed['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and bool(observed['devices']) and all(d['physical_id']!=3 for d in observed['devices']))
   else:
    gate(case+'/actual-native-exit',read(ROOT/r['output']/'native-exit.json')['return_code']==r['return_code']);gate(case+'/native-transport-collected',all(c['return_code']==(1 if case=='empty-only' and c['phase']=='original-nvcomp-CRC32' else 0) for c in commands));build=r['build'];gate(case+'/native-build-provenance',proof(build['evidence'],sources=['tools/moat/cuda_crc32.py',p['source']],outcome='EXECUTED') and build['original_sha256']==sample['source_sha256'] and read(ROOT/build['evidence']/'sdk-identity.json')==build['sdk'] and digest(ROOT/build['evidence']/'nvcomp_crc32.cu')==build['instrumented_sha256'])
   gate(case+'/'+backend+'/process-semantics',(r['return_code']!=0) if case=='empty-only' else r['return_code']==0)
   v=values[backend][case];gate(case+'/'+backend+'/current-independent-CPU',v['status']=='PASSED' and v['run']==r and proof(v['evidence'],sources=['tools/moat/crc32_reference.py','tools/moat/validate_crc32.py'],parent=r['experiment_id'],case=case,backend='cpu-validation',sample=p['sample_id'],comparison=comp,outcome='PASSED'))
   cpu=ROOT/v['evidence'];rawcpu=ROOT/read(cpu/'manifest.json')['raw_artifact_dir'];gate(case+'/'+backend+'/CPU-frozen-input',guarded(lambda: bool(fixture(rawcpu/'inputs',mh,'crc32',case))));refs.append(r['evidence'])
  a=ROOT/records['rocm'][case]['output'];c=ROOT/records['cuda'][case]['output']
  if case!='empty-only':
   for name in ['input.bin','offsets.bin','sizes.bin','crc32.bin']:gate(case+'/native-exact-'+name,digest(a/name)==digest(c/name))
 negative=load('rewrite-crc32-negative.json')['tests'];modes={'checksum','CRC32C-polynomial','chunk-offset','trailing-checksum-byte','iteration-count','timing-NaN','input-byte','truncate-checksum'};gate('complete-unique-negative-modes',len(negative)==len(modes) and {r['mode'] for r in negative}==modes)
 for r in negative:
  case='chunk-boundary' if r['mode']=='chunk-offset' else 'original';run=records['rocm'][case];gate('negative/'+r['mode'],r['case']==case and r['passed'] and proof(r['evidence'],sources=['tools/moat/crc32_negative.py','tools/moat/crc32_reference.py'],parent=run['experiment_id'],case=case,backend='cpu-negative',comparison=run['comparison_id'],outcome='PASSED',check_names={r['mode']}))
 runtime=load('rewrite-crc32-runtime.json')['tests'];tests={'no-files','flag-without-file','unknown-flag','missing-file','zero-chunks'};gate('complete-unique-CLI-contract',len(runtime)==len(tests) and {r['test'] for r in runtime}==tests)
 for r in runtime:gate('CLI/'+r['test'],r['passed'] and proof(r['evidence'],sources=['tools/moat/crc32_runtime.py','rocm/backends/codec/crc32.hpp'],parent=b['experiment_id'],backend='rocm-invalid-cli',outcome='EXPECTED_REJECTION',check_names={r['test']}))
 trace=load('rewrite-crc32-trace.json');refs.append(trace['evidence'])
 def trace_check():
  directory,raw,meta=evidence(trace['evidence'],sources=['tools/moat/profile_crc32.py','rocm/backends/codec/crc32.hpp'],parent=b['experiment_id'],case='original',backend='rocm-profile',sample=p['sample_id']+'/backend-trace',comparison='crc32/original/'+digest(ROOT/p['fixture_root']/'original/manifest.json'),outcome='PROFILE_OBSERVED');s=read(directory/'kernel-summary.json')
  if {k:v for k,v in trace.items() if k!='evidence'}!=s or s['return_code'] or s['binary']!=b['binary'] or s['build_experiment_id']!=b['experiment_id'] or s['input_manifest_sha256']!=digest(ROOT/p['fixture_root']/'original/manifest.json') or s['binary_sha256']!=b['binary_sha256'] or s['crc_kernel_dispatches']!=5:return False
  fixture(raw/'inputs',s['input_manifest_sha256'],'crc32','original');command=next(c for c in read(directory/'commands.json') if c['phase']=='profile');pos=command['argv'].index('--');return command['return_code']==0 and command['argv'][pos+1:]==[str(ROOT/b['binary'])]+fixture(raw/'inputs')['argv'] and command['cwd']==str(raw/'inputs')
 gate('actual-five-CRC32-GPU-kernel-dispatches',guarded(trace_check))
 return p,b,checks,sorted(set(refs))

def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args();profile,b,checks,refs=collect();ok=all(c['passed'] for c in checks);r=dict(sample_id=profile['sample_id'],kind='crc32',status='PASSED' if ok else 'FAILED',checks=checks,implementation=profile['implementation'],implementation_sha256=digest(ROOT/profile['implementation']),dependencies=b['dependencies'],case_count=7,numeric_case_count=6,semantic_rejection_cases=1,case_ids=profile['cases'],evidence_references=refs,source_commit=git('rev-parse','HEAD').strip(),scope='Original batched IEEE/PKZIP CRC32 file/chunk/iteration contract; six numeric cases plus native zero-chunk rejection, project error exit normalized to 1')
 if args.apply:
  if not ok:raise SystemExit('CRC32 qualification refused: '+str([c['check'] for c in checks if not c['passed']]))
  e=Experiment('R4',profile['sample_id'],'composite-qualification',sources=[__file__,ROOT/'tools/moat/qualification_common.py',ROOT/'migration/reports/rewrite-R4-review.json']);write(e.path/'qualification.json',r);r.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(checks=checks)));run=load('rewrite-crc32-rocm.json')['original'];r.update(rocm_evidence=run['evidence'],cuda_evidence=load('rewrite-crc32-cuda.json')['original']['evidence'],environment=read(ROOT/run['evidence']/'backend.observed.json'));r['devices']=r['environment']['devices']
  with (ROOT/'migration/.state.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'migration/samples.yaml';cat=read(path);s=next(s for s in cat['samples'] if s['id']==profile['sample_id']);cases=['rewrite/R4/crc32/'+c for c in profile['cases']]+['rewrite/R4/crc32/negative','rewrite/R4/crc32/CLI','rewrite/R4/crc32/GPU-trace','rewrite/R4/crc32/review'];s.update(status='PASSED',level='L4',required_cases=cases,passed_cases=cases,selected_validation=r,reason_code='VALIDATED_MOAT_REWRITE',reason='HIP IEEE/PKZIP CRC32：6个数值场景逐chunk通过zlib和真实native nvCOMP；零chunk按原生语义拒绝，错误退出规范化为1。文件/分块/迭代、8注入、5CLI与5次实际GPU核及独立复审通过；不是CRC32C。',cuda_baseline='PASSED',cuda_comparison='PASSED');s['attempts'].append(r);s['evidence'] += [r['evidence'],'migration/reports/rewrite-R4-qualification.json'];write(path,cat)
 write(ROOT/'migration/reports/rewrite-R4-qualification.json',r);print(r['status'],[c['check'] for c in checks if not c['passed']]);return int(not ok)
if __name__=='__main__':raise SystemExit(main())
