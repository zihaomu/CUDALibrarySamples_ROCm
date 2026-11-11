#!/usr/bin/env python3
"""Execute all four complete original C++ flood workflows and retain every file."""
import json,shutil
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from image_progress import record
def main():
 b=json.loads((ROOT/'migration/reports/image-flood-frontend-build.json').read_text());spec=json.loads((ROOT/'migration/rewrite/image-flood-original-contract.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['binary'])==b['binary_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());rows=[]
 for rule in spec['workflows']:
  e=Experiment('I3',spec['sample_id'],'rocm-original',case=rule['case'],sources=[__file__,ROOT/'migration/rewrite/image-flood-original-contract.json',*[ROOT/n for n in b['dependencies']]],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());cwd=e.path/'work';cwd.mkdir();inp=e.path/('images' if rule['default_paths'] else 'inputs');inp.mkdir();out=inp if rule['default_paths'] else e.path/'outputs';out.mkdir(exist_ok=True);audit=e.path/'audit';audit.mkdir()
  for c in spec['datasets'][rule['dataset']]:
   p=ROOT/c['path'];assert p.stat().st_size==c['bytes'] and digest(p)==c['sha256'];shutil.copyfile(p,inp/c['filename'])
  argv=[str(ROOT/b['binary'])]+([] if rule['default_paths'] else ['--input-dir',str(inp),'--output-dir',str(out)]);rc=e.command(argv,'actual-five-mode-two-image-five-RGB-product-workflow',cwd=cwd,env=dict(MIGRATION_IMAGE_FLOOD_AUDIT_DIR=str(audit)),timeout=600);r=dict(case=rule['case'],dataset=rule['dataset'],default_paths=rule['default_paths'],return_code=rc,inputs=str(inp.relative_to(ROOT)),outputs=str(out.relative_to(ROOT)),audit=str(audit.relative_to(ROOT)),build=b,experiment_id=e.id,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');rows.append(r);write(ROOT/'migration/reports/image-flood-originals.json',rows);record('I3','flood完整C++/'+rule['case']+'五分支、2输入5RGB/5mask与元数据审计rc='+str(rc)+'；独立CPU另验。',[r['evidence']]);print(rule['case'],rc,flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':raise SystemExit(main())
