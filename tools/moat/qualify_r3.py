#!/usr/bin/env python3
"""Qualify the two completed R3 candidates without clearing other PARTIAL gaps."""
import argparse,fcntl,json
from experiment import ROOT,Experiment,write,digest,git
import qualify_first as gates
gates.REVIEW_PATHS += ['migration/rewrite/extensions.json','tests/fixtures/rewrite-extensions']
def load(name):return json.loads((ROOT/'migration/reports'/name).read_text())
def collect(kind):
 profiles=json.loads((ROOT/'migration/rewrite/extensions.json').read_text())['profiles'];p=next(p for p in profiles if p['kind']==kind);checks=[];references=[]
 def gate(name,value):checks.append(dict(check=name,passed=bool(value)))
 def proof(evidence,sources,**identity):
  references.append(evidence);return gates.auxiliary(evidence,sources,**identity)
 review=load('rewrite-R3-review.json');gate('current-independent-review',review.get('verdict')=='APPROVED' and gates.review_identity(review))
 required={'ncc':{'original','changed-values','changed-template','no-timing','repeat','constant-template','constant-image','constant-both'},'svd':{'original','changed-values','irregular','layout','repeat','rank-deficient','rank-truncated'}}[kind]
 gate('frozen-complete-cases',set(p['cases'])==required and len(p['cases'])==len(required));build=load('rewrite-extension-builds.json')[kind]
 sample=next(s for s in json.loads((ROOT/'migration/samples.yaml').read_text())['samples'] if s['id']==p['sample_id']);gate('unchanged-original-source',digest(ROOT/p['source'])==sample['source_sha256'])
 def environment_gate(case,run):
  observed=json.loads((ROOT/run['evidence']/'backend.observed.json').read_text())
  gate(case+'/locked-real-GPU',observed.get('image_id')=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and observed.get('rocm_release')=='10.1.0' and bool(observed.get('devices')) and all(d['physical_id']!=3 for d in observed['devices']))
 gate('current-compiled-source',all(digest(ROOT/n)==sha for n,sha in build['dependencies'].items()));gate('current-build-recipe',build['build_recipe_sha256']==digest(ROOT/'tools/moat/build_extensions.py'));gate('binary-identity',digest(ROOT/build['binary'])==build['binary_sha256']);gate('sealed-build',not gates.check(ROOT/build['evidence']))
 if kind=='ncc':
  records={backend:load(f'rewrite-ncc-{backend}.json') for backend in ['rocm','cuda']};values=load('rewrite-ncc-validation.json');comparisons=load('rewrite-ncc-native-comparison.json')
  for case in p['cases']:
   a=records['rocm'][case];b=records['cuda'][case];gate(case+'/same-manifest',a['input_manifest_sha256']==b['input_manifest_sha256']);gate(case+'/current-build',a['build']['experiment_id']==build['experiment_id'])
   environment_gate(case,a)
   for backend,r in [('rocm',a),('cuda',b)]:
    gate(case+'/'+backend+'/sealed-run',not gates.check(ROOT/r['evidence']));v=values[backend+'/'+case];gate(case+'/'+backend+'/current-CPU',v['status']=='PASSED' and v['run']['experiment_id']==r['experiment_id'] and proof(v['evidence'],['tools/moat/ncc_reference.py','tools/moat/validate_ncc.py'],parent=r['experiment_id'],comparison=r['input_manifest_sha256']))
   comp=next(c for c in comparisons['cases'] if c['case']==case);gate(case+'/native-comparison',comp['status']=='PASSED' and comp['rocm']['experiment_id']==a['experiment_id'] and comp['cuda']['experiment_id']==b['experiment_id'] and proof(comp['evidence'],['tools/moat/compare_ncc.py'],parent=a['experiment_id'],comparison=a['input_manifest_sha256']))
  negative=load('rewrite-ncc-negative.json');runtime=load('rewrite-ncc-runtime.json');gate('negative-count',len(negative['tests'])==3)
  for r in negative['tests']:gate('negative/'+r['mode'],r['passed'] and proof(r['evidence'],['tools/moat/ncc_negative.py','tools/moat/ncc_reference.py'],parent=records['rocm']['original']['experiment_id']))
  gate('runtime-count',len(runtime['tests'])==7)
  for r in runtime['tests']:gate('CLI/'+r['test'],r['passed'] and proof(r['evidence'],['tools/moat/ncc_runtime.py',p['implementation']],parent=build['experiment_id'],expected_outcome='EXPECTED_REJECTION'))
 else:
  records={backend:load(f'rewrite-extension-{backend}.json') for backend in ['rocm','cuda','native-approx']};values={backend:load(f'rewrite-extension-{backend}-validation.json') for backend in records}
  for case in p['cases']:
   key=kind+'/'+case;a=records['rocm'][key];b=records['cuda'][key];gate(case+'/same-input',a['comparison_id']==b['comparison_id']);gate(case+'/current-build',a['build']['experiment_id']==build['experiment_id'])
   environment_gate(case,a)
   for backend,r in [('rocm',a),('cuda',b)]:
    gate(case+'/'+backend+'/sealed-run',r['return_code']==0 and not gates.check(ROOT/r['evidence']));v=values[backend][key];gate(case+'/'+backend+'/CPU',v['status']=='PASSED' and v['run']['experiment_id']==r['experiment_id'] and proof(v['evidence'],['tools/moat/svd_reference.py','tools/moat/validate_extensions.py','tools/moat/inputs.py'],parent=r['experiment_id'],comparison=r['comparison_id'],input_hash=r['input_manifest_sha256']))
  key='svd/original';r=records['native-approx'][key];v=values['native-approx'][key];gate('native-original-gesvda',v['status']=='PASSED' and r['comparison_id']==records['rocm'][key]['comparison_id'] and proof(v['evidence'],['tools/moat/svd_reference.py','tools/moat/validate_extensions.py'],parent=r['experiment_id'],comparison=r['comparison_id'],input_hash=r['input_manifest_sha256']) and not gates.check(ROOT/r['evidence']))
  trace=next(r for r in load('rewrite-solver-backend-traces.json')['profiles'] if r['name']=='rank-svd');references.append(trace['evidence']);gate('actual-native-GPU-SVD-kernels',trace['return_code']==0 and trace['binary_sha256']==build['binary_sha256'] and any('bdsqr_compute' in n for n in trace.get('solver_algorithm_kernel_names',[])) and not gates.check(ROOT/trace['evidence']))
  negative=load('rewrite-svd-negative.json');runtime=load('rewrite-svd-runtime.json');gate('negative-count',len(negative['tests'])==5)
  for r in negative['tests']:
   run=records['rocm']['svd/'+r['case']];gate('negative/'+r['mode'],r['passed'] and proof(r['evidence'],['tools/moat/extensions_negative.py','tools/moat/svd_reference.py','tools/moat/inputs.py'],parent=run['experiment_id'],comparison=run['comparison_id'],input_hash=run['input_manifest_sha256']))
  gate('runtime-count',len(runtime['tests'])==11)
  for r in runtime['tests']:gate('descriptor/'+r['test'],r['passed'] and proof(r['evidence'],['tools/moat/svd_runtime.py','rocm/backends/solver/rank_svd.hpp'],parent=build['experiment_id'],expected_outcome='EXPECTED_REJECTION'))
 return p,build,checks,sorted(set(references))

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args();results=[]
 for kind in ['ncc','svd']:
  p,b,checks,references=collect(kind);ok=all(c['passed'] for c in checks);r=dict(kind=kind,sample_id=p['sample_id'],status='PASSED' if ok else 'FAILED',checks=checks,scope='MOAT R3 full original contract plus registered variants; independent composite qualification',implementation=p['implementation'],implementation_sha256=digest(ROOT/p['implementation']),dependencies=b['dependencies'],case_count=len(p['cases']),case_ids=p['cases'],evidence_references=references,source_commit=git('rev-parse','HEAD').strip())
  if args.apply:
   if not ok:raise SystemExit('Refusing R3 qualification '+kind+': '+str([c['check'] for c in checks if not c['passed']]))
   e=Experiment('R3',p['sample_id'],'composite-qualification',sources=[__file__,ROOT/'tools/moat/qualify_first.py',ROOT/'migration/reports/rewrite-R3-review.json']);write(e.path/'qualification.json',r);r['qualification_id']=e.id;r['evidence']=e.finish('PASSED',dict(checks=checks))
   run=load('rewrite-ncc-rocm.json')['original'] if kind=='ncc' else load('rewrite-extension-rocm.json')['svd/original'];r['rocm_evidence']=run['evidence'];r['environment']=json.loads((ROOT/run['evidence']/'backend.observed.json').read_text());r['devices']=r['environment']['devices'];r['cuda_evidence']=load('rewrite-ncc-cuda.json')['original']['evidence'] if kind=='ncc' else load('rewrite-extension-cuda.json')['svd/original']['evidence']
  results.append(r);print(kind,r['status'],[c['check'] for c in checks if not c['passed']],flush=True)
 write(ROOT/'migration/reports/rewrite-R3-qualification.json',dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',qualifications=results))
 if args.apply:
  with (ROOT/'migration/.state.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);path=ROOT/'migration/samples.yaml';cat=json.loads(path.read_text())
   for r in results:
    s=next(s for s in cat['samples'] if s['id']==r['sample_id']);cases=['rewrite/R3/'+r['kind']+'/'+c for c in r['case_ids']]+['rewrite/R3/'+r['kind']+'/independent-review-and-qualification'];s.update(status='PASSED',level='L4',reason_code='VALIDATED_MOAT_REWRITE',reason='完整原始合同、登记变体、独立CPU/同字节CUDA、负向/边界与独立复审通过。实际路线：'+s['actual_library']+'。性能不作跨设备比较。',required_cases=cases,passed_cases=cases,selected_validation=r,cuda_comparison='PASSED',cuda_baseline='PASSED');s['attempts'].append(r)
    for evidence in [r['evidence'],'migration/reports/rewrite-R3-qualification.json']:
     if evidence not in s['evidence']:s['evidence'].append(evidence)
   write(path,cat)
 return int(any(r['status']!='PASSED' for r in results))
if __name__=='__main__':raise SystemExit(main())
