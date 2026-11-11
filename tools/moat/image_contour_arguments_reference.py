#!/usr/bin/env python3
"""Independently validate the fixed argument matrix and every preserved byte."""
import hashlib,json
import numpy as np
from experiment import ROOT,Experiment,write
from image_contour_model import model
from image_progress import record

def expected_storage(case):
 w,h,p=case['width'],case['height'],case['pitch'];data=(ROOT/case['fixture']/'input.bin').read_bytes();image=np.frombuffer(data,np.uint8).reshape(h,p)[:,:w];v=model(image);n=w*h;k,m,_=map(int,v['totals']);out=dict(src=data)
 for name,step,pad,key in [('raw',4*w+20,167,'raw'),('labels',4*w+28,185,'labels'),('mask',w+13,171,'mask')]:
  a=np.full((h,step),pad,np.uint8);blob=v[key].astype('<u4' if name!='mask' else 'u1').view(np.uint8).reshape(h,-1);a[:,:blob.shape[1]]=blob;out[name]=a.tobytes()
 out['info']=v['info'].astype('<u4').tobytes()+bytes([221])*((n-k)*28);out['geometry']=v['geometry'].astype('<u4').tobytes()+bytes([205])*((4*n-m)*36);out['totals']=v['totals'].astype('<u4').tobytes();out['render_work']=bytes([219])*(4*(5*n+7*n+1));out['out']=bytes([173])*(h*(w+17));return out,v

def replace(value,base,setup):
 if not isinstance(value,str):return value
 name=value[1:];offset=1 if name.endswith('+1') else -1 if name.endswith('-1') else 0
 if offset:name=name[:-2]
 return (setup[name] if name in ['tiny','host'] else base[name])+offset

def validate(run):
 if run['return_code']!=0:raise ValueError('actual argument worker success')
 contract=json.loads((ROOT/'migration/rewrite/image-contour-argument-contract.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());case=next(c for c in profile['cases'] if c['case']==contract['source_case']);out=ROOT/run['outputs'];setup=json.loads((out/'setup.json').read_text());rows=json.loads((out/'runs.json').read_text());rules=contract['cases'];expected,math=expected_storage(case);w,h=case['width'],case['height'];n=w*h;k,m,_=map(int,math['totals']);checks=[];base_d=setup['descriptor'];base_r=setup['render'];expected['work']=(out/'baseline/work.bin').read_bytes();names=set(expected)
 if len(rows)!=61 or {(r['case']) for r in rows}!=set(rules) or len(set(r['case'] for r in rows))!=61:raise ValueError('all unique independent argument/query obligations')
 if {p.name for p in (out/'baseline').iterdir()}!={n+'.bin' for n in names}:raise ValueError('all initial buffers captured')
 for name,blob in expected.items():
  if (out/'baseline'/(name+'.bin')).read_bytes()!=blob:raise ValueError('independent initial buffer '+name)
 d_fields=dict(width=w,height=h,input_pitch=case['pitch'],raw_pitch=4*w+20,labels_pitch=4*w+28,mask_pitch=w+13,info_capacity=n,geometry_capacity=4*n);checks.append(dict(check='actual-base-descriptor-contract',passed=all(base_d[k]==v for k,v in d_fields.items()) and len(expected['work'])==base_d['workspace_bytes'] and base_d['workspace_bytes']>0 and base_d['workspace_bytes']%4==0))
 r_fields=dict(labels_pitch=4*w+28,components=k,edge_count=m,start=0,stop=k,limit=2**32-1,output_pitch=w+17,workspace_bytes=4*(5*n+7*k+1),width=w,height=h);checks.append(dict(check='actual-render-base-uses-queried-minimum-workspace',passed=all(base_r[k]==v for k,v in r_fields.items())))
 checks.append(dict(check='actual-small-physical-HIP-allocation',passed=0<setup['tiny_observed_bytes']<4*n*36 and setup['tiny_requested_bytes']==16 and setup['tiny']!=0))
 baseline={n:hashlib.sha256(b).hexdigest() for n,b in expected.items()}
 for row in rows:
  rule=rules[row['case']];api=rule['api'];before=row['before'];after=row['after'];identity=row['api']==api and row['return_code']==rule['return_code'];args=True;query=True
  if api in ['run','render']:
   base=base_d if api=='run' else base_r;wanted=dict(base)
   if 'descriptor' in rule['changes']:wanted=None
   else:
    for field,value in rule['changes'].items():wanted[field]=replace(value,base,setup)
   args=row['actual_arguments']==wanted
  elif 'query' in api:
   args=row['actual_arguments']==rule['params']
   if api.endswith('null'):query=row['query_bytes'] is None
   elif rule['return_code']==1:query=row['query_bytes']==0
   elif api=='render-query':qw,qh,qk=rule['params'];query=row['query_bytes']==4*(5*qw*qh+7*qk+1)
   else:query=isinstance(row['query_bytes'],int) and row['query_bytes']>0 and row['query_bytes']%4==0
  elif api=='positive':
   args=row['actual_arguments']==base_d
   for name,blob in expected.items():
    if name not in ['work','render_work','out'] and (out/'after-errors'/(name+'.bin')).read_bytes()!=blob:args=False
  storage=set(before)==names and set(after)==names and before==baseline and (after==baseline if api!='positive' else True)
  checks.append(dict(check=row['case'],passed=identity and args and query and storage,actual_return_code=row['return_code'],actual_arguments_bound=args,query_result_correct=query,all_initial_storage_bound_and_preserved=storage))
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=61,checks=checks)

def main():
 run=json.loads((ROOT/'migration/reports/image-contour-arguments.json').read_text());e=Experiment('I2','Contour-arguments-fixed-CPU-check','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_contour_model.py',ROOT/'tools/moat/image_ccl_reference.py',ROOT/'migration/rewrite/image-contour-profile.json',ROOT/'migration/rewrite/image-contour-argument-contract.json'],parent=run['experiment_id'])
 try:v=validate(run)
 except Exception as error:v=dict(status='FAILED',case_count=0,checks=[dict(check='complete-independent-argument-contract',passed=False,error=repr(error))])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=v['checks']));write(ROOT/'migration/reports/image-contour-arguments-validation.json',v);record('I2','Contour61项实际参数/query/物理范围/完整存储与恢复独立CPU核对：'+v['status'],[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
