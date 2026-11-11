#!/usr/bin/env python3
"""Independent fixed-role checks for all mutated device data and output bytes."""
import argparse,copy,hashlib,json
import numpy as np
from experiment import ROOT,Experiment,write
from image_contour_model import model,reconstruct
from image_progress import record
NAMES=['src','raw','labels','mask','info','geometry','totals']
def expected_buffers():
 image=np.array([[0,1]],np.uint8);v=model(image);out={};out['src']=np.array([0,1]+[197]*11,np.uint8).tobytes()
 for name,pitch,pad,key in [('raw',28,167,'raw'),('labels',36,185,'labels'),('mask',15,171,'mask')]:
  b=bytearray([pad]*pitch);data=v[key].astype('<u4' if name!='mask' else 'u1').tobytes();b[:len(data)]=data;out[name]=bytes(b)
 for name in ['info','geometry','totals']:out[name]=v[name].astype('<u4').tobytes()
 return out,v

def mutation(name,original):
 data={n:bytearray(b) for n,b in original.items()};g=np.frombuffer(data['geometry'],'<u4').reshape(8,9);info=np.frombuffer(data['info'],'<u4').reshape(2,7);labels=np.frombuffer(data['labels'],'<u4')
 if name=='missing-root-edge':g[:7]=g[1:].copy()
 elif name=='duplicate-edge':g[1]=g[0]
 elif name=='swapped-edge-order':g[[0,1]]=g[[1,0]]
 elif name=='wrong-order':g[2,2]=0
 elif name=='wrong-loop-ID':g[2,1]=1
 elif name=='unknown-loop-ID':g[2,1]=7
 elif name=='invalid-component':g[0,0]=2
 elif name=='out-of-ROI-vertex':g[0,5]=999
 elif name=='wrong-owner':g[0,7]=1
 elif name=='wrong-contour-count':info[0,0]=0
 elif name in ['wrong-edge-count','empty-range-bad-info']:info[0,1]=3
 elif name=='wrong-loop-count':info[0,2]=0
 elif name=='wrong-bbox':info[0,3]=1
 elif name=='forged-bypass-count':info[0,0]=2**32-1
 elif name=='out-of-range-label':labels[0]=2
 return {n:hashlib.sha256(b).hexdigest() for n,b in data.items()}

def validate(run):
 if run['return_code']!=0 or run['legacy']:raise ValueError('current ABI2 producer required')
 contract=json.loads((ROOT/'migration/rewrite/image-contour-data-error-contract.json').read_text());out=ROOT/run['outputs'];original,base=expected_buffers();rows=json.loads((out/'runs.json').read_text());rules=contract['cases'];checks=[]
 if len(rows)!=len(rules) or {r['case'] for r in rows}!=set(rules):raise ValueError('complete fixed data-error and positive obligations')
 if {p.name for p in (out/'baseline').iterdir()}!={n+'.bin' for n in NAMES}:raise ValueError('baseline storage set')
 for n,blob in original.items():
  if (out/'baseline'/(n+'.bin')).read_bytes()!=blob:raise ValueError('actual baseline bytes '+n)
 expected_files={'runs.json','baseline',*(n+'.bin' for n in rules)}
 if {p.name for p in out.iterdir()}!=expected_files:raise ValueError('complete output collection')
 for row in rows:
  name=row['case'];rule=rules[name];expected_sha=mutation(name,original);identity=row['kind']==rule['kind'] and row['return_code']==rule['return_code'] and row['output']==name+'.bin';storage=row['before']==row['after']==expected_sha;actual=(out/(name+'.bin')).read_bytes()
  if rule['kind']=='pixels':
   wanted=reconstruct(base['geometry'],base['labels'],base['info'],rule['start'],rule['stop'],rule['limit']);expected=bytes(wanted.ravel())+bytes([173])*17
  else:expected=bytes([173])*19
  checks.append(dict(check=name,passed=identity and storage and actual==expected,actual_return_code=row['return_code'],read_only_storage_exact=storage,output_bytes_exact=actual==expected))
 return dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=len(checks),checks=checks)

def legacy_comparison(run):
 if run['return_code']!=0 or not run['legacy']:raise ValueError('real legacy observation required')
 out=ROOT/run['outputs'];original,base=expected_buffers();rs=json.loads((out/'runs.json').read_text());r=rs[0];actual=(out/r['output']).read_bytes();expected_output=bytes([173])*19;actual_pixels=actual[:2];checks=[dict(check='original-valid-baseline-is-correct',passed=all((out/'baseline'/(n+'.bin')).read_bytes()==b for n,b in original.items())),dict(check='incomplete-geometry-must-reject-before-output-write',passed=r['return_code']==1 and actual==expected_output,actual_return_code=r['return_code'],actual_pixels=list(actual_pixels),complete_expected_pixels=[0,0])];return dict(status='FAILED_CONTRACT' if not checks[1]['passed'] else 'UNEXPECTED_REJECTION',checks=checks,scope='Historical ABI1 contract failure, excluded from support; ABI2 current tests are separate.')

def main():
 p=argparse.ArgumentParser();p.add_argument('--legacy',action='store_true');a=p.parse_args();name='legacy-data-error' if a.legacy else 'data-errors';run=json.loads((ROOT/f'migration/reports/image-contour-{name}.json').read_text());e=Experiment('I2','Contour-'+name+'-CPU','CPU-reference',sources=[__file__,ROOT/'tools/moat/image_contour_model.py',ROOT/'tools/moat/image_ccl_reference.py',ROOT/'migration/rewrite/image-contour-data-error-contract.json'],parent=run['experiment_id'])
 try:v=legacy_comparison(run) if a.legacy else validate(run)
 except Exception as error:v=dict(status='FAILED',checks=[dict(check='complete-data-contract',passed=False,error=repr(error))])
 write(e.path/'results.json',v);passed=v['status']=='PASSED';v['evidence']=e.finish('PASSED' if passed else 'NUMERIC_MISMATCH',dict(status='PASSED' if passed else 'FAILED',checks=v['checks']));write(ROOT/f'migration/reports/image-contour-{name}-validation.json',v);record('I2','Contour '+('ABI1历史缺边合同失败（不计支持）' if a.legacy else 'ABI2全部固定畸形设备数据/恢复/边界limit')+'独立CPU/真实返回码/完整只读存储与目标字节检查：'+v['status'],[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return 0 if passed or a.legacy and v['status']=='FAILED_CONTRACT' else 1
if __name__=='__main__':raise SystemExit(main())
