#!/usr/bin/env python3
"""Actual GPU ABI execution; no CPU component computation."""
import argparse,ctypes as C,hashlib,json
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[2]
class Descriptor(C.Structure):
 _fields_=[('input',C.c_void_p),('input_pitch',C.c_uint64),('labels',C.c_void_p),('labels_pitch',C.c_uint64),('compact',C.c_void_p),('compact_pitch',C.c_uint64),('count',C.c_void_p),('workspace',C.c_void_p),('workspace_bytes',C.c_uint64),('width',C.c_int),('height',C.c_int)]
def sha(data):return hashlib.sha256(data).hexdigest()
def load(lib):
 l=C.CDLL(str(lib));l.rocm_image_ccl8_workspace_size.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint64)];l.rocm_image_ccl8_run.argtypes=[C.POINTER(Descriptor),C.c_void_p];l.rocm_image_ccl8_batch.argtypes=[C.POINTER(Descriptor),C.c_int,C.c_void_p];return l
class GPUImage:
 def __init__(self,l,data,w,h,pitch,stream):
  self.w,self.h,self.pitch=w,h,pitch;self.lp=4*w+20;self.cp=4*w+28;self.data=data;self.stream=stream;size=C.c_uint64();rc=l.rocm_image_ccl8_workspace_size(w,h,C.byref(size));assert rc==0
  with torch.cuda.stream(stream):
   self.src=torch.tensor(list(data),dtype=torch.uint8,device='cuda');self.raw=torch.full((h*self.lp,),167,dtype=torch.uint8,device='cuda');self.comp=torch.full((h*self.cp,),185,dtype=torch.uint8,device='cuda');self.count=torch.full((1,),-19,dtype=torch.int32,device='cuda');self.scratch=torch.full((size.value,),211,dtype=torch.uint8,device='cuda')
  self.descriptor=Descriptor(self.src.data_ptr(),pitch,self.raw.data_ptr(),self.lp,self.comp.data_ptr(),self.cp,self.count.data_ptr(),self.scratch.data_ptr(),size.value,w,h)
 def run(self,l):
  with torch.cuda.stream(self.stream):rc=l.rocm_image_ccl8_run(C.byref(self.descriptor),self.stream.cuda_stream)
  self.stream.synchronize();return rc
 def save(self,out):
  self.stream.synchronize();out.mkdir(parents=True,exist_ok=True);raw=self.raw.cpu().numpy().tobytes();comp=self.comp.cpu().numpy().tobytes();src=self.src.cpu().numpy().tobytes();(out/'labels.bin').write_bytes(raw);(out/'compact.bin').write_bytes(comp);(out/'input-after.bin').write_bytes(src);record=dict(width=self.w,height=self.h,input_pitch=self.pitch,labels_pitch=self.lp,compact_pitch=self.cp,reported_count=int(self.count.cpu().item()),input_before_sha256=sha(self.data),input_after_sha256=sha(src),files={n:dict(bytes=(out/n).stat().st_size,sha256=sha((out/n).read_bytes())) for n in ['labels.bin','compact.bin','input-after.bin']});(out/'output.json').write_text(json.dumps(record,indent=2)+'\n');return record
 def checksum(self):
  self.stream.synchronize();return [sha(t.cpu().numpy().tobytes()) for t in [self.src,self.raw,self.comp,self.count,self.scratch]]
def main():
 p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--expected-sha',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--runtime',action='store_true');a=p.parse_args();assert sha(Path(a.library).read_bytes())==a.expected_sha;l=load(a.library);spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());out=a.output;out.mkdir(parents=True,exist_ok=True);rows=[];stream=torch.cuda.Stream()
 if not a.runtime:
  for c in spec['cases']:
   d=ROOT/c['fixture'];assert sha((d/'manifest.json').read_bytes())==c['manifest_sha256'];m=json.loads((d/'manifest.json').read_text())
   for n,v in m['files'].items():assert (d/n).stat().st_size==v['bytes'] and sha((d/n).read_bytes())==v['sha256']
   g=GPUImage(l,(d/'input.bin').read_bytes(),c['width'],c['height'],c['pitch'],stream);rc=g.run(l);r=g.save(out/c['case']);rows.append(dict(case=c['case'],return_code=rc,**r));print(c['case'],rc,r['reported_count'],flush=True)
 else:
  c=next(c for c in spec['cases'] if c['case']=='noise-847');data=(ROOT/c['fixture']/'input.bin').read_bytes();g=GPUImage(l,data,c['width'],c['height'],c['pitch'],stream)
  for name,change in [('null-input',{'input':None}),('null-labels',{'labels':None}),('null-compact',{'compact':None}),('null-count',{'count':None}),('null-workspace',{'workspace':None}),('zero-width',{'width':0}),('negative-height',{'height':-1}),('excess-width',{'width':32769}),('input-pitch-small',{'input_pitch':c['width']-1}),('labels-pitch-small',{'labels_pitch':c['width']*4-4}),('compact-pitch-small',{'compact_pitch':c['width']*4-4}),('unaligned-label-pitch',{'labels_pitch':c['width']*4+1}),('unaligned-compact-pitch',{'compact_pitch':c['width']*4+1}),('unaligned-workspace',{'workspace':g.scratch.data_ptr()+1}),('unaligned-label',{'labels':g.raw.data_ptr()+1}),('unaligned-count',{'count':g.count.data_ptr()+1}),('short-workspace',{'workspace_bytes':g.descriptor.workspace_bytes-1}),('input-output-overlap',{'labels':g.src.data_ptr()}),('output-output-overlap',{'compact':g.raw.data_ptr(),'compact_pitch':g.lp}),('count-workspace-overlap',{'count':g.scratch.data_ptr()}),('pitch-overflow',{'input_pitch':2**64-1}),('host-memory',{'input':C.cast(C.create_string_buffer(data),C.c_void_p).value}),('device-allocation-too-small',{'labels':g.count.data_ptr()})]:
   d=Descriptor.from_buffer_copy(bytes(g.descriptor));host=None
   if name=='host-memory':host=C.create_string_buffer(data);change['input']=C.cast(host,C.c_void_p).value
   for k,v in change.items():setattr(d,k,v)
   before=g.checksum();rc=l.rocm_image_ccl8_run(C.byref(d),stream.cuda_stream);after=g.checksum();rows.append(dict(case=name,kind='expected-error',return_code=rc,expected_return_code=1,before=before,after=after));print(name,rc,flush=True)
  for name,w,h,valid in [('workspace-1',1,1,True),('workspace-recursive',515,513,True),('query-zero',0,7,False),('query-negative',-1,7,False),('query-too-large',32768,32768,False)]:
   size=C.c_uint64(999);rc=l.rocm_image_ccl8_workspace_size(w,h,C.byref(size));rows.append(dict(case=name,kind='workspace-query',return_code=rc,width=w,height=h,bytes=size.value,valid=valid))
  for name,desc,n in [('null-descriptors',None,1),('zero-batch',C.byref(g.descriptor),0),('negative-batch',C.byref(g.descriptor),-1),('excess-batch',C.byref(g.descriptor),65537)]:
   before=g.checksum();rc=l.rocm_image_ccl8_batch(desc,n,stream.cuda_stream);rows.append(dict(case=name,kind='expected-error',return_code=rc,expected_return_code=1,before=before,after=g.checksum()))
  h=GPUImage(l,data,c['width'],c['height'],c['pitch'],stream);ds=(Descriptor*2)(g.descriptor,h.descriptor);ds[1].width=0;before=g.checksum()+h.checksum();rc=l.rocm_image_ccl8_batch(ds,2,stream.cuda_stream);rows.append(dict(case='batch-full-preflight',kind='expected-error',return_code=rc,expected_return_code=1,before=before,after=g.checksum()+h.checksum()))
  ds=(Descriptor*2)(g.descriptor,h.descriptor);ds[1].compact=ds[0].compact;ds[1].compact_pitch=ds[0].compact_pitch;before=g.checksum()+h.checksum();rc=l.rocm_image_ccl8_batch(ds,2,stream.cuda_stream);rows.append(dict(case='batch-cross-image-overlap',kind='expected-error',return_code=rc,expected_return_code=1,before=before,after=g.checksum()+h.checksum()))
  for name,payload in [('after-errors',data),('repeat',data),('changed-input',bytes([0]*len(data)))]:
   if name=='changed-input':
    with torch.cuda.stream(stream):g.src.zero_()
    g.data=payload
   rc=g.run(l);rec=g.save(out/name);rows.append(dict(case=name,kind='pixels',source_case=c['case'] if name!='changed-input' else None,return_code=rc,**rec));(out/name/'input-before.bin').write_bytes(payload)
  cs=[spec['cases'][i] for i in [0,2,10,12,21]];gs=[GPUImage(l,(ROOT/c['fixture']/'input.bin').read_bytes(),c['width'],c['height'],c['pitch'],stream) for c in cs];ds=(Descriptor*len(gs))(*(g.descriptor for g in gs));rc=l.rocm_image_ccl8_batch(ds,len(gs),stream.cuda_stream)
  for i,(g,c) in enumerate(zip(gs,cs)):
   name='heterogeneous-batch-'+str(i);rec=g.save(out/name);rows.append(dict(case=name,kind='pixels',source_case=c['case'],return_code=rc,**rec));(out/name/'input-before.bin').write_bytes(g.data)
  from concurrent.futures import ThreadPoolExecutor
  def independent(i):
   s=torch.cuda.Stream();g=GPUImage(l,data,c['width'],c['height'],c['pitch'],s);rc=g.run(l);name='concurrent-'+str(i);rec=g.save(out/name);(out/name/'input-before.bin').write_bytes(data);return dict(case=name,kind='pixels',source_case=c['case'],return_code=rc,**rec)
  # Use the original small descriptor geometry/data for concurrent independent states.
  c=next(c for c in spec['cases'] if c['case']=='noise-847')
  with ThreadPoolExecutor(max_workers=2) as pool:rows.extend(pool.map(independent,[0,1]))
 (out/'runs.json').write_text(json.dumps(rows,indent=2)+'\n');return 0
if __name__=='__main__':raise SystemExit(main())
