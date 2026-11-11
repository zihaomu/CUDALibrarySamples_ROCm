#!/usr/bin/env python3
"""Execute both real original contour workflows with default and selected ranges."""
import json,os,sys
import numpy as np
from experiment import ROOT,Experiment,write,digest
from image_contour_build import dependencies
from snapshot import capture
from image_progress import record
JOBS=[(family,case,'default') for family in ['NPP','NPP+'] for case in ['original','constant-0','annulus','diagonal-touch-two-loops','independent-noise-875231']]+[('NPP+','large-single-selected-ID-override','default'),('NPP+','large-multiple-ID-bypass','default'),('NPP+','large-multiple-ID-bypass','single-ID-override'),('NPP+','annulus','all-markers'),('NPP+','annulus','empty')]
def main():
 spec=json.loads((ROOT/'migration/rewrite/image-contour-profile.json').read_text());b=json.loads((ROOT/'migration/reports/image-contour-frontends-build.json').read_text());assert b['status']=='BUILT' and all(digest(ROOT/n)==v for n,v in b['dependencies'].items()) and all(digest(ROOT/r['binary'])==r['binary_sha256'] for r in b['binaries']);rows=[]
 for family,name,mode in JOBS:
  case=next(c for c in spec['cases'] if c['case']==(('npp' if family=='NPP' else 'plus')+'-original-CircuitBoard' if name=='original' else name));w,h=case['width'],case['height'];e=Experiment('I2',family+'/findContour::'+('findContour.cpp' if family=='NPP' else 'findContourNPPPlus.cpp'),'rocm-original',case=name+'/'+mode,sources=[__file__,ROOT/'rocm/common/image/contour_sample.hpp',*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());cwd=e.path/'work';cwd.mkdir();out=e.path/'outputs';out.mkdir();audit=e.path/'audit';audit.mkdir();inputs=e.path/'inputs';inputs.mkdir();blob=(ROOT/case['fixture']/'input.bin').read_bytes();dense=np.frombuffer(blob,np.uint8).reshape(h,case['pitch'])[:,:w].copy();inp=inputs/'input.raw';dense.tofile(inp);binary=next(r for r in b['binaries'] if r['family']==family);cmd=[str(ROOT/binary['binary'])]
  if name=='original':
   out=cwd/'images';out.mkdir();inp=out/'CircuitBoard_2048x1024_8u.raw';dense.tofile(inp);assert digest(inp)==case['original']['sha256']
  else:cmd+=['--input',str(inp),'--output-dir',str(out),'--width',str(w),'--height',str(h)]
  if mode=='single-ID-override':cmd+=['--start-id','1','--stop-id','2']
  elif mode=='all-markers':cmd+=['--start-id','0','--stop-id','3']
  elif mode=='empty':cmd+=['--start-id','2','--stop-id','2']
  rc=e.command(cmd,'actual-full-C++-file-and-geometry-workflow',cwd=cwd,env=dict(os.environ,MIGRATION_IMAGE_CONTOUR_AUDIT_DIR=str(audit)),timeout=300);r=dict(family=family,case=name,mode=mode,fixture_case=case['case'],return_code=rc,outputs=str(out.relative_to(ROOT)),audit=str(audit.relative_to(ROOT)),input=str(inp.relative_to(ROOT)),input_sha256=digest(inp),binary=binary,build=b,experiment_id=e.id,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');rows.append(r);write(ROOT/'migration/reports/image-contour-originals.json',rows);record('I2',family+'/'+name+'/'+mode+'真实C++文件/有序geometry诊断/重建rc='+str(rc)+'；全部文件及像素/几何/范围的独立CPU验收随后进行。',[r['evidence']]);print(family,name,mode,rc,flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':raise SystemExit(main())
