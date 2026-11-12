#!/usr/bin/env python3
"""Observe actual descriptors, whole storage, aliases and streams for frozen runtime cases."""
import argparse,ctypes as C,hashlib,json,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_flood_build import dependencies
from image_flood_inputs import load_case
from image_progress import record

def worker(a):
 import numpy as np,torch,_rocm_sdk_core
 from image_flood_worker import Descriptor,load
 from snapshot import capture
 observed=capture();devices={d['logical_id']:d['physical_id'] for d in observed['devices']}
 if set(devices.values())!={0,1} or len(devices)!=2:raise ValueError('exact physical0/1 visibility; only physical1 owns image storage')
 current=next(k for k,v in devices.items() if v==1);foreign=next(k for k,v in devices.items() if v==0);torch.cuda.set_device(current)
 hip=C.CDLL(str(Path(_rocm_sdk_core.__file__).parent/'lib/libamdhip64.so.7'))
 for name,args in [('hipMalloc',[C.POINTER(C.c_void_p),C.c_size_t]),('hipFree',[C.c_void_p]),('hipMemset',[C.c_void_p,C.c_int,C.c_size_t]),('hipMemcpy',[C.c_void_p,C.c_void_p,C.c_size_t,C.c_int]),('hipSetDevice',[C.c_int]),('hipStreamCreate',[C.POINTER(C.c_void_p)]),('hipStreamDestroy',[C.c_void_p]),('hipStreamGetDevice',[C.c_void_p,C.POINTER(C.c_int)])]:getattr(hip,name).argtypes=args
 def checked(code):
  if code:raise RuntimeError('HIP observer failure '+str(code))
 library=load(a.library,a.sha);profile=json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text());cases={c['case']:c for c in profile['cases']};contract=json.loads((ROOT/'migration/rewrite/image-flood-runtime-contract.json').read_text());a.output.mkdir(parents=True);write(a.output/'devices.json',observed);held=[];states={};rows={}
 def plain(d):
  return {k:(list(v) if isinstance(v,C.Array) else v) for k,_ in d._fields_ for v in [getattr(d,k)]}
 class State:
  def __init__(self,c,default=False):
   self.case=c;self.payload=load_case(c);self.stream=torch.cuda.default_stream(current) if default else torch.cuda.Stream(device=current);w,h=c['width'],c['height'];wb=C.c_uint64();checked(library.rocm_image_flood_workspace_size(w,h,C.byref(wb)));self.wb=wb.value;self.host=C.create_string_buffer(bytes([83])*32,32);self.small=C.c_void_p();checked(hip.hipMalloc(C.byref(self.small),16));checked(hip.hipMemset(self.small,71,16))
   with torch.cuda.stream(self.stream):
    self.buffers={'input':torch.from_numpy(np.frombuffer(self.payload+bytes([103])*32,np.uint8).copy()).to('cuda'),'output':torch.full((h*(3*w+19)+32,),185,dtype=torch.uint8,device='cuda'),'mask':torch.full((h*(w+23)+32,),171,dtype=torch.uint8,device='cuda'),'region':torch.full((64,),167,dtype=torch.uint8,device='cuda'),'workspace':torch.full((self.wb+32,),211,dtype=torch.uint8,device='cuda')}
   self.stream.synchronize();self.descriptor=Descriptor(version=1,descriptor_bytes=160,width=w,height=h,mode=c['mode'],seed_x=c['seed'][0],seed_y=c['seed'][1],input=self.buffers['input'].data_ptr(),input_pitch=c['pitch'],output=self.buffers['output'].data_ptr(),output_pitch=3*w+19,mask=self.buffers['mask'].data_ptr(),mask_pitch=w+23,region=self.buffers['region'].data_ptr(),workspace=self.buffers['workspace'].data_ptr(),workspace_bytes=self.wb)
   for key in ['lower','upper','fill','boundary']:setattr(self.descriptor,key,(C.c_uint32*3)(*c[key]))
   held.append(self)
  def addresses(self):return {**{k:dict(pointer=t.data_ptr(),bytes=t.numel()) for k,t in self.buffers.items()},'small':dict(pointer=self.small.value,bytes=16),'host':dict(pointer=C.addressof(self.host),bytes=32)}
  def capture(self):
   self.stream.synchronize();data={k:t.cpu().numpy().tobytes() for k,t in self.buffers.items()};small=C.create_string_buffer(16);checked(hip.hipMemcpy(small,self.small,16,2));data['small']=small.raw;data['host']=self.host.raw;return data
  def input(self,payload):
   with torch.cuda.stream(self.stream):self.buffers['input'].copy_(torch.from_numpy(np.frombuffer(payload+bytes([103])*32,np.uint8).copy()).to('cuda'))
   self.stream.synchronize()
 def resolve(value,s):
  if not isinstance(value,str):return value
  parts=value.split('+');base=s.addresses()[parts[0]]['pointer'];return base+(int(parts[1]) if len(parts)==2 else 0)
 def execute(rule,barrier=None):
  torch.cuda.set_device(current);kind=rule['kind'];name=rule['case'];folder=a.output/name;folder.mkdir();c=cases[rule['source_case']]
  if kind=='rejected':s=State(c)
  else:
   if rule['state'] not in states:states[rule['state']]=State(c,default=rule['state']=='A')
   s=states[rule['state']]
   payload=load_case(c)
   if rule['input_change']=='zero-logical':
    b=np.frombuffer(payload,np.uint8).copy().reshape(c['height'],c['pitch']);b[:,:3*c['width']]=0;payload=b.tobytes()
   s.input(payload)
  d=Descriptor.from_buffer_copy(s.descriptor);changes=rule.get('changes',{})
  for key,value in changes.items():setattr(d,key,(C.c_uint32*3)(*value) if isinstance(value,list) else resolve(value,s))
  if kind=='alias':d.output=d.input;d.output_pitch=d.input_pitch
  if kind=='no-mask':d.mask=None;d.mask_pitch=0
  stream=s.stream.cuda_stream;special=C.c_void_p()
  if kind=='foreign':checked(hip.hipSetDevice(foreign));checked(hip.hipStreamCreate(C.byref(special)));checked(hip.hipSetDevice(current));stream=special.value
  elif kind=='destroyed':checked(hip.hipStreamCreate(C.byref(special)));stream=special.value;checked(hip.hipStreamDestroy(special))
  before=s.capture()
  if barrier:barrier.wait()
  started=time.monotonic_ns();rc=library.rocm_image_flood_run(None if name=='null-descriptor' else C.byref(d),stream);api_error_cache=hip.hipGetLastError();s.stream.synchronize();finished=time.monotonic_ns();owner=C.c_int(-1);query=hip.hipStreamGetDevice(C.c_void_p(stream),C.byref(owner));cleared=hip.hipGetLastError();after=s.capture()
  if kind=='foreign':checked(hip.hipSetDevice(foreign));checked(hip.hipStreamDestroy(special));checked(hip.hipSetDevice(current))
  hashes={}
  for stage,data in [('before',before),('after',after)]:
   p=folder/stage;p.mkdir();hashes[stage]={}
   for key,payload in data.items():(p/(key+'.bin')).write_bytes(payload);hashes[stage][key]=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
  row=dict(case=name,kind=kind,source_case=rule['source_case'],state=rule.get('state'),input_change=rule.get('input_change'),return_code=rc,descriptor=plain(d),null_descriptor=name=='null-descriptor',buffers=s.addresses(),stream_id=stream,stream_query_return_code=query,stream_owner=owner.value,query_last_error_cleared=cleared,api_last_error_cleared=api_error_cache,current_device=current,started_ns=started,finished_ns=finished,files=hashes);print(name,rc,flush=True);return row
 try:
  for rule in contract['cases']:
   if rule['case'] in rows:continue
   if rule['kind']=='query':
    result=C.c_uint64(777);rc=library.rocm_image_flood_workspace_size(rule['width'],rule['height'],None if rule['null_result'] else C.byref(result));rows[rule['case']]=dict(case=rule['case'],kind='query',width=rule['width'],height=rule['height'],null_result=rule['null_result'],return_code=rc,bytes=None if rule['null_result'] else result.value)
   elif rule['kind']=='concurrent':
    pair=[r for r in contract['cases'] if r['kind']=='concurrent'];barrier=threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
     futures=[pool.submit(execute,r,barrier) for r in pair]
     for future in futures:
      row=future.result();rows[row['case']]=row
   else:rows[rule['case']]=execute(rule)
   write(a.output/'runs.json',[rows[r['case']] for r in contract['cases'] if r['case'] in rows])
  return 0
 finally:
  for s in held:checked(hip.hipFree(s.small))

def main():
 p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--library');p.add_argument('--sha');p.add_argument('--output',type=Path);a=p.parse_args()
 if a.worker:return worker(a)
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/image-flood-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I3','FloodFill-fixed-complete-runtime-arguments-alias-streams','rocm-runtime',sources=[__file__,ROOT/'tools/moat/image_flood_worker.py',ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-runtime-contract.json',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command([sys.executable,__file__,'--worker','--library',str(ROOT/b['library']),'--sha',b['library_sha256'],'--output',str(out)],'all-frozen-query-real-allocation-alias-reuse-and-stream-cases',timeout=900);r=dict(return_code=rc,build=b,experiment_id=e.id,outputs=str(out.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/image-flood-runtime.json',r);record('I3','flood72固定query/参数/真实分配/alias/复用变化/禁mask/并发/外设备及销毁流实际执行rc='+str(rc)+'；全存储字节与实际描述符另验。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
