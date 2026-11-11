#!/usr/bin/env python3
import json,sys
from experiment import ROOT,Experiment,write,digest
from image_flood_build import dependencies
from snapshot import capture
from image_progress import record
def main():
 b=json.loads((ROOT/'migration/reports/image-flood-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I3','FloodFill-twenty-nine-complete-RGB-inputs','rocm-prototype',sources=[__file__,ROOT/'tools/moat/image_flood_worker.py',ROOT/'tools/moat/image_flood_inputs.py',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';rc=e.command([sys.executable,str(ROOT/'tools/moat/image_flood_worker.py'),'--library',str(ROOT/b['library']),'--sha',b['library_sha256'],'--output',str(out)],'all-full-RGB-results-masks-inclusive-metadata-and-padding',timeout=900);r=dict(return_code=rc,build=b,experiment_id=e.id,outputs=str(out.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/'migration/reports/image-flood-all.json',r);record('I3','29完整RGB flood输入/5实际模式/独立mask与元数据GPU执行rc='+str(rc)+'；独立CPU及完整文件/运行合同待验，不增支持数。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
