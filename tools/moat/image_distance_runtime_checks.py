#!/usr/bin/env python3
"""Positive and adversarial replay of the actual runtime/CLI/original readers."""
import copy,hashlib,json,shutil,tempfile
from pathlib import Path
from unittest.mock import patch
from experiment import ROOT,Experiment,write,digest
import image_distance_arguments_reference as arguments
import image_distance_states_reference as states
import image_distance_state_reference as state_values
import image_distance_cli as cli
import image_distance_original_reference as originals
from image_progress import record

NAMES=['actual69arguments-pass','actual27states-pass','actual19CLI-pass','actual4original-workflows-pass','argument-API-role-redefined','argument-query-value-forged','argument-descriptor-redefined','argument-paired-hashes-forged','argument-missing-case','state-role-redefined','state-input-change-redefined','concurrent-streams-not-distinct','concurrent-intervals-not-overlapping','foreign-stream-owner-redefined','destroyed-query-cache-redefined','optional-output-role-redefined','nonfinite-rejection-output-and-matching-hash-forged','CLI-actual-argv-redefined','CLI-input-path-redirected','CLI-log-path-redefined','original-duplicate-workflow','original-actual-cutoff-redefined','original-stdout-truncated']

def run_checks():
 checks=[];cache={};model=state_values.model
 def cached(a,mode,cutoff=0.,remap=0):
  key=(a.shape,a.dtype.str,hashlib.sha256(a.tobytes()).hexdigest(),mode,cutoff,remap)
  if key not in cache:cache[key]=model(a,mode,cutoff,remap)
  return cache[key]
 def check(name,fn,wanted=True):
  try:actual=bool(fn())
  except (OSError,ValueError,TypeError,KeyError,IndexError,StopIteration):actual=False
  checks.append(dict(check=name,passed=actual==wanted))
 def load(name):return json.loads((ROOT/f'migration/reports/image-distance-{name}.json').read_text())
 arg=load('arguments');state=load('states');cli_rows=load('cli');original_rows=load('originals')
 with tempfile.TemporaryDirectory(prefix='distance-runtime-readers-') as temporary,patch.object(arguments,'model',cached),patch.object(state_values,'model',cached),patch.object(originals,'model',cached):
  base=Path(temporary)
  check(NAMES[0],lambda:arguments.validate(arg)['status']=='PASSED');check(NAMES[1],lambda:states.validate(state)['status']=='PASSED');check(NAMES[2],lambda:cli.validate(cli_rows)['status']=='PASSED');check(NAMES[3],lambda:all(r['status']=='PASSED' for r in originals.validate(original_rows)))
  def view(name,run,validator,edit=None,file=None,change=None,coupled=None):
   out=base/name;out.mkdir();source=ROOT/run['outputs'];target=None if file is None else Path(file).parts[0]
   for p in source.iterdir():
    if p.is_dir():
     if p.name==target:shutil.copytree(p,out/p.name)
     else:(out/p.name).symlink_to(p,target_is_directory=True)
    else:shutil.copyfile(p,out/p.name)
   rows=json.loads((out/'runs.json').read_text())
   if file:change(out/file)
   if edit:edit(rows)
   if coupled:coupled(rows,out)
   write(out/'runs.json',rows);return validator(dict(run,outputs=str(out)))['status']=='PASSED'
  check('argument-API-role-redefined',lambda:view('arg-role',arg,arguments.validate,edit=lambda rs:rs[0].update(api='query')),False)
  check('argument-query-value-forged',lambda:view('arg-query',arg,arguments.validate,edit=lambda rs:next(r for r in rs if r['case']=='query-valid').update(query_bytes=1)),False)
  def wrong_descriptor(rows):next(r for r in rows if r['api']=='run' and r['actual_arguments'] is not None)['actual_arguments']['width']=0
  check('argument-descriptor-redefined',lambda:view('arg-descriptor',arg,arguments.validate,edit=wrong_descriptor),False)
  def paired(rows):rows[0]['before']={k:'0'*64 for k in rows[0]['before']};rows[0]['after']=dict(rows[0]['before'])
  check('argument-paired-hashes-forged',lambda:view('arg-paired',arg,arguments.validate,edit=paired),False);check('argument-missing-case',lambda:view('arg-missing',arg,arguments.validate,edit=lambda rs:rs.pop()),False)
  check('state-role-redefined',lambda:view('state-role',state,states.validate,edit=lambda rs:rs[0].update(kind='numeric')),False)
  check('state-input-change-redefined',lambda:view('state-input',state,states.validate,edit=lambda rs:rs[0].update(input_change='zero-logical')),False)
  def same_stream(rows):pair=[r for r in rows if r['kind']=='concurrent'];pair[1]['stream_id']=pair[0]['stream_id']
  check('concurrent-streams-not-distinct',lambda:view('state-same-stream',state,states.validate,edit=same_stream),False)
  def no_overlap(rows):pair=[r for r in rows if r['kind']=='concurrent'];span=pair[1]['finished_ns']-pair[1]['started_ns'];pair[1]['started_ns']=pair[0]['finished_ns']+1;pair[1]['finished_ns']=pair[1]['started_ns']+span
  check('concurrent-intervals-not-overlapping',lambda:view('state-time',state,states.validate,edit=no_overlap),False)
  check('foreign-stream-owner-redefined',lambda:view('state-owner',state,states.validate,edit=lambda rs:next(r for r in rs if r['kind']=='foreign').update(stream_device=1,foreign_device=1)),False)
  check('destroyed-query-cache-redefined',lambda:view('state-cache',state,states.validate,edit=lambda rs:next(r for r in rs if r['kind']=='destroyed').update(query_last_error_cleared=0)),False)
  check('optional-output-role-redefined',lambda:view('state-optional',state,states.validate,edit=lambda rs:next(r for r in rs if r['kind']=='optional').update(disabled_outputs=[])),False)
  def flip(p):b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
  def same_hash(rows,out):next(r for r in rows if r['case']=='numeric-NaN-float64')['after']['distance']=digest(out/'numeric-NaN-float64/distance.bin')
  check('nonfinite-rejection-output-and-matching-hash-forged',lambda:view('state-bad-output',state,states.validate,file='numeric-NaN-float64/distance.bin',change=flip,coupled=same_hash),False)
  row=next(r for r in cli_rows if r['case']=='missing-input-value');meta=json.loads((ROOT/row['evidence']/'manifest.json').read_text());text=(ROOT/meta['raw_artifact_dir']/'commands.json').read_text();loads=json.loads
  def changed_commands(value,*args,**kwargs):
   v=loads(value,*args,**kwargs)
   if value==text:v[0]['argv'][-1]='--output-dir'
   return v
  with patch.object(cli.json,'loads',changed_commands):check('CLI-actual-argv-redefined',lambda:cli.validate(cli_rows)['status']=='PASSED',False)
  redirected=copy.deepcopy(cli_rows);redirected[0]['inputs']='build/image-distance-original-fixtures/original';check('CLI-input-path-redirected',lambda:cli.validate(redirected)['status']=='PASSED',False)
  wrong_logs=copy.deepcopy(cli_rows);wrong_logs[0]['stdout']=wrong_logs[0]['stderr'];check('CLI-log-path-redefined',lambda:cli.validate(wrong_logs)['status']=='PASSED',False)
  duplicate=copy.deepcopy(original_rows);duplicate[-1]=copy.deepcopy(duplicate[0]);check('original-duplicate-workflow',lambda:all(r['status']=='PASSED' for r in originals.validate(duplicate)),False)
  source=next(r for r in original_rows if r['case']=='explicit-original');rule=next(r for r in json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text())['workflows'] if r['case']==source['case']);meta=json.loads((ROOT/source['evidence']/'manifest.json').read_text());original_raw=ROOT/meta['raw_artifact_dir']
  def original(name,edit):
   d=base/name;shutil.copytree(original_raw,d);r=copy.deepcopy(source)
   for key in ['inputs','outputs','audit']:r[key]=str(d/(ROOT/r[key]).relative_to(original_raw))
   r['evidence']=str(d);edit(d,r);return originals.validate_one(r,rule,raw_override=d)['status']=='PASSED'
  def cutoff(d,r):p=d/'audit/signed-lith-original/workflow.json';v=json.loads(p.read_text());v['cutoff']=.5;write(p,v)
  check('original-actual-cutoff-redefined',lambda:original('original-cutoff',cutoff),False)
  check('original-stdout-truncated',lambda:original('original-stdout',lambda d,r:(d/r['stdout']).write_text('')),False)
 if len(checks)!=len(NAMES) or {c['check'] for c in checks}!=set(NAMES):raise ValueError('all fixed runtime reader mutations')
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=len(checks),checks=checks)

def main():
 path=ROOT/'migration/rewrite/image-distance-runtime-validator-cases.json'
 if json.loads(path.read_text())!=NAMES:raise ValueError('frozen runtime reader inventory')
 e=Experiment('I2','Distance-runtime-CLI-original-validator-mutations','CPU-validator-test',sources=[__file__,path,*[ROOT/'tools/moat'/n for n in ['image_distance_arguments_reference.py','image_distance_states_reference.py','image_distance_state_reference.py','image_distance_cli.py','image_distance_original_reference.py','image_distance_reference.py','image_distance_inputs.py','image_distance_model.py']],*[ROOT/'migration/rewrite'/n for n in ['image-distance-profile.json','image-distance-original-contract.json','image-distance-state-contract.json','image-distance-argument-contract.json','image-distance-cli-contract.json']]])
 try:v=run_checks()
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='all-real-runtime-reader-mutations',passed=False,error=repr(error))])
 write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-distance-runtime-checks.json',v);record('I2','EDT23项实际69参数/27状态/19CLI/4原流程验收器正反向role/输入/时序/stream/paired-hash/文件与诊断伪造：'+v['status'],[v['evidence']]);print(v['status'],v.get('case_count'),[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
