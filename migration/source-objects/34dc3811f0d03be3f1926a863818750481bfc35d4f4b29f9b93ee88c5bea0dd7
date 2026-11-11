#!/usr/bin/env python3
"""Independent OpenCV components per exact value; complete pixels and partition checks."""
import argparse,json,csv,hashlib,collections
from pathlib import Path
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def reference(a):
 # OpenCV labels binary masks. Running it independently for each exact byte
 # value includes value-zero components without merging different values.
 n=a.size;indices=np.arange(n,dtype=np.uint32);roots=np.empty(n,np.uint32)
 for value in np.unique(a):
  mask=(a==value);k,b=cv2.connectedComponents(mask.astype(np.uint8),connectivity=8,ltype=cv2.CV_32S);b=b.ravel();selected=mask.ravel();mins=np.full(k,n,dtype=np.uint32);np.minimum.at(mins,b[selected],indices[selected]);roots[selected]=mins[b[selected]]+1
 unique=np.unique(roots);compact=(np.searchsorted(unique,roots)+1).astype(np.uint32);return roots.reshape(a.shape),compact.reshape(a.shape),len(unique)
def canonical(labels):
 _,inverse=np.unique(labels,return_inverse=True);inverse=inverse.ravel();mins=np.full(int(inverse.max())+1,labels.size,np.uint32);np.minimum.at(mins,inverse,np.arange(labels.size,dtype=np.uint32));return (mins[inverse]+1).reshape(labels.shape)
def exact(name,a,b):
 ok=a.shape==b.shape and a.dtype==b.dtype
 return dict(check=name,passed=ok and np.array_equal(a,b),mismatched_values=int(np.count_nonzero(a!=b)) if ok else None,actual_shape=list(a.shape),expected_shape=list(b.shape))
def file(path,size,sha=None):
 p=Path(path)
 if not p.is_file() or p.stat().st_size!=size or sha is not None and digest(p)!=sha:raise ValueError('file identity/length '+str(p))
 return p.read_bytes()
def validate_output(case,record,out,input_bytes=None):
 checks=[];w,h,pitch=record['width'],record['height'],record['input_pitch'];expected_config=(case['width'],case['height'],case['pitch']) if case is not None else (w,h,pitch);checks.append(dict(check='exact-geometry-and-pitch',passed=(w,h,pitch)==expected_config));input_bytes=input_bytes if input_bytes is not None else (ROOT/case['fixture']/'input.bin').read_bytes();a=np.frombuffer(input_bytes,np.uint8).reshape(h,pitch)[:,:w];raw,comp,k=reference(a)
 if set(record['files'])!={'labels.bin','compact.bin','input-after.bin'}:raise ValueError('complete output file manifest')
 for name,v in record['files'].items():file(out/name,v['bytes'],v['sha256'])
 for name,expected,pad in [('labels',raw,167),('compact',comp,185)]:
  step=record[name+'_pitch'];b=np.frombuffer(file(out/(name+'.bin'),h*step),np.uint8).reshape(h,step);labels=b[:,:w*4].copy().view('<u4').reshape(h,w);checks.extend([exact(name+'/all-pixels',labels,expected),dict(check=name+'/padding',passed=step>=4*w and step%4==0 and bool(np.all(b[:,4*w:]==pad)))])
 checks.append(dict(check='input-identity-receipts',passed=record['input_before_sha256']==record['input_after_sha256']==hashlib.sha256(input_bytes).hexdigest()))
 checks.extend([dict(check='all-input-and-padding-preserved',passed=file(out/'input-after.bin',len(input_bytes))==input_bytes),dict(check='actual-device-count',passed=record['reported_count']==k),dict(check='zero-is-a-real-component',passed=bool(np.all(raw>0)) and bool(np.all(comp>0)))])
 return dict(case=record['case'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',component_count=k,checks=checks)
def validate_masks(run):
 spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());out=ROOT/run['outputs'];rows=json.loads((out/'runs.json').read_text());expected={c['case']:c for c in spec['cases']}
 if run['return_code']!=0 or len(rows)!=len(expected) or {r['case'] for r in rows}!=set(expected):raise ValueError('complete unique successful cases')
 results=[]
 for r in rows:
  if r['return_code']!=0:raise ValueError('GPU status')
  results.append(validate_output(expected[r['case']],r,out/r['case']))
 return results

def validate_runtime(run):
 out=ROOT/run['outputs'];rows=json.loads((out/'runs.json').read_text());expected_names=['null-input','null-labels','null-compact','null-count','null-workspace','zero-width','negative-height','excess-width','input-pitch-small','labels-pitch-small','compact-pitch-small','unaligned-label-pitch','unaligned-compact-pitch','unaligned-workspace','unaligned-label','unaligned-count','short-workspace','input-output-overlap','output-output-overlap','count-workspace-overlap','pitch-overflow','host-memory','device-allocation-too-small','workspace-1','workspace-recursive','query-zero','query-negative','query-too-large','null-descriptors','zero-batch','negative-batch','excess-batch','batch-full-preflight','batch-cross-image-overlap','after-errors','repeat','changed-input',*['heterogeneous-batch-'+str(i) for i in range(5)],'concurrent-0','concurrent-1']
 if run['return_code']!=0 or len(rows)!=len(expected_names) or {r['case'] for r in rows}!=set(expected_names):raise ValueError('runtime complete unique matrix')
 spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());cases={c['case']:c for c in spec['cases']};results=[]
 obligations=json.loads((ROOT/'migration/rewrite/image-ccl-runtime-contract.json').read_text())['cases']
 if set(obligations)!=set(expected_names):raise ValueError('independent runtime obligations')
 def workspace_bytes(w,h):
  n=w*h;words=2*n+1
  while n>256:n=(n+255)//256;words+=2*n
  return words*4
 def initialized_storage(source):
  c=cases[source];w,h=c['width'],c['height'];payload=(ROOT/c['fixture']/'input.bin').read_bytes()
  return [hashlib.sha256(x).hexdigest() for x in [payload,bytes([167])*(h*(4*w+20)),bytes([185])*(h*(4*w+28)),int(-19).to_bytes(4,'little',signed=True),bytes([211])*workspace_bytes(w,h)]]
 for r in rows:
  obligation=obligations[r['case']]
  if r['kind']!=obligation['kind'] or r['return_code']!=obligation['return_code']:raise ValueError('runtime role and actual status '+r['case'])
  if r['kind']=='pixels' and (r['source_case']!=obligation['source_case'] or any(r[k]!=obligation[k] for k in ['width','height','input_pitch','labels_pitch','compact_pitch'])):raise ValueError('runtime frozen source and geometry '+r['case'])
  if r['kind']=='workspace-query' and any(type(r[k]) is not type(obligation[k]) or r[k]!=obligation[k] for k in ['valid','width','height']):raise ValueError('runtime frozen query parameters '+r['case'])
  if r['kind']=='pixels':
   c=cases.get(r['source_case']);input_bytes=(out/r['case']/'input-before.bin').read_bytes()
   if c is not None and input_bytes!=(ROOT/c['fixture']/'input.bin').read_bytes():raise ValueError('runtime original fixture')
   if r['case']=='changed-input' and any(input_bytes):raise ValueError('changed-input must really change to zero')
   v=validate_output(c,r,out/r['case'],input_bytes);v['checks'].append(dict(check='actual-GPU-return-code',passed=r['return_code']==0));v['status']='PASSED' if all(c['passed'] for c in v['checks']) else 'FAILED';results.append(v)
  elif r['kind']=='expected-error':
   expected_storage=initialized_storage(obligation['source_case'])*obligation['states'];checks=[dict(check='actual-return-code',passed=r['return_code']==1 and r['expected_return_code']==1),dict(check='all-storage-unchanged',passed=r['before']==r['after']==expected_storage)];results.append(dict(case=r['case'],status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks))
  elif r['kind']=='workspace-query':
   n=r['width']*r['height'];size=2*n+1
   if r['valid']:
    while n>256:n=(n+255)//256;size+=2*n
   passed=r['return_code']==(0 if r['valid'] else 1) and r['bytes']==(size*4 if r['valid'] else 0);results.append(dict(case=r['case'],status='PASSED' if passed else 'FAILED',checks=[dict(check='actual-query-result',passed=passed)]))
  else:raise ValueError('unknown runtime kind')
 return results

def validate_native(rows):
 spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());cases={c['case']:c for c in spec['cases']};results=[]
 for r in rows:
  if 'case' not in r:continue
  c=cases[r['case']];w,h=c['width'],c['height'];out=ROOT/r['outputs'];a=np.fromfile(ROOT/c['fixture']/'input.bin',np.uint8).reshape(h,c['pitch'])[:,:w];ref,_,count=reference(a);v=dict(family=r['family'],case=r['case'],process_return_code=r['return_code'],collection_return_code=r['collection_return_code'],expected_component_count=count,variants={})
  if not r['return_code']:
   if set(r['files'])!={'labels.bin','compact.bin','counts.json'}:raise ValueError('complete actual native files')
   for n,q in r['files'].items():file(out/n,q['bytes'],q['sha256'])
   for name in ['labels','compact']:
    b=np.frombuffer(file(out/(name+'.bin'),h*w*4),'<u4').reshape(h,w);canon=canonical(b);v['variants'][name]=dict(conformance='PASSED' if np.array_equal(canon,ref) else 'FAILED',partition_mismatched_pixels=int(np.count_nonzero(canon!=ref)),actual_components=len(np.unique(b)),max_actual_label=int(b.max()),zero_label_pixels=int(np.count_nonzero(b==0)))
   v['reported_count']=json.loads((out/'counts.json').read_text())['reported_count']
  else:v['native_API_rejection_observation']=True
  results.append(v)
 expected={(family,c['case']) for family in ['NPP','NPP+'] for c in spec['cases']}
 if len(results)!=len(expected) or {(r['family'],r['case']) for r in results}!=expected:raise ValueError('all native comparisons required')
 return results

def validate_trace(run):
 results=validate_masks(run);m=json.loads((ROOT/run['evidence']/'manifest.json').read_text());raw=ROOT/m['raw_artifact_dir'];files=list((raw/'trace').rglob('*kernel_trace.csv'));agents=list((raw/'trace').rglob('*agent_info.csv'))
 if len(files)!=1 or len(agents)!=1:raise ValueError('one real trace and agent inventory')
 rows=list(csv.DictReader(files[0].open()));gpu=[r for r in rows if '::' in r['Kernel_Name'] and ('anonymous namespace' in r['Kernel_Name'])];counter=collections.Counter()
 for r in gpu:
  for name in ['initialize','root_flags','block_scan','scan_offsets','output','hook','compress']:
   if '::'+name+'(' in r['Kernel_Name']:counter[name]+=1
 checks=[dict(check='trace/'+n,passed=counter[n]==27) for n in ['initialize','root_flags','output']]+[dict(check='trace/'+n,passed=counter[n]>=27) for n in ['block_scan','hook','compress']]+[dict(check='trace/nonempty-hierarchical-prefix-add',passed=counter['scan_offsets']>0)]
 lookup={r['Node_Id']:r for r in csv.DictReader(agents[0].open())};observed=json.loads((raw/'backend.observed.json').read_text());allowed={d['pci_bdf'] for d in observed['devices'] if d['physical_id']!=3}
 for r in gpu:
  agent=lookup[r['Agent_Id'].split()[-1]];location=int(agent['Location_Id']);bdf=f"{int(agent['Domain']):04x}:{location>>8:02x}:{(location>>3)&31:02x}.{location&7}"
  if bdf not in allowed or int(r['End_Timestamp'])<=int(r['Start_Timestamp']) or int(r['Grid_Size_X'])<=0:raise ValueError('actual trace device/time/grid')
 checks.append(dict(check='trace/all-project-kernels-on-guarded-physical-GPU',passed=bool(gpu) and bool(allowed)))
 results.append(dict(case='raw-GPU-trace',status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,kernel_dispatches=dict(counter)));return results

def validate_native_originals(rows):
 spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());expected={('NPP','default'),('NPP+','default'),('NPP+','batch-compression')}
 if len(rows)!=3 or {(r['family'],r['mode']) for r in rows}!=expected:raise ValueError('three native original configurations')
 results=[]
 for r in rows:
  if r['return_code'] or r['collection_return_code']:raise ValueError('actual native original failure')
  out=ROOT/r['outputs'];inputs=[x for x in spec['originals'] if x['source'].startswith(r['family']+'/')];allowed={(ROOT/x['source']).name for x in inputs};values=[]
  for x in inputs:
   w,h=x['width'],x['height'];name=(ROOT/x['source']).name;blob=file(out/name,x['bytes'],x['sha256']);ref,_,count=reference(np.frombuffer(blob,np.uint8).reshape(h,w));prefix='Lena' if name.startswith('lena_') else name[:name.rindex('_'+str(w)+'x')];variants=[('UF',False),('UF',True),('UFBatch',False)]+([('UFBatch',True)] if r['family']=='NPP' or r['mode']=='batch-compression' else [])
   for suffix,compressed in variants:
    name=prefix+'_'+('CompressedMarkerLabels' if compressed else 'LabelMarkers')+suffix+f'_8Way_{w}x{h}_32u.raw';allowed.add(name);a=np.frombuffer(file(out/name,w*h*4),'<u4').reshape(h,w);canon=canonical(a);values.append(dict(file=name,expected_components=count,actual_components=len(np.unique(a)),partition_mismatched_pixels=int(np.count_nonzero(canon!=ref)),conformance='PASSED' if np.array_equal(canon,ref) else 'FAILED'))
  if set(r['files'])!=allowed or {p.name for p in out.iterdir()}!=allowed:raise ValueError('exact native original file set')
  for n,v in r['files'].items():file(out/n,v['bytes'],v['sha256'])
  results.append(dict(family=r['family'],mode=r['mode'],file_count=len(values),results=values))
 return results

def validate_streams(run):
 if run['return_code']!=0:raise ValueError('stream producer failed')
 out=ROOT/run['outputs'];rows=json.loads((out/'runs.json').read_text());spec=json.loads((ROOT/'migration/rewrite/image-ccl-stream-contract.json').read_text());obligations=spec['cases'];profile=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());case=next(c for c in profile['cases'] if c['case']==spec['source_case']);devices=json.loads((out/'devices.json').read_text())['devices'];mapping={d['logical_id']:d['physical_id'] for d in devices}
 if set(mapping.values())!=set(spec['visible_physical_gpus']) or len(rows)!=3 or {r['case'] for r in rows}!=set(obligations):raise ValueError('complete guarded stream cases')
 results=[];positive=next(r for r in rows if r['case']=='default-stream')
 for r in rows:
  rule=obligations[r['case']]
  if r['kind']!=rule['kind'] or r['return_code']!=rule['return_code'] or r['stream_query_return_code']!=rule['stream_query_return_code'] or mapping[r['current_device']]!=1:raise ValueError('fixed stream role/status/device')
  if r['case']=='default-stream':
   if r['source_case']!=case['case'] or r['stream_device']!=r['current_device']:raise ValueError('actual default stream identity')
   results.append(validate_output(case,r,out/r['case']))
  else:
   before=r['before'];after=r['after'];expected=[positive['files']['input-after.bin']['sha256'],positive['files']['labels.bin']['sha256'],positive['files']['compact.bin']['sha256'],hashlib.sha256(int(positive['reported_count']).to_bytes(4,'little',signed=True)).hexdigest()]
   if len(before)!=5 or before!=after or before[:4]!=expected or not isinstance(before[4],str) or len(before[4])!=64:raise ValueError('rejected stream storage unchanged and bound to actual positive output')
   if r['case']=='foreign-device-stream' and (r['stream_device']!=r['foreign_device'] or mapping[r['foreign_device']]!=0 or r['foreign_device']==r['current_device']):raise ValueError('actual foreign stream identity')
   results.append(dict(case=r['case'],status='PASSED',checks=[dict(check='actual-stream-query-and-CCL-rejection',passed=True),dict(check='complete-storage-preserved',passed=True)]))
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['masks','runtime','native','native-originals','trace','streams'],default='masks');a=p.parse_args();run=json.loads((ROOT/f'migration/reports/image-ccl-{a.kind}.json').read_text());e=Experiment('I2','CCL-'+a.kind+'-independent-CPU','CPU-reference',sources=[__file__,ROOT/'migration/rewrite/image-ccl-profile.json',ROOT/'migration/rewrite/image-ccl-runtime-contract.json',ROOT/'migration/rewrite/image-ccl-stream-contract.json'],parent=run.get('experiment_id') if isinstance(run,dict) else None)
 try:
  if a.kind in {'native','native-originals'}:results=validate_native(run) if a.kind=='native' else validate_native_originals(run);status='PASSED';note='Comparison completed; native partition conformance is reported separately, including failures.'
  else:results=validate_runtime(run) if a.kind=='runtime' else validate_trace(run) if a.kind=='trace' else validate_streams(run) if a.kind=='streams' else validate_masks(run);status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED';note='All GPU pixels/partition/compact/count/padding and complete runtime storage checks.'
  v=dict(status=status,case_count=len(results),results=results,note=note,opencv_version=cv2.__version__)
 except Exception as error:v=dict(status='FAILED',error=repr(error),results=[])
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='independent-full-contract',passed=v['status']=='PASSED')]));write(ROOT/f'migration/reports/image-ccl-{a.kind}-validation.json',v);record('I2','CCL '+a.kind+'独立CPU完整验收：'+v['status']+'；native分区正确性与项目GPU验收分别记录。',[v['evidence']]);print(v['status'],v.get('error'),[(r['case'],[c for c in r.get('checks',[]) if not c['passed']]) for r in v['results'] if r.get('status')=='FAILED'][:4]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
