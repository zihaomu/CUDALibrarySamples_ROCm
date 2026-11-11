#!/usr/bin/env python3
"""Exercise actual malformed descriptors, physical allocation spans and size queries."""
import argparse,ctypes as C,json,sys
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record
from image_distance_build import dependencies

def resolve(value,base,setup):
 if not isinstance(value,str):return value
 if value in ['NaN','Infinity','-Infinity']:return float(value.replace('Infinity','inf'))
 if not value.startswith('$'):raise ValueError('frozen argument expression')
 key=value[1:];delta=1 if key.endswith('+1') else -1 if key.endswith('-1') else 0
 if delta:key=key[:-2]
 return (base[key] if key in base else setup[key])+delta

def worker(a):
 import torch
 from image_distance_inputs import load_case
 from image_distance_worker import load,Descriptor
 from image_distance_runtime_common import State,plain,hip_library
 contract=json.loads((ROOT/'migration/rewrite/image-distance-argument-contract.json').read_text());spec=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());case=next(c for c in spec['cases'] if c['case']==contract['source_case']);lib=load(a.library,a.sha);stream=torch.cuda.Stream();state=State(lib,case,load_case(case),stream);assert state.run()==0;stream.synchronize();out=Path(a.output);out.mkdir(parents=True);state.save(out/'baseline');base=plain(state.d);hip=hip_library();tiny=C.c_void_p();assert hip.hipMalloc(C.byref(tiny),16)==0;origin=C.c_void_p();observed=C.c_size_t();assert hip.hipMemGetAddressRange(C.byref(origin),C.byref(observed),tiny)==0;host=C.create_string_buffer(case['height']*case['pitch']);setup=dict(descriptor=base,tiny=tiny.value,tiny_requested_bytes=16,tiny_observed_bytes=observed.value,host=C.addressof(host),source_case=case['case']);w=case['width'];setup.update(minimum_input_pitch=4*w,minimum_distance_pitch=8*w,minimum_visualization_pitch=2*w,minimum_indices_pitch=4*w,minimum_relative_pitch=4*w,minimum_site_ids_pitch=8*w,minimum_sites_xy_pitch=16*w);write(out/'setup.json',setup);rows=[]
 try:
  for rule in contract['cases']:
   api=rule['api'];before=state.snapshot();actual=None;size=None
   if api=='run':
    if 'descriptor' in rule['changes']:rc=lib.rocm_image_distance_run(None,stream.cuda_stream)
    else:
     fields={k:resolve(v,base,setup) for k,v in rule['changes'].items()};arguments=dict(base,**fields);d=Descriptor(**arguments);actual=plain(d);rc=lib.rocm_image_distance_run(C.byref(d),stream.cuda_stream)
   elif api in ['query','query-null']:
    actual=rule['params'];query=C.c_uint64(12345);rc=lib.rocm_image_distance_workspace_size(*actual,None if api=='query-null' else C.byref(query));size=None if api=='query-null' else query.value
   elif api=='positive':actual=base;rc=state.run();stream.synchronize();state.save(out/'after-errors')
   else:raise ValueError('fixed actual API kind')
   after=state.snapshot();row=dict(case=rule['case'],api=api,return_code=rc,actual_arguments=actual,query_bytes=size,before=before,after=after);rows.append(row);write(out/'runs.json',rows);print(rule['case'],rc,flush=True)
 finally:assert hip.hipFree(tiny)==0
 return 0

def main():
 p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--output');p.add_argument('--library');p.add_argument('--sha');a=p.parse_args()
 if a.worker:return worker(a)
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/image-distance-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==v for n,v in b['dependencies'].items());e=Experiment('I2','Distance-actual-argument-query-and-physical-range-contracts','rocm-runtime',sources=[__file__,ROOT/'tools/moat/image_distance_runtime_common.py',ROOT/'tools/moat/image_distance_worker.py',ROOT/'tools/moat/image_distance_inputs.py',ROOT/'migration/rewrite/image-distance-argument-contract.json',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command([sys.executable,__file__,'--worker','--output',str(out),'--library',str(ROOT/b['library']),'--sha',b['library_sha256']],'real-malformed-C-ABI-and-all-preserved-device-storage',timeout=300);r=dict(return_code=rc,build=b,experiment_id=e.id,outputs=str(out.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('OBSERVED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/image-distance-arguments.json',r);record('I2','EDT69项真实C ABI描述符/尺寸/query/物理小分配/重叠/alignment/恢复执行rc='+str(rc)+'；完整GPU字节和固定实际参数由独立CPU另验。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
