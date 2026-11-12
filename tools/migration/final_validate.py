#!/usr/bin/env python3
"""Audit scope, selected proof identities, generated documentation and environment gates."""
import collections,datetime,hashlib,json,pathlib,re,subprocess,urllib.parse,sys
from catalog import ROOT,BASE,CANDIDATES
from run import digest
from operator_support import summarize
from batch2_spec import ALL
from batch3_spec import ALL as BATCH3
from batches4_8_spec import ALL as BATCHES4_8
from batches9_11_spec import ALL as BATCHES9_11
from batches12_15_spec import ALL as BATCHES12_15, LIMITS as LIMITS12_15, kind as kind12_15

def main():
 errors=[];checks={};cat=json.loads((ROOT/'migration/samples.yaml').read_text());samples=cat['samples'];counts=collections.Counter(s['status'] for s in samples);proofs={}
 def require(ok,message):
  if not ok:errors.append(message)
 sys.path.insert(0,str(ROOT/'tools/moat'))
 from selected_proofs import inspect as inspect_selected
 rewrite_checks=[inspect_selected(s) for s in samples if s['status']=='PASSED' and s.get('reason_code')=='VALIDATED_MOAT_REWRITE']
 for r in rewrite_checks:require(r['status']=='PASSED','Selected MOAT qualification: '+r['sample_id']+' '+str(r['errors']))
 selected_rewrites={r['sample_id'] for r in rewrite_checks if r['status']=='PASSED'}
 def superseded(source):
  return next(s for s in samples if s['source']==source)['id'] in selected_rewrites
 def withdrawn(source):
  s=next(s for s in samples if s['source']==source)
  return source=='cuDSS/simple_reordering_phase/simple_reordering_phase.cpp' and s['status']=='PARTIAL' and s['reason_code']=='VENDOR_PERMUTATION_POLICY_DIFFERS' and bool(s.get('historical_selected_validation')) and 'migration/reports/rewrite-reordering-cpp-repair.json' in s['evidence']
 require(len(samples)==639 and len({s['id'] for s in samples})==639,'Expected 639 unique source entrypoints')
 require(not counts['NOT_STARTED'] and not counts['IN_PROGRESS'],'Unfinished sample states remain')
 require(len(cat['sources'])==866 and len(cat['build_definitions'])==477,'Upstream inventory denominator changed')
 tracked=[r['path'] for r in cat['sources']+cat['build_definitions']];modified=subprocess.check_output(['git','diff','--name-only',BASE,'--']+tracked,cwd=ROOT,text=True).splitlines();require(not modified,'Original CUDA sources/builds modified: '+str(modified))
 for r in cat['sources']:require(digest(ROOT/r['path'])==r['sha256'],'Upstream source identity changed: '+r['path'])
 for s in samples:
  require(bool(s['attempts']) and bool(s['evidence']) and bool(s['reason']),s['id']+' lacks attempted outcome/evidence/reason')
  require(bool(s.get('retry_condition')) and bool(s['required_cases']),s['id']+' lacks retry condition/functional contract')
  require(s['cuda_baseline']!='NOT_RUN' and s['cuda_comparison']!='NOT_RUN',s['id']+' lacks CUDA result or explicit comparison block')
  for path in s['evidence']:require((ROOT/path).exists(),'Missing evidence '+path)
  if s['status']=='PASSED':
   require(s['level']=='L4' and set(s['passed_cases'])==set(s['required_cases']) and bool(s['actual_library']),s['id']+' invalid PASSED gates')
   source=ROOT/s['implementation'];h=digest(source);records=[s.get('selected_validation',{}),s.get('original_profile_validation',{})]+list(reversed(s['attempts']));matches=[r for r in records if r.get('status')=='PASSED' and h in [r.get('implementation_sha256'),r.get('ported_sha256'),r.get('source_sha256'),r.get('original_port_sha256')]]
   require(bool(matches),s['id']+' has no PASSED proof for current implementation')
   if not matches:continue
   proof=matches[0]
   if s['milestone']=='M1':
    matching=[r for r in matches if r.get('scope','').startswith('M1 extended')];require(bool(matching),s['id']+' missing current M1 proof')
    if matching:proof=matching[0];require(proof.get('common_sha256')==digest(ROOT/'rocm/common/check.hpp'),s['id']+' stale M1 common header')
   env=proof.get('environment',{});env=json.loads((ROOT/env).read_text()) if isinstance(env,str) and (ROOT/env).exists() else env
   devices=proof.get('devices') or (env.get('devices') if isinstance(env,dict) else None) or s.get('original_port',{}).get('devices')
   require(bool(devices),s['id']+' has no physical device proof')
   if isinstance(devices,list):require(all(d['physical_id']!=3 for d in devices),s['id']+' selects excluded physical GPU3')
   for name,sha in proof.get('dependencies',{}).items():require(digest(ROOT/name)==sha,s['id']+' stale dependency '+name)
   if proof.get('algorithm_sha256'):require(proof['algorithm_sha256']==digest(ROOT/'rocm/cuDSS/common/sparse_chol.hpp'),s['id']+' stale sparse algorithm')
   if proof.get('shim_sha256'):require(proof['shim_sha256']==digest(ROOT/'rocm/cuDSS/common/fortran_shim.cpp'),s['id']+' stale Fortran shim')
   if proof.get('callback_sha256'):require(proof['callback_sha256']==digest(ROOT/'rocm/cuFFT/lto_callback_window_1d/window_callback.hip'),s['id']+' stale JIT callback')
   proofs[s['id']]={'implementation':s['implementation'],'sha256':h,'evidence':proof.get('evidence'),'physical_devices':devices}
  if s['level'] in {'L0','L1'}:require(not s['actual_library'],s['id']+' claims linked library before compilation')
  if s['status']=='PARTIAL':require(set(s['passed_cases'])<set(s['required_cases']),s['id']+' partial state lacks explicit missing case')
 require({s['family'] for s in samples}==set(CANDIDATES),'Missing family in inventory')
 # Check only generated migration sections, preserving unrelated upstream links.
 pages=list((ROOT/'migration/sample-reports').rglob('*.md'));require(len(pages)==639,'Expected 639 detail pages')
 support_docs=[ROOT/'migration'/p for p in ['README.md','usage.md','upstream.md','history/README.md','reports/support-log-index.md','reports/operator-support.md']]+list((ROOT/'migration/reports/support-log-index').glob('*.md'))
 generated=[ROOT/'README.md']+[ROOT/family/'README.md' for family in CANDIDATES]+pages+support_docs
 root_text=(ROOT/'README.md').read_text()
 operators=json.loads((ROOT/'migration/reports/operator-support.json').read_text());require(operators==summarize(cat),'Operator counts or source-profile mapping are stale')
 require(f'{operators["verified_operator_families"]} 个按模块去重的算子/功能族' in root_text,'Root README operator total is stale')
 matrix=root_text.split('## 模块支持矩阵',1)[-1].split('## 验证范围',1)[0];matrix_rows=[line for line in matrix.splitlines() if line.startswith('| [')];require(len(matrix_rows)==len(CANDIDATES),'Expected all 30 modules in homepage support matrix')
 for family,row in operators['modules'].items():
  line=next((line for line in matrix_rows if line.startswith('| ['+family+'](')),None);c=collections.Counter(s['status'] for s in samples if s['family']==family)
  if line:
   cells=[v.strip() for v in line.split('|')[1:-1]];expected=[str(row['verified_operator_family_count']),str(c['PASSED'])+'/'+str(row['sample_count']),str(c['PARTIAL']),str(c['FAILED'])];require(cells[2:6]==expected,family+' homepage counts differ from evidence')
  else:require(False,'Missing homepage module '+family)
 for state in ['PASSED','PARTIAL','FAILED','BLOCKED','UNSUPPORTED']:
  if counts[state] or state in {'PASSED','PARTIAL','FAILED'}:require(bool(re.search(r'\| [^|]*（'+state+r'） \| '+str(counts[state])+r' \|',root_text)),'Root README stale count for '+state)
 require(not re.search(r'第二批|第三批|MOAT|\b[BR]\d{1,2}(?!\d)|已收口|实时进展',root_text),'Root README contains development history')
 for s in samples:
  p=ROOT/'migration/sample-reports'/(s['source']+'.md');text=p.read_text();require(f'**{s["status"]} / {s["level"]}**' in text and s['reason'].rstrip() in text and s['source_sha256'] in text,s['id']+' stale detail page')
 for family in CANDIDATES:
  text=(ROOT/family/'README.md').read_text().split('<!-- ROCM-MIGRATION:START -->')[-1];c=collections.Counter(s['status'] for s in samples if s['family']==family)
  for state in ['PASSED','PARTIAL','FAILED','BLOCKED','UNSUPPORTED','NOT_STARTED','IN_PROGRESS']:require(f'{state} {c[state]}' in text,family+' stale family count '+state)
 link_count=0
 for p in generated:
  text=p.read_text()
  if p==ROOT/'README.md':text=text.split('## 上游 CUDA Library Samples 说明')[0]
  elif p not in pages and p not in support_docs:text=text.split('<!-- ROCM-MIGRATION:START -->')[-1].split('<!-- ROCM-MIGRATION:END -->')[0]
  for target in re.findall(r'\]\(([^)]+)\)',text):
   target=urllib.parse.unquote(target.split('#')[0])
   if not target or '://' in target or target.startswith('mailto:'):continue
   link_count+=1;require((p.parent/target).exists(),str(p.relative_to(ROOT))+' broken link '+target)
 canonical=ROOT.parent/'doc/cuda_samples_on_rocm_design.md'
 if canonical.exists():require((ROOT/'migration/design.md').read_bytes()==canonical.read_bytes(),'Design snapshot differs from canonical document')
 m1=json.loads((ROOT/'migration/reports/m1-comparison.json').read_text());require(len(m1)==16 and all(r['status']=='PASSED' for r in m1) and sum(len(r['cases']) for r in m1)==95,'M1 16/95 comparison incomplete')
 more=json.loads((ROOT/'migration/reports/additional-comparison.json').read_text());require(len(more)==54 and all(r['status']=='PASSED' for r in more),'Additional 54 comparisons incomplete')
 batch=json.loads((ROOT/'migration/reports/batch2-validation.json').read_text());require(len(batch)==len(ALL) and {r['source'] for r in batch}==set(ALL),'Batch2 sample scope incomplete')
 for r in batch:
  require(r['status']==r['cuda_comparison']=='PASSED' and {c['case'] for c in r['cases']}==set(ALL[r['source']]) and all(c['status']=='PASSED' for c in r['cases']) and all(c['status']=='PASSED' and c['identical_input'] for c in r['cuda_cases']),'Batch2 qualification incomplete '+r['source'])
 negative=json.loads((ROOT/'migration/reports/batch2-negative-checks.json').read_text());require(negative['status']=='PASSED' and len(negative['checks'])==21 and all(c['rejected'] for c in negative['checks']),'Negative numerical gates incomplete')
 batch3=json.loads((ROOT/'migration/reports/batch3-validation.json').read_text());require(len(batch3)==8 and {r['source'] for r in batch3}==set(BATCH3),'Batch3 sample scope incomplete')
 for r in batch3:
  require(r['status']==r['cuda_comparison']=='PASSED' and {c['case'] for c in r['cases']}==set(BATCH3[r['source']]) and len(r['cuda_cases'])==len(r['cases']) and all(c['status']=='PASSED' and all(v['passed'] for v in c['checks']) for c in r['cases']) and all(c['status']=='PASSED' and c['identical_input'] and c['cuda_cpu_checks']['status']=='PASSED' for c in r['cuda_cases']),'Batch3 qualification incomplete '+r['source'])
  require(r['validation_source_sha256']==digest(ROOT/'tools/migration/batch3_validate.py') and r['dependencies']['tools/migration/batch3_reference.py']==digest(ROOT/'tools/migration/batch3_reference.py'),'Batch3 oracle identity stale '+r['source'])
 negative3=json.loads((ROOT/'migration/reports/batch3-negative-checks.json').read_text());require(negative3['status']=='PASSED' and len(negative3['checks'])==24 and all(c['rejected'] for c in negative3['checks']),'Batch3 numerical/graph negative gates incomplete')
 inputs3=json.loads((ROOT/'migration/reports/batch3-input-regeneration.json').read_text());require(inputs3['status']=='PASSED' and len(inputs3['checks'])==36 and all(c['passed'] for c in inputs3['checks']),'Batch3 input identity replay incomplete')
 for r in json.loads((ROOT/'migration/reports/batch3-inputs.json').read_text())['fixtures']:require(digest(ROOT/r['shared_rhs'])==r['inputs']['input_rhs.bin']['sha256'],'Batch3 shared RHS identity changed')
 require('Regenerated and hash-verified 27 input buffers' in (ROOT/'migration/reports/batch2-fixture-replay.log').read_text(),'Tensor fixture regeneration not verified')
 cohort=json.loads((ROOT/'migration/reports/batches4_8-validation.json').read_text());require(len(cohort)==26 and {r['source'] for r in cohort}==set(BATCHES4_8),'B4-B8 target inventory incomplete')
 for r in cohort:
  require(r['status']==r['cuda_comparison']=='PASSED' and {c['case'] for c in r['cases']}==set(BATCHES4_8[r['source']]) and len(r['cuda_cases'])==len(r['cases']) and all(c['status']=='PASSED' and all(v['passed'] for v in c['checks']) for c in r['cases']) and all(c['status']=='PASSED' and c['identical_input'] and c['cuda_cpu_checks']['status']=='PASSED' and all(x['passed'] for x in c['cuda_cpu_checks']['checks']) for c in r['cuda_cases']),'B4-B8 case/math/semantics incomplete '+r['source'])
  require(r['validation_source_sha256']==digest(ROOT/'tools/migration/batches4_8_validate.py'),'B4-B8 qualifier changed '+r['source'])
  for name,sha in r['dependencies'].items():require(digest(ROOT/name)==sha,'B4-B8 current oracle/helper changed '+name)
  require(digest(ROOT/r['implementation'])==r['implementation_sha256'],'B4-B8 implementation changed '+r['source'])
  require(r['environment']['rocm_release']=='10.1.0' and r['environment']['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03','B4-B8 environment identity changed '+r['source'])
 neg48=json.loads((ROOT/'migration/reports/batches4_8-negative.json').read_text());require(neg48['status']=='PASSED' and neg48['oracles']==26 and len(neg48['tests'])==52 and all(v['rejected'] for v in neg48['tests']) and neg48['generator_sha256']==digest(ROOT/'tools/migration/batches4_8_negative.py'),'B4-B8 52 output corruption gates incomplete')
 runtime48=json.loads((ROOT/'migration/reports/batches4_8-runtime-checks.json').read_text());require(runtime48['status']=='PASSED' and len(runtime48['tests'])==4 and all(x['rejected'] for x in runtime48['tests']) and runtime48['generator_sha256']==digest(ROOT/'tools/migration/batches4_8_runtime_checks.py'),'B4-B8 runtime rejection gates incomplete')
 semantic48=json.loads((ROOT/'migration/reports/batches4_8-semantic-negative.json').read_text());require(semantic48['status']=='PASSED' and len(semantic48['tests'])==8 and all(x['rejected'] for x in semantic48['tests']) and semantic48['generator_sha256']==digest(ROOT/'tools/migration/batches4_8_semantic_negative.py'),'B4-B8 eight semantic fault gates incomplete');checks['batches4_8_semantic_faults_rejected']=len(semantic48['tests'])
 inputs48=json.loads((ROOT/'migration/reports/batches4_8-input-replay.json').read_text());require(inputs48['status']=='PASSED' and len(inputs48['checks'])==54 and all(x['passed'] for x in inputs48['checks']) and inputs48['generator_sha256']==digest(ROOT/'tools/migration/batches4_8_input_replay.py'),'B5 captured input recipe regeneration incomplete')
 for r in cohort:
  sample=next(x for x in samples if x['source']==r['source'])
  if r['cuda_baseline_kind']=='COMPATIBLE_CUDA_MATH_BASELINE':require(sample['cuda_baseline']=='FAILED' and sample['cuda_comparison_mode']==r['cuda_baseline_kind'],'Missing native-CUDA API limitation '+r['source'])
 checks.update(batches4_8_samples=len(cohort),batches4_8_cases=sum(len(r['cases']) for r in cohort),batches4_8_corruptions_rejected=len(neg48['tests']),batches4_8_runtime_guards=len(runtime48['tests']),batches4_8_input_buffers_verified=len(inputs48['checks']),batches4_8_compatible_cuda_baselines=sum(r['cuda_baseline_kind']=='COMPATIBLE_CUDA_MATH_BASELINE' for r in cohort))
 ctest=(ROOT/'migration/reports/ctest-final.log').read_text();require('100% tests passed, 0 tests failed out of 16' in ctest,'Final 16 CTest checks not passed')
 perf=json.loads((ROOT/'migration/reports/performance-comparison.json').read_text());require(perf['status']=='BLOCKED' and len(perf['profiles'])==6 and all(v['qualified_speed_ratio'] is None for v in perf['profiles']),'Performance ratio incorrectly qualified')
 manifest=json.loads((ROOT/'migration/source-tree.json').read_text())
 cohort911=json.loads((ROOT/'migration/reports/batches9_11-validation.json').read_text());require(len(cohort911)==19 and {r['source'] for r in cohort911}==set(BATCHES9_11),'B9-B11 inventory incomplete')
 def sealed_hash(name):
  p=ROOT/name
  return digest(p) if p.exists() else manifest['files'].get(name,{}).get('sha256')
 for r in cohort911:
  require(r['status']==r['cuda_comparison']=='PASSED' and r.get('current_source_proof') and r.get('current_cuda_source_proof'),'B9-B11 execution/source gate failed '+r['source'])
  require({c['case'] for c in r['cases']}==set(BATCHES9_11[r['source']]) and len(r['cuda_cases'])==len(r['cases']) and all(c['status']=='PASSED' and c['checks'] and all(v['passed'] for v in c['checks']) for c in r['cases']) and all(c['status']=='PASSED' and c['identical_input'] and c['cuda_cpu_checks']['status']=='PASSED' and all(v['passed'] for v in c['cuda_cpu_checks']['checks']) for c in r['cuda_cases']),'B9-B11 independent numerical/CLI checks incomplete '+r['source'])
  require(r['validation_source_sha256']==digest(ROOT/'tools/migration/batches9_11_validate.py') and (superseded(r['source']) or withdrawn(r['source']) or sealed_hash(r['implementation'])==r['implementation_sha256']),'B9-B11 qualifier/implementation stale '+r['source'])
  require(manifest['files'].get('build/cuda-observed/'+r['source'],{}).get('sha256')==r['cuda_implementation_sha256'],'B9-B11 CUDA observation stale '+r['source'])
  for name,sha in dict(r['dependencies'],**r['cuda_dependencies']).items():require(sealed_hash(name)==sha,'B9-B11 helper/oracle stale '+name)
  allowed_pci={int(d['gpu']):d['bdf'].lower() for d in json.loads((ROOT/'migration/environments/physical-device-map.json').read_text()) if int(d['gpu']) in {0,1}}
  require(r['environment']['rocm_release']=='10.1.0' and r['environment']['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and len(allowed_pci)==2 and len(r['environment']['devices'])==1 and all(d['physical_id'] in allowed_pci and d['pci_bdf'].lower()==allowed_pci[d['physical_id']] for d in r['environment']['devices']),'B9-B11 environment/device identity changed '+r['source'])
  for c in r['cases']+[c['cuda_cpu_checks'] for c in r['cuda_cases']]:
   m=c['output_manifest'];require((ROOT/m['path']).exists() and digest(ROOT/m['path'])==m['sha256'] and m['files']>0,'B9-B11 output manifest missing '+r['source']+' '+c.get('case','CUDA'))
   if (ROOT/m['path']).exists():
    for n,v in json.loads((ROOT/m['path']).read_text()).items():
     if pathlib.Path(n).suffix in {'.log','.json'}:require((ROOT/m['path']).parent.joinpath(n).exists() and digest((ROOT/m['path']).parent/n)==v['sha256'],'B9-B11 archived payload altered '+r['source']+' '+n)
  s=next(s for s in samples if s['source']==r['source']);partial=r['batch']=='b10' or '/benchmarks/' in r['source'] or '/simple_get_set/' in r['source']
  require(r['contract_status']==('PARTIAL' if partial else 'PASSED'),'B9-B11 historical contract changed '+r['source'])
  if not superseded(r['source']) and not withdrawn(r['source']):require(s['status']==r['contract_status'],'B9-B11 current contract differs without replacement '+r['source'])
  if partial and not superseded(r['source']):require(bool(r['missing_contract']) and set(s['passed_cases'])<set(s['required_cases']),'B9-B11 partial missing contract absent '+r['source'])
 neg911=json.loads((ROOT/'migration/reports/batches9_11-negative.json').read_text());require(neg911['status']=='PASSED' and neg911['oracles']==19 and neg911['output_faults']==38 and neg911['semantic_faults']==9 and len(neg911['tests'])==47 and all(x['rejected'] for x in neg911['tests']) and neg911['generator_sha256']==digest(ROOT/'tools/migration/batches9_11_negative.py'),'B9-B11 independent rejection gates incomplete')
 runtime911=json.loads((ROOT/'migration/reports/batches9_11-runtime-checks.json').read_text());require(runtime911['status']=='PASSED' and len(runtime911['tests'])==23 and all(x['passed'] for x in runtime911['tests']) and runtime911['generator_sha256']==digest(ROOT/'tools/migration/batches9_11_runtime_checks.py'),'B9-B11 runtime/file CLI gates incomplete')
 interop=json.loads((ROOT/'migration/reports/b9-cross-interop-inputs.json').read_text());require(len(interop)==16 and {x['producer_backend'] for x in interop}=={'rocm','cuda'} and all((ROOT/x['producer_evidence']).exists() and len(x['streams'])==16 for x in interop),'B9 cross-vendor stream provenance missing')
 checks.update(batches9_11_profiles=len(cohort911),batches9_11_complete_profiles=sum(r['contract_status']=='PASSED' for r in cohort911),batches9_11_partial_profiles=sum(r['contract_status']=='PARTIAL' for r in cohort911),batches9_11_cases=sum(len(r['cases']) for r in cohort911),batches9_11_faults_rejected=len(neg911['tests']),batches9_11_runtime_checks=len(runtime911['tests']),b9_cross_vendor_producers=len(interop))
 cohort1215=json.loads((ROOT/'migration/reports/batches12_15-validation.json').read_text());require(len(cohort1215)==20 and {r['source'] for r in cohort1215}==set(BATCHES12_15),'B12-B15 target inventory incomplete')
 binary_index=json.loads((ROOT/'migration/reports/binary-outputs.json').read_text())
 for r in cohort1215:
  require(r['status']==r['cuda_comparison']=='PASSED' and r['current_source_proof'] and r['current_cuda_source_proof'],'B12-B15 execution/source gate failed '+r['source'])
  require({c['case'] for c in r['cases']}==set(BATCHES12_15[r['source']]) and len(r['cuda_cases'])==len(r['cases']) and all(c['status']=='PASSED' and c['checks'] and all(x['passed'] for x in c['checks']) for c in r['cases']) and all(c['status']=='PASSED' and c['identical_input'] and c['cuda_cpu_checks']['status']=='PASSED' and all(x['passed'] for x in c['cuda_cpu_checks']['checks']) for c in r['cuda_cases']),'B12-B15 independent numerical/semantics checks incomplete '+r['source'])
  require(r['validation_source_sha256']==digest(ROOT/'tools/migration/batches12_15_validate.py') and (superseded(r['source']) or sealed_hash(r['implementation'])==r['implementation_sha256']),'B12-B15 qualifier/implementation stale '+r['source'])
  require(manifest['files'].get('build/cuda-observed/'+r['source'],{}).get('sha256')==r['cuda_implementation_sha256'],'B12-B15 CUDA source stale '+r['source'])
  for name,sha in dict(r['dependencies'],**r['cuda_dependencies']).items():require(sealed_hash(name)==sha,'B12-B15 oracle/helper stale '+name)
  require(r['environment']['rocm_release']=='10.1.0' and r['environment']['image_id']=='sha256:a79c374ab2bc93c0e4358da6c7bda5cb84cf1308e8aff74fc99fc95c511cbd03' and all(d['physical_id'] in [0,2] for d in r['environment']['devices']),'B12-B15 environment/device mismatch '+r['source'])
  if r['execution_model']!='single':require({d['physical_id'] for d in r['environment']['devices']}=={0,2},'B12-B15 two-GPU allocation missing '+r['source'])
  for c in r['cases']+[c['cuda_cpu_checks'] for c in r['cuda_cases']]:
   m=c['output_manifest'];mp=ROOT/m['path'];require(mp.exists() and digest(mp)==m['sha256'] and m['files']>0,'B12-B15 output manifest missing '+r['source'])
   if mp.exists():
    entries=json.loads(mp.read_text());require(len(entries)==m['files'],'B12-B15 manifest file count stale '+r['source'])
    for n,v in entries.items():
     f=mp.parent/n
     if pathlib.Path(n).suffix in {'.log','.json','.txt'}:require(f.exists() and digest(f)==v['sha256'],'B12-B15 archived log/metadata altered '+str(f))
     else:
      original=str(f.relative_to(ROOT)).replace('migration/reports/evidence/','artifacts/',1);require(binary_index.get(original,{}).get('sha256')==v['sha256'],'B12-B15 binary output identity missing '+original)
  s=next(s for s in samples if s['source']==r['source']);partial=kind12_15(r['source']) in LIMITS12_15
  require(r['contract_status']==('PARTIAL' if partial else 'PASSED'),'B12-B15 historical contract changed '+r['source'])
  if not superseded(r['source']):
   require(s['status']==r['contract_status'],'B12-B15 current contract differs without replacement '+r['source'])
   if partial:require(r['missing_contract'] and set(s['passed_cases'])<set(s['required_cases']),'B12-B15 missing partial contract '+r['source'])
   require(s['cuda_comparison_mode']==r['cuda_baseline_kind'],'B12-B15 selected baseline mode differs without replacement '+r['source'])
  require(r['cuda_baseline_kind']=='COMPATIBLE_CUDA_MATH_BASELINE' and r['native_cuda_attempt'] is not None,'B12-B15 historical vendor and compatible baseline conflated '+r['source'])
 neg1215=json.loads((ROOT/'migration/reports/batches12_15-negative.json').read_text());require(neg1215['status']=='PASSED' and neg1215['oracles']==20 and neg1215['output_faults']==40 and neg1215['semantic_faults']==13 and len(neg1215['tests'])==53 and all(x['rejected'] for x in neg1215['tests']) and neg1215['generator_sha256']==digest(ROOT/'tools/migration/batches12_15_negative.py'),'B12-B15 rejection gates incomplete')
 runtime1215=json.loads((ROOT/'migration/reports/batches12_15-runtime-checks.json').read_text());require(runtime1215['status']=='PASSED' and len(runtime1215['tests'])==10 and all(x['passed'] for x in runtime1215['tests']) and runtime1215['generator_sha256']==digest(ROOT/'tools/migration/batches12_15_runtime_checks.py'),'B12-B15 runtime guards incomplete')
 npp=json.loads((ROOT/'migration/reports/batch15-native-comparison.json').read_text());require(npp['generator_sha256']==digest(ROOT/'tools/migration/batch15_native_compare.py') and npp['native_probe_source_sha256']==digest(ROOT/'tools/migration/probes/batch15_native_cuda.cu'),'Native NPP oracle identity stale')
 nd=next(x for x in npp['rows'] if x['kind']=='distance' and x['case']=='original');require(nd['status']=='PASSED' and len(nd['comparisons'])==2 and all(x['max_abs']==0 and x['integer_truncation_exact'] and x['amd_displacement_is_valid_nearest_site'] and x['native_displacement_is_valid_nearest_site'] for x in nd['comparisons']),'Original two-image NPP distance/Voronoi agreement incomplete')
 nc=next(x for x in npp['rows'] if x['kind']=='canny' and x['case']=='original');require(nc['status']=='DIFFERENT' and nc['comparisons'][0]['different']>0,'Known Canny native semantic gap lost')
 failure=json.loads((ROOT/'migration/reports/batch15-native-voronoi-failure.json').read_text());require(digest(ROOT/failure['failed_source_object'])==failure['failed_header_sha256'],'Historical Voronoi failed source missing')
 caps=json.loads((ROOT/'migration/reports/batches12_15-capabilities.json').read_text());require(caps['source_sha256']==digest(ROOT/caps['source']) and caps['native_normal_header_build_return_code']!=0,'Native rocRAND normal-header capability evidence changed')
 checks.update(batches12_15_profiles=len(cohort1215),batches12_15_complete_profiles=sum(r['contract_status']=='PASSED' for r in cohort1215),batches12_15_partial_profiles=sum(r['contract_status']=='PARTIAL' for r in cohort1215),batches12_15_cases=sum(len(r['cases']) for r in cohort1215),batches12_15_faults_rejected=len(neg1215['tests']),batches12_15_runtime_guards=len(runtime1215['tests']),batches12_15_native_vendor_attempts=len(cohort1215),native_NPP_original_distance_images=len(nd['comparisons']))
 for r in cohort:require(manifest['files'].get('build/cuda-observed/'+r['source'],{}).get('sha256')==r['cuda_implementation_sha256'],'B4-B8 CUDA source identity stale '+r['source'])
 for r in batch3:require(manifest['files'].get('build/cuda-observed/'+r['source'],{}).get('sha256')==r['cuda_implementation_sha256'],'Batch3 CUDA source identity stale '+r['source'])
 for name,r in manifest['files'].items():
  archived_observation=name.startswith(('build/cuda-observed/','build/cuda-observed-fft/')) and not (ROOT/name).exists();require((archived_observation or (ROOT/name).exists() and digest(ROOT/name)==r['sha256']) and digest(ROOT/r['object'])==r['sha256'],'Source seal mismatch '+name)
 for name,r in manifest['fixtures'].items():require(digest(ROOT/name)==r['sha256'],'Fixture seal mismatch '+name)
 diff=subprocess.run(['git','diff','--check'],cwd=ROOT,text=True,capture_output=True);require(diff.returncode==0,'git diff --check: '+diff.stdout+diff.stderr)
 staged=subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,text=True,capture_output=True);require(staged.returncode==0,'git diff --cached --check: '+staged.stdout+staged.stderr)
 checks.update(unique_entrypoints=len(samples),terminal_counts=dict(counts),families=len(CANDIDATES),verified_operator_families=operators['verified_operator_families'],modules_with_verified_operators=operators['modules_with_verified_operators'],upstream_sources_unchanged=len(cat['sources']),upstream_build_definitions_unchanged=len(cat['build_definitions']),current_qualified_proofs=len(proofs),detail_pages=len(pages),generated_relative_links=link_count,m1_samples=16,m1_required_cases=95,additional_comparisons=len(more),batch2_samples=len(batch),batch2_cases=sum(len(r['cases']) for r in batch),batch2_corrupted_outputs_rejected=len(negative['checks']),ctest_samples=16,performance_profiles=6,performance_qualification='BLOCKED',source_files_sealed=len(manifest['files']),source_tree_sha256=manifest['tree_sha256'])
 checks.update(batch3_samples=len(batch3),batch3_cases=sum(len(r['cases']) for r in batch3),batch3_corruptions_rejected=len(negative3['checks']),batch3_input_buffers_verified=len(inputs3['checks']))
 report={'status':'PASSED' if not errors else 'FAILED','scope':'Consistency and proof integrity of the recorded execution outcomes; not a claim that failed/unimplemented samples were successfully migrated.','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'errors':errors,'qualified_implementations':proofs};(ROOT/'migration/reports/final-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':report['status'],'checks':checks,'errors':errors},indent=2,ensure_ascii=False));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
