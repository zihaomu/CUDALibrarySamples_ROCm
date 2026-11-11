#!/usr/bin/env python3
"""Run frozen C3 masks plus each actual C++/Python file and timing workflow."""
import argparse,json,os,sys
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from canny_color_build import dependencies
from image_progress import record

def main():
 p=argparse.ArgumentParser();p.add_argument('--originals',action='store_true');a=p.parse_args();spec=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());build=json.loads((ROOT/'migration/reports/canny-color-build.json').read_text());library=ROOT/build['library'];binary=ROOT/build['binary']
 if build['status']!='BUILT' or any(digest(ROOT/n)!=sha for n,sha in build['dependencies'].items()) or digest(library)!=build['library_sha256'] or digest(binary)!=build['binary_sha256']:raise RuntimeError('Stale C3 build')
 env=dict(os.environ,PYTHONPATH=str(ROOT/'build/image-gpu-site')+':'+str(ROOT/'rocm/python'),MIGRATION_IMAGE_COLOR_LIBRARY=str(library),LD_LIBRARY_PATH=str(ROOT/'build/image-opencv/lib')+':'+os.environ.get('LD_LIBRARY_PATH',''))
 jobs=[('masks','all',None)] if not a.originals else [(language,c['case'],c) for language in ['cpp','python'] for c in spec['cases'] if c['case'] in {'original-teapot','constant-zero','isoluminant-color-step','weak-step-with-strong-seed','independent-noise-983743'}]
 rows=[]
 for language,name,case in jobs:
  sid='NPP/nppCanny::npp_canny_simple.'+('cpp' if language=='cpp' else 'py') if language!='masks' else 'C3-Canny-both-public-APIs';e=Experiment('I1',sid,'rocm-original' if a.originals else 'rocm-run',case=name,sources=[__file__,ROOT/'tools/moat/canny_color_worker.py',*dependencies()],parent=build['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';audit=e.path/'audit';out.mkdir();audit.mkdir();current=dict(env,MIGRATION_IMAGE_AUDIT_DIR=str(audit))
  if not a.originals:
   out.rmdir();command=[sys.executable,str(ROOT/'tools/moat/canny_color_worker.py'),'--library',str(library),'--expected-sha',build['library_sha256'],'--output',str(out)]
  else:
   image=ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg' if name=='original-teapot' else ROOT/case['fixture']/'image.png'
   command=([str(binary)] if language=='cpp' else [sys.executable,str(ROOT/'rocm/ported/NPP/nppCanny/npp_canny_simple.py')])+[str(image)]
  rc=e.command(command,'actual-'+language+'-full-workflow',env=current,cwd=out if a.originals else ROOT,timeout=300);row=dict(case=name,language=language,return_code=rc,experiment_id=e.id,build=build,outputs=str(out.relative_to(ROOT)),audit=str(audit.relative_to(ROOT)))
  write(e.path/'run.json',row);row['evidence']=e.finish('EXECUTED' if not rc else 'RUNTIME_ERROR');rows.append(row);write(ROOT/('migration/reports/canny-color-originals.json' if a.originals else 'migration/reports/canny-color-rocm.json'),rows);record('I1','C3 '+language+'/'+name+'实际执行rc='+str(rc)+'；完整输出待独立验收。',[row['evidence']]);print(language,name,rc,flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':raise SystemExit(main())
