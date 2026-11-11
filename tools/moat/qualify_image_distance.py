#!/usr/bin/env python3
"""Qualify the complete signed/unsigned distance entrypoint from current raw proofs."""
import argparse,json,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from qualify_canny_plus import sealed,reviewed
from image_distance_build import dependencies
from image_distance_inputs import load_case
import image_distance_reference as core
import image_distance_original_reference as originals
import image_distance_arguments_reference as arguments
import image_distance_states_reference as states
import image_distance_cli as cli
import image_distance_trace as trace
import image_distance_native_reference as native
import image_distance_regression as regression

SAMPLE='NPP+/distanceTransform::unsignedAndSignedDistanceTransformNPPPlus.cpp'
IMPLEMENTATION='rocm/ported/NPP+/distanceTransform/unsignedAndSignedDistanceTransformNPPPlus.cpp'
COMPARISON='ALGORITHM_VARIANT_EXACT_PROJECT_TYPED_SDF'
def load(name):return json.loads((ROOT/f'migration/reports/image-distance-{name}.json').read_text())
def cold_inventory(children):
 sizes={'contracts':1,'original-contracts':1,'state-contracts':1,'build':1,'all':1,'frontend-build':1,'originals':4,'arguments':1,'states':1}
 if len(children)!=12 or {c['name'] for c in children}!=set(sizes) or len({c['relative'] for c in children})!=12 or len({c['report']['evidence'] for c in children})!=12:return False
 for name,count in sizes.items():
  rows=[c for c in children if c['name']==name]
  if len(rows)!=count or {c['index'] for c in rows}!=set(range(count)):return False
  if any(c['relative']!=f'child-evidence/{name}/{c["index"]}' for c in rows):return False
 rules=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text())['workflows'];ids=[c['report']['case'] for c in children if c['name']=='originals']
 return len(set(ids))==4 and set(ids)=={r['case'] for r in rules}

def collect(review=None):
 spec=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());b=load('build');fb=load('frontend-build');refs=set();sources={str(p.relative_to(ROOT)) for p in dependencies()};checks=[]
 def gate(name,fn):
  try:ok=bool(fn())
  except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration,AssertionError,subprocess.CalledProcessError):ok=False
  checks.append(dict(check=name,passed=ok));return ok
 def report(r,member,backend=None):
  refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies'])
  return (backend is None or m['backend']==backend) and m['experiment_id']==r.get('experiment_id',m['experiment_id']) and json.loads((d/member).read_text())=={k:v for k,v in r.items() if k!='evidence'}
 def observed(r):
  d,_,_=sealed(r['evidence']);o=json.loads((d/'backend.observed.json').read_text())
  return o['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and o['rocm_release']=='10.1.0' and bool(o['devices']) and all(x['physical_id']!=3 for x in o['devices'])
 def commands(r):return json.loads((ROOT/r['evidence']/'commands.json').read_text())
 def frozen():
  for name,file,count in [('contracts','image-distance-profile.json',30),('original-contracts','image-distance-original-contract.json',4),('state-contracts','image-distance-state-contract.json',27)]:
   r=load(name);d,m,src=sealed(r['evidence']);refs.add(r['evidence']);sources.update(src['dependencies']);profile=json.loads((ROOT/'migration/rewrite'/file).read_text())
   if not report(r,'contracts.json','CPU-contract') or r['status']!='FROZEN' or profile['status']!='FROZEN' or json.loads((d/'profile.json').read_text())!=profile or r.get('case_count',r.get('workflows'))!=count:return False
  return spec['sample_id']==SAMPLE and spec['case_count']==len(spec['cases'])==30 and len({c['case'] for c in spec['cases']})==30 and len(spec['original_case_ids'])==5 and spec['original_output_count']==12 and digest(ROOT/spec['original_source'])==spec['original_source_sha256'] and digest(ROOT/'migration/rewrite/image-distance-policy.json')==spec['source_policy_sha256']
 gate('three-frozen-complete-input-workflow-and-state-contracts',frozen)
 def fixtures():
  state=json.loads((ROOT/'migration/rewrite/image-distance-state-contract.json').read_text());original=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text())
  for c in [*spec['cases'],*state['numeric_cases'].values()]:
   load_case(c)
   if c.get('original') and digest(ROOT/c['original']['source'])!=c['original']['sha256']:return False
  return len(state['numeric_cases'])==13 and len(original['datasets'])==3 and all((ROOT/c['path']).stat().st_size==c['bytes'] and digest(ROOT/c['path'])==c['sha256'] for rows in original['datasets'].values() for c in rows)
 gate('all-frozen-input-config-padding-and-original-byte-identities',fixtures)
 def builds():
  expected={str(p.relative_to(ROOT)):digest(p) for p in dependencies()};full=dict(expected,**{n:digest(ROOT/n) for n in [IMPLEMENTATION,'rocm/common/image/distance_sample.hpp']})
  if not report(b,'build.json','rocm-build') or not observed(b) or b['status']!='BUILT' or b['abi_version']!=1 or b['dependencies']!=expected or b['build_recipe_sha256']!=digest(ROOT/'tools/moat/image_distance_build.py') or digest(ROOT/b['library'])!=b['library_sha256'] or len(commands(b))!=1 or commands(b)[0]['return_code'] or '-ffp-contract=off' not in commands(b)[0]['argv']:return False
  return report(fb,'build.json','rocm-build') and observed(fb) and fb['backend']==b and fb['status']=='BUILT' and fb['implementation']==IMPLEMENTATION and fb['dependencies']==full and fb['build_recipe_sha256']==digest(ROOT/'tools/moat/image_distance_frontend_build.py') and digest(ROOT/fb['binary'])==fb['binary_sha256'] and len(commands(fb))==1 and commands(fb)[0]['return_code']==0 and '-ffp-contract=off' in commands(fb)[0]['argv']
 gate('ABI1-current-no-contraction-HIP-library-and-full-C++-caller',builds)
 def gpu(name,backend,worker):
  r=load(name)
  if not report(r,'run.json',backend) or not observed(r) or r['return_code'] or r['build']!=b:return False
  cs=commands(r);m=json.loads((ROOT/r['evidence']/'manifest.json').read_text())
  return len(cs)==1 and cs[0]['return_code']==0 and str(ROOT/'tools/moat'/worker) in cs[0]['argv'] and str(ROOT/b['library']) in cs[0]['argv'] and b['library_sha256'] in cs[0]['argv'] and cs[0]['argv'][cs[0]['argv'].index('--output')+1]==str(ROOT/r['outputs']) and m['parent_experiment_id']==b['experiment_id']
 for name,backend,worker in [('all','rocm-prototype','image_distance_worker.py'),('arguments','rocm-runtime','image_distance_arguments.py'),('states','rocm-runtime','image_distance_states.py'),('trace','rocm-trace','image_distance_worker.py')]:gate(name+'/actual-guarded-current-library-process',lambda name=name,backend=backend,worker=worker:gpu(name,backend,worker))
 def cpu(name,fn,count):
  r=load(name+'-validation');actual=fn(load(name));expected=actual if isinstance(actual,dict) else dict(status='PASSED' if all(x['status']=='PASSED' for x in actual) else 'FAILED',case_count=len(actual),results=actual)
  if name=='originals':expected['file_count']=sum(x['file_count'] for x in actual)
  if not report(r,'results.json','CPU-reference') or r['status']!='PASSED' or r['case_count']!=count or {k:v for k,v in r.items() if k!='evidence'}!=expected:return False
  if name in {'arguments','states','trace','native'}:
   m=json.loads((ROOT/r['evidence']/'manifest.json').read_text())
   if m['parent_experiment_id']!=load(name)['experiment_id']:return False
  return True
 for name,fn,count in [('all',core.validate,30),('originals',originals.validate,4),('arguments',arguments.validate,69),('states',states.validate,27),('cli',cli.validate,19),('trace',trace.validate,31),('native',native.validate,5),('regression',regression.validate,14)]:gate(name+'/independently-recomputed-complete-contract',lambda name=name,fn=fn,count=count:cpu(name,fn,count))
 def original_runs(name):
  rows=load(name)
  if len(rows)!=(4 if name=='originals' else 19):return False
  for r in rows:
   if not report(r,'run.json','rocm-original' if name=='originals' else 'rocm-CLI') or not observed(r) or r['build']!=fb:return False
   cs=commands(r);m=json.loads((ROOT/r['evidence']/'manifest.json').read_text())
   if len(cs)!=1 or cs[0]['return_code']!=r['return_code'] or cs[0]['argv'][0]!=str(ROOT/fb['binary']) or m['parent_experiment_id']!=fb['experiment_id']:return False
  return True
 for name in ['originals','cli']:gate(name+'/complete-current-C++-process-matrix',lambda name=name:original_runs(name))
 def native_run():
  r=load('native')
  return report(r,'run.json','cuda-original') and r['status']=='EXECUTED' and r['return_code']==r['collection_return_code']==0 and len(commands(r))==6 and all(c['return_code']==0 for c in commands(r)) and digest(ROOT/r['original_source'])==r['original_source_sha256']
 gate('unchanged-CUDA-original-all-files-binary-SDK-and-device-receipts',native_run)
 def legacy():
  rb=load('regression-build')
  if not report(rb,'build.json','rocm-build') or not observed(rb) or rb['status']!='BUILT' or set(rb['binaries'])!={'distance','ncc'} or len(commands(rb))!=2 or any(c['return_code'] for c in commands(rb)) or any(digest(ROOT/n)!=sha for n,sha in rb['dependencies'].items()) or any(digest(ROOT/x['binary'])!=x['sha256'] for x in rb['binaries'].values()):return False
  rows=load('regression')
  for r in rows:
   if not report(r,'run.json','rocm-regression') or not observed(r) or r['build']!=rb:return False
   m=json.loads((ROOT/r['evidence']/'manifest.json').read_text())
   if m['parent_experiment_id']!=rb['experiment_id'] or m['experiment_outcome']!=('EXPECTED_REJECTION' if r['expected_return_code'] else 'EXECUTED'):return False
  return len(rows)==14
 gate('fresh-unchanged-legacy-EDT-and-full-NCC-regression-binaries',legacy)
 def models():
  r=load('model-checks');names=[x['check'] for x in r['checks']]
  return report(r,'checks.json','CPU-model') and r['status']=='PASSED' and r['case_count']==len(names)==len(set(names))==100 and all(c['passed'] for c in r['checks'])
 gate('100-analytic-exhaustive-site-cost-and-dimension-model-checks',models)
 def mutations(name,filename,count):
  r=load(name);names=json.loads((ROOT/'migration/rewrite'/filename).read_text())
  return report(r,'checks.json','CPU-validator-test') and r['status']=='PASSED' and r['case_count']==len(r['checks'])==len(names)==count and len({x['check'] for x in r['checks']})==count and {x['check'] for x in r['checks']}==set(names) and all(x['passed'] for x in r['checks'])
 for name,file,count in [('checks','image-distance-validator-cases.json',34),('runtime-checks','image-distance-runtime-validator-cases.json',23)]:gate(name+'/all-fixed-real-validator-mutations',lambda name=name,file=file,count=count:mutations(name,file,count))
 def cold():
  r=load('cold')
  if not report(r,'cold.json','host-cold-replay') or r['status']!='PASSED' or r['return_code'] or not r['checks'] or not all(x['passed'] for x in r['checks']) or not cold_inventory(r['children']):return False
  d,m,_=sealed(r['evidence']);raw=ROOT/m['raw_artifact_dir'];groups={n:[c for c in r['children'] if c['name']==n] for n in ['contracts','original-contracts','state-contracts','build','all','frontend-build','originals','arguments','states']};cb=groups['build'][0]['report'];cf=groups['frontend-build'][0]['report']
  if cb['dependencies']!=b['dependencies'] or cb['abi_version']!=1 or cb['build_recipe_sha256']!=b['build_recipe_sha256'] or digest(raw/groups['build'][0]['relative']/Path(cb['library']).name)!=cb['library_sha256'] or cf['backend']!=cb or cf['dependencies']!=fb['dependencies'] or cf['build_recipe_sha256']!=fb['build_recipe_sha256'] or digest(raw/groups['frontend-build'][0]['relative']/Path(cf['binary']).name)!=cf['binary_sha256']:return False
  for child in r['children']:
   p=raw/child['relative'];seal=json.loads((p/'child-seal.json').read_text())['files'];src=json.loads((p/'source.json').read_text());meta=json.loads((p/'manifest.json').read_text());cs=json.loads((p/'commands.json').read_text()) if (p/'commands.json').exists() else []
   if src['commit']!=r['source_commit'] or meta['experiment_outcome'] not in {'OBSERVED','EXECUTED','PASSED'} or meta['experiment_id']!=child['report'].get('experiment_id',meta['experiment_id']) or any(c['return_code'] for c in cs) or any(not(p/n).is_file() or (p/n).stat().st_size!=v['bytes'] or digest(p/n)!=v['sha256'] for n,v in seal.items()) or any(digest(ROOT/src['source_objects'][n])!=sha or digest(ROOT/n)!=sha for n,sha in src['dependencies'].items()):return False
   sources.update(src['dependencies'])
   if child['name'] in {'all','arguments','states'} and child['report']['build']!=cb:return False
   if child['name']=='originals' and child['report']['build']!=cf:return False
   if json.loads((p/('cold.json' if child['name']=='cold' else 'run.json' if child['name'] in {'all','arguments','states','originals'} else 'build.json' if child['name'] in {'build','frontend-build'} else 'contracts.json')).read_text())!={k:v for k,v in child['report'].items() if k!='evidence'}:return False
  for name,file in [('contracts','image-distance-profile.json'),('original-contracts','image-distance-original-contract.json'),('state-contracts','image-distance-state-contract.json')]:
   if json.loads((raw/groups[name][0]['relative']/'profile.json').read_text())!=json.loads((ROOT/'migration/rewrite'/file).read_text()):return False
  for name,fn in [('all',core.validate),('arguments',arguments.validate),('states',states.validate)]:
   entry=groups[name][0];p=raw/entry['relative'];run=dict(entry['report'],outputs=str(p/'outputs'),evidence=str(p));actual=fn(run,raw_override=p) if name=='all' else fn(run)
   if actual!=json.loads((d/(name+'-CPU.json')).read_text()) or (not all(x['status']=='PASSED' for x in actual) if isinstance(actual,list) else actual['status']!='PASSED'):return False
  rules={x['case']:x for x in json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text())['workflows']};actual=[]
  for child in groups['originals']:
   p=raw/child['relative'];run=dict(child['report']);old=Path(r['clone'])/json.loads((p/'manifest.json').read_text())['raw_artifact_dir']
   for field in ['inputs','outputs','audit']:run[field]=str(p/(Path(r['clone'])/run[field]).relative_to(old))
   run['evidence']=str(p);actual.append(originals.validate_one(run,rules[run['case']],raw_override=p))
  return actual==json.loads((d/'originals-CPU.json').read_text()) and all(x['status']=='PASSED' for x in actual)
 gate('twelve-child-clean-checkout-rebuild-full-inputs-files-and-runtime',cold)
 sources.update({'tools/moat/qualify_image_distance.py','tools/moat/publish_image_distance.py','tools/moat/qualify_canny_plus.py','tools/moat/qualify_first.py','tools/moat/selected_proofs.py','tools/moat/audit.py','tools/moat/snapshot.py','tools/migration/device_guard.py','migration/environments/project.lock.json','migration/rewrite/image-acceptance-policy.json'})
 gate('three-independent-exact-source-and-proof-reviews',lambda:reviewed(review,sorted(sources),refs))
 return checks,refs,sorted(sources),b,spec

def metadata():
 r=load('all');return dict(rocm_evidence=r['evidence'],cuda_evidence=load('native')['evidence'],environment=r['evidence']+'/backend.observed.json',devices=json.loads((ROOT/r['evidence']/'backend.observed.json').read_text())['devices'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');a=p.parse_args();review=load('review') if (ROOT/'migration/reports/image-distance-review.json').exists() else None;checks,refs,sources,b,spec=collect(review);status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';print(status,[c['check'] for c in checks if not c['passed']],flush=True)
 if a.dry_run or status!='PASSED':return int(status!='PASSED')
 q=dict(sample_id=SAMPLE,kind='image-distance-full',status=status,implementation=IMPLEMENTATION,implementation_sha256=digest(ROOT/IMPLEMENTATION),dependencies=load('frontend-build')['dependencies'],case_ids=[c['case'] for c in spec['cases']],case_count=30,comparison_mode=COMPARISON,checks=checks,evidence_references=sorted(refs),source_commit=review['source_commit'],scope='Complete five-image/twelve-file C++ workflow, deterministic subpixel threshold-crossing SDF with independent CPU reference. Native signed-distance algorithm and Voronoi conventions differ; no vendor ABI/performance/wave64/Windows claim.',**metadata());e=Experiment('I2',SAMPLE,'composite-qualification',sources=[ROOT/n for n in sources]);write(e.path/'qualification.json',q);q.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status=status,checks=checks)));write(ROOT/'migration/reports/image-distance-qualification.json',q);return 0
if __name__=='__main__':raise SystemExit(main())
