#!/usr/bin/env python3
import argparse,json,sys
from experiment import ROOT,Experiment,write,digest
from image_contour_build import dependencies
from snapshot import capture
from image_progress import record
def main():
 p=argparse.ArgumentParser();p.add_argument('--small',action='store_true');a=p.parse_args();b=json.loads((ROOT/'migration/reports/image-contour-build.json').read_text());assert b['status']=='BUILT' and digest(ROOT/b['library'])==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());e=Experiment('I2','Contour-GPU-complete-geometry-'+('small' if a.small else 'all'),'rocm-prototype',sources=[__file__,ROOT/'tools/moat/image_contour_worker.py',*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';cmd=[sys.executable,str(ROOT/'tools/moat/image_contour_worker.py'),'--library',str(ROOT/b['library']),'--sha',b['library_sha256'],'--output',str(out)]+(['--small'] if a.small else []);rc=e.command(cmd,'actual-GPU-label-boundary-loops-order-and-geometry-raster',timeout=600);r=dict(return_code=rc,small=a.small,outputs=str(out.relative_to(ROOT)),build=b,experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/('migration/reports/image-contour-'+('small' if a.small else 'all')+'.json'),r);record('I2','Contour GPU '+('small' if a.small else 'all')+'真实几何/排序/重建执行rc='+str(rc)+'；尚待独立CPU和完整原例验收，不增加支持数。',[r['evidence']]);print(rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
