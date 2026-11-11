#!/usr/bin/env python3
"""Recompute complete CCL entry qualifications from immutable independent proofs."""
import argparse,copy,json,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from qualify_canny_plus import sealed,reviewed
from image_ccl_build import dependencies
import image_ccl_reference as oracle
from image_ccl_original_reference import validate as original_validate
ENTRIES={'NPP/batchedLabelMarkersAndCompression::batchedLabelMarkersAndCompression.cpp':'rocm/ported/NPP/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompression.cpp','NPP+/batchedLabelMarkersAndCompression::batchedLabelMarkersAndCompressionNPPPlus.cpp':'rocm/ported/NPP+/batchedLabelMarkersAndCompression/batchedLabelMarkersAndCompressionNPPPlus.cpp'}
def load(name):return json.loads((ROOT/f'migration/reports/image-ccl-{name}.json').read_text())
def collect(review=None):
 spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());b=load('build');nb=load('native-build');checks=[];refs=set();sources={str(p.relative_to(ROOT)) for p in dependencies()}
 def gate(name,fn):
  try:ok=bool(fn())
  except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration,AssertionError,subprocess.CalledProcessError):ok=False
  checks.append(dict(check=name,passed=ok));return ok
 def report(r,member,backend=None):
  refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies']);return (backend is None or m['backend']==backend) and m['experiment_id']==r.get('experiment_id',m['experiment_id']) and json.loads((d/member).read_text())=={k:v for k,v in r.items() if k!='evidence'}
 def commands(r):return json.loads((ROOT/r['evidence']/'commands.json').read_text())
 def observed(r):
  d,m,_=sealed(r['evidence']);o=json.loads((d/'backend.observed.json').read_text());return o['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and o['rocm_release']=='10.1.0' and bool(o['devices']) and all(x['physical_id']!=3 for x in o['devices'])
 def frozen():
  r=load('contracts');refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies']);return r['status']=='FROZEN' and r['cases']==27 and json.loads((d/'profile.json').read_text())==spec and all(digest(ROOT/n)==sha for n,sha in spec['original_sources'].items())
 gate('frozen-27-complete-equal-value-eight-connected-contracts',frozen)
 def fixtures():
  if len(spec['cases'])!=27 or len({c['case'] for c in spec['cases']})!=27 or len(spec['originals'])!=10:return False
  for c in spec['cases']:
   d=ROOT/c['fixture']
   if digest(d/'manifest.json')!=c['manifest_sha256']:return False
   for n,v in json.loads((d/'manifest.json').read_text())['files'].items():
    if (d/n).stat().st_size!=v['bytes'] or digest(d/n)!=v['sha256']:return False
  return all(digest(ROOT/x['source'])==x['sha256'] and (ROOT/x['source']).stat().st_size==x['bytes'] for x in spec['originals'])
 gate('complete-original-inputs-and-padded-independent-fixture-identities',fixtures)
 def build():
  return report(b,'build.json','rocm-build') and observed(b) and b['status']=='BUILT' and b['dependencies']=={str(p.relative_to(ROOT)):digest(p) for p in dependencies()} and b['build_recipe_sha256']==digest(ROOT/'tools/moat/image_ccl_build.py') and digest(ROOT/b['library'])==b['library_sha256'] and len(b['binaries'])==3 and {(r['family'],r['mode']) for r in b['binaries']}=={('NPP','default'),('NPP+','default'),('NPP+','batch-compression')} and all(digest(ROOT/r['binary'])==r['sha256'] for r in b['binaries']) and all(c['return_code']==0 for c in commands(b))
 gate('current-HIP-library-and-three-real-C++-binaries',build)
 def gpu(name):
  r=load(name)
  if not report(r,'run.json','rocm-'+name) or r['build']!=b or r['return_code'] or not observed(r):return False
  cs=commands(r);m=json.loads((ROOT/r['evidence']/'manifest.json').read_text());worker='image_ccl_streams.py' if name=='streams' else 'image_ccl_worker.py';return len(cs)==1 and cs[0]['return_code']==0 and m['parent_experiment_id']==b['experiment_id'] and str(ROOT/'tools/moat'/worker) in cs[0]['argv'] and str(ROOT/b['library']) in cs[0]['argv'] and b['library_sha256'] in cs[0]['argv'] and ('rocprofv3' in cs[0]['argv'])==(name=='trace') and ('--runtime' in cs[0]['argv'])==(name=='runtime')
 for name in ['masks','runtime','trace','streams']:gate(name+'/actual-guarded-current-library-and-worker',lambda name=name:gpu(name))
 def cpu(kind,fn,count):
  v=load(kind+'-validation');actual=fn();return report(v,'results.json','CPU-reference') and v['status']=='PASSED' and v['case_count']==count and v['results']==actual and all(r.get('status','PASSED')=='PASSED' for r in actual) and json.loads((ROOT/v['evidence']/'manifest.json').read_text())['experiment_outcome']=='PASSED'
 for name,count,fn in [('masks',27,oracle.validate_masks),('runtime',44,oracle.validate_runtime),('trace',28,oracle.validate_trace),('streams',3,oracle.validate_streams)]:gate(name+'/independent-full-numerical-and-execution-checks',lambda name=name,count=count,fn=fn:cpu(name,lambda:fn(load(name)),count))
 def originals(kind):
  rs=load(kind);expected=15 if kind=='originals' else 39
  modes=[('NPP','default'),('NPP+','default'),('NPP+','batch-compression')];cases=[str(n) for n in range(1,6)] if kind=='originals' else ['default-directory','help','missing-b','zero','negative','above-five','noninteger','duplicate','unknown-option','missing-input','truncated-input','unwritable-output','no-GPU'];matrix={(f,m,c) for f,m in modes for c in cases}
  if len(rs)!=expected or {(r['family'],r['mode'],r['case']) for r in rs}!=matrix:return False
  for r in rs:
   if not report(r,'run.json','rocm-original' if kind=='originals' else 'rocm-CLI') or r['build']!=b or r['binary'] not in b['binaries'] or not observed(r):return False
   cs=commands(r);m=json.loads((ROOT/r['evidence']/'manifest.json').read_text());target=r['binary'];command=cs[0]
   if len(cs)!=1 or command['return_code']!=r['return_code'] or r['return_code']!=r['expected_return_code'] or command['argv'][0]!=str(ROOT/target['binary']) or m['parent_experiment_id']!=b['experiment_id']:return False
   if r['case']=='no-GPU' and command['environment_changes']['HIP_VISIBLE_DEVICES']!='':return False
  return True
 for kind,count in [('originals',15),('cli',39)]:
  gate(kind+'/all-original-and-conditional-branches-actual-current-binary',lambda kind=kind:originals(kind));gate(kind+'/all-complete-raw-files-counts-and-specific-CLI-errors',lambda kind=kind,count=count:cpu(kind,lambda:[original_validate(r,kind=='cli') for r in load(kind)],count))
 def nativebuild():
  return report(nb,'build.json','cuda-build') and nb['status']=='BUILT' and all(c['return_code']==0 for c in commands(nb)) and len(nb['identities'])==9 and len(nb['originals'])==3 and all(r['return_code']==0 for r in nb['originals'])
 gate('actual-two-vendor-APIs-and-three-unchanged-original-builds',nativebuild)
 def native():
  rows=load('native');rs=[r for r in rows if 'case' in r]
  if len(rs)!=54 or {(r['family'],r['case']) for r in rs}!={(f,c['case']) for f in ['NPP','NPP+'] for c in spec['cases']}:return False
  for r in rs:
   if not report(r,'run.json','cuda-run') or r['return_code'] or r['collection_return_code'] or r['build']!=nb:return False
   d,m,_=sealed(r['evidence']);cs=commands(r);c=next(c for c in spec['cases'] if c['case']==r['case']);receipt=json.loads((d/cs[1]['stdout']).read_text().splitlines()[0]);binary=nb['remote']+'/'+r['family']+'-probe'
   if len(cs)!=3 or any(x['return_code'] for x in cs) or receipt!=dict(binary_sha256=nb['identities'][binary],input_manifest_sha256=c['manifest_sha256']) or m['case_id']!=r['case'] or r['input_manifest_sha256']!=c['manifest_sha256']:return False
  return True
 gate('54-real-native-API-runs-bound-to-input-and-binary-hashes',native)
 gate('native-all-54-comparisons-with-mathematical-failures-preserved',lambda:cpu('native',lambda:oracle.validate_native(load('native')),54))
 def native_originals():
  rs=load('native-originals')
  if len(rs)!=3:return False
  for r in rs:
   if not report(r,'run.json','cuda-original') or r['return_code'] or r['collection_return_code'] or r['build']!=nb:return False
   d,m,_=sealed(r['evidence']);cs=commands(r);config=r['config'];receipt=json.loads((d/cs[0]['stdout']).read_text().splitlines()[0]);expected={Path(x['source']).name:(x['sha256'],x['bytes']) for x in spec['originals'] if x['source'].startswith(r['family']+'/')}
   if len(cs)!=2 or any(c['return_code'] for c in cs) or config['binary_sha256']!=nb['identities'][config['binary']] or receipt!=dict(binary_sha256=config['binary_sha256'],inputs=config['inputs']) or {Path(x['path']).name:(x['sha256'],x['bytes']) for x in config['inputs']}!=expected:return False
  return True
 gate('three-unchanged-native-originals-actual-binary-input-receipts',native_originals)
 gate('native-original-execution-has-sealed-successful-preflight',lambda:report(load('native-originals-preflight'),'preflight.json','host-preflight') and load('native-originals-preflight')['status']=='READY' and all(c['passed'] for c in load('native-originals-preflight')['checks']))
 def native_guard_tests():
  r=load('native-guard-tests')
  if not report(r,'checks.json','CPU-selftest') or r['status']!='PASSED' or r['case_count']!=3 or len(r['checks'])!=3 or not all(c['passed'] for c in r['checks']) or len(r['child_evidence'])!=3:return False
  for ref in r['child_evidence']:
   refs.add(ref);d,m,src=sealed(ref);sources.update(src['dependencies']);v=json.loads((d/'preflight.json').read_text())
   if m['backend']!='host-preflight' or m['experiment_outcome']!='EXPECTED_REJECTION' or v['status']!='REJECTED' or not any(c['passed'] is False for c in v['checks']):return False
  return True
 gate('three-real-native-original-preflight-failure-paths',native_guard_tests)
 gate('all-55-native-original-outputs-CPU-partition-comparison',lambda:cpu('native-originals',lambda:oracle.validate_native_originals(load('native-originals')),3))
 def mutations():
  r=load('checks');return report(r,'checks.json','CPU-validator-test') and r['status']=='PASSED' and r['case_count']==len(r['checks'])==31 and all(c['passed'] for c in r['checks']) and len({c['check'] for c in r['checks']})==31
 gate('31-actual-validator-positive-negative-and-BFS-checks',mutations)
 def cold():
  r=load('cold')
  if not report(r,'cold.json','host-cold-replay') or r['status']!='PASSED' or r['return_code'] or not r['checks'] or not all(c['passed'] for c in r['checks']) or len(r['children'])!=20:return False
  d,m,_=sealed(r['evidence']);raw=ROOT/m['raw_artifact_dir'];groups={n:[c for c in r['children'] if c['name']==n] for n in ['contracts','build','masks','runtime','streams','originals']}
  if any(len(groups[n])!=(15 if n=='originals' else 1) for n in groups):return False
  cb=groups['build'][0]['report'];binary=raw/groups['build'][0]['relative']/Path(cb['library']).name
  if cb['dependencies']!=b['dependencies'] or digest(binary)!=cb['library_sha256']:return False
  for child in r['children']:
   p=raw/child['relative'];seal=json.loads((p/'child-seal.json').read_text())['files'];src=json.loads((p/'source.json').read_text());meta=json.loads((p/'manifest.json').read_text());cs=json.loads((p/'commands.json').read_text()) if (p/'commands.json').exists() else []
   if src['commit']!=r['source_commit'] or meta['experiment_outcome'] not in {'OBSERVED','EXECUTED','PASSED'} or any(c['return_code'] for c in cs) or any(not(p/n).is_file() or (p/n).stat().st_size!=v['bytes'] or digest(p/n)!=v['sha256'] for n,v in seal.items()) or any(digest(ROOT/src['source_objects'][n])!=sha for n,sha in src['dependencies'].items()):return False
   sources.update(src['dependencies'])
   if child['name'] in {'masks','runtime','streams','originals'} and child['report']['build']!=cb:return False
  for name,fn in [('masks',oracle.validate_masks),('runtime',oracle.validate_runtime),('streams',oracle.validate_streams)]:
   entry=groups[name][0];run=dict(entry['report'],outputs=str(raw/entry['relative']/'outputs'));actual=fn(run)
   if actual!=json.loads((d/(name+'-CPU.json')).read_text()) or not all(v['status']=='PASSED' for v in actual):return False
  actual=[]
  for entry in groups['originals']:
   p=raw/entry['relative'];run=dict(entry['report'],outputs=str(p/'outputs'),evidence=str(p));actual.append(original_validate(run,raw_override=p))
  return actual==json.loads((d/'originals-CPU.json').read_text()) and all(v['status']=='PASSED' for v in actual)
 gate('clean-clone-rebuilt-library-27-masks-44-runtime-three-streams-and-15-full-workflows',cold)
 sources.update({'migration/rewrite/image-ccl-stream-contract.json','migration/rewrite/image-ccl-runtime-contract.json','tools/moat/qualify_image_ccl.py','tools/moat/publish_image_ccl.py','tools/moat/qualify_canny_plus.py','tools/moat/qualify_first.py','tools/moat/audit.py','tools/moat/snapshot.py','tools/migration/device_guard.py','migration/environments/project.lock.json','migration/rewrite/image-acceptance-policy.json'})
 gate('three-independent-review-scopes-current-executable-tree-and-proofs',lambda:reviewed(review,sorted(sources),refs))
 return checks,refs,sorted(sources),b,spec

def main():
 p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');a=p.parse_args();review=load('review') if (ROOT/'migration/reports/image-ccl-review.json').exists() else None;checks,refs,sources,b,spec=collect(review);status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';print(status,[c['check'] for c in checks if not c['passed']],flush=True)
 if a.dry_run or status!='PASSED':return int(status!='PASSED')
 rows=[]
 for sid,implementation in ENTRIES.items():
  q=dict(sample_id=sid,kind='image-ccl-full',status=status,implementation=implementation,implementation_sha256=digest(ROOT/implementation),dependencies=b['dependencies'],case_ids=[c['case'] for c in spec['cases']],case_count=27,comparison_mode=spec['comparison_mode'],checks=checks,evidence_references=sorted(refs),source_commit=review['source_commit'],scope='Complete original C++ individual and heterogeneous batch label/compression workflows, all values incl zero, NPP+ default and CUDA11U1 branches. Native mathematical defects independently recorded.');e=Experiment('I2',sid,'composite-qualification',sources=[ROOT/n for n in sources]);write(e.path/'qualification.json',q);q.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status=status,checks=checks)));r=load('masks');q.update(rocm_evidence=r['evidence'],cuda_evidence=next(x['evidence'] for x in load('native') if x.get('case')=='three-by-three-stale-root'),environment=r['evidence']+'/backend.observed.json',devices=json.loads((ROOT/r['evidence']/'backend.observed.json').read_text())['devices']);rows.append(q)
 write(ROOT/'migration/reports/image-ccl-qualification.json',dict(status='PASSED',qualifications=rows));return 0
if __name__=='__main__':raise SystemExit(main())
