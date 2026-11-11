#!/usr/bin/env python3
"""Call actual contour/query/render APIs with independently fixed bad arguments."""
import ctypes as C,json,sys
from pathlib import Path
import numpy as np
import torch
from experiment import ROOT,Experiment,write,digest
from image_contour_worker import Descriptor
from image_contour_runtime_common import State,load_library
from image_contour_build import dependencies
from image_progress import record

def descriptor(d):return {n:int(getattr(d,n) or 0) for n,_ in Descriptor._fields_}
def substitute(value,base,tiny,host):
 if not isinstance(value,str):return value
 token=value[1:];suffix=1 if token.endswith('+1') else -1 if token.endswith('-1') else 0
 if suffix:token=token[:-2]
 return ({'tiny':tiny,'host':host}.get(token,base.get(token)))+suffix

def worker(out,library,sha):
 import _rocm_sdk_core
 spec=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());contract=json.loads((ROOT/'migration/rewrite/image-contour-argument-contract.json').read_text());c=next(c for c in spec['cases'] if c['case']==contract['source_case']);data=(ROOT/c['fixture']/'input.bin').read_bytes();stream=torch.cuda.Stream();s=State(load_library(library,sha),data,c['width'],c['height'],c['pitch'],stream);assert s.run()==0;l=s.lib;out.mkdir(parents=True);s.save_baseline(out/'baseline');extra=['work','render_work','out']
 for n in extra:getattr(s,n).cpu().numpy().tofile(out/'baseline'/(n+'.bin'))
 def snapshots():return dict(s.snapshots(),**{n:__import__('hashlib').sha256(getattr(s,n).cpu().numpy().tobytes()).hexdigest() for n in extra})
 hip=C.CDLL(str(Path(_rocm_sdk_core.__file__).parent/'lib/libamdhip64.so.7'));hip.hipMalloc.argtypes=[C.POINTER(C.c_void_p),C.c_size_t];hip.hipMemGetAddressRange.argtypes=[C.POINTER(C.c_void_p),C.POINTER(C.c_size_t),C.c_void_p];hip.hipFree.argtypes=[C.c_void_p];tiny=C.c_void_p();assert hip.hipMalloc(C.byref(tiny),16)==0;base=C.c_void_p();extent=C.c_size_t();assert hip.hipMemGetAddressRange(C.byref(base),C.byref(extent),tiny)==0
 if extent.value>=4*s.n*36:hip.hipFree(tiny);raise RuntimeError('Tiny physical range not below required geometry size; no invalid-pointer call executed')
 host=C.create_string_buffer(data);host_pointer=C.cast(host,C.c_void_p).value;minimum=C.c_uint64();assert l.rocm_image_contour_reconstruct_workspace_size(s.w,s.h,s.k,C.byref(minimum))==0;base_d=descriptor(s.descriptor);base_r=dict(labels=s.labels.data_ptr(),labels_pitch=s.lp,info=s.info.data_ptr(),components=s.k,geometry=s.geometry.data_ptr(),edge_count=s.m,start=0,stop=s.k,limit=2**32-1,output=s.out.data_ptr(),output_pitch=s.op,workspace=s.render_work.data_ptr(),workspace_bytes=minimum.value,width=s.w,height=s.h,stream=stream.cuda_stream);write(out/'setup.json',dict(descriptor=base_d,render=base_r,tiny=tiny.value,tiny_observed_bytes=extent.value,tiny_requested_bytes=16,host=host_pointer));rows=[]
 try:
  for name,rule in contract['cases'].items():
   before=snapshots();api=rule['api'];actual=None;value=None
   if api=='run':
    d=Descriptor.from_buffer_copy(bytes(s.descriptor));actual=dict(base_d)
    if 'descriptor' in rule['changes']:ptr=None;actual=None
    else:
     for field,v in rule['changes'].items():setattr(d,field,substitute(v,base_d,tiny.value,host_pointer));actual[field]=int(getattr(d,field) or 0)
     ptr=C.byref(d)
    code=l.rocm_image_contour_run(ptr,stream.cuda_stream)
   elif api=='render':
    actual=dict(base_r)
    for field,v in rule['changes'].items():actual[field]=substitute(v,base_r,tiny.value,host_pointer)
    code=l.rocm_image_contour_reconstruct(*(actual[n] for n in base_r))
   elif api.startswith('run-query'):
    value=C.c_uint64(999);code=l.rocm_image_contour_workspace_size(*rule['params'],None if api.endswith('null') else C.byref(value));value=None if api.endswith('null') else value.value;actual=rule['params']
   elif api.startswith('render-query'):
    value=C.c_uint64(999);code=l.rocm_image_contour_reconstruct_workspace_size(*rule['params'],None if api.endswith('null') else C.byref(value));value=None if api.endswith('null') else value.value;actual=rule['params']
   elif api=='positive':code=s.run();actual=descriptor(s.descriptor);s.save_baseline(out/'after-errors')
   else:raise ValueError(api)
   stream.synchronize();rows.append(dict(case=name,api=api,return_code=code,actual_arguments=actual,query_bytes=value,before=before,after=snapshots()));write(out/'runs.json',rows);print(name,code,flush=True)
 finally:hip.hipFree(tiny)
 return 0

def main():
 if len(sys.argv)>1:return worker(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/image-contour-build.json').read_text());e=Experiment('I2','Contour-actual-argument-and-query-errors','rocm-runtime',sources=[__file__,ROOT/'tools/moat/image_contour_runtime_common.py',ROOT/'tools/moat/image_contour_worker.py',ROOT/'migration/rewrite/image-contour-argument-contract.json',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command([sys.executable,__file__,str(out),str(ROOT/b['library']),b['library_sha256']],'actual-fixed-C-ABI-and-workspace-queries',timeout=180);r=dict(return_code=rc,outputs=str(out.relative_to(ROOT)),build=b,experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/image-contour-arguments.json',r);record('I2','Contour参数/实际物理分配范围/所有指针跨度对齐重叠/范围/query/错误后恢复实际执行rc='+str(rc)+'；独立固定角色及原始存储/返回码验收另行进行。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
