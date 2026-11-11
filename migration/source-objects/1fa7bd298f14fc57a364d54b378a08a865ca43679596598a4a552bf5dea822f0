#!/usr/bin/env python3
"""Exercise caller streams, lifetimes and invalid spans on the actual HIP device."""
import argparse,ctypes,json,os,sys
from pathlib import Path
from experiment import ROOT,Experiment,write,digest

OUTPUT_CASES=['repeat-first','repeat-second','changed-input','cpu-uint8',
 'cpu-float16','cpu-float32','cpu-float64','gpu-float16','gpu-float32',
 'noncontiguous','stream-a','stream-b','concurrent-a','concurrent-b','after-errors']
PY_ERRORS=['rank-one','rank-three','zero-size','negative-threshold','reverse-threshold',
 'large-threshold','fractional-threshold','not-tensor']
ABI_ERRORS=['zero-width','negative-height','large-width','bad-channels','negative-low',
 'reverse-threshold','large-high','null-source','null-output','null-workspace',
 'short-source-pitch','short-output-pitch','short-source-span','short-output-span',
 'short-workspace','overstated-source-allocation','overstated-output-allocation',
 'overstated-workspace-allocation','alias-input-output','alias-input-workspace',
 'alias-output-workspace','misaligned-workspace','host-source','overflow-pitch']

def contract():
 return dict(schema_version=1,outputs=OUTPUT_CASES,python_errors=PY_ERRORS,ABI_errors=ABI_ERRORS,
  expected_ABI_status=1,actual_device='Guarded single gfx1201 device; two caller-owned nondefault streams',
  wrong_device_scope='Cross-device handles are rejected by the API; no extra busy or forbidden GPU is opened for this single-device qualification.')

def worker(out,library,expected_sha,trace_only=False):
 import concurrent.futures
 import numpy as np,torch
 sys.path.insert(0,str(ROOT/'rocm/python'))
 from image.canny import CannyEdgeDetector
 assert digest(library)==expected_sha
 out.mkdir(parents=True);detector=CannyEdgeDetector(library);rows=[];pending=[]
 base=np.random.default_rng(20261111).integers(0,256,(37,49),dtype=np.uint8)
 binary=np.where(base>127,255,0).astype(np.uint8)
 def submit(name,tensor,expected,stream=None):
  stream=stream or torch.cuda.current_stream()
  with torch.cuda.stream(stream):result=detector(tensor,72,256)
  pending.append((name,result,expected.copy(),stream))
 if trace_only:
  a=torch.from_numpy(base).cuda();b=torch.from_numpy(np.flip(base,1).copy()).cuda()
  submit('trace-first',a,base);submit('trace-changed',b,np.flip(base,1).copy())
 else:
  gpu=torch.from_numpy(base).cuda();submit('repeat-first',gpu,base);submit('repeat-second',gpu,base)
  changed=np.flip(base,1).copy();submit('changed-input',torch.from_numpy(changed).cuda(),changed)
  submit('cpu-uint8',torch.from_numpy(base),base)
  for place,dtypes in [('cpu',[torch.float16,torch.float32,torch.float64]),('gpu',[torch.float16,torch.float32])]:
   for dtype in dtypes:
    tensor=torch.from_numpy(binary).to(dtype)/255
    if place=='gpu':tensor=tensor.cuda()
    submit(place+'-'+str(dtype).split('.')[-1],tensor,binary)
  padded=torch.zeros((37,98),dtype=torch.uint8,device='cuda');padded[:,::2]=gpu
  submit('noncontiguous',padded[:,::2],base)
  streams=[torch.cuda.Stream(),torch.cuda.Stream()]
  for stream in streams:stream.wait_stream(torch.cuda.current_stream())
  submit('stream-a',gpu,base,streams[0]);submit('stream-b',torch.from_numpy(changed).cuda(),changed,streams[1])
  def thread_job(index):
   torch.cuda.set_device(0)
   with torch.cuda.stream(streams[index]):
    independent=CannyEdgeDetector(library);source=torch.from_numpy(base if index==0 else changed).cuda()
    return independent(source,72,256)
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   futures=[pool.submit(thread_job,i) for i in range(2)]
   for i,f in enumerate(futures):pending.append(('concurrent-'+('a' if i==0 else 'b'),f.result(),(base if i==0 else changed).copy(),streams[i]))
  # Pressure the caching allocator after temporary input/workspace references die.
  pressure=[torch.full((37*49*8,),231,dtype=torch.uint8,device='cuda') for _ in range(32)]
  bad=[torch.zeros(4),torch.zeros(2,3,4),torch.zeros(0,3),gpu,gpu,gpu,gpu,[[1]]]
  thresholds=[(72,256)]*3+[(-1,256),(257,256),(72,32768),(1.5,256),(72,256)]
  for name,tensor,(lo,hi) in zip(PY_ERRORS,bad,thresholds):
   try:detector(tensor,lo,hi)
   except (ValueError,TypeError):rows.append(dict(case='python/'+name,passed=True))
   else:rows.append(dict(case='python/'+name,passed=False))
  h,w=base.shape;output=torch.full_like(gpu,173);space=torch.empty(h*w*8,dtype=torch.uint8,device='cuda')
  original=[gpu.data_ptr(),gpu.numel(),w,w,h,1,72,256,output.data_ptr(),output.numel(),w,space.data_ptr(),space.numel(),0]
  changes=[{3:0},{4:-1},{3:32769},{5:2},{6:-1},{6:257},{7:32768},{0:0},{8:0},{11:0},
   {2:w-1},{10:w-1},{1:gpu.numel()-1},{9:output.numel()-1},{12:space.numel()-1},
   {1:1<<40},{9:1<<40},{12:1<<40},{8:gpu.data_ptr()},{11:gpu.data_ptr()},
   {11:output.data_ptr()},{11:space.data_ptr()+1},{0:base.ctypes.data},{2:(1<<64)-1}]
  for name,change in zip(ABI_ERRORS,changes):
   args=original.copy()
   for k,v in change.items():args[k]=v
   rc=detector.call(*args);rows.append(dict(case='ABI/'+name,status=rc,passed=rc==1))
  # All rejected calls must leave caller storage and input untouched.
  torch.cuda.synchronize()
  rows.append(dict(case='rejected-call-output-preserved',passed=bool(torch.all(output==173).item())))
  rows.append(dict(case='rejected-call-input-preserved',passed=bool(np.array_equal(gpu.cpu().numpy(),base))))
  submit('after-errors',gpu,base)
 torch.cuda.synchronize()
 for name,result,expected,stream in pending:
  d=out/name;d.mkdir();expected.tofile(d/'input.bin');result.cpu().numpy().tofile(d/'output.bin')
  write(d/'config.json',dict(width=expected.shape[1],height=expected.shape[0],pitch=expected.shape[1],channels=1,low=72,high=256))
  rows.append(dict(case=name,passed=True,stream=int(stream.cuda_stream),files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in d.iterdir()}))
 write(out/'results.json',rows)
 if not all(r['passed'] for r in rows):raise RuntimeError('runtime contract failed: '+str([r for r in rows if not r['passed']]))

def main():
 p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--trace-only',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--library',type=Path);p.add_argument('--expected-sha');a=p.parse_args()
 if a.worker:return worker(a.output,a.library,a.expected_sha,a.trace_only)
 from snapshot import capture
 from image_progress import record
 from canny_plus_build import dependencies
 spec=ROOT/'migration/rewrite/canny-plus-runtime.json'
 if not spec.exists():write(spec,contract())
 if json.loads(spec.read_text())!=contract():raise RuntimeError('Runtime case contract changed')
 build=json.loads((ROOT/'migration/reports/canny-plus-build.json').read_text());library=ROOT/build['library']
 if any(digest(ROOT/n)!=sha for n,sha in build['dependencies'].items()) or digest(library)!=build['library_sha256']:raise RuntimeError('Stale library')
 e=Experiment('I1','CannyPlus-runtime','rocm-trace' if a.trace_only else 'rocm-runtime',sources=[__file__,spec,*dependencies()],parent=build['experiment_id']);write(e.path/'backend.observed.json',capture())
 command=[sys.executable,__file__,'--worker','--output',str(e.path/'outputs'),'--library',str(library),'--expected-sha',build['library_sha256']]
 if a.trace_only:command=['rocprofv3','--kernel-trace','--hip-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--']+command+['--trace-only']
 env=dict(os.environ,PYTHONPATH=str(ROOT/'build/image-gpu-site')+os.pathsep+str(ROOT/'rocm/python'))
 rc=e.command(command,'actual-trace' if a.trace_only else 'actual-runtime-and-invalid-ABI',env=env,timeout=300)
 result=dict(return_code=rc,experiment_id=e.id,build=build,outputs=str((e.path/'outputs').relative_to(ROOT)),trace=str((e.path/'trace').relative_to(ROOT)))
 write(e.path/'run.json',result);result['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/('migration/reports/canny-plus-trace.json' if a.trace_only else 'migration/reports/canny-plus-runtime.json'),result)
 record('I1','Canny '+('实际GPU trace' if a.trace_only else 'stream/并发/ABI负向')+'执行rc='+str(rc)+'；独立数值核对与资格仍单列。',[result['evidence']]);print(rc,result['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
