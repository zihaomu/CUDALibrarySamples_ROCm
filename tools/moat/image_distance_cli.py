#!/usr/bin/env python3
"""Exercise and independently bind the complete original-caller error matrix."""
import argparse,json,os
from pathlib import Path
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def execute():
 from snapshot import capture
 spec=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text());inputs=spec['datasets']['original'];rules=json.loads((ROOT/'migration/rewrite/image-distance-cli-contract.json').read_text())['cases'];b=json.loads((ROOT/'migration/reports/image-distance-frontend-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['binary'])==b['binary_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());rows=[]
 for rule in rules:
  name=rule['case'];e=Experiment('I2','Distance-full-original-CLI','rocm-CLI',case=name,sources=[__file__,ROOT/'migration/rewrite/image-distance-cli-contract.json',ROOT/'migration/rewrite/image-distance-original-contract.json',*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());cwd=e.path/'work';cwd.mkdir();inp=e.path/('images' if name=='missing-default' else 'inputs');out=inp if name=='missing-default' else e.path/'outputs';audit=e.path/'audit';audit.mkdir()
  if name!='missing-default':
   inp.mkdir();out.mkdir()
   for c in inputs:(inp/c['filename']).write_bytes((ROOT/c['path']).read_bytes())
   if name in ['missing-first','missing-last']:(inp/inputs[0 if name=='missing-first' else -1]['filename']).unlink()
   elif name=='truncated-first':p=inp/inputs[0]['filename'];p.write_bytes(p.read_bytes()[:-1])
   elif name=='trailing-last':p=inp/inputs[-1]['filename'];p.write_bytes(p.read_bytes()+bytes(4))
   elif name in ['nonfinite-circle','nonfinite-Lith']:
    c=inputs[2 if name=='nonfinite-circle' else -1];p=inp/c['filename'];a=np.frombuffer(p.read_bytes(),c['dtype']).copy();a[0]=np.nan;p.write_bytes(a.tobytes())
   elif name=='output-directory-is-file':out.rmdir();out.write_text('blocks output directory')
   elif name=='first-output-is-directory':(out/(inputs[0]['output_prefix']+'_64f.raw')).mkdir()
  command=[str(ROOT/b['binary'])]+([] if name=='missing-default' else ['--input-dir',str(inp),'--output-dir',str(out),*rule['args']]);env=dict(os.environ,MIGRATION_IMAGE_DISTANCE_AUDIT_DIR=str(audit))
  if name.startswith('help'):command=[str(ROOT/b['binary']),'--help']
  if name in ['help-no-GPU','no-GPU']:env['HIP_VISIBLE_DEVICES']=''
  rc=e.command(command,'actual-five-image-C++-'+name,cwd=cwd,env=env,timeout=600);r=dict(case=name,return_code=rc,inputs=str(inp.relative_to(ROOT)),outputs=str(out.relative_to(ROOT)),audit=str(audit.relative_to(ROOT)),build=b,experiment_id=e.id,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if rc==rule['return_code'] else 'CLI_GAP');rows.append(r);write(ROOT/'migration/reports/image-distance-cli.json',rows);record('I2','EDT真实C++ CLI/'+name+'返回'+str(rc)+'；按独立固定19用例的命令/输入/具体错误/输出集合另验。',[r['evidence']]);print(name,rc,flush=True)
 return 0

def validate(rows):
 rules=json.loads((ROOT/'migration/rewrite/image-distance-cli-contract.json').read_text())['cases'];expected={r['case']:r for r in rules};inputs=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text())['datasets']['original']
 if len(rows)!=19 or {r['case'] for r in rows}!=set(expected):raise ValueError('complete nineteen unique fixed CLI cases')
 results=[]
 for r in rows:
  name=r['case'];rule=expected[name];meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text());inp=raw/('images' if name=='missing-default' else 'inputs');out=inp if name=='missing-default' else raw/'outputs';audit=raw/'audit';argv=[str(ROOT/r['build']['binary'])]+([] if name=='missing-default' else ['--input-dir',str(inp),'--output-dir',str(out),*rule['args']]);argv=[str(ROOT/r['build']['binary']),'--help'] if name.startswith('help') else argv
  if len(commands)!=1:raise ValueError('actual one CLI command')
  cmd=commands[0];stdout=(raw/r['stdout']).read_text();stderr=(raw/r['stderr']).read_text();bound=cmd['argv']==argv and cmd['cwd']==str(raw/'work') and cmd['return_code']==r['return_code']==rule['return_code'] and cmd['stdout']==r['stdout'] and cmd['stderr']==r['stderr'] and (ROOT/r['inputs']).resolve()==inp.resolve() and (ROOT/r['outputs']).resolve()==out.resolve() and (ROOT/r['audit']).resolve()==audit.resolve() and cmd['environment_changes']['MIGRATION_IMAGE_DISTANCE_AUDIT_DIR']==str(audit);checks=[dict(check='actual-complete-CLI-command-path-status-and-log-binding',passed=bound)]
  if name=='missing-default':checks.append(dict(check='actual-absent-default-input-directory',passed=not inp.exists()))
  else:
   wanted=set()
   for i,c in enumerate(inputs):
    path=inp/c['filename']
    if name=='missing-first' and i==0 or name=='missing-last' and i==len(inputs)-1:checks.append(dict(check=c['case']+'/actually-missing-input',passed=not path.exists()));continue
    wanted.add(c['filename']);data=(ROOT/c['path']).read_bytes()
    if name=='truncated-first' and i==0:data=data[:-1]
    elif name=='trailing-last' and i==len(inputs)-1:data+=bytes(4)
    elif name=='nonfinite-circle' and i==2 or name=='nonfinite-Lith' and i==len(inputs)-1:a=np.frombuffer(data,c['dtype']).copy();a[0]=np.nan;data=a.tobytes()
    checks.append(dict(check=c['case']+'/actual-full-or-malformed-input',passed=path.is_file() and path.read_bytes()==data))
   checks.append(dict(check='exact-actual-input-file-set',passed={p.name for p in inp.iterdir()}==wanted))
  if name.startswith('help'):checks.append(dict(check='actual-help-with-no-runtime-error',passed='[--input-dir DIR] [--output-dir DIR]' in stdout and 'five original inputs' in stdout and not stderr.strip()))
  else:checks.append(dict(check='actual-specific-error-and-no-success-output',passed=not stdout.strip() and 'Distance error:' in stderr and rule['diagnostic'] in stderr))
  if name=='output-directory-is-file':checks.append(dict(check='actual-output-directory-conflict',passed=out.is_file() and out.read_text()=='blocks output directory'))
  elif name=='missing-default':checks.append(dict(check='no-output-on-missing-default',passed=not out.exists()))
  elif name=='first-output-is-directory':checks.append(dict(check='actual-first-file-conflict-with-no-other-outputs',passed={p.name for p in out.iterdir()}=={inputs[0]['output_prefix']+'_64f.raw'} and (out/(inputs[0]['output_prefix']+'_64f.raw')).is_dir()))
  else:checks.append(dict(check='no-products-from-help-or-rejected-workflow',passed=out.is_dir() and not list(out.iterdir())))
  checks.append(dict(check='no-audit-products-from-rejected-workflow',passed=audit.is_dir() and not list(audit.iterdir())))
  if name in ['help-no-GPU','no-GPU']:checks.append(dict(check='actual-empty-device-mask',passed=cmd['environment_changes']['HIP_VISIBLE_DEVICES']==''))
  results.append(dict(case=name,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks))
 return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=19,results=results)

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 if not a.check:return execute()
 e=Experiment('I2','Distance-complete-CLI-independent-CPU','CPU-reference',sources=[__file__,ROOT/'migration/rewrite/image-distance-cli-contract.json',ROOT/'migration/rewrite/image-distance-original-contract.json'])
 try:v=validate(json.loads((ROOT/'migration/reports/image-distance-cli.json').read_text()))
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='complete-fixed-actual-CLI-and-malformed-inputs',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-distance-cli-validation.json',v);record('I2','EDT19项真实CLI完整命令/有效及畸形输入/默认路径/无设备/诊断/空输出独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
