#!/usr/bin/env python3
"""Independently check every actual runtime descriptor, storage byte and stream relation."""
import hashlib,json
import numpy as np
from experiment import ROOT,Experiment,write
from image_flood_inputs import load_case
from image_flood_reference import model,exact_file
from image_progress import record
def workspace(w,h):return ((3*w*h+3)//4)*4+4*w*h+4
def initial(c,payload):
 w,h=c['width'],c['height'];return {'input':payload+bytes([103])*32,'output':bytes([185])*(h*(3*w+19)+32),'mask':bytes([171])*(h*(w+23)+32),'region':bytes([167])*64,'workspace':bytes([211])*(workspace(w,h)+32),'small':bytes([71])*16,'host':bytes([83])*32}
def storage(folder,record,sizes):
 if {p.name for p in folder.iterdir()}!={k+'.bin' for k in sizes} or set(record)!=set(sizes):raise ValueError('all runtime buffer files including guards and real short allocation')
 result={}
 for key,size in sizes.items():
  v=record[key]
  if v['bytes']!=size:raise ValueError('full runtime buffer length')
  result[key]=exact_file(folder/(key+'.bin'),size,v['sha256'])
 return result
def expected_descriptor(c,pointers):
 w,h=c['width'],c['height'];d=dict(version=1,descriptor_bytes=160,width=w,height=h,mode=c['mode'],seed_x=c['seed'][0],seed_y=c['seed'][1],reserved=0,input=pointers['input']['pointer'],input_pitch=c['pitch'],output=pointers['output']['pointer'],output_pitch=3*w+19,mask=pointers['mask']['pointer'],mask_pitch=w+23,region=pointers['region']['pointer'],workspace=pointers['workspace']['pointer'],workspace_bytes=workspace(w,h),reserved_tail=0)
 for k in ['lower','upper','fill','boundary']:d[k]=c[k]
 return d
def resolve(value,pointers):
 if not isinstance(value,str):return value
 parts=value.split('+');return pointers[parts[0]]['pointer']+(int(parts[1]) if len(parts)==2 else 0)
def validate(run):
 contract=json.loads((ROOT/'migration/rewrite/image-flood-runtime-contract.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text());cases={c['case']:c for c in profile['cases']};rules=contract['cases'];out=ROOT/run['outputs'];rows=json.loads((out/'runs.json').read_text());meta=json.loads((ROOT/run['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];commands=json.loads((raw/'commands.json').read_text());devices={d['logical_id']:d['physical_id'] for d in json.loads((out/'devices.json').read_text())['devices']}
 if run['return_code'] or contract['status']!='FROZEN' or contract['case_count']!=len(rows) or len(rows)!=len(rules) or len(rules)!=63 or [r['case'] for r in rows]!=[r['case'] for r in rules] or set(devices.values())!={0,1} or len(devices)!=2 or out.resolve()!=(raw/'outputs').resolve() or len(commands)!=1 or commands[0]['return_code']:raise ValueError('all63 ordered actual runtime calls on exact allowed devices')
 argv=commands[0]['argv']
 if str(ROOT/'tools/moat/image_flood_runtime.py') not in argv or '--worker' not in argv or argv[argv.index('--output')+1]!=str(out) or argv[argv.index('--library')+1]!=str(ROOT/run['build']['library']) or argv[argv.index('--sha')+1]!=run['build']['library_sha256']:raise ValueError('actual runtime worker/library/output identity')
 wanted={r['case'] for r in rules if r['kind']!='query'}|{'runs.json','devices.json'}
 if {p.name for p in out.iterdir()}!=wanted:raise ValueError('exact runtime inventory')
 states={};pointers={};results=[];concurrent=[]
 for row,rule in zip(rows,rules):
  name=rule['case'];kind=rule['kind'];checks=[dict(check='fixed-runtime-role-and-actual-return-code',passed=row['kind']==kind and row['return_code']==rule['return_code'])]
  if kind=='query':
   checks.append(dict(check='fixed-query-dimensions-null-result-and-byte-count',passed=all(row[k]==rule[k] for k in ['width','height','null_result','bytes'])))
  else:
   c=cases[rule['source_case']];w,h=c['width'],c['height'];payload=load_case(c)
   if rule.get('input_change')=='zero-logical':
    b=np.frombuffer(payload,np.uint8).copy().reshape(h,c['pitch']);b[:,:3*w]=0;payload=b.tobytes()
   baseline=initial(c,payload);sizes={k:len(v) for k,v in baseline.items()};addresses=row['buffers'];checks.append(dict(check='all-real-buffer-addresses-and-complete-allocation-sizes',passed=set(addresses)==set(sizes) and all(type(addresses[k]['pointer']) is int and addresses[k]['pointer']>0 and addresses[k]['bytes']==sizes[k] for k in sizes)))
   before=storage(out/name/'before',row['files']['before'],sizes);after=storage(out/name/'after',row['files']['after'],sizes);expected=states.get(rule.get('state'),baseline).copy();expected['input']=baseline['input'];checks.append(dict(check='all-initial-or-reused-bytes-bound-independently-before-call',passed=before==expected));d=expected_descriptor(c,addresses)
   for key,value in rule.get('changes',{}).items():d[key]=resolve(value,addresses)
   if kind=='alias':d['output']=d['input'];d['output_pitch']=d['input_pitch']
   elif kind=='no-mask':d['mask']=None;d['mask_pitch']=0
   checks.extend([dict(check='every-actual-argument-pointer-pitch-capacity-and-mode',passed=row['descriptor']==d and row['null_descriptor']==(name=='null-descriptor') and row['source_case']==rule['source_case'] and row['state']==rule.get('state') and row['input_change']==rule.get('input_change')),dict(check='current-image-device-is-physical1',passed=devices.get(row['current_device'])==1)])
   if rule['return_code']:
    checks.append(dict(check='every-caller-buffer-preserved-on-rejection',passed=before==after))
   else:
    a=np.frombuffer(payload,np.uint8).reshape(h,c['pitch'])[:,:3*w].copy().reshape(h,w,3);target=model(a,c);expected=dict(before);output_key='input' if kind=='alias' else 'output';pitch=c['pitch'] if kind=='alias' else 3*w+19;data=bytearray(expected[output_key])
    for y in range(h):data[y*pitch:y*pitch+3*w]=target['output'][y].tobytes()
    expected[output_key]=bytes(data)
    if kind!='no-mask':
     data=bytearray(expected['mask']);pitch=w+23
     for y in range(h):data[y*pitch:y*pitch+w]=target['mask'][y].tobytes()
     expected['mask']=bytes(data)
    expected['region']=target['region'].tobytes()+expected['region'][32:]
    checks.extend([dict(check='all-valid-source-output-mask-metadata-small-and-host-bytes',passed=all(after[k]==expected[k] for k in expected if k!='workspace')),dict(check='workspace-end-guard-preserved',passed=after['workspace'][workspace(w,h):]==before['workspace'][workspace(w,h):])])
    state=rule['state'];states[state]=after
    if state in pointers:checks.append(dict(check='actual-buffer-addresses-reused-for-same-instance',passed=addresses==pointers[state]))
    else:pointers[state]=addresses
   query=709 if kind=='destroyed' else 0;checks.append(dict(check='actual-stream-query-and-cleared-observer-error-cache',passed=row['stream_query_return_code']==row['query_last_error_cleared']==query))
   if kind=='foreign':checks.append(dict(check='actual-foreign-stream-is-empty-physical0-stream',passed=row['stream_id']!=0 and devices.get(row['stream_owner'])==0))
   elif kind!='destroyed':checks.append(dict(check='actual-stream-owner-and-default-vs-created-stream',passed=devices.get(row['stream_owner'])==1 and ((row['stream_id']==0)==(rule.get('state')=='A'))))
   else:checks.append(dict(check='actual-destroyed-nondefault-stream-and-backend-error',passed=row['stream_id']!=0 and row['api_last_error_cleared']==709))
   if kind=='concurrent':concurrent.append(row)
  results.append(dict(case=name,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks))
 if len(concurrent)!=2:raise ValueError('two distinct actual concurrent instances required')
 a,b=concurrent;checks=[dict(check='distinct-created-concurrent-streams',passed=a['stream_id']!=b['stream_id'] and a['stream_id']!=0 and b['stream_id']!=0),dict(check='all-concurrent-instance-address-ranges-disjoint',passed=all(x['pointer']+x['bytes']<=y['pointer'] or y['pointer']+y['bytes']<=x['pointer'] for x in a['buffers'].values() for y in b['buffers'].values())),dict(check='actual-API-and-own-stream-synchronization-intervals-overlap',passed=all(type(r[k]) is int and r[k]>0 for r in [a,b] for k in ['started_ns','finished_ns']) and max(a['started_ns'],b['started_ns'])<min(a['finished_ns'],b['finished_ns']))];results.append(dict(case='two-concurrent-instance-relations',status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks));return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(rules),results=results)
def main():
 run=json.loads((ROOT/'migration/reports/image-flood-runtime.json').read_text());e=Experiment('I3','FloodFill-full-runtime-storage-and-stream-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_flood_reference.py',ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-profile.json',ROOT/'migration/rewrite/image-flood-runtime-contract.json'],parent=run['experiment_id'])
 try:v=validate(run)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all63-actual-descriptors-complete-buffers-aliases-reuse-streams-concurrency',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-flood-runtime-validation.json',v);record('I3','flood63固定运行项/完整before-after所有buffer与guards/真实分配/指针role/query/默认与alias/禁mask/并发/错误流独立CPU：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
