#!/usr/bin/env python3
"""Freeze, execute and independently check complete flood C++ CLI/file errors."""
import argparse,json,shutil
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record
def freeze():
 cases=[]
 def add(name,args,mode='append',error=None,change=None,no_gpu=False):cases.append(dict(case=name,args=args,args_mode=mode,return_code=0 if name.startswith('help') else 1,error_contains=error,change=change,no_gpu=no_gpu))
 add('help',['--help'],'replace');add('help-no-GPU',['--help'],'replace',no_gpu=True);add('unknown',['--bogus'],error='Unknown option: --bogus');add('missing-input-value',['--input-dir'],'replace','Missing option value: --input-dir');add('missing-output-value',['--output-dir'],'replace','Missing option value: --output-dir');add('empty-input',['--input-dir',''],'replace','Missing option value: --input-dir');add('empty-output',['--output-dir',''],'replace','Missing option value: --output-dir');add('option-as-value',['--input-dir','--output-dir','@OUTPUT@'],'replace','Missing option value: --input-dir');add('duplicate-input',['--input-dir','@INPUT@'],error='Duplicate option: --input-dir');add('duplicate-output',['--output-dir','@OUTPUT@'],error='Duplicate option: --output-dir');add('missing-default',[],'default','Input size or file invalid:',change='missing-default');add('missing-first',[],error='Input size or file invalid:',change='missing-first');add('missing-last',[],error='Input size or file invalid:',change='missing-last');add('truncated-first',[],error='Input size or file invalid:',change='truncated-first');add('trailing-last',[],error='Input size or file invalid:',change='trailing-last');add('output-directory-is-file',[],error='directory',change='output-directory-is-file');add('first-product-is-directory',[],error='Product path is not a file:',change='first-product-is-directory');add('no-GPU',[],error=['No HIP GPU available','HIP:'],no_gpu=True)
 v=dict(schema_version=1,status='FROZEN',cases=cases,case_count=len(cases),help_stdout='Usage: floodFill [--input-dir images] [--output-dir products]\nFive complete RGB flood workflows; default input/output ../images.\n');e=Experiment('I3','FloodFill-original-CLI-and-malformed-file-contracts','CPU-contract',sources=[__file__,ROOT/'migration/rewrite/image-flood-original-contract.json']);write(ROOT/'migration/rewrite/image-flood-cli-contract.json',v);write(e.path/'profile.json',v);r=dict(status='FROZEN',case_count=len(cases));write(e.path/'contracts.json',r);r['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-flood-cli-contracts.json',r);record('I3','flood完整入口CLI/默认路径/畸形文件/输出冲突/无GPU合同固定'+str(len(cases))+'项；帮助无需GPU，拒绝不产生产品或审计结果。',[r['evidence']]);print(r['status'],r['case_count']);return 0
def argv(rule,binary,inp,out):
 values={'@INPUT@':str(inp),'@OUTPUT@':str(out)};args=[values.get(v,v) for v in rule['args']];base=[] if rule['args_mode'] in ['replace','default'] else ['--input-dir',str(inp),'--output-dir',str(out)];return [str(binary),*base,*args]
def execute():
 from snapshot import capture
 spec=json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text());inputs=spec['datasets']['original'];rules=json.loads((ROOT/'migration/rewrite/image-flood-cli-contract.json').read_text())['cases'];b=json.loads((ROOT/'migration/reports/image-flood-frontend-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['binary'])==b['binary_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());rows=[]
 for rule in rules:
  name=rule['case'];e=Experiment('I3','FloodFill-complete-original-CLI','rocm-CLI',case=name,sources=[__file__,ROOT/'migration/rewrite/image-flood-cli-contract.json',ROOT/'migration/rewrite/image-flood-original-contract.json',*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());cwd=e.path/'work';cwd.mkdir();inp=e.path/('images' if rule['args_mode']=='default' else 'inputs');out=inp if rule['args_mode']=='default' else e.path/'outputs';audit=e.path/'audit';audit.mkdir()
  if name!='missing-default':
   inp.mkdir();out.mkdir()
   for c in inputs:
    assert digest(ROOT/c['path'])==c['sha256'];shutil.copyfile(ROOT/c['path'],inp/c['filename'])
   if name in ['missing-first','missing-last']:(inp/inputs[0 if name=='missing-first' else -1]['filename']).unlink()
   elif name=='truncated-first':p=inp/inputs[0]['filename'];p.write_bytes(p.read_bytes()[:-1])
   elif name=='trailing-last':p=inp/inputs[-1]['filename'];p.write_bytes(p.read_bytes()+b'\x7f')
   elif name=='output-directory-is-file':out.rmdir();out.write_bytes(b'blocks output directory')
   elif name=='first-product-is-directory':(out/spec['originals'][0]['product']).mkdir()
  env=dict(MIGRATION_IMAGE_FLOOD_AUDIT_DIR=str(audit))
  if rule['no_gpu']:env['HIP_VISIBLE_DEVICES']=''
  rc=e.command(argv(rule,ROOT/b['binary'],inp,out),'actual-complete-RGB-C++-CLI-'+name,cwd=cwd,env=env,timeout=600);r=dict(case=name,return_code=rc,inputs=str(inp.relative_to(ROOT)),outputs=str(out.relative_to(ROOT)),audit=str(audit.relative_to(ROOT)),build=b,experiment_id=e.id,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish(('EXPECTED_REJECTION' if rc else 'EXECUTED') if rc==rule['return_code'] else 'CLI_GAP');rows.append(r);write(ROOT/'migration/reports/image-flood-cli.json',rows);record('I3','flood真实CLI/'+name+'返回'+str(rc)+'；固定命令/输入/诊断/空产品集合由CPU另验。',[r['evidence']]);print(name,rc,flush=True)
 return 0
def validate(rows,raw_overrides=None):
 spec=json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text());contract=json.loads((ROOT/'migration/rewrite/image-flood-cli-contract.json').read_text());rules={r['case']:r for r in contract['cases']};inputs=spec['datasets']['original'];results=[]
 if contract['status']!='FROZEN' or len(rows)!=len(rules) or len(rows)!=18 or {r['case'] for r in rows}!=set(rules):raise ValueError('all18 unique frozen CLI cases')
 for r in rows:
  rule=rules[r['case']];name=rule['case'];meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=Path(raw_overrides[name]) if raw_overrides else ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text());inp=raw/('images' if rule['args_mode']=='default' else 'inputs');out=inp if rule['args_mode']=='default' else raw/'outputs';audit=raw/'audit'
  if len(commands)!=1:raise ValueError('one actual CLI producer command')
  cmd=commands[0];stored=Path(cmd['cwd']).parent;origin=stored
  for _ in Path(meta['raw_artifact_dir']).parts:origin=origin.parent
  stored_inp=stored/('images' if rule['args_mode']=='default' else 'inputs');stored_out=stored_inp if rule['args_mode']=='default' else stored/'outputs'
  stdout=(raw/r['stdout']).read_text();stderr=(raw/r['stderr']).read_text();checks=[dict(check='actual-fixed-argv-cwd-return-logs-and-input-output-audit-binding',passed=origin/meta['raw_artifact_dir']==stored and cmd['argv']==argv(rule,origin/r['build']['binary'],stored_inp,stored_out) and cmd['cwd']==str(stored/'work') and cmd['return_code']==r['return_code']==rule['return_code'] and cmd['stdout']==r['stdout'] and cmd['stderr']==r['stderr'] and (ROOT/r['inputs']).resolve()==inp.resolve() and (ROOT/r['outputs']).resolve()==out.resolve() and (ROOT/r['audit']).resolve()==audit.resolve() and cmd['environment_changes']['MIGRATION_IMAGE_FLOOD_AUDIT_DIR']==str(stored/'audit'))]
  if name=='missing-default':checks.append(dict(check='actual-absent-default-input-directory',passed=not inp.exists()))
  else:
   wanted=set()
   for i,c in enumerate(inputs):
    p=inp/c['filename']
    if name=='missing-first' and i==0 or name=='missing-last' and i==len(inputs)-1:checks.append(dict(check=c['filename']+'/actually-missing',passed=not p.exists()));continue
    wanted.add(c['filename']);expected=(ROOT/c['path']).read_bytes()
    if len(expected)!=c['bytes'] or __import__('hashlib').sha256(expected).hexdigest()!=c['sha256']:raise ValueError('frozen CLI source bytes')
    if name=='truncated-first' and i==0:expected=expected[:-1]
    elif name=='trailing-last' and i==len(inputs)-1:expected+=b'\x7f'
    checks.append(dict(check=c['filename']+'/actual-full-or-deliberately-malformed-input',passed=p.is_file() and p.read_bytes()==expected))
   checks.append(dict(check='exact-CLI-input-inventory',passed={p.name for p in inp.iterdir()}==wanted))
  if name.startswith('help'):checks.append(dict(check='exact-help-with-empty-stderr',passed=stdout==contract['help_stdout'] and stderr==''))
  else:
   errors=rule['error_contains'];errors=errors if isinstance(errors,list) else [errors];checks.append(dict(check='specific-rejection-diagnostic-and-empty-stdout',passed=stdout=='' and 'Flood fill error:' in stderr and any(error in stderr for error in errors)))
  if name=='missing-default':checks.append(dict(check='no-created-default-products',passed=not out.exists()))
  elif name=='output-directory-is-file':checks.append(dict(check='exact-unmodified-output-directory-conflict',passed=out.is_file() and out.read_bytes()==b'blocks output directory'))
  elif name=='first-product-is-directory':p=out/spec['originals'][0]['product'];checks.append(dict(check='exact-empty-product-path-directory-with-no-partial-products',passed=out.is_dir() and {p.name for p in out.iterdir()}=={spec['originals'][0]['product']} and p.is_dir() and not list(p.iterdir())))
  else:checks.append(dict(check='no-products-from-help-or-rejected-flow',passed=out.is_dir() and not list(out.iterdir())))
  checks.append(dict(check='no-audit-products-from-rejected-or-help-flow',passed=audit.is_dir() and not list(audit.iterdir())))
  if rule['no_gpu']:checks.append(dict(check='actual-empty-HIP-device-mask',passed=cmd['environment_changes']['HIP_VISIBLE_DEVICES']==''))
  results.append(dict(case=name,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks))
 return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(rules),results=results)
def main():
 p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
 if a.freeze:return freeze()
 if not a.check:return execute()
 e=Experiment('I3','FloodFill-complete-CLI-independent-CPU','CPU-reference',sources=[__file__,ROOT/'migration/rewrite/image-flood-cli-contract.json',ROOT/'migration/rewrite/image-flood-original-contract.json'])
 try:v=validate(json.loads((ROOT/'migration/reports/image-flood-cli.json').read_text()))
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all18-full-CLI-commands-inputs-diagnostics-and-empty-products',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-flood-cli-validation.json',v);record('I3','flood18真实CLI的完整命令/输入与畸形字节/具体诊断/拒绝及help空输出独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
