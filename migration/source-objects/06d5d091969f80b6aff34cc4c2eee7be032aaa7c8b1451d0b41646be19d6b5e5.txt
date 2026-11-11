#!/usr/bin/env python3
"""Execute the fixed complete five-image workflows with original names and paths."""
import json,os,shutil
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record

def main():
 spec=json.loads((ROOT/'migration/rewrite/image-distance-original-contract.json').read_text());b=json.loads((ROOT/'migration/reports/image-distance-frontend-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['binary'])==b['binary_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());rows=[]
 for rule in spec['workflows']:
  inputs=spec['datasets'][rule['dataset']];e=Experiment('I2','NPP+/distanceTransform::unsignedAndSignedDistanceTransformNPPPlus.cpp','rocm-original',case=rule['case'],sources=[__file__,ROOT/'migration/rewrite/image-distance-original-contract.json',*[ROOT/n for n in b['dependencies']],*[ROOT/r['path'] for r in inputs]],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());cwd=e.path/'work';cwd.mkdir();inp=e.path/('images' if rule['default_paths'] else 'inputs');inp.mkdir();out=inp if rule['default_paths'] else e.path/'outputs';out.mkdir(exist_ok=True);audit=e.path/'audit';audit.mkdir()
  for r in inputs:
   source=ROOT/r['path'];assert source.stat().st_size==r['bytes'] and digest(source)==r['sha256'];shutil.copyfile(source,inp/r['filename'])
  command=[str(ROOT/b['binary'])]+([] if rule['default_paths'] else ['--input-dir',str(inp),'--output-dir',str(out)]);rc=e.command(command,'actual-complete-five-image-and-twelve-output-workflow',cwd=cwd,env=dict(os.environ,MIGRATION_IMAGE_DISTANCE_AUDIT_DIR=str(audit)),timeout=900);r=dict(case=rule['case'],dataset=rule['dataset'],default_paths=rule['default_paths'],return_code=rc,inputs=str(inp.relative_to(ROOT)),outputs=str(out.relative_to(ROOT)),audit=str(audit.relative_to(ROOT)),build=b,experiment_id=e.id,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');rows.append(r);write(ROOT/'migration/reports/image-distance-originals.json',rows);record('I2','Signed/unsigned EDT真实C++/'+rule['case']+'五图12文件实际执行rc='+str(rc)+'；全部像素/sites/原始命名和stdout由独立CPU另验。',[r['evidence']]);print(rule['case'],rc,flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':raise SystemExit(main())
