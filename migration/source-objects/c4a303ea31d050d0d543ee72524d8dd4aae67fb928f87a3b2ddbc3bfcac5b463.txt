#!/usr/bin/env python3
"""Independently bind the fixed argument matrix and preserved GPU storage."""
import hashlib,json
import numpy as np
from experiment import ROOT,Experiment,write
from image_distance_model import model
from image_distance_inputs import load_case
from image_progress import record

def replacement(value,base,setup):
 if not isinstance(value,str) or not value.startswith('$'):return value
 key=value[1:];offset=1 if key.endswith('+1') else -1 if key.endswith('-1') else 0
 if offset:key=key[:-2]
 return (base[key] if key in base else setup[key])+offset

def validate(run):
 if run['return_code']:raise ValueError('actual complete argument worker success')
 contract=json.loads((ROOT/'migration/rewrite/image-distance-argument-contract.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());case=next(c for c in profile['cases'] if c['case']==contract['source_case']);out=ROOT/run['outputs'];setup=json.loads((out/'setup.json').read_text());rows=json.loads((out/'runs.json').read_text());rules={r['case']:r for r in contract['cases']};w,h=case['width'],case['height'];n=w*h;base=setup['descriptor'];payload=load_case(case);image=np.frombuffer(payload,np.uint8).reshape(h,case['pitch'])[:,:w*4].copy().view('<f4').reshape(h,w);math=model(image,case['mode'],case['cutoff'],case['remap_circle']);known=dict(src=payload);formats={'distance':('<f8',1,167,40),'visualization':('<u2',1,185,18),'indices':('<i2',2,171,20),'relative':('<i2',2,173,28),'site_ids':('<u8',1,205,24),'sites_xy':('<f8',2,221,32)};pitches={};checks=[]
 if len(rows)!=69 or len(rules)!=69 or {r['case'] for r in rows}!=set(rules):raise ValueError('all unique fixed sixty-nine argument obligations')
 for key,(dtype,channels,pad,extra) in formats.items():
  dt=np.dtype(dtype);pitch=w*channels*dt.itemsize+extra;pitches[key]=pitch;data=(out/'baseline'/(key+'.bin')).read_bytes()
  if len(data)!=h*pitch:raise ValueError('full baseline buffer '+key)
  packed=np.frombuffer(data,np.uint8).reshape(h,pitch);logical=packed[:,:w*channels*dt.itemsize].copy().view(dt).reshape((h,w) if channels==1 else(h,w,channels));expect=math[key];okay=np.array_equal(logical,expect)
  if key=='distance':okay=not np.any(np.isnan(logical)) and np.array_equal(np.isfinite(logical),np.isfinite(expect)) and np.array_equal(np.isposinf(logical),np.isposinf(expect)) and np.array_equal(np.isneginf(logical),np.isneginf(expect)) and np.array_equal(np.signbit(logical),np.signbit(expect)) and np.array_equal(logical==0,expect==0) and bool(np.all(np.abs(logical-expect)<=2e-11+1e-12*np.abs(expect)))
  if not okay or not np.all(packed[:,w*channels*dt.itemsize:]==pad):raise ValueError('independent baseline values/padding '+key)
  known[key]=data
 known['work']=(out/'baseline/work.bin').read_bytes()
 if {p.name for p in (out/'baseline').iterdir()}!={k+'.bin' for k in known} or (out/'baseline/src.bin').read_bytes()!=payload or len(known['work'])!=80*n+8:raise ValueError('complete source and scratch baseline')
 baseline={k:hashlib.sha256(v).hexdigest() for k,v in known.items()};expected=dict(width=w,height=h,input_pitch=case['pitch'],workspace_bytes=80*n+8,mode=case['mode'],input_type=case['input_type'],remap_circle=case['remap_circle'],reserved=0,cutoff=case['cutoff'],**{k+'_pitch':v for k,v in pitches.items()});minimum=dict(minimum_input_pitch=4*w,minimum_distance_pitch=8*w,minimum_visualization_pitch=2*w,minimum_indices_pitch=4*w,minimum_relative_pitch=4*w,minimum_site_ids_pitch=8*w,minimum_sites_xy_pitch=16*w)
 checks.append(dict(check='actual-base-geometry-type-threshold-workspace-and-minimum-pitches',passed=setup['source_case']==case['case'] and all(base[k]==v for k,v in expected.items()) and all(setup[k]==v for k,v in minimum.items()) and all(isinstance(base[k],int) and base[k]>0 for k in ['input','distance','workspace','visualization','indices','relative','site_ids','sites_xy'])))
 checks.append(dict(check='actual-independent-physical-small-allocation',passed=setup['tiny_requested_bytes']==16 and 0<setup['tiny_observed_bytes']<80*n+8 and setup['tiny']>0 and setup['host']>0))
 for row in rows:
  rule=rules[row['case']];api=rule['api'];identity=row['api']==api and row['return_code']==rule['return_code'];query=True;args=True
  if api=='run':wanted=None if 'descriptor' in rule['changes'] else dict(base,**{k:replacement(v,base,setup) for k,v in rule['changes'].items()});args=row['actual_arguments']==wanted
  elif api in ['query','query-null']:
   args=row['actual_arguments']==rule['params'];query=row['query_bytes'] is None if api=='query-null' else row['query_bytes']==(80*rule['params'][0]*rule['params'][1]+8 if rule['return_code']==0 else 0)
  elif api=='positive':
   args=row['actual_arguments']==base
   if {p.name for p in (out/'after-errors').iterdir()}!={k+'.bin' for k in known}:args=False
   for key,data in known.items():
    if key!='work' and (out/'after-errors'/(key+'.bin')).read_bytes()!=data:args=False
  else:args=False
  storage=set(row['before'])==set(known) and set(row['after'])==set(known) and row['before']==baseline and (row['after']==baseline if api!='positive' else all(row['after'][k]==baseline[k] for k in known if k!='work'));checks.append(dict(check=row['case'],passed=identity and args and query and storage,actual_return_code=row['return_code'],actual_parameters_bound=args,actual_query_correct=query,complete_baseline_preserved=storage))
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=69,checks=checks)

def main():
 run=json.loads((ROOT/'migration/reports/image-distance-arguments.json').read_text());e=Experiment('I2','Distance-fixed-argument-independent-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_distance_model.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'migration/rewrite/image-distance-profile.json',ROOT/'migration/rewrite/image-distance-argument-contract.json'],parent=run['experiment_id'])
 try:v=validate(run)
 except Exception as error:v=dict(status='FAILED',case_count=0,checks=[dict(check='complete-independent-argument-matrix',passed=False,error=repr(error))])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-distance-arguments-validation.json',v);record('I2','EDT69项真实描述符/query/物理span与八完整存储、实际调用参数和错误后恢复独立CPU：'+v['status'],[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
