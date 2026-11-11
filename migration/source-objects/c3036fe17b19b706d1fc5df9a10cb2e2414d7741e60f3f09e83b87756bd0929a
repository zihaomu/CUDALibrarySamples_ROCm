#!/usr/bin/env python3
import json,sys
from experiment import ROOT,Experiment,write,digest
from image_distance_build import dependencies
from snapshot import capture
from image_progress import record
def main():
 b=json.loads((ROOT/'migration/reports/image-distance-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I2','Distance-thirty-complete-inputs','rocm-prototype',sources=[__file__,ROOT/'tools/moat/image_distance_worker.py',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command([sys.executable,str(ROOT/'tools/moat/image_distance_worker.py'),'--library',str(ROOT/b['library']),'--sha',b['library_sha256'],'--output',str(out)],'all-pitched-distance-and-real-subpixel-voronoi-outputs',timeout=900);r=dict(return_code=rc,build=b,experiment_id=e.id,outputs=str(out.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/image-distance-all.json',r);record('I2','30组signed/unsigned原始完整输入实际HIP执行rc='+str(rc)+'；独立CPU全数组和原入口验收待完成，不计支持。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
