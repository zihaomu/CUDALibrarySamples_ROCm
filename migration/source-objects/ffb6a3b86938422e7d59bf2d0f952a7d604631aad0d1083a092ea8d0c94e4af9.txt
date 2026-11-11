#!/usr/bin/env python3
"""Validate fixed state/stream roles and exact untouched state-reuse tails."""
import hashlib,json
import numpy as np
from experiment import ROOT,Experiment,write
from image_contour_state_reference import expected_state
from image_contour_model import reconstruct
from image_progress import record

def validate(run):
 if run['return_code']!=0:raise ValueError('actual state worker success')
 contract=json.loads((ROOT/'migration/rewrite/image-contour-state-contract.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());cases={c['case']:c for c in profile['cases']};out=ROOT/run['outputs'];rows=json.loads((out/'runs.json').read_text());rules=contract['cases'];observed=json.loads((out/'devices.json').read_text());devices={d['logical_id']:d['physical_id'] for d in observed['devices']}
 if set(devices.values())!={0,1} or len(rows)!=11 or [r['case'] for r in rows]!=[r['case'] for r in rules]:raise ValueError('all fixed ordered states on allowed devices')
 states={};maths={};results=[];concurrent=[];negative=None
 for row,rule in zip(rows,rules):
  name=rule['case'];c=cases[rule['source_case']];w,h,pitch=c['width'],c['height'],c['pitch'];data=(ROOT/c['fixture']/'input.bin').read_bytes();data=bytes(len(data)) if rule['all_input_bytes_zero'] else data;kind=rule['kind'];checks=[dict(check='independently-fixed-state-role-input-and-return-code',passed=row['kind']==kind and row['source_case']==rule['source_case'] and row['all_input_bytes_zero'] is rule['all_input_bytes_zero'] and row['return_code']==rule['return_code'])]
  if kind in ['core','render']:
   checks.append(dict(check='actual-geometry-and-physical-device',passed=[row['width'],row['height'],row['input_pitch']]==[w,h,pitch] and devices[row['current_device']]==1))
   if kind=='core':
    current,math=expected_state(data,w,h,pitch,states.get(rule['state']));states[rule['state']]=current;maths[rule['state']]=math;d=out/name
    if {p.name for p in d.iterdir()}!={n+'.bin' for n in current}:raise ValueError('complete core state snapshots')
    for key,blob in current.items():checks.append(dict(check=key+'/full-prefix-padding-and-reuse-tail',passed=(d/(key+'.bin')).read_bytes()==blob))
   else:
    math=maths[rule['state']];image=reconstruct(math['geometry'],math['labels'],math['info'],0,len(math['info']),2**32-1);step=w+17;expected=np.full((h,step),173,np.uint8);expected[:,:w]=image;checks.append(dict(check='actual-complete-raster-and-padding',passed=row['output_pitch']==step and (out/(name+'.bin')).read_bytes()==expected.tobytes()))
   if name.startswith('concurrent-'):concurrent.append(row['stream_id']);checks.append(dict(check='real-nondefault-instance-stream',passed=row['stream_id']!=0))
   else:checks.append(dict(check='real-default-stream',passed=row['stream_id']==0))
  else:
   if negative is None:
    base=out/'negative-baseline';known=states['X'];names=set(known)|{'work','render_work','out'}
    if {p.name for p in base.iterdir()}!={n+'.bin' for n in names}:raise ValueError('all rejected-stream baseline buffers')
    for n,blob in known.items():
     if (base/(n+'.bin')).read_bytes()!=blob:raise ValueError('negative baseline changed core bytes '+n)
    math=maths['X'];render=reconstruct(math['geometry'],math['labels'],math['info'],0,len(math['info']),2**32-1);expected=np.full((h,w+17),173,np.uint8);expected[:,:w]=render
    if (base/'out.bin').read_bytes()!=expected.tobytes():raise ValueError('negative baseline output bytes')
    negative={n:hashlib.sha256((base/(n+'.bin')).read_bytes()).hexdigest() for n in names}
   checks.extend([dict(check='complete-source-output-scratch-preserved',passed=row['before']==row['after']==negative),dict(check='actual-stream-query-status-and-physical-owner',passed=row['stream_query_return_code']==rule['stream_query_return_code'] and row['stream_id']!=0 and devices[row['current_device']]==1)])
   if name.startswith('foreign'):checks.append(dict(check='actual-foreign-device-stream',passed=row['stream_device']==row['foreign_device'] and devices[row['foreign_device']]==0 and row['foreign_device']!=row['current_device']))
  results.append(dict(case=name,status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks))
 results.append(dict(case='two-independent-concurrent-stream-identities',status='PASSED' if len(concurrent)==len(set(concurrent))==2 else 'FAILED',checks=[dict(check='distinct-real-nondefault-streams',passed=len(concurrent)==len(set(concurrent))==2)]));return dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=11,results=results)

def main():
 run=json.loads((ROOT/'migration/reports/image-contour-states.json').read_text());e=Experiment('I2','Contour-state-streams-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_contour_state_reference.py',ROOT/'tools/moat/image_contour_model.py',ROOT/'tools/moat/image_ccl_reference.py',ROOT/'migration/rewrite/image-contour-state-contract.json',ROOT/'migration/rewrite/image-contour-profile.json'],parent=run['experiment_id'])
 try:v=validate(run)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='complete-fixed-states-streams-and-storage',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-contour-states-validation.json',v);record('I2','Contour默认流/复用变化/并发实例与外设备/销毁流的11项完整像素/geometry/未写尾部/存储/真实stream独立CPU检查：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
