#!/usr/bin/env python3
"""Execute real HIP contour graph/order and geometry-driven rasterization."""
import argparse,ctypes as C,json,hashlib
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[2]
class Descriptor(C.Structure):
 _fields_=[('input',C.c_void_p),('input_pitch',C.c_uint64),('raw_labels',C.c_void_p),('raw_pitch',C.c_uint64),('labels',C.c_void_p),('labels_pitch',C.c_uint64),('mask',C.c_void_p),('mask_pitch',C.c_uint64),('info',C.c_void_p),('info_capacity',C.c_uint64),('geometry',C.c_void_p),('geometry_capacity',C.c_uint64),('totals',C.c_void_p),('workspace',C.c_void_p),('workspace_bytes',C.c_uint64),('width',C.c_int),('height',C.c_int)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--library',required=True);p.add_argument('--sha',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--small',action='store_true');a=p.parse_args();assert sha(a.library)==a.sha;l=C.CDLL(a.library);l.rocm_image_contour_abi_version.restype=C.c_uint32;assert l.rocm_image_contour_abi_version()==2;l.rocm_image_contour_reconstruct_workspace_size.argtypes=[C.c_int,C.c_int,C.c_uint32,C.POINTER(C.c_uint64)];l.rocm_image_contour_workspace_size.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint64)];l.rocm_image_contour_run.argtypes=[C.POINTER(Descriptor),C.c_void_p];l.rocm_image_contour_reconstruct.argtypes=[C.c_void_p,C.c_uint64,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint64,C.c_void_p,C.c_uint64,C.c_int,C.c_int,C.c_void_p];spec=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());a.output.mkdir(parents=True);rows=[];stream=torch.cuda.Stream()
 for c in spec['cases']:
  w,h,pitch=c['width'],c['height'],c['pitch'];n=w*h
  if a.small and n>5000:continue
  fixture=ROOT/c['fixture'];assert sha(fixture/'manifest.json')==c['manifest_sha256']
  for name,v in json.loads((fixture/'manifest.json').read_text())['files'].items():assert (fixture/name).stat().st_size==v['bytes'] and sha(fixture/name)==v['sha256']
  where=a.output/c['case'];where.mkdir();rp,lp,mp,op=4*w+20,4*w+28,w+13,w+17;wb=C.c_uint64();assert l.rocm_image_contour_workspace_size(w,h,C.byref(wb))==0
  with torch.cuda.stream(stream):
   src=torch.from_numpy(np.frombuffer((fixture/'input.bin').read_bytes(),np.uint8).copy()).to('cuda');raw=torch.full((h*rp,),167,dtype=torch.uint8,device='cuda');labels=torch.full((h*lp,),185,dtype=torch.uint8,device='cuda');mask=torch.full((h*mp,),171,dtype=torch.uint8,device='cuda');info=torch.full((n*28,),221,dtype=torch.uint8,device='cuda');geometry=torch.full((4*n*36,),205,dtype=torch.uint8,device='cuda');totals=torch.full((3,),-1,dtype=torch.int32,device='cuda');work=torch.full((wb.value,),211,dtype=torch.uint8,device='cuda');d=Descriptor(src.data_ptr(),pitch,raw.data_ptr(),rp,labels.data_ptr(),lp,mask.data_ptr(),mp,info.data_ptr(),n,geometry.data_ptr(),4*n,totals.data_ptr(),work.data_ptr(),wb.value,w,h);rc=l.rocm_image_contour_run(C.byref(d),stream.cuda_stream)
  stream.synchronize();count=totals.cpu().numpy().astype(np.uint32);k,edges,loops=map(int,count);row=dict(case=c['case'],return_code=rc,width=w,height=h,input_pitch=pitch,raw_pitch=rp,labels_pitch=lp,mask_pitch=mp,totals=[k,edges,loops],ranges=[])
  if rc==0 and 0<k<=n and 0<edges<=4*n:
   for name,tensor in [('raw.bin',raw),('labels.bin',labels),('mask.bin',mask),('input-after.bin',src)]:tensor.cpu().numpy().tofile(where/name)
   info.view(torch.int32).view(n,7)[:k].cpu().numpy().astype('<u4').tofile(where/'info.bin');geometry.view(torch.int32).view(4*n,9)[:edges].cpu().numpy().astype('<u4').tofile(where/'geometry.bin');count.astype('<u4').tofile(where/'totals.bin')
   intervals=[('all',0,k,2**32-1),('default',1,k,262144),('empty',k,k,262144)]+([('single-ID-override',1,2,262144)] if c['case']=='large-multiple-ID-bypass' else [])
   for name,start,stop,limit in intervals:
    with torch.cuda.stream(stream):
     output=torch.full((h*op,),173,dtype=torch.uint8,device='cuda');rwb=C.c_uint64();assert l.rocm_image_contour_reconstruct_workspace_size(w,h,k,C.byref(rwb))==0;scratch=torch.full((rwb.value,),219,dtype=torch.uint8,device='cuda');code=l.rocm_image_contour_reconstruct(labels.data_ptr(),lp,info.data_ptr(),k,geometry.data_ptr(),edges,start,stop,limit,output.data_ptr(),op,scratch.data_ptr(),rwb.value,w,h,stream.cuda_stream)
    stream.synchronize();filename='reconstruction-'+name+'.bin';output.cpu().numpy().tofile(where/filename);row['ranges'].append(dict(case=name,start=start,stop=stop,limit=limit,return_code=code,output_pitch=op,file=filename))
   # On small cases preserve every unused record byte for strict canary checks.
   if n<=5000:
    info.view(torch.int32).view(n,7)[k:].cpu().numpy().view(np.uint8).tofile(where/'unused-info.bin');geometry.view(torch.int32).view(4*n,9)[edges:].cpu().numpy().view(np.uint8).tofile(where/'unused-geometry.bin')
  row['files']={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in where.iterdir()};(where/'run.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row);(a.output/'runs.json').write_text(json.dumps(rows,indent=2)+'\n');print(c['case'],rc,[k,edges,loops],[(r['case'],r['return_code']) for r in row['ranges']],flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':raise SystemExit(main())
