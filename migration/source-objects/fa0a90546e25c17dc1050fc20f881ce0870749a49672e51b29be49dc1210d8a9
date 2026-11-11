#!/usr/bin/env python3
"""Check every fixed state, descriptor, stream owner, overlap interval and byte."""
import json
import numpy as np
from experiment import ROOT,Experiment,write
from image_distance_inputs import load_case
from image_distance_state_reference import initial,hashes,read_state,check_values,descriptor,spans,FORMATS
from image_progress import record

def validate(run):
 if run['return_code']:raise ValueError('actual complete states worker success')
 contract=json.loads((ROOT/'migration/rewrite/image-distance-state-contract.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());cases={c['case']:c for c in profile['cases']};cases.update(contract['numeric_cases']);out=ROOT/run['outputs'];rules=contract['cases'];rows=json.loads((out/'runs.json').read_text());devices={d['logical_id']:d['physical_id'] for d in json.loads((out/'devices.json').read_text())['devices']}
 if set(devices.values())!={0,1} or len(devices)!=2 or len(rows)!=27 or [r['case'] for r in rows]!=[r['case'] for r in rules]:raise ValueError('all fixed ordered twenty-seven states on physical0/1 only')
 states={};pointers={};concurrent=[];results=[];negative=None
 for row,rule in zip(rows,rules):
  name=rule['case'];kind=rule['kind'];case=cases[rule['source_case']];payload=load_case(case);state=rule['state'];disabled=rule['disabled_outputs'];checks=[dict(check='independently-fixed-state-source-mode-and-return-code',passed=row['kind']==kind and row['source_case']==rule['source_case'] and row['input_change']==rule['input_change'] and row['disabled_outputs']==disabled and row['return_code']==rule['return_code'])]
  if rule['input_change']=='zero-logical':
   a=np.frombuffer(payload,np.uint8).copy().reshape(case['height'],case['pitch']);a[:,:case['width']*np.dtype(case['dtype']).itemsize]=0;payload=a.tobytes()
  after=read_state(out/name,case);checks.append(dict(check='reported-after-hashes-bound-to-all-raw-bytes',passed=row['after']==hashes(after)));checks.append(descriptor(case,row['descriptor'],disabled));checks.append(dict(check='actual-current-device-is-physical1',passed=devices[row['current_device']]==1))
  if kind in ['foreign','destroyed']:
   if negative is None:
    negative=read_state(out/'negative-baseline',case)
    if negative!=states[state]:raise ValueError('exact actual last A state bound to rejected-stream baseline')
   checks.append(dict(check='all-source-output-workspace-preserved-on-rejected-stream',passed=row['before']==row['after']==hashes(negative) and after==negative));query=0 if kind=='foreign' else 709;checks.append(dict(check='actual-nondefault-rejected-stream-query-and-cache',passed=row['stream_id']!=0 and row['stream_query_return_code']==query and row['query_last_error_cleared']==query))
   if kind=='foreign':checks.append(dict(check='actual-foreign-stream-owned-by-physical0',passed=row['foreign_device']==row['stream_device'] and devices[row['foreign_device']]==0 and row['foreign_device']!=row['current_device']))
  else:
   before=states.get(state,initial(case,payload)).copy();before['src']=payload
   if kind=='optional':
    for k,v in initial(case,payload).items():
     if k not in ['src','work']:before[k]=v
   checks.append(dict(check='all-expected-initial-or-reused-bytes-bound-before-call',passed=row['before']==hashes(before)));checks.extend(check_values(after,case,payload,disabled,rejected=rule['return_code']!=0));checks.append(dict(check='actual-valid-stream-owner-and-error-cache',passed=row['stream_query_return_code']==0 and row['query_last_error_cleared']==0 and devices[row['stream_device']]==1 and ((row['stream_id']==0)==(kind=='default'))))
   states[state]=after
   if state in pointers:checks.append(dict(check='actual-instance-buffer-reuse',passed=all(row['descriptor'][k]==pointers[state][k] for k in ['input','workspace','distance'])))
   else:pointers[state]=row['descriptor']
   if kind=='concurrent':concurrent.append((row,case))
  results.append(dict(case=name,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks))
 if len(concurrent)!=2:raise ValueError('exactly two actual concurrent instances')
 (a,ac),(b,bc)=concurrent;ar,br=spans(ac,a['descriptor']),spans(bc,b['descriptor']);checks=[dict(check='distinct-actual-nondefault-streams',passed=a['stream_id']!=b['stream_id'] and a['stream_id']!=0 and b['stream_id']!=0),dict(check='all-actual-instance-device-spans-disjoint',passed=all(ap+an<=bp or bp+bn<=ap for ap,an in ar for bp,bn in br)),dict(check='actual-API-plus-own-stream-sync-intervals-overlap',passed=isinstance(a['started_ns'],int) and isinstance(b['started_ns'],int) and 0<a['started_ns']<a['finished_ns'] and 0<b['started_ns']<b['finished_ns'] and max(a['started_ns'],b['started_ns'])<min(a['finished_ns'],b['finished_ns']))];results.append(dict(case='two-independent-concurrent-instance-relations',status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks));return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=27,results=results)

def main():
 run=json.loads((ROOT/'migration/reports/image-distance-states.json').read_text());e=Experiment('I2','Distance-full-state-streams-extremes-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_distance_state_reference.py',ROOT/'tools/moat/image_distance_model.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'migration/rewrite/image-distance-state-contract.json',ROOT/'migration/rewrite/image-distance-profile.json'],parent=run['experiment_id'])
 try:v=validate(run)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all-fixed-states-real-streams-extreme-data-and-complete-storage',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-distance-states-validation.json',v);record('I2','EDT27真实默认/变化复用/并发/可选输出/错误流/极值/次正规与32768最大行列完整GPU字节及实际描述符/区间独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
