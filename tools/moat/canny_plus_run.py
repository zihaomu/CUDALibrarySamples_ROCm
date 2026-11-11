#!/usr/bin/env python3
"""Run both frozen cases and the unchanged-size/iteration Python file workflow."""
import argparse,json,os,sys
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from canny_plus_build import dependencies
from image_progress import record

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');a=p.parse_args()
 spec=json.loads((ROOT/'migration/rewrite/canny-plus-profile.json').read_text());build=json.loads((ROOT/'migration/reports/canny-plus-build.json').read_text())
 if build['status']!='BUILT' or any(digest(ROOT/n)!=sha for n,sha in build['dependencies'].items()):raise RuntimeError('Build source closure stale')
 library=ROOT/build['library'];assert digest(library)==build['library_sha256']
 worker=ROOT/'tools/moat/canny_plus_worker.py';files=[__file__,ROOT/'tools/moat/canny_plus_build.py',*dependencies()]+([] if a.original else [worker])
 e=Experiment('I1',spec['sample_id'],'rocm-original' if a.original else 'rocm-run',sources=files,parent=build['experiment_id']);write(e.path/'backend.observed.json',capture())
 site=str(ROOT/'build/image-gpu-site');env=dict(os.environ,PYTHONPATH=site+os.pathsep+str(ROOT/'rocm/python'),MIGRATION_IMAGE_LIBRARY=str(library),MIGRATION_IMAGE_AUDIT_DIR=str(e.path/'audit'))
 if a.original:
  command=[sys.executable,str(ROOT/spec['implementation']),'--input',str(ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg'),'--output',str(e.path/'outputs')]
 else:command=[sys.executable,str(worker),'--profile',str(ROOT/'migration/rewrite/canny-plus-profile.json'),'--library',str(library),'--expected-sha',build['library_sha256'],'--output',str(e.path/'outputs')]
 rc=e.command(command,'actual-full-original-Python-profile' if a.original else 'actual-frozen-case-Torch-and-C-ABI',timeout=1800,env=env)
 result=dict(status='EXECUTED' if not rc else 'FAILED',return_code=rc,experiment_id=e.id,build=build,outputs=str((e.path/'outputs').relative_to(ROOT)),audit=str((e.path/'audit').relative_to(ROOT)))
 write(e.path/'run.json',result);result['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');write(ROOT/('migration/reports/canny-plus-original.json' if a.original else 'migration/reports/canny-plus-rocm.json'),result)
 record('I1','NPP+ '+('8尺寸/1000循环原始文件流程' if a.original else '31组Torch/C ABI完整mask')+' GPU执行：'+result['status']+'；下一步独立CPU/原生对照。',[result['evidence']]);print(rc,result['evidence']);return rc
if __name__=='__main__':raise SystemExit(main())
