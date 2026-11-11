#!/usr/bin/env python3
"""Qualify each real C3 language entry from complete shared and caller proofs."""
import argparse,copy,json,math,subprocess
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from qualify_canny_plus import sealed,reviewed
from canny_color_build import dependencies
from canny_color_reference import validate_masks,validate_originals,ORIGINAL_CASES
from canny_color_runtime_validate import validate as runtime_validate
from canny_color_cpp_reference import validate as cpp_validate
from canny_color_original_reference import validate as native_original_validate
from canny_color_cli import validate as cli_validate,FAULTS as CLI_CASES

def load(name):return json.loads((ROOT/('migration/reports/canny-color-'+name+'.json')).read_text())

def collect(language,review=None):
 spec=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());b=load('build');nb=load('native-build');native=load('native');gpu=load('rocm');originals=load('originals');checks=[];refs=set();sources=set();sid='NPP/nppCanny::npp_canny_simple.'+('cpp' if language=='cpp' else 'py');implementation='rocm/ported/NPP/nppCanny/npp_canny_simple.'+('cpp' if language=='cpp' else 'py')
 def gate(name,fn):
  try:ok=bool(fn())
  except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration,AssertionError,subprocess.CalledProcessError):ok=False
  checks.append(dict(check=name,passed=ok));return ok
 def report(r,member,backend=None):
  refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies'])
  return (not backend or m['backend']==backend) and m['experiment_id']==r.get('experiment_id',m['experiment_id']) and json.loads((d/member).read_text())=={k:v for k,v in r.items() if k not in {'evidence','parent'}}
 gate('two-original-languages-and-22-unique-inputs',lambda:language in {'cpp','python'} and sid in spec['sample_ids'] and implementation in spec['implementations'] and len(spec['cases'])==22 and len({c['case'] for c in spec['cases']})==22 and spec['original']['warmup']==1 and spec['original']['iterations']==10 and all(digest(ROOT/n)==sha for n,sha in spec['sources'].items()))
 def frozen():
  refs.add(spec['fixture_evidence']);d,m,src=sealed(spec['fixture_evidence']);sources.update(src['dependencies']);expected=dict(spec);expected.pop('fixture_evidence');return json.loads((d/'profile.json').read_text())==expected and m['backend']=='CPU-fixtures'
 gate('frozen-separate-classical-C3-contract-and-holdouts',frozen)
 def replay():
  r=load('fixture-replay');refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies']);v=json.loads((d/'replay.json').read_text());return v=={k:x for k,x in r.items() if k!='evidence'} and v['status']=='PASSED' and len(v['checks'])==22 and {c['check'] for c in v['checks']}=={c['case'] for c in spec['cases']} and all(c['passed'] is True for c in v['checks']) and m['experiment_outcome']=='PASSED'
 gate('deterministic-input-and-PNG-reconstruction',replay)
 def sdk():
  r=json.loads((ROOT/'migration/reports/image-opencv-sdk.json').read_text());prefix=ROOT/r['prefix'];return report(r,'SDK.json','host-setup') and r==b['SDK'] and r['status']=='READY' and digest(prefix/'manifest.json')==b['SDK_manifest_sha256'] and bool(r['headers']) and bool(r['libraries']) and all(digest(prefix/n)==v['sha256'] for n,v in r['headers'].items()) and all(digest(prefix/'lib'/n)==v['sha256'] for n,v in r['libraries'].items())
 gate('actual-private-OpenCV-headers-and-SO-identities',sdk)
 def build():
  return report(b,'build.json','rocm-build') and b['status']=='BUILT' and set(b['dependencies'])=={str(p.relative_to(ROOT)) for p in dependencies()} and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items()) and digest(ROOT/b['library'])==b['library_sha256'] and digest(ROOT/b['binary'])==b['binary_sha256'] and b['build_recipe_sha256']==digest(ROOT/'tools/moat/canny_color_build.py') and all(c['return_code']==0 for c in json.loads((ROOT/b['evidence']/'commands.json').read_text()))
 gate('current-C-ABI-library-and-real-C++-binary-build',build)
 gate('native-22-unique-cases',lambda:len(native)==22 and {r['case'] for r in native}=={c['case'] for c in spec['cases']})
 gate('native-real-NPP-build',lambda:report(nb,'build.json','cuda-build') and nb['status']=='BUILT' and len(nb['libraries'])==2 and all(c['return_code']==0 for c in json.loads((ROOT/nb['evidence']/'commands.json').read_text())))
 for r in native:
  def native_case(r=r):
   if not report(r,'run.json','cuda-run') or r['build']!=nb or r['return_code'] or r['collection_return_code']:return False
   d,m,_=sealed(r['evidence']);cs=json.loads((d/'commands.json').read_text());receipt=json.loads((d/cs[0]['stdout']).read_text().splitlines()[0]);case=next(c for c in spec['cases'] if c['case']==r['case']);return m['case_id']==r['case'] and m['parent_experiment_id']==nb['experiment_id'] and m['comparison_id']==case['manifest_sha256'] and receipt==dict(binary_sha256=nb['binary_sha256'],input_manifest_sha256=case['manifest_sha256']) and all(c['return_code']==0 for c in cs) and nb['remote']+'/canny' in cs[0]['argv'][-1] and 'CUDA_VISIBLE_DEVICES' in cs[0]['argv'][-1]
  gate('native/'+r['case']+'/frozen-command-and-binary-receipt',native_case)
 def gpu_run(r,lang):
  if not report(r,'run.json','rocm-run' if lang=='masks' else 'rocm-original') or r['build']!=b or r['return_code']:return False
  d,m,_=sealed(r['evidence']);cs=json.loads((d/'commands.json').read_text());snapshot=json.loads((d/'backend.observed.json').read_text());target=ROOT/b['binary'] if lang=='cpp' else ROOT/'rocm/ported/NPP/nppCanny/npp_canny_simple.py' if lang=='python' else ROOT/'tools/moat/canny_color_worker.py'
  return m['parent_experiment_id']==b['experiment_id'] and len(cs)==1 and cs[0]['return_code']==0 and str(target) in cs[0]['argv'] and cs[0]['environment_changes']['MIGRATION_IMAGE_COLOR_LIBRARY']==str(ROOT/b['library']) and snapshot['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and snapshot['rocm_release']=='10.1.0' and bool(snapshot['devices']) and all(d['physical_id']!=3 for d in snapshot['devices'])
 gate('actual-guarded-GPU-22-mask-producer',lambda:len(gpu)==1 and gpu_run(gpu[0],'masks'))
 gate('all-ten-original-language-workflows',lambda:len(originals)==10 and {(r['language'],r['case']) for r in originals}=={(l,c) for l in ['cpp','python'] for c in ORIGINAL_CASES})
 for r in originals:gate('original/'+r['language']+'/'+r['case']+'/actual-current-binary',lambda r=r:gpu_run(r,r['language']))
 def cpu(name,actual):
  r=load(name);refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies']);stored=json.loads((d/'results.json').read_text());value=actual();return stored==value=={k:v for k,v in r.items() if k not in {'evidence','parent'}} and value['status']=='PASSED' and bool(value['checks']) and all(c['passed'] is True for c in value['checks']) and m['experiment_outcome']=='PASSED'
 gate('22-full-masks-independent-CPU-and-native-differences',lambda:cpu('validation',lambda:validate_masks(gpu[0],spec,native)))
 gate('ten-original-file-preprocessing-PNG-and-loop-checks',lambda:cpu('originals-validation',lambda:validate_originals(originals,spec)))
 for name,is_trace in [('runtime',False),('trace',True)]:
  r=load(name)
  def run_ok(r=r,is_trace=is_trace):
   if not report(r,'run.json','rocm-trace' if is_trace else 'rocm-runtime') or r['build']!=b or r['return_code']:return False
   d,m,_=sealed(r['evidence']);cs=json.loads((d/'commands.json').read_text());snapshot=json.loads((d/'backend.observed.json').read_text());return len(cs)==1 and cs[0]['return_code']==0 and str(ROOT/b['library']) in cs[0]['argv'] and m['parent_experiment_id']==b['experiment_id'] and bool(snapshot['devices']) and all(x['physical_id']!=3 for x in snapshot['devices']) and snapshot['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03'
  gate(name+'/actual-guarded-current-library',run_ok);gate(name+'/independent-input-output-return-code-and-dispatch-checks',lambda name=name,r=r,is_trace=is_trace:cpu(name+'-validation',lambda:runtime_validate(r,is_trace)))
 cpp=load('cpp-runtime')
 def cpp_run():
  if not report(cpp,'run.json','rocm-C++-runtime') or cpp['build']!=b or cpp['return_code'] or digest(ROOT/cpp['binary'])!=cpp['binary_sha256']:return False
  d,m,_=sealed(cpp['evidence']);cs=json.loads((d/'commands.json').read_text());return m['parent_experiment_id']==b['experiment_id'] and len(cs)==2 and all(c['return_code']==0 for c in cs) and cs[1]['argv']==[str(ROOT/cpp['binary']),str(ROOT/cpp['fixture']),str(ROOT/cpp['outputs'])] and str(ROOT/'rocm/probes/image/canny_color_cpp_contract.cpp') in cs[0]['argv']
 gate('actual-C++-class-ROI-errors-and-independent-instances',cpp_run);gate('C++-class-complete-CPU-pixels-and-specific-diagnostics',lambda:cpu('cpp-runtime-validation',lambda:cpp_validate(cpp)))
 cli=load('cli');gate('all-ten-CLI-and-no-device-branches',lambda:len(cli)==10 and {(r['language'],r['case']) for r in cli}=={(l,c) for l in ['cpp','python'] for c in CLI_CASES})
 for r in cli:
  def cli_run(r=r):
   if not report(r,'run.json','rocm-CLI') or r['build']!=b:return False
   d,m,_=sealed(r['evidence']);cs=json.loads((d/'commands.json').read_text());target=[str(ROOT/b['binary'])] if r['language']=='cpp' else ['/opt/venv/bin/python3',str(ROOT/'rocm/ported/NPP/nppCanny/npp_canny_simple.py')]
   return m['parent_experiment_id']==b['experiment_id'] and len(cs)==1 and cs[0]['argv']==target and cs[0]['return_code']==r['return_code'] and cs[0]['cwd']==str(ROOT/r['work']) and cs[0]['environment_changes']['HIP_VISIBLE_DEVICES']==('' if r['case']=='no-GPU' else '0')
  gate('CLI/'+r['language']+'/'+r['case']+'/actual-entry-and-device-mask',cli_run)
 gate('CLI-default-full-pixels-and-specific-rejections',lambda:cpu('cli-validation',lambda:cli_validate(cli)))
 def cli_timings():
  for row in cli:
   if row['case']!='default-image':continue
   info=json.loads((ROOT/row['audit']/'workflow.json').read_text())
   if not all(math.isfinite(t) and t>0 for t in [*info['timings_ms'],info['gray_ms'],info['color_ms']]):return False
  return True
 gate('default-CLI-measurements-are-real-positive-finite',cli_timings)
 def mutations():
  r=load('checks');refs.add(r['evidence']);d,m,src=sealed(r['evidence']);sources.update(src['dependencies']);v=json.loads((d/'checks.json').read_text());names=json.loads((ROOT/'migration/rewrite/canny-color-negative-cases.json').read_text());return v=={k:x for k,x in r.items() if k!='evidence'} and v==json.loads((d/'validation.json').read_text()) and v['status']=='PASSED' and v['case_count']==len(names)==39 and len(v['checks'])==39 and {c['check'] for c in v['checks']}==set(names) and all(c['passed'] is True for c in v['checks']) and m['experiment_outcome']=='PASSED'
 gate('complete-39-validator-positive-and-negative-experiments',mutations)
 original=load('original-cuda-cpp')
 def original_run():
  if not report(original,'result.json','cuda-original') or original['status']!='EXECUTED' or original['return_code'] or original['original_source_sha256']!=spec['sources']['NPP/nppCanny/npp_canny_simple.cpp']:return False
  d,m,_=sealed(original['evidence']);cs=json.loads((d/'commands.json').read_text());return m['sample_id']=='NPP/nppCanny::npp_canny_simple.cpp' and all(c['return_code']==0 for c in cs) and any(c['phase']=='build-unmodified-original-C++' and '/usr/local/cuda-13.4/bin/nvcc' in c['argv'][-1] for c in cs) and any(c['phase']=='actual-unmodified-original-file-benchmark' and original['binary_sha256'] in c['argv'][-1] and 'CUDA_VISIBLE_DEVICES' in c['argv'][-1] for c in cs)
 gate('unmodified-original-CUDA-C++-workflow',original_run);gate('original-CUDA-three-PNGs-match-native-API-and-OpenCV',lambda:cpu('original-cuda-validation',lambda:native_original_validate(original)))
 py=load('original-cuda-python');gate('original-CUDA-Python-prerequisite-status-distinct',lambda:report(py,'result.json','cuda-original') and py['status']=='BLOCKED' and py['return_code']!=0 and py['original_source_sha256']==spec['sources']['NPP/nppCanny/npp_canny_simple.py'] and 'No module named' in (ROOT/py['evidence']/'logs/0001-original-Python-toolchain-inventory.stderr.log').read_text())
 def cold():
  r=load('cold')
  if not report(r,'cold.json','host-cold-replay') or r['status']!='PASSED' or r['return_code'] or not r['checks'] or not all(c['passed'] is True for c in r['checks']) or len(r['children'])!=15:return False
  d,m,_=sealed(r['evidence']);raw=ROOT/m['raw_artifact_dir'];groups={n:[c for c in r['children'] if c['name']==n] for n in ['SDK','environment','fixtures','build','masks','originals']}
  if any(len(groups[n])!=(10 if n=='originals' else 1) for n in groups):return False
  build=groups['build'][0]['report'];where=raw/groups['build'][0]['relative'];library=where/Path(build['library']).name
  if build['dependencies']!=b['dependencies'] or digest(library)!=build['library_sha256'] or any(build['SDK'][n]!=b['SDK'][n] for n in ['headers','libraries']):return False
  for child in r['children']:
   path=raw/child['relative'];seal=json.loads((path/'child-seal.json').read_text())['files'];src=json.loads((path/'source.json').read_text());meta=json.loads((path/'manifest.json').read_text());commands=json.loads((path/'commands.json').read_text()) if (path/'commands.json').exists() else []
   if meta['experiment_outcome'] not in {'EXECUTED','PASSED'} or src['commit']!=r['source_commit'] or any(c['return_code']!=0 for c in commands) or any(not (path/n).is_file() or (path/n).stat().st_size!=v['bytes'] or digest(path/n)!=v['sha256'] for n,v in seal.items()) or any(digest(ROOT/src['source_objects'][n])!=sha for n,sha in src['dependencies'].items()):return False
   if child['name'] in {'masks','originals'} and (child['report']['build']!=build or meta['parent_experiment_id']!=build['experiment_id']):return False
  masks=copy.deepcopy(groups['masks'][0]['report']);masks['outputs']=str(raw/groups['masks'][0]['relative']/'outputs');actual=validate_masks(masks,spec,native)
  if actual!=json.loads((d/'masks-CPU.json').read_text()) or actual['status']!='PASSED':return False
  originals=[]
  for entry in groups['originals']:
   row=copy.deepcopy(entry['report']);row['outputs']=str(raw/entry['relative']/'outputs');row['audit']=str(raw/entry['relative']/'audit');originals.append(row)
  actual=validate_originals(originals,spec)
  return actual==json.loads((d/'originals-CPU.json').read_text()) and actual['status']=='PASSED' and actual['case_count']==10
 gate('fresh-SDK-checkout-build-22-masks-and-ten-originals',cold)
 sources.update(b['dependencies']);sources.update({'tools/moat/qualify_canny_color.py','tools/moat/publish_canny_color.py','tools/moat/qualify_canny_plus.py','tools/moat/qualify_first.py','tools/moat/audit.py','tools/moat/snapshot.py','tools/migration/device_guard.py','migration/environments/project.lock.json','migration/rewrite/image-acceptance-policy.json'})
 # The SDK's generated lock is an immutable JSON data object, not a tracked
 # source path. Review its committed content-addressed copy while retaining
 # the original path in the qualification's current dependency closure.
 names=set(sources)
 for name in ['build/image-opencv/manifest.json']:
  if name in names:
   object_name='migration/source-objects/'+digest(ROOT/name);names.remove(name);names.add(object_name);sources.add(object_name)
 gate('three-distinct-scopes-review-current-source-and-proof-set',lambda:reviewed(review,sorted(names),refs))
 return checks,refs,sorted(sources),b,spec

def main():
 p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');a=p.parse_args();path=ROOT/'migration/reports/canny-color-review.json';review=json.loads(path.read_text()) if path.exists() else None;rows=[];failed=False
 for language in ['cpp','python']:
  checks,refs,sources,b,spec=collect(language,review);status='PASSED' if checks and all(c['passed'] for c in checks) else 'FAILED';print(language,status,[c['check'] for c in checks if not c['passed']],flush=True)
  failed|=status!='PASSED'
  if not a.dry_run and status=='PASSED':
   implementation='rocm/ported/NPP/nppCanny/npp_canny_simple.'+('cpp' if language=='cpp' else 'py');sid='NPP/nppCanny::'+Path(implementation).name;row=dict(sample_id=sid,kind='image-canny-c3-full/'+language,status=status,implementation=implementation,implementation_sha256=digest(ROOT/implementation),dependencies=b['dependencies'],case_ids=[c['case'] for c in spec['cases']],case_count=22,comparison_mode=spec['comparison_mode'],checks=checks,evidence_references=sorted(refs),source_commit=review['source_commit'],scope='Complete original C++/Python three-output/10-loop workflow; explicit classical 8-connected hysteresis variant, independent exact CPU masks, native differences, streams/concurrent instances and real negative/trace/cold-checkout proofs. No native pixel-identity or cross-device performance claim.');e=Experiment('I1',sid,'composite-qualification',sources=[ROOT/n for n in sources]);write(e.path/'qualification.json',row);row.update(qualification_id=e.id,evidence=e.finish('PASSED',dict(status=status,checks=checks)));run=load('rocm')[0];d=ROOT/run['evidence'];row.update(rocm_evidence=run['evidence'],cuda_evidence=load('native')[0]['evidence'],environment=str((d/'backend.observed.json').relative_to(ROOT)),devices=json.loads((d/'backend.observed.json').read_text())['devices']);rows.append(row)
 if not a.dry_run:write(ROOT/'migration/reports/canny-color-qualification.json',dict(status='PASSED' if len(rows)==2 else 'FAILED',qualifications=rows))
 return int(failed)
if __name__=='__main__':raise SystemExit(main())
