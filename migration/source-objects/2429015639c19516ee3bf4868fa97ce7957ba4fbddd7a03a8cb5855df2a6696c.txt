#!/usr/bin/env python3
"""Freeze complete original RGB product/CLI workflows before their first execution."""
import json
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_flood_inputs import load_case
from image_progress import record
def main():
 profile=json.loads((ROOT/'migration/rewrite/image-flood-profile.json').read_text());originals=[c for c in profile['cases'] if c['original']];e=Experiment('I3','FloodFill-five-mode-original-file-workflow-contracts','CPU-contract',sources=[__file__,ROOT/'tools/moat/image_flood_inputs.py',ROOT/'migration/rewrite/image-flood-profile.json']);base=ROOT/'build/image-flood-original-fixtures';datasets={}
 for name in ['original','changed-full-size','constant-full-size']:
  d=base/name;d.mkdir(parents=True,exist_ok=True);inputs={}
  for c in originals:
   w,h=c['width'],c['height'];payload=load_case(c);a=np.frombuffer(payload,np.uint8).reshape(h,c['pitch'])[:,:w*3].copy().reshape(h,w,3)
   if name=='changed-full-size':a=((a.astype(np.uint16)+17)%256).astype(np.uint8)
   elif name=='constant-full-size':a[:]=[37,71,113] if c['mode']<3 else [101,151,201]
   file=__import__('pathlib').Path(c['original']['source']).name;p=d/file;data=a.tobytes()
   if file in inputs and p.read_bytes()!=data:raise ValueError('one original image per dataset reused consistently')
   p.write_bytes(data);inputs[file]=dict(filename=file,width=w,height=h,bytes=len(data),sha256=digest(p),path=str(p.relative_to(ROOT)))
  datasets[name]=list(inputs.values())
 workflows=[dict(case='default-original',dataset='original',default_paths=True),dict(case='explicit-original',dataset='original',default_paths=False),dict(case='changed-full-size',dataset='changed-full-size',default_paths=False),dict(case='constant-full-size',dataset='constant-full-size',default_paths=False)]
 v=dict(schema_version=1,status='FROZEN',sample_id=profile['sample_id'],datasets=datasets,workflows=workflows,originals=[{k:c[k] for k in ['case','width','height','mode','seed','lower','upper','fill','boundary','product','original']} for c in originals],default_paths='cwd/../images for both inputs and five RGB products',required_output_count=5,stdout='Exactly five BoundsRect lines, inclusive right/bottom bbox, count and original RGB seed.',audit='Separate per-mode input/output/mask/region typed buffers and workflow metadata; no audit data in product directory.',errors='All two full input files and five target paths preflighted, all five computations completed before products are written. CLI diagnostics and exact return codes tested separately.');write(ROOT/'migration/rewrite/image-flood-original-contract.json',v);write(e.path/'profile.json',v);r=dict(status='FROZEN',workflows=4,datasets=3,input_files=6,output_files=20);write(e.path/'contracts.json',r);r['evidence']=e.finish('OBSERVED');write(ROOT/'migration/reports/image-flood-original-contracts.json',r);record('I3','完整flood入口首次执行前固定默认/显式原图、变化完整规模、常量完整规模4流程，共20RGB文件；每流程5mask/count/bbox/seed审计与实际命令/默认路径完整绑定。',[r['evidence']]);print(r['status'],r['evidence']);return 0
if __name__=='__main__':raise SystemExit(main())
