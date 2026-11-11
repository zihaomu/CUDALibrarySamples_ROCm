#!/usr/bin/env python3
"""Run the actual HIP backend with full padded device buffers."""
import argparse,ctypes as C,json
from pathlib import Path
import numpy as np
import torch
from experiment import ROOT,write,digest
from image_distance_inputs import load_case

class Descriptor(C.Structure):
 _fields_=[('input',C.c_void_p),('input_pitch',C.c_uint64),('distance',C.c_void_p),('distance_pitch',C.c_uint64),('visualization',C.c_void_p),('visualization_pitch',C.c_uint64),('indices',C.c_void_p),('indices_pitch',C.c_uint64),('relative',C.c_void_p),('relative_pitch',C.c_uint64),('site_ids',C.c_void_p),('site_ids_pitch',C.c_uint64),('sites_xy',C.c_void_p),('sites_xy_pitch',C.c_uint64),('workspace',C.c_void_p),('workspace_bytes',C.c_uint64),('cutoff',C.c_double),('width',C.c_int32),('height',C.c_int32),('mode',C.c_uint32),('input_type',C.c_uint32),('remap_circle',C.c_uint32),('reserved',C.c_uint32)]

def load(path,sha):
 assert digest(path)==sha;l=C.CDLL(str(path));l.rocm_image_distance_abi_version.restype=C.c_uint32;assert l.rocm_image_distance_abi_version()==1;l.rocm_image_distance_workspace_size.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint64)];l.rocm_image_distance_run.argtypes=[C.POINTER(Descriptor),C.c_void_p];return l

def main():
 p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--sha',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();l=load(a.library,a.sha);spec=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());a.output.mkdir(parents=True);rows=[];stream=torch.cuda.Stream()
 for case in spec['cases']:
  name=case['case'];w,h=case['width'],case['height'];n=w*h;d=a.output/name;d.mkdir();payload=load_case(case);wb=C.c_uint64();assert l.rocm_image_distance_workspace_size(w,h,C.byref(wb))==0;pitches=dict(distance=w*8+40,visualization=w*2+18,indices=w*4+20,relative=w*4+28,site_ids=w*8+24,sites_xy=w*16+32);pads=dict(distance=167,visualization=185,indices=171,relative=173,site_ids=205,sites_xy=221)
  with torch.cuda.stream(stream):
   src=torch.from_numpy(np.frombuffer(payload,np.uint8).copy()).to('cuda');work=torch.full((wb.value,),211,dtype=torch.uint8,device='cuda');outputs={k:torch.full((h*pitch,),pads[k],dtype=torch.uint8,device='cuda') for k,pitch in pitches.items()}
  descriptor=Descriptor(input=src.data_ptr(),input_pitch=case['pitch'],workspace=work.data_ptr(),workspace_bytes=wb.value,cutoff=case['cutoff'],width=w,height=h,mode=case['mode'],input_type=case['input_type'],remap_circle=case['remap_circle'],reserved=0)
  for key,tensor in outputs.items():setattr(descriptor,key,tensor.data_ptr());setattr(descriptor,key+'_pitch',pitches[key])
  rc=l.rocm_image_distance_run(C.byref(descriptor),stream.cuda_stream);stream.synchronize();src.cpu().numpy().tofile(d/'input-after.bin')
  for key,tensor in outputs.items():tensor.cpu().numpy().tofile(d/(key+'.bin'))
  r=dict(case=name,width=w,height=h,input_pitch=case['pitch'],pitches=pitches,pads=pads,return_code=rc,workspace_bytes=wb.value,descriptor_bytes=C.sizeof(Descriptor),input_before_sha256=__import__('hashlib').sha256(payload).hexdigest(),files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in d.iterdir() if p.is_file()});rows.append(r);write(a.output/'runs.json',rows);print(name,rc,flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':raise SystemExit(main())
