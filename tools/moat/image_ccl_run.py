#!/usr/bin/env python3
import argparse,json,sys
from experiment import ROOT,Experiment,write,digest
from image_ccl_build import dependencies
from image_progress import record
from snapshot import capture
def main():
 p=argparse.ArgumentParser();p.add_argument('--runtime',action='store_true');p.add_argument('--trace',action='store_true');a=p.parse_args();b=json.loads((ROOT/'migration/reports/image-ccl-build.json').read_text());lib=ROOT/b['library'];assert b['status']=='BUILT' and digest(lib)==b['library_sha256'] and all(digest(ROOT/n)==sha for n,sha in b['dependencies'].items());worker=ROOT/'tools/moat/image_ccl_worker.py';kind='runtime' if a.runtime else 'trace' if a.trace else 'masks';e=Experiment('I2','CCL-'+kind,'rocm-'+kind,sources=[__file__,worker,*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';cmd=[sys.executable,str(worker),'--library',str(lib),'--expected-sha',b['library_sha256'],'--output',str(out)]+(['--runtime'] if a.runtime else [])
 if a.trace:cmd=['rocprofv3','--kernel-trace','--output-format','csv','--output-directory',str(e.path/'trace'),'--',*cmd]
 rc=e.command(cmd,'actual-CCL-'+kind,timeout=300);r=dict(status='EXECUTED' if not rc else 'FAILED',return_code=rc,outputs=str(out.relative_to(ROOT)),build=b,experiment_id=e.id);write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/('migration/reports/image-ccl-'+kind+'.json'),r);record('I2','CCL '+kind+'实际GPU执行rc='+str(rc)+'；独立CPU像素/ABI/trace验收另行执行。',[r['evidence']]);print(kind,rc,r['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
