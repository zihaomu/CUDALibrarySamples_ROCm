#!/usr/bin/env python3
"""Real default/foreign/destroyed stream execution on guarded physical GPU0/1."""
import ctypes as C,json,sys
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_ccl_build import dependencies
from image_progress import record
from snapshot import capture

def actual_worker(output,library,expected):
 import torch,_rocm_sdk_core
 from image_ccl_worker import GPUImage,load
 from snapshot import capture
 observed=capture();devices=observed['devices'];assert {d['physical_id'] for d in devices}=={0,1};current=next(d['logical_id'] for d in devices if d['physical_id']==1);other=next(d['logical_id'] for d in devices if d['physical_id']==0);torch.cuda.set_device(current);assert digest(library)==expected;l=load(library);hip=C.CDLL(str(Path(_rocm_sdk_core.__file__).parent/'lib/libamdhip64.so.7'));hip.hipStreamCreateWithFlags.argtypes=[C.POINTER(C.c_void_p),C.c_uint];hip.hipStreamGetDevice.argtypes=[C.c_void_p,C.POINTER(C.c_int)];hip.hipStreamDestroy.argtypes=[C.c_void_p];hip.hipSetDevice.argtypes=[C.c_int]
 spec=json.loads((ROOT/'migration/rewrite/image-ccl-profile.json').read_text());case=next(c for c in spec['cases'] if c['case']=='noise-847');d=ROOT/case['fixture'];data=(d/'input.bin').read_bytes();stream=torch.cuda.default_stream(current);assert stream.cuda_stream==0;g=GPUImage(l,data,case['width'],case['height'],case['pitch'],stream);where=Path(output);where.mkdir(parents=True);device=C.c_int(-1);query=hip.hipStreamGetDevice(None,C.byref(device));rc=g.run(l);r=g.save(where/'default-stream');rows=[dict(case='default-stream',kind='pixels',return_code=rc,stream_query_return_code=query,stream_device=device.value,current_device=current,source_case=case['case'],**r)]
 for name in ['foreign-device-stream','destroyed-stream']:
  s=C.c_void_p();assert hip.hipSetDevice(other if name=='foreign-device-stream' else current)==0;assert hip.hipStreamCreateWithFlags(C.byref(s),1)==0;assert hip.hipSetDevice(current)==0;before=g.checksum()
  if name=='destroyed-stream':assert hip.hipStreamDestroy(s)==0
  device=C.c_int(-1);query=hip.hipStreamGetDevice(s,C.byref(device));rc=l.rocm_image_ccl8_run(C.byref(g.descriptor),s);after=g.checksum();rows.append(dict(case=name,kind='expected-error',return_code=rc,stream_query_return_code=query,stream_device=device.value,current_device=current,foreign_device=other,before=before,after=after))
  if name=='foreign-device-stream':assert hip.hipSetDevice(other)==0;assert hip.hipStreamDestroy(s)==0;assert hip.hipSetDevice(current)==0
 write(where/'runs.json',rows);write(where/'devices.json',observed);print([(r['case'],r['return_code'],r['stream_query_return_code']) for r in rows]);return 0

def main():
 if len(sys.argv)>1:return actual_worker(sys.argv[1],sys.argv[2],sys.argv[3])
 b=json.loads((ROOT/'migration/reports/image-ccl-build.json').read_text());assert b['status']=='BUILT' and all(digest(ROOT/n)==v for n,v in b['dependencies'].items());e=Experiment('I2','CCL-default-foreign-destroyed-streams','rocm-streams',sources=[__file__,ROOT/'tools/moat/image_ccl_worker.py',ROOT/'migration/rewrite/image-ccl-stream-contract.json',*dependencies()],parent=b['experiment_id'])
 try:
  observed=capture();write(e.path/'backend.observed.json',observed)
  if {d['physical_id'] for d in observed['devices']}!={0,1}:raise RuntimeError('Need exactly guarded physical GPU0/1; no pixel work started')
 except Exception as error:
  ref=e.finish('GUARD_FAILED',reason=repr(error));record('I2','额外stream验收设备guard拒绝：'+repr(error),[ref]);return 1
 out=e.path/'outputs';rc=e.command([sys.executable,__file__,str(out),str(ROOT/b['library']),b['library_sha256']],'actual-default-foreign-destroyed-streams',timeout=180);r=dict(return_code=rc,outputs=str(out.relative_to(ROOT)),build=b,experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/image-ccl-streams.json',r);record('I2','CCL真实默认流及外设备/销毁流执行rc='+str(rc)+'；仅GPU1计算像素，GPU0仅创建外设备stream，GPU3未暴露。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
