#!/usr/bin/env python3
"""Actual default/foreign/dead streams, overlapping instances and extreme input states."""
import argparse,ctypes as C,json,sys,time
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_distance_build import dependencies
from image_progress import record

def worker(a):
 import threading,torch
 from snapshot import capture
 from image_distance_worker import load,Descriptor
 from image_distance_runtime_common import State,plain,hip_library
 from image_distance_inputs import load_case
 contract=json.loads((ROOT/'migration/rewrite/image-distance-state-contract.json').read_text());profile=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());cases={c['case']:c for c in profile['cases']};cases.update(contract['numeric_cases']);lib=load(a.library,a.sha);hip=hip_library();hip.hipStreamSynchronize.argtypes=[C.c_void_p];out=Path(a.output);out.mkdir(parents=True);observed=capture();write(out/'devices.json',observed);mapping={d['logical_id']:d['physical_id'] for d in observed['devices']};assert set(mapping.values())=={0,1};device=next(k for k,v in mapping.items() if v==1);foreign_device=next(k for k,v in mapping.items() if v==0);torch.cuda.set_device(device);states={};rows=[]
 def create(key,case):
  state=State(lib,case,load_case(case),torch.cuda.Stream());state.stream.synchronize();states[key]=state;return state
 def observe(rule,state,stream_id,rc,before,start=None,end=None):
  owner=C.c_int(-1);query=hip.hipStreamGetDevice(stream_id,C.byref(owner));cached_error=hip.hipGetLastError();return dict(case=rule['case'],kind=rule['kind'],source_case=rule['source_case'],input_change=rule['input_change'],disabled_outputs=rule['disabled_outputs'],return_code=rc,descriptor=plain(state.d),stream_id=stream_id,stream_query_return_code=query,query_last_error_cleared=cached_error,stream_device=owner.value,current_device=torch.cuda.current_device(),before=before,after=state.snapshot(),started_ns=start,finished_ns=end)
 def save_row(rule,state,row):state.save(out/rule['case']);rows.append(row);write(out/'runs.json',rows);print(rule['case'],row['return_code'],flush=True)
 rules=contract['cases'];index=0
 while index<len(rules):
  rule=rules[index];kind=rule['kind'];case=cases[rule['source_case']]
  if kind=='concurrent':
   pair=rules[index:index+2];assert len(pair)==2 and all(r['kind']=='concurrent' for r in pair);barrier=threading.Barrier(2);values=[None,None];errors=[];before=[]
   for r in pair:
    state=create(r['state'],cases[r['source_case']]);before.append(state.snapshot())
   def thread_call(at):
    try:
     torch.cuda.set_device(device);r=pair[at];state=states[r['state']];barrier.wait(timeout=30);start=time.monotonic_ns();rc=state.run();state.stream.synchronize();end=time.monotonic_ns();values[at]=observe(r,state,state.stream.cuda_stream,rc,before[at],start,end)
    except BaseException as error:errors.append(repr(error))
   threads=[threading.Thread(target=thread_call,args=(i,)) for i in range(2)]
   for t in threads:t.start()
   for t in threads:t.join(timeout=300)
   if errors or any(t.is_alive() for t in threads) or any(v is None for v in values):raise RuntimeError('actual concurrent calls '+str(errors))
   for r,v in zip(pair,values):save_row(r,states[r['state']],v)
   index+=2;continue
  if kind=='default':
   state=states.get(rule['state']) or create(rule['state'],case)
   if rule['input_change']=='zero-logical':state.changed_zero_input();state.stream.synchronize()
   elif rule['case']=='restored-original':
    import numpy as np
    with torch.cuda.stream(state.stream):state.src.copy_(torch.from_numpy(np.frombuffer(load_case(case),np.uint8).copy()).to('cuda'))
    state.stream.synchronize()
   before=state.snapshot();rc=state.run(stream=0);torch.cuda.synchronize();save_row(rule,state,observe(rule,state,0,rc,before))
  elif kind in ['foreign','destroyed']:
   state=states[rule['state']]
   if kind=='foreign':
    state.save(out/'negative-baseline');torch.cuda.set_device(foreign_device);foreign=C.c_void_p();assert hip.hipStreamCreate(C.byref(foreign))==0;torch.cuda.set_device(device);stream_id=foreign.value
   else:
    dead=C.c_void_p();assert hip.hipStreamCreate(C.byref(dead))==0;stream_id=dead.value;assert hip.hipStreamDestroy(dead)==0
   before=state.snapshot();rc=state.run(stream=stream_id);row=observe(rule,state,stream_id,rc,before);row['foreign_device']=foreign_device if kind=='foreign' else None;save_row(rule,state,row)
   if kind=='foreign':torch.cuda.set_device(foreign_device);assert hip.hipStreamDestroy(foreign)==0;torch.cuda.set_device(device)
  elif kind=='optional':
   state=states.get(rule['state']) or create(rule['state'],case);state.reset_outputs();state.stream.synchronize();before=state.snapshot();d=Descriptor.from_buffer_copy(state.d)
   for name in rule['disabled_outputs']:setattr(d,name,None);setattr(d,name+'_pitch',0)
   rc=state.run(descriptor=d);state.stream.synchronize();row=observe(rule,state,state.stream.cuda_stream,rc,before);row['descriptor']=plain(d);save_row(rule,state,row)
  elif kind=='numeric':
   state=create(rule['state'],case);before=state.snapshot();rc=state.run();state.stream.synchronize();save_row(rule,state,observe(rule,state,state.stream.cuda_stream,rc,before))
  else:raise ValueError('fixed state role')
  index+=1
 return 0

def main():
 p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--output');p.add_argument('--library');p.add_argument('--sha');a=p.parse_args()
 if a.worker:return worker(a)
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/image-distance-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I2','Distance-actual-states-streams-overlap-and-extremes','rocm-runtime',sources=[__file__,ROOT/'tools/moat/image_distance_runtime_common.py',ROOT/'tools/moat/image_distance_worker.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'migration/rewrite/image-distance-state-contract.json',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command([sys.executable,__file__,'--worker','--output',str(out),'--library',str(ROOT/b['library']),'--sha',b['library_sha256']],'actual-27-device-states-and-independent-concurrent-streams',timeout=900);r=dict(return_code=rc,build=b,experiment_id=e.id,outputs=str(out.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('OBSERVED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/image-distance-states.json',r);record('I2','EDT27实际默认/复用/变化恢复/并发实例/可选输出/外设备销毁stream/极值与最大行列执行rc='+str(rc)+'；GPU1像素/GPU0空stream，独立CPU全字节与实际descriptor另验。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
