#!/usr/bin/env python3
"""Freeze full original EDT workflow identities before caller implementation."""
import json
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_progress import record

def main():
 profile=json.loads((ROOT/'migration/rewrite/image-distance-profile.json').read_text());originals=[c for c in profile['cases'] if c['original']];e=Experiment('I2','Distance-five-image-original-workflow-contracts','CPU-contract',sources=[__file__,ROOT/'migration/rewrite/image-distance-profile.json',*[ROOT/c['original']['source'] for c in originals]]);base=ROOT/'build/image-distance-original-fixtures';datasets={}
 for dataset in ['original','changed-full-size','constant-zero-level']:
  d=base/dataset;d.mkdir(parents=True,exist_ok=True);inputs=[]
  for c in originals:
   w,h=c['width'],c['height'];dtype=np.dtype(c['dtype']);name=c['case'];file=__import__('pathlib').Path(c['original']['source']).name
   if dataset=='original':data=(ROOT/c['original']['source']).read_bytes()
   else:
    y,x=np.indices((h,w))
    if dataset=='constant-zero-level':a=np.zeros((h,w),dtype) if not c['mode'] else np.full((h,w),.5 if c['remap_circle'] else c['cutoff'],dtype)
    elif not c['mode']:
     a=np.full((h,w),255,np.uint8);a[((x*7+y*11+17)%89)==0]=0
    elif c['remap_circle']:a=np.clip(.5+(x-w*.375+y*.125)/(2*w),0.,1.).astype(dtype)
    else:a=(c['cutoff']+(x-w*.4375+y*.0625)/w*.125).astype(dtype)
    data=np.asarray(a,dtype=dtype).tobytes()
   p=d/file;p.write_bytes(data);inputs.append(dict(case=name,filename=file,width=w,height=h,dtype=c['dtype'],mode=c['mode'],input_type=c['input_type'],cutoff=c['cutoff'],remap_circle=c['remap_circle'],output_prefix=c['output_prefix'],path=str(p.relative_to(ROOT)),bytes=len(data),sha256=digest(p)))
  datasets[dataset]=inputs
 workflows=[dict(case='default-original',dataset='original',default_paths=True),dict(case='explicit-original',dataset='original',default_paths=False),dict(case='changed-full-size',dataset='changed-full-size',default_paths=False),dict(case='constant-zero-level',dataset='constant-zero-level',default_paths=False)]
 v=dict(schema_version=1,status='FROZEN',datasets=datasets,workflows=workflows,required_output_count=12,default_paths='cwd/../images for both original inputs and outputs',stdout='Five named complete GPU workflows per successful process; all inputs preflighted before computation and all computations completed before file writes.',signed_lith_indices='SignedDistanceLithTransformVoronoiIndices_554x554_16s.raw',signed_lith_relative='SignedDistanceLithTransformVoronoiRelativeManhattan_554x554_16s.raw',audit='Optional independent audit per input: original dense bytes, complete typed outputs including selected GPU site IDs/coordinates, metadata. Outside product output directory.');write(ROOT/'migration/rewrite/image-distance-original-contract.json',v);write(e.path/'profile.json',v);r=dict(status='FROZEN',workflows=len(workflows),datasets=len(datasets),input_files=sum(len(v) for v in datasets.values()),output_files=12*len(workflows));write(e.path/'contracts.json',r);r['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-distance-original-contracts.json',r);record('I2','EDT真实原入口实现前固定4完整流程：默认/显式原图、独立完整规模变化、零level常量；每次五输入12输出，共48产品文件，实际GPU sites审计另目录。',[r['evidence']]);print(r['status'],r['workflows'],r['evidence']);return 0
if __name__=='__main__':raise SystemExit(main())
