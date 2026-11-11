#!/usr/bin/env python3
"""Check full original RGB files, all five mask/metadata audits and actual commands."""
import json
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write
from image_flood_reference import model,exact_file
from image_progress import record
def validate_one(r,rule,raw_override=None):
 spec=json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text());inputs={c['filename']:c for c in spec['datasets'][rule['dataset']]};meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=Path(raw_override) if raw_override else ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text());inp=ROOT/r['inputs'];out=ROOT/r['outputs'];audit=ROOT/r['audit'];default=rule['default_paths'];in_name='images' if default else 'inputs';out_name='images' if default else 'outputs'
 if r['case']!=rule['case'] or r['dataset']!=rule['dataset'] or r['default_paths'] is not default or r['return_code'] or len(commands)!=1:raise ValueError('frozen complete original identity')
 cmd=commands[0];stored_raw=Path(cmd['cwd']).parent;origin=stored_raw
 for _ in Path(meta['raw_artifact_dir']).parts:origin=origin.parent
 wanted=[str(origin/r['build']['binary'])]+([] if default else ['--input-dir',str(stored_raw/in_name),'--output-dir',str(stored_raw/out_name)])
 checks=[dict(check='actual-full-command-default-paths-build-output-and-audit-binding',passed=origin/meta['raw_artifact_dir']==stored_raw and cmd['argv']==wanted and cmd['cwd']==str(stored_raw/'work') and cmd['return_code']==0 and cmd['stdout']==r['stdout'] and cmd['stderr']==r['stderr'] and inp.resolve()==(raw/in_name).resolve() and out.resolve()==(raw/out_name).resolve() and audit.resolve()==(raw/'audit').resolve() and cmd['environment_changes']['MIGRATION_IMAGE_FLOOD_AUDIT_DIR']==str(stored_raw/'audit'))];products={};stdout=[]
 if {p.name for p in audit.iterdir()}!={c['case'] for c in spec['originals']}:raise ValueError('all five complete GPU audit directories')
 for c in spec['originals']:
  name=Path(c['original']['source']).name;f=inputs[name];payload=exact_file(inp/name,f['bytes'],f['sha256']);a=np.frombuffer(payload,np.uint8).reshape(c['height'],c['width'],3);expected=model(a,c);d=audit/c['case'];names={'input.bin','output.bin','mask.bin','region.bin','workflow.json'}
  if {p.name for p in d.iterdir()}!=names:raise ValueError('complete actual C++ GPU buffer audit')
  checks.append(dict(check=c['case']+'/actual-original-input-bytes',passed=exact_file(d/'input.bin',len(payload))==payload))
  for k in ['output','mask','region']:
   target=expected[k];actual=np.frombuffer(exact_file(d/(k+'.bin'),target.nbytes),target.dtype).reshape(target.shape);checks.append(dict(check=c['case']+'/all-'+k,passed=bool(np.array_equal(actual,target))))
  checks.append(dict(check=c['case']+'/actual-mode-geometry-and-seed',passed=json.loads((d/'workflow.json').read_text())=={k:c[k] for k in ['case','mode','width','height','seed']}));products[c['product']]=expected['output'];v=expected['region'].tolist();stdout.append(f'BoundsRect x {v[0]} y {v[1]} width {v[2]} height {v[3]} count {v[4]} seed0 {v[5]} seed1 {v[6]} seed2 {v[7]}.')
 allowed=set(products)|(set(inputs) if default else set());checks.append(dict(check='exact-five-full-RGB-products-and-input-inventory',passed={p.name for p in out.iterdir()}==allowed and (default or {p.name for p in inp.iterdir()}==set(inputs))))
 for name,expected in products.items():checks.append(dict(check=name+'/complete-RGB-values',passed=exact_file(out/name,expected.nbytes)==expected.tobytes()))
 checks.extend([dict(check='five-actual-stdout-region-information-lines',passed=(raw/r['stdout']).read_text().splitlines()==stdout),dict(check='empty-runtime-stderr',passed=not(raw/r['stderr']).read_text().strip())]);return dict(case=r['case'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',file_count=5,checks=checks)
def validate(rows):
 spec=json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text());rules={r['case']:r for r in spec['workflows']}
 if len(rows)!=4 or {r['case'] for r in rows}!=set(rules):raise ValueError('all four unique complete original workflows')
 return [validate_one(r,rules[r['case']]) for r in rows]
def main():
 e=Experiment('I3','FloodFill-four-complete-originals-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_flood_reference.py',ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-profile.json',ROOT/'migration/rewrite/image-flood-original-contract.json'])
 try:results=validate(json.loads((ROOT/'migration/reports/image-flood-originals.json').read_text()));v=dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=4,file_count=20,results=results)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='four-actual-original-commands-and-all-twenty-RGB-products',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-flood-originals-validation.json',v);record('I3','flood4真实C++完整流程/20RGB产品/全量mask-count-bbox-seed审计独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
