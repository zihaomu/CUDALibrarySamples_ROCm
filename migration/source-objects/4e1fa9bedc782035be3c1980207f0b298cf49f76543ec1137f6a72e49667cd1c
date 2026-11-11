#!/usr/bin/env python3
"""Execute every frozen RGB flood input through the real HIP C ABI."""
import argparse,ctypes as C,hashlib,json
from pathlib import Path
import numpy as np
import torch
from experiment import ROOT,write,digest
from image_flood_inputs import load_case
class Descriptor(C.Structure):
 _fields_=[('version',C.c_uint32),('descriptor_bytes',C.c_uint32),('width',C.c_int32),('height',C.c_int32),('mode',C.c_uint32),('seed_x',C.c_int32),('seed_y',C.c_int32),('reserved',C.c_uint32),('input',C.c_void_p),('input_pitch',C.c_uint64),('output',C.c_void_p),('output_pitch',C.c_uint64),('mask',C.c_void_p),('mask_pitch',C.c_uint64),('lower',C.c_uint32*3),('upper',C.c_uint32*3),('fill',C.c_uint32*3),('boundary',C.c_uint32*3),('region',C.c_void_p),('workspace',C.c_void_p),('workspace_bytes',C.c_uint64),('reserved_tail',C.c_uint64)]
def load(path,sha):
 if digest(path)!=sha:raise ValueError('current flood library identity')
 l=C.CDLL(str(path));l.rocm_image_flood_abi_version.restype=C.c_uint32
 if l.rocm_image_flood_abi_version()!=1 or C.sizeof(Descriptor)!=160:raise ValueError('flood ABI1/160')
 l.rocm_image_flood_workspace_size.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint64)];l.rocm_image_flood_run.argtypes=[C.POINTER(Descriptor),C.c_void_p];return l
def main():
 p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--sha',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();l=load(a.library,a.sha);spec=json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text());a.output.mkdir(parents=True);stream=torch.cuda.Stream();rows=[]
 for c in spec['cases']:
  w,h=c['width'],c['height'];folder=a.output/c['case'];folder.mkdir();payload=load_case(c);wb=C.c_uint64();assert l.rocm_image_flood_workspace_size(w,h,C.byref(wb))==0;output_pitch=3*w+19;mask_pitch=w+23
  with torch.cuda.stream(stream):
   src=torch.from_numpy(np.frombuffer(payload,np.uint8).copy()).to('cuda');dst=torch.full((h*output_pitch,),185,dtype=torch.uint8,device='cuda');mask=torch.full((h*mask_pitch,),171,dtype=torch.uint8,device='cuda');region=torch.full((32,),167,dtype=torch.uint8,device='cuda');work=torch.full((wb.value,),211,dtype=torch.uint8,device='cuda')
  d=Descriptor(version=1,descriptor_bytes=C.sizeof(Descriptor),width=w,height=h,mode=c['mode'],seed_x=c['seed'][0],seed_y=c['seed'][1],input=src.data_ptr(),input_pitch=c['pitch'],output=dst.data_ptr(),output_pitch=output_pitch,mask=mask.data_ptr(),mask_pitch=mask_pitch,region=region.data_ptr(),workspace=work.data_ptr(),workspace_bytes=wb.value)
  for k in ['lower','upper','fill','boundary']:setattr(d,k,(C.c_uint32*3)(*c[k]))
  rc=l.rocm_image_flood_run(C.byref(d),stream.cuda_stream);stream.synchronize()
  for name,t in [('input-after',src),('output',dst),('mask',mask),('region',region)]:t.cpu().numpy().tofile(folder/(name+'.bin'))
  row=dict(case=c['case'],return_code=rc,width=w,height=h,input_pitch=c['pitch'],output_pitch=output_pitch,mask_pitch=mask_pitch,workspace_bytes=wb.value,descriptor_bytes=C.sizeof(Descriptor),input_before_sha256=hashlib.sha256(payload).hexdigest(),parameters={k:c[k] for k in ['mode','seed','lower','upper','fill','boundary']},files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in folder.iterdir()});rows.append(row);write(a.output/'runs.json',rows);print(c['case'],rc,flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':raise SystemExit(main())
