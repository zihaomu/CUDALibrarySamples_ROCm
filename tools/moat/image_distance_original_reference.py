#!/usr/bin/env python3
"""Independently check the complete five-image C++ file, command and GPU-site workflow."""
import json
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_distance_model import model
from image_distance_reference import exact_file
from image_progress import record

def values(path,expected,floating=False):
 a=np.frombuffer(exact_file(path,expected.nbytes),expected.dtype).reshape(expected.shape)
 if not floating:return bool(np.array_equal(a,expected))
 mask=np.isfinite(expected)
 if np.any(np.isnan(a)) or not np.array_equal(mask,np.isfinite(a)) or not np.array_equal(np.isposinf(a),np.isposinf(expected)) or not np.array_equal(np.isneginf(a),np.isneginf(expected)) or not np.array_equal(np.signbit(a),np.signbit(expected)) or not np.array_equal(a==0,expected==0):return False
 return bool(np.all(np.abs(a[mask]-expected[mask])<=2e-11+1e-12*np.abs(expected[mask])))

def validate_one(r,rule,raw_override=None):
 spec=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text());inputs=spec['datasets'][rule['dataset']]
 if r['return_code'] or r['case']!=rule['case'] or r['dataset']!=rule['dataset'] or r['default_paths'] is not rule['default_paths']:raise ValueError('frozen workflow identity/status')
 meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=Path(raw_override) if raw_override is not None else ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text())
 if len(commands)!=1:raise ValueError('one actual original command')
 command=commands[0];stored_raw=Path(command['cwd']).parent;origin=stored_raw
 for part in Path(meta['raw_artifact_dir']).parts:origin=origin.parent
 if origin/meta['raw_artifact_dir']!=stored_raw:raise ValueError('actual original repository/root binding')
 directory='images' if rule['default_paths'] else 'inputs';outname='images' if rule['default_paths'] else 'outputs';wanted=[str(origin/r['build']['binary'])]+([] if rule['default_paths'] else ['--input-dir',str(stored_raw/directory),'--output-dir',str(stored_raw/outname)]);inp=ROOT/r['inputs'];out=ROOT/r['outputs'];audit=ROOT/r['audit'];checks=[dict(check='complete-actual-command-and-input-output-audit-log-binding',passed=command['argv']==wanted and command['return_code']==0 and command['cwd']==str(stored_raw/'work') and inp.resolve()==(raw/directory).resolve() and out.resolve()==(raw/outname).resolve() and audit.resolve()==(raw/'audit').resolve() and command['environment_changes']['MIGRATION_IMAGE_DISTANCE_AUDIT_DIR']==str(stored_raw/'audit') and command['stdout']==r['stdout'] and command['stderr']==r['stderr'])];product={};stdout=[]
 if {p.name for p in audit.iterdir()}!={c['case'] for c in inputs}:raise ValueError('all five actual GPU audit directories')
 for c in inputs:
  w,h=c['width'],c['height'];payload=exact_file(inp/c['filename'],c['bytes'],c['sha256']);source=np.frombuffer(payload,c['dtype']).reshape(h,w);expected=model(source,c['mode'],c['cutoff'],c['remap_circle']);prefix=c['output_prefix'];product[prefix+'_64f.raw']=expected['distance'];product[prefix+'_16u.raw']=expected['visualization']
  if c['input_type']==1:product[spec['signed_lith_indices']]=expected['indices'];product[spec['signed_lith_relative']]=expected['relative']
  a=audit/c['case'];fields={k+'.bin':v for k,v in expected.items() if k in ['distance','visualization','indices','relative','site_ids','sites_xy']}
  if {p.name for p in a.iterdir()}!=set(fields)|{'input.bin','workflow.json'}:raise ValueError('all typed actual GPU audit buffers')
  checks.append(dict(check=c['case']+'/actual-input-read-by-C++',passed=exact_file(a/'input.bin',len(payload))==payload))
  for name,target in fields.items():checks.append(dict(check=c['case']+'/all-'+name,passed=values(a/name,target,name=='distance.bin')))
  workflow=dict(case=c['case'],width=w,height=h,mode=c['mode'],input_type=c['input_type'],remap_circle=c['remap_circle'],cutoff=c['cutoff']);checks.append(dict(check=c['case']+'/actual-mode-type-preprocess-and-threshold',passed=json.loads((a/'workflow.json').read_text())==workflow));stdout.append(f"Distance GPU workflow complete: {c['case']} {w}x{h} mode {c['mode']} input_type {c['input_type']}")
 allowed=set(product)|({c['filename'] for c in inputs} if rule['default_paths'] else set())
 checks.append(dict(check='exact-complete-twelve-original-product-files',passed=len(product)==12 and {p.name for p in out.iterdir()}==allowed))
 if not rule['default_paths']:checks.append(dict(check='exact-five-separate-input-files',passed={p.name for p in inp.iterdir()}=={c['filename'] for c in inputs}))
 for name,target in product.items():checks.append(dict(check=name+'/all-original-product-values',passed=values(out/name,target,target.dtype==np.dtype('<f8'))))
 checks.extend([dict(check='actual-five-workflow-stdout',passed=(raw/r['stdout']).read_text().splitlines()==stdout),dict(check='actual-empty-runtime-stderr',passed=not(raw/r['stderr']).read_text().strip())]);return dict(case=r['case'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',file_count=12,checks=checks)

def validate(rows):
 rules=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text())['workflows'];expected={r['case']:r for r in rules}
 if len(rows)!=4 or {r['case'] for r in rows}!=set(expected):raise ValueError('all four unique complete original workflows')
 result=[]
 for r in rows:
  v=validate_one(r,expected[r['case']]);result.append(v);print(r['case'],v['status'],flush=True)
 return result

def main():
 e=Experiment('I2','Distance-original-four-workflows-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_distance_model.py',ROOT/'tools/moat/image_distance_reference.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'migration/rewrite/image-distance-original-contract.json']);rows=json.loads((ROOT/'migration/reports/image-distance-originals.json').read_text())
 try:results=validate(rows);v=dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(results),file_count=sum(r['file_count'] for r in results),results=results)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='complete-original-files-inputs-sites-modes-default-paths-and-command-binding',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-distance-originals-validation.json',v);record('I2','Signed/unsigned EDT四真实C++完整流程/48产品文件与全量实际GPU site/Voronoi审计独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[(r['case'],[x for x in r['checks'] if not x['passed']]) for r in v['results'] if r['status']=='FAILED'][:3]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
