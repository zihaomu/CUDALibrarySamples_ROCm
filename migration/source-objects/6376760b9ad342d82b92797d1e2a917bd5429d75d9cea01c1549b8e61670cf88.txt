#!/usr/bin/env python3
"""Audit scope, selected proof identities, generated documentation and environment gates."""
import collections,datetime,hashlib,json,pathlib,re,subprocess,urllib.parse
from catalog import ROOT,BASE,CANDIDATES
from run import digest
from operator_support import summarize
from batch2_spec import ALL
from batch3_spec import ALL as BATCH3

def main():
 errors=[];checks={};cat=json.loads((ROOT/'migration/samples.yaml').read_text());samples=cat['samples'];counts=collections.Counter(s['status'] for s in samples);proofs={}
 def require(ok,message):
  if not ok:errors.append(message)
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
 generated=[ROOT/'README.md']+[ROOT/family/'README.md' for family in CANDIDATES]+pages
 root_text=(ROOT/'README.md').read_text()
 operators=json.loads((ROOT/'migration/reports/operator-support.json').read_text());require(operators==summarize(cat),'Operator counts or source-profile mapping are stale')
 require(f'{operators["verified_operator_families"]} 个按模块去重的算子/功能族' in root_text,'Root README operator total is stale')
 matrix=root_text.split('## 模块支持矩阵',1)[-1].split('## 未通过和不支持的具体原因',1)[0];matrix_rows=[line for line in matrix.splitlines() if line.startswith('| [')];require(len(matrix_rows)==len(CANDIDATES),'Expected all 30 modules in homepage support matrix')
 for family,row in operators['modules'].items():
  line=next((line for line in matrix_rows if line.startswith('| ['+family+'](')),None);c=collections.Counter(s['status'] for s in samples if s['family']==family)
  if line:
   cells=[v.strip() for v in line.split('|')[1:-1]];expected=[str(row['verified_operator_family_count']),str(c['PASSED'])+'/'+str(row['sample_count']),str(c['PARTIAL']),str(c['FAILED']),str(c['UNSUPPORTED']),str(c['BLOCKED'])];require(cells[2:8]==expected,family+' homepage counts differ from evidence')
  else:require(False,'Missing homepage module '+family)
 for state in ['PASSED','PARTIAL','FAILED','BLOCKED','UNSUPPORTED','NOT_STARTED','IN_PROGRESS']:require(f'{state}: {counts[state]}' in root_text,'Root README stale count for '+state)
 for s in samples:
  p=ROOT/'migration/sample-reports'/(s['source']+'.md');text=p.read_text();require(f'**{s["status"]} / {s["level"]}**' in text and s['reason'].rstrip() in text and s['source_sha256'] in text,s['id']+' stale detail page')
 for family in CANDIDATES:
  text=(ROOT/family/'README.md').read_text().split('<!-- ROCM-MIGRATION:START -->')[-1];c=collections.Counter(s['status'] for s in samples if s['family']==family)
  for state in ['PASSED','PARTIAL','FAILED','BLOCKED','UNSUPPORTED','NOT_STARTED','IN_PROGRESS']:require(f'{state} {c[state]}' in text,family+' stale family count '+state)
 link_count=0
 for p in generated:
  text=p.read_text()
  if p==ROOT/'README.md':text=text.split('## 上游 CUDA Library Samples 说明')[0]
  elif p not in pages:text=text.split('<!-- ROCM-MIGRATION:START -->')[-1].split('<!-- ROCM-MIGRATION:END -->')[0]
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
 ctest=(ROOT/'migration/reports/ctest-final.log').read_text();require('100% tests passed, 0 tests failed out of 16' in ctest,'Final 16 CTest checks not passed')
 perf=json.loads((ROOT/'migration/reports/performance-comparison.json').read_text());require(perf['status']=='BLOCKED' and len(perf['profiles'])==6 and all(v['qualified_speed_ratio'] is None for v in perf['profiles']),'Performance ratio incorrectly qualified')
 manifest=json.loads((ROOT/'migration/source-tree.json').read_text())
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
