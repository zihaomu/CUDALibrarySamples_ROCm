#!/usr/bin/env python3
"""GPU-owned state for actual contour ABI/runtime investigations."""
import ctypes as C,hashlib
import numpy as np
import torch
from image_contour_worker import Descriptor

def load_library(path,expected_sha,legacy=False):
 assert hashlib.sha256(open(path,'rb').read()).hexdigest()==expected_sha;l=C.CDLL(str(path));l.rocm_image_contour_abi_version.restype=C.c_uint32;abi=int(l.rocm_image_contour_abi_version());assert abi==(1 if legacy else 2);l.rocm_image_contour_workspace_size.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_uint64)];l.rocm_image_contour_run.argtypes=[C.POINTER(Descriptor),C.c_void_p]
 if not legacy:l.rocm_image_contour_reconstruct_workspace_size.argtypes=[C.c_int,C.c_int,C.c_uint32,C.POINTER(C.c_uint64)]
 l.rocm_image_contour_reconstruct.argtypes=[C.c_void_p,C.c_uint64,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint64,C.c_void_p,C.c_uint64,C.c_int,C.c_int,C.c_void_p];return l
class State:
 def __init__(self,lib,data,w,h,pitch,stream,legacy=False):
  self.lib,self.stream,self.legacy=lib,stream,legacy;self.w,self.h,self.pitch=w,h,pitch;self.n=w*h;self.rp,self.lp,self.mp,self.op=4*w+20,4*w+28,w+13,w+17;self.data=data;wb=C.c_uint64();assert lib.rocm_image_contour_workspace_size(w,h,C.byref(wb))==0;self.wb=wb.value
  with torch.cuda.stream(stream):
   self.src=torch.from_numpy(np.frombuffer(data,np.uint8).copy()).to('cuda');self.raw=torch.full((h*self.rp,),167,dtype=torch.uint8,device='cuda');self.labels=torch.full((h*self.lp,),185,dtype=torch.uint8,device='cuda');self.mask=torch.full((h*self.mp,),171,dtype=torch.uint8,device='cuda');self.info=torch.full((self.n*28,),221,dtype=torch.uint8,device='cuda');self.geometry=torch.full((4*self.n*36,),205,dtype=torch.uint8,device='cuda');self.totals=torch.full((3,),-1,dtype=torch.int32,device='cuda');self.work=torch.full((self.wb,),211,dtype=torch.uint8,device='cuda');self.out=torch.full((h*self.op,),173,dtype=torch.uint8,device='cuda')
   rw=C.c_uint64(4*(self.n+1));assert legacy or lib.rocm_image_contour_reconstruct_workspace_size(w,h,self.n,C.byref(rw))==0;self.rwb=rw.value;self.render_work=torch.full((self.rwb,),219,dtype=torch.uint8,device='cuda')
  self.descriptor=Descriptor(self.src.data_ptr(),pitch,self.raw.data_ptr(),self.rp,self.labels.data_ptr(),self.lp,self.mask.data_ptr(),self.mp,self.info.data_ptr(),self.n,self.geometry.data_ptr(),4*self.n,self.totals.data_ptr(),self.work.data_ptr(),self.wb,w,h)
 def run(self):
  rc=self.lib.rocm_image_contour_run(C.byref(self.descriptor),self.stream.cuda_stream);self.stream.synchronize();self.k,self.m,self.loops=map(int,self.totals.cpu().tolist());return rc
 def render(self,start=0,stop=None,limit=2**32-1,count=None):
  return self.lib.rocm_image_contour_reconstruct(self.labels.data_ptr(),self.lp,self.info.data_ptr(),self.k,self.geometry.data_ptr(),self.m if count is None else count,start,self.k if stop is None else stop,limit,self.out.data_ptr(),self.op,self.render_work.data_ptr(),self.rwb,self.w,self.h,self.stream.cuda_stream)
 def reset_output(self):
  with torch.cuda.stream(self.stream):self.out.fill_(173)
 def snapshots(self):
  self.stream.synchronize();return {n:hashlib.sha256(getattr(self,n).cpu().numpy().tobytes()).hexdigest() for n in ['src','raw','labels','mask','info','geometry','totals']}
 def save_baseline(self,out):
  out.mkdir(parents=True);self.stream.synchronize()
  for n in ['src','raw','labels','mask','info','geometry','totals']:getattr(self,n).cpu().numpy().tofile(out/(n+'.bin'))
