#!/usr/bin/env python3
"""Qualify both contour entrypoints from full, independently checked evidence."""
import argparse,ast,json,shlex,subprocess
import numpy as np
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from qualify_canny_plus import sealed,reviewed
from image_contour_build import dependencies
import image_contour_reference as masks
import image_contour_original_reference as originals
import image_contour_arguments_reference as arguments
import image_contour_data_reference as data
import image_contour_states_reference as states
import image_contour_cli as cli
import image_contour_trace as trace
ENTRIES={'NPP/findContour::findContour.cpp':'rocm/ported/NPP/findContour/findContour.cpp','NPP+/findContour::findContourNPPPlus.cpp':'rocm/ported/NPP+/findContour/findContourNPPPlus.cpp'}
def load(name):return json.loads((ROOT/f'migration/reports/image-contour-{name}.json').read_text())
def cold_inventory(children):
 sizes={'contracts':1,'build':1,'all':1,'frontends-build':1,'originals':15,'data-errors':1,'arguments':1,'states':1};rules=json.loads((ROOT/'migration/rewrite/image-contour-original-contract.json').read_text())['cases']
 if len(children)!=22 or {c['name'] for c in children}!=set(sizes) or len({c['relative'] for c in children})!=22 or len({c['report']['evidence'] for c in children})!=22:return False
 for name,count in sizes.items():
  rows=[c for c in children if c['name']==name]
  if len(rows)!=count or {c['index'] for c in rows}!=set(range(count)):return False
 ids=[(c['report']['family'],c['report']['case'],c['report']['mode']) for c in children if c['name']=='originals'];return len(set(ids))==15 and set(ids)=={(r['family'],r['case'],r['mode']) for r in rules}

def native_result(r,spec,commands):
 from image_ccl_reference import reference,canonical
 from image_contour_model import boundaries8
 family=r['family'];source=family+'/findContour/'+('findContour.cpp' if family=='NPP' else 'findContourNPPPlus.cpp');case=next(c for c in spec['cases'] if c['case']==('npp' if family=='NPP' else 'plus')+'-original-CircuitBoard');original=case['original'];w,h=case['width'],case['height'];n=w*h;shape=f'{w}x{h}';names={'CircuitBoard_'+shape+'_8u.raw':n,'CircuitBoard_LabelMarkersUF_8Way_'+shape+'_32u.raw':4*n,'CircuitBoard_CompressedMarkerLabelsUF_8Way_'+shape+'_32u.raw':4*n,'CircuitBoard_Contours_8Way_'+shape+'_8u.raw':n}
 if family=='NPP+':names['CircuitBoard_ContoursReconstructed_8Way_'+shape+'_8u.raw']=n
 output=ROOT/r['outputs']
 if set(r['files'])!=set(names) or {p.name for p in output.iterdir()}!=set(names) or r['source']!=source or r['source_sha256']!=digest(ROOT/source) or r['input_sha256']!=original['sha256']:raise ValueError('complete frozen native source/input/output inventory')
 for name,size in names.items():
  p=output/name;v=r['files'][name]
  if p.stat().st_size!=size or v['bytes']!=size or digest(p)!=v['sha256']:raise ValueError('complete native raw bytes')
 input_path=output/('CircuitBoard_'+shape+'_8u.raw')
 if digest(input_path)!=original['sha256']:raise ValueError('native frozen input hash')
 execute=next(c for c in commands if c['phase']=='execute-unmodified-native-default');code=shlex.split(execute['argv'][-1])[-1];tree=ast.parse(code);config=next(json.loads(node.value.args[0].value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='c' for x in node.targets));remote='/tmp/'+r['experiment_id'];expected_config=dict(source=remote+'/'+Path(source).name,source_sha256=digest(ROOT/source),input=remote+'/images/'+input_path.name,input_sha256=original['sha256'],binary=remote+'/original',cwd=remote)
 if config!=expected_config:raise ValueError('native actual execution configuration')
 meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];receipt=json.loads((raw/execute['stdout']).read_text().splitlines()[0]);compile=next(c for c in commands if c['phase']=='compile-unmodified-original');args=shlex.split(compile['argv'][-1])
 if receipt.get('source_sha256')!=config['source_sha256'] or receipt.get('input_sha256')!=config['input_sha256'] or len(receipt.get('binary_sha256',''))!=64 or config['source'] not in args or args[args.index('-o')+1]!=config['binary']:raise ValueError('actual native build/run hash receipt')
 image=np.fromfile(input_path,np.uint8).reshape(h,w);expected,_,k=reference(image);result=dict(family=family,expected_components=k,label_partitions={});labels=None
 for key in ['LabelMarkersUF','CompressedMarkerLabelsUF']:
  labels=np.fromfile(output/('CircuitBoard_'+key+'_8Way_'+shape+'_32u.raw'),'<u4').reshape(h,w);result['label_partitions'][key]=dict(components=len(np.unique(labels)),partition_mismatched_pixels=int(np.count_nonzero(canonical(labels)!=expected)))
 mask=np.fromfile(output/('CircuitBoard_Contours_8Way_'+shape+'_8u.raw'),np.uint8).reshape(h,w)
 if set(np.unique(mask))!={0,255} or not np.array_equal(mask==0,boundaries8(labels)):raise ValueError('native contour encoding and own-partition eight-neighbor geometry')
 return result
def collect(review=None):
 spec=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());b=load('build');fb=load('frontends-build');refs=set();sources={str(p.relative_to(ROOT)) for p in dependencies()};checks=[]
 def gate(name,fn):
  try:ok=bool(fn())
  except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration,AssertionError,subprocess.CalledProcessError):ok=False
  checks.append(dict(check=name,passed=ok));return ok
 def report(r,member,backend=None):
  refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies']);return (backend is None or m['backend']==backend) and json.loads((d/member).read_text())=={k:v for k,v in r.items() if k!='evidence'}
 def observed(r):
  d,_,_=sealed(r['evidence']);o=json.loads((d/'backend.observed.json').read_text());return o['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and o['rocm_release']=='10.1.0' and bool(o['devices']) and all(x['physical_id']!=3 for x in o['devices'])
 def commands(r):return json.loads((ROOT/r['evidence']/'commands.json').read_text())
 def frozen():
  r=load('contracts');refs.add(r['evidence']);d,_,src=sealed(r['evidence']);sources.update(src['dependencies']);return r['status']=='FROZEN' and r['case_count']==22 and json.loads((d/'profile.json').read_text())==spec and len(spec['cases'])==22 and len({c['case'] for c in spec['cases']})==22
 gate('frozen-full-22-input-contract',frozen)
 def fixtures():
  for c in spec['cases']:
   p=ROOT/c['fixture']
   if digest(p/'manifest.json')!=c['manifest_sha256']:return False
   for n,v in json.loads((p/'manifest.json').read_text())['files'].items():
    if (p/n).stat().st_size!=v['bytes'] or digest(p/n)!=v['sha256']:return False
   if c.get('original') and digest(ROOT/c['original']['source'])!=c['original']['sha256']:return False
  return True
 gate('full-original-and-independent-input-byte-identities',fixtures)
 def builds():
  expected={str(p.relative_to(ROOT)):digest(p) for p in dependencies()}
  if not report(b,'build.json','rocm-build') or not observed(b) or b['status']!='BUILT' or b['abi_version']!=2 or b['dependencies']!=expected or b['build_recipe_sha256']!=digest(ROOT/'tools/moat/image_contour_build.py') or digest(ROOT/b['library'])!=b['library_sha256'] or any(c['return_code'] for c in commands(b)):return False
  return report(fb,'build.json','rocm-build') and observed(fb) and fb['backend']==b and fb['status']=='BUILT' and fb['build_recipe_sha256']==digest(ROOT/'tools/moat/image_contour_frontends_build.py') and all(digest(ROOT/n)==sha for n,sha in fb['dependencies'].items()) and len(fb['binaries'])==2 and {r['family'] for r in fb['binaries']}=={'NPP','NPP+'} and all(digest(ROOT/r['binary'])==r['binary_sha256'] for r in fb['binaries']) and all(c['return_code']==0 for c in commands(fb))
 gate('ABI2-current-HIP-backend-and-both-actual-C++-binaries',builds)
 def gpu(name,backend,worker):
  r=load(name)
  if not report(r,'run.json',backend) or not observed(r) or r['return_code'] or r['build']!=b:return False
  cs=commands(r);m=json.loads((ROOT/r['evidence']/'manifest.json').read_text());return len(cs)==1 and cs[0]['return_code']==0 and str(ROOT/'tools/moat'/worker) in cs[0]['argv'] and str(ROOT/b['library']) in cs[0]['argv'] and b['library_sha256'] in cs[0]['argv'] and m['parent_experiment_id']==b['experiment_id']
 for name,backend,worker in [('all','rocm-prototype','image_contour_worker.py'),('data-errors','rocm-data-errors','image_contour_data_errors.py'),('arguments','rocm-runtime','image_contour_arguments.py'),('states','rocm-runtime','image_contour_states.py'),('trace','rocm-trace','image_contour_worker.py')]:gate(name+'/actual-guarded-current-library',lambda name=name,backend=backend,worker=worker:gpu(name,backend,worker))
 def cpu(name,fn,count):
  r=load(name+'-validation');actual=fn(load(name));expected=actual if isinstance(actual,dict) else dict(status='PASSED' if all(x['status']=='PASSED' for x in actual) else 'FAILED',case_count=len(actual),results=actual)
  if name=='originals':expected['file_count']=sum(x['file_count'] for x in actual)
  return report(r,'results.json','CPU-reference') and r['status']=='PASSED' and r['case_count']==count and {k:v for k,v in r.items() if k!='evidence'}==expected
 for name,fn,count in [('all',lambda r:masks.validate(r,expected_small=False),22),('originals',originals.validate,15),('data-errors',data.validate,26),('arguments',arguments.validate,61),('states',states.validate,11),('cli',cli.validate,32),('trace',trace.validate,18)]:gate(name+'/recomputed-independent-complete-contract',lambda name=name,fn=fn,count=count:cpu(name,fn,count))
 def original_runs(name):
  rows=load(name)
  for r in rows:
   if not report(r,'run.json','rocm-original' if name=='originals' else 'rocm-CLI') or not observed(r) or r['build']!=fb or r['binary'] not in fb['binaries']:return False
   cs=commands(r);m=json.loads((ROOT/r['evidence']/'manifest.json').read_text())
   if len(cs)!=1 or cs[0]['return_code']!=r['return_code'] or cs[0]['argv'][0]!=str(ROOT/r['binary']['binary']) or m['parent_experiment_id']!=fb['experiment_id']:return False
  return len(rows)==(15 if name=='originals' else 32)
 for name in ['originals','cli']:gate(name+'/complete-current-executables-and-processes',lambda name=name:original_runs(name))
 def native():
  rs=json.loads((ROOT/'migration/reports/image-I2-contour-native-originals.json').read_text())
  if len(rs)!=2 or {r['family'] for r in rs}!={'NPP','NPP+'}:return False
  for r in rs:
   if not report(r,'run.json','cuda-original') or any(r[k] for k in ['build_return_code','run_return_code','collection_return_code']) or digest(ROOT/r['source'])!=r['source_sha256'] or any(c['return_code'] for c in commands(r)):return False
  actual=[native_result(r,spec,commands(r)) for r in rs];r=json.loads((ROOT/'migration/reports/image-I2-contour-native-research.json').read_text());refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies'])
  if m['backend']!='CPU-research' or json.loads((d/'results.json').read_text())!=r['results'] or r['status']!='OBSERVED' or len(r['results'])!=2 or {x['family'] for x in r['results']}!={'NPP','NPP+'}:return False
  previous={x['family']:x for x in r['results']};return all(x['expected_components']==262 and x['label_partitions']['CompressedMarkerLabelsUF']['partition_mismatched_pixels']>0 and all(x[k]==previous[x['family']][k] for k in ['family','expected_components','label_partitions']) for x in actual)
 gate('unchanged-CUDA-originals-and-vendor-mathematical-failures-separate',native)
 def legacy():
  r=load('legacy-data-error');v=load('legacy-data-error-validation');return report(r,'run.json','rocm-data-errors') and report(v,'results.json','CPU-reference') and r['legacy'] is True and r['build']['experiment_id']=='20261111T145921.077073Z-I2-rocm-build-b6c174a07f' and digest(ROOT/r['build']['library'])==r['build']['library_sha256'] and v['status']=='FAILED_CONTRACT' and data.legacy_comparison(r)=={k:x for k,x in v.items() if k!='evidence'}
 gate('real-ABI1-truncated-geometry-failure-retained-and-excluded',legacy)
 def mutations():
  r=load('checks');names=json.loads((ROOT/'migration/rewrite/image-contour-validator-cases.json').read_text());return report(r,'checks.json','CPU-validator-test') and r['status']=='PASSED' and r['case_count']==len(r['checks'])==len(names)==58 and {x['check'] for x in r['checks']}==set(names) and all(x['passed'] for x in r['checks'])
 gate('58-fixed-real-validator-mutations',mutations)
 def cold():
  r=load('cold')
  if not report(r,'cold.json','host-cold-replay') or r['status']!='PASSED' or r['return_code'] or not r['checks'] or not all(x['passed'] for x in r['checks']) or not cold_inventory(r['children']):return False
  d,m,_=sealed(r['evidence']);raw=ROOT/m['raw_artifact_dir'];groups={n:[c for c in r['children'] if c['name']==n] for n in ['contracts','build','all','frontends-build','originals','data-errors','arguments','states']}
  if any(len(groups[n])!=(15 if n=='originals' else 1) for n in groups):return False
  cb=groups['build'][0]['report'];cf=groups['frontends-build'][0]['report'];lib=raw/groups['build'][0]['relative']/Path(cb['library']).name
  if cb['dependencies']!=b['dependencies'] or cb['abi_version']!=2 or digest(lib)!=cb['library_sha256'] or cf['backend']!=cb:return False
  for child in r['children']:
   p=raw/child['relative'];seal=json.loads((p/'child-seal.json').read_text())['files'];src=json.loads((p/'source.json').read_text());meta=json.loads((p/'manifest.json').read_text());cs=json.loads((p/'commands.json').read_text()) if (p/'commands.json').exists() else []
   if src['commit']!=r['source_commit'] or meta['experiment_outcome'] not in {'OBSERVED','EXECUTED','PASSED'} or meta['experiment_id']!=child['report'].get('experiment_id',meta['experiment_id']) or any(c['return_code'] for c in cs) or any(not(p/n).is_file() or (p/n).stat().st_size!=v['bytes'] or digest(p/n)!=v['sha256'] for n,v in seal.items()) or any(digest(ROOT/src['source_objects'][n])!=sha for n,sha in src['dependencies'].items()):return False
   sources.update(src['dependencies'])
   if child['name'] in {'all','data-errors','arguments','states'} and child['report']['build']!=cb:return False
   if child['name']=='originals' and child['report']['build']!=cf:return False
  for name,fn in [('all',masks.validate),('data-errors',data.validate),('arguments',arguments.validate),('states',states.validate)]:
   entry=groups[name][0];run=dict(entry['report'],outputs=str(raw/entry['relative']/'outputs'));actual=fn(run)
   if actual!=json.loads((d/(name+'-CPU.json')).read_text()) or (not all(x['status']=='PASSED' for x in actual) if isinstance(actual,list) else actual['status']!='PASSED'):return False
  rules=json.loads((ROOT/'migration/rewrite/image-contour-original-contract.json').read_text())['cases'];bykey={(x['family'],x['case'],x['mode']):x for x in rules};identities=[(x['report']['family'],x['report']['case'],x['report']['mode']) for x in groups['originals']];actual=[]
  if len(identities)!=len(bykey) or len(set(identities))!=len(identities) or set(identities)!=set(bykey):return False
  for child in groups['originals']:
   p=raw/child['relative'];run=dict(child['report']);old=Path(r['clone'])/json.loads((p/'manifest.json').read_text())['raw_artifact_dir']
   for field in ['input','outputs','audit']:run[field]=str(p/(Path(r['clone'])/run[field]).relative_to(old))
   run['evidence']=str(p);actual.append(originals.validate_one(run,bykey[(run['family'],run['case'],run['mode'])],raw_override=p))
  return actual==json.loads((d/'originals-CPU.json').read_text()) and all(x['status']=='PASSED' for x in actual)
 gate('clean-checkout-new-build-22-full-inputs-15-workflows-and-all-runtime-contracts',cold)
 sources.update({'tools/moat/qualify_image_contour.py','tools/moat/publish_image_contour.py','tools/moat/qualify_canny_plus.py','tools/moat/qualify_first.py','tools/moat/audit.py','tools/moat/snapshot.py','tools/migration/device_guard.py','migration/environments/project.lock.json','migration/rewrite/image-acceptance-policy.json'})
 gate('three-independent-current-tree-and-proof-reviews',lambda:reviewed(review,sorted(sources),refs))
 return checks,refs,sorted(sources),b,spec

def main():
 p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');a=p.parse_args();review=load('review') if (ROOT/'migration/reports/image-contour-review.json').exists() else None;checks,refs,sources,b,spec=collect(review);status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';print(status,[c['check'] for c in checks if not c['passed']],flush=True)
 if a.dry_run or status!='PASSED':return int(status!='PASSED')
 rows=[]
 for sid,implementation in ENTRIES.items():
  q=dict(sample_id=sid,kind='image-contour-full',status=status,implementation=implementation,implementation_sha256=digest(ROOT/implementation),dependencies=load('frontends-build')['dependencies'],case_ids=[c['case'] for c in spec['cases']],case_count=22,comparison_mode=spec['comparison_mode'],checks=checks,evidence_references=sorted(refs),source_commit=review['source_commit'],scope='Complete original C++ masks, compact labels, component statistics, ordered closed geometry, range/bypass reconstruction and diagnostics. Project cell-edge representation replaces proprietary packed ABI; native partition defects remain separate.');e=Experiment('I2',sid,'composite-qualification',sources=[ROOT/n for n in sources]);write(e.path/'qualification.json',q);q.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status=status,checks=checks)));r=load('all');q.update(rocm_evidence=r['evidence'],cuda_evidence=json.loads((ROOT/'migration/reports/image-I2-contour-native-originals.json').read_text())[0]['evidence'],environment=r['evidence']+'/backend.observed.json',devices=json.loads((ROOT/r['evidence']/'backend.observed.json').read_text())['devices']);rows.append(q)
 write(ROOT/'migration/reports/image-contour-qualification.json',dict(status='PASSED',qualifications=rows));return 0
if __name__=='__main__':raise SystemExit(main())
