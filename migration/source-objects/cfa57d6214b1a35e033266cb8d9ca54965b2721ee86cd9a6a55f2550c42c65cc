#!/usr/bin/env python3
"""Actual default-file, file-error and no-device branches of both C3 programs."""
import argparse,json,os,shutil,sys
from experiment import ROOT,Experiment,write,digest
from image_progress import record
FAULTS=['default-image','missing-image','invalid-image','unwritable-output','no-GPU']

def validate(rows):
 import cv2,numpy as np
 from image_validation import coverage,file_set,array_check
 from canny_color_reference import model
 profile=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());case=next(c for c in profile['cases'] if c['case']=='original-teapot');fixture=ROOT/case['fixture'];c=json.loads((fixture/'config.json').read_text());h,w=c['height'],c['width'];source=np.fromfile(fixture/'input.bin',np.uint8).reshape(h,c['pitch'])[:,:3*w].reshape(h,w,3);mask,_=model(fixture);gray=cv2.Canny(cv2.cvtColor(source,cv2.COLOR_BGR2GRAY),50,100,L2gradient=True);channels=cv2.split(source);merged=cv2.bitwise_or(cv2.Canny(channels[0],50,100,L2gradient=True),cv2.bitwise_or(cv2.Canny(channels[1],50,100,L2gradient=True),cv2.Canny(channels[2],50,100,L2gradient=True)));checks=[coverage([dict(case=r['language']+'/'+r['case']) for r in rows],[dict(case=l+'/'+f) for l in ['cpp','python'] for f in FAULTS])]
 for r in rows:
  name=r['language']+'/'+r['case'];d=ROOT/r['evidence'];commands=json.loads((d/'commands.json').read_text());stderr=(d/commands[0]['stderr']).read_text();work=ROOT/r['work'];audit=ROOT/r['audit']
  if r['case']=='default-image':
   checks.append(dict(check=name+'/actual-success',passed=r['return_code']==0));checks.append(file_set(work,['image.jpg','edges_npp.png','edges_opencv_gray.png','edges_opencv_3ch.png']))
   for n,a in [('edges_npp.png',mask),('edges_opencv_gray.png',gray),('edges_opencv_3ch.png',merged)]:
    actual=cv2.imread(str(work/n),cv2.IMREAD_UNCHANGED);checks.append(dict(check=name+'/'+n,passed=actual is not None and actual.shape==a.shape and actual.dtype==np.uint8 and np.array_equal(actual,a)))
   checks+= [array_check(audit/'input.bin',np.ascontiguousarray(source),digest(audit/'input.bin')),array_check(audit/'mask.bin',mask,digest(audit/'mask.bin'))];info=json.loads((audit/'workflow.json').read_text());checks.append(dict(check=name+'/complete-default-workflow',passed=info['width']==w and info['height']==h and info['warmup']==1 and info['iterations']==info['gray_iterations']==info['color_iterations']==10 and len(info['timings_ms'])==10))
  else:
   text=stderr.lower();specific=('could not read' in text) if r['case'] in {'missing-image','invalid-image'} else ('image output failed' in text and 'edges_npp.png' in text) if r['case']=='unwritable-output' else ('no hip device' in text or 'no rocm-capable device' in text);checks.append(dict(check=name+'/actual-expected-exit-and-specific-error',passed=r['return_code']==1 and specific))
 return dict(status='PASSED' if checks and all(c['passed'] is True for c in checks) else 'FAILED',checks=checks,case_count=len(rows))

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 if a.check:
  rows=json.loads((ROOT/'migration/reports/canny-color-cli.json').read_text());e=Experiment('I1','C3-Canny-CLI-independent-check','CPU-reference',sources=[__file__,ROOT/'tools/moat/canny_color_reference.py',ROOT/'tools/moat/image_canny_stages_reference.py',ROOT/'tools/moat/image_validation.py'])
  try:v=validate(rows)
  except Exception as error:v=dict(status='FAILED',checks=[dict(check='complete-CLI-data',passed=False,error=repr(error))])
  write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',v);write(ROOT/'migration/reports/canny-color-cli-validation.json',v);record('I1','两语言10项默认文件/错误文件/输出失败/无GPU分支独立检查：'+v['status']+'。',[v['evidence']]);print(v['status'],[c for c in v['checks'] if not c['passed']]);return int(v['status']!='PASSED')
 from canny_color_build import dependencies
 from snapshot import capture
 b=json.loads((ROOT/'migration/reports/canny-color-build.json').read_text());rows=[]
 if any(digest(ROOT/n)!=sha for n,sha in b['dependencies'].items()) or digest(ROOT/b['library'])!=b['library_sha256'] or digest(ROOT/b['binary'])!=b['binary_sha256']:raise RuntimeError('Stale C3 CLI build')
 for language in ['cpp','python']:
  for fault in FAULTS:
   e=Experiment('I1','NPP/nppCanny::npp_canny_simple.'+('cpp' if language=='cpp' else 'py'),'rocm-CLI',case=fault,sources=[__file__,*dependencies()],parent=b['experiment_id']);write(e.path/'backend.observed.json',capture());work=e.path/'work';audit=e.path/'audit';work.mkdir();audit.mkdir()
   if fault not in {'missing-image','invalid-image'}:shutil.copyfile(ROOT/'NPP+/cannyEdgeDetectorPython/Teapot.jpg',work/'image.jpg')
   if fault=='invalid-image':(work/'image.jpg').write_text('invalid image bytes')
   if fault=='unwritable-output':(work/'edges_npp.png').mkdir()
   env=dict(os.environ,PYTHONPATH=str(ROOT/'build/image-gpu-site')+':'+str(ROOT/'rocm/python'),MIGRATION_IMAGE_COLOR_LIBRARY=str(ROOT/b['library']),MIGRATION_IMAGE_AUDIT_DIR=str(audit),LD_LIBRARY_PATH=str(ROOT/'build/image-opencv/lib')+':'+os.environ.get('LD_LIBRARY_PATH',''))
   if fault=='no-GPU':env['HIP_VISIBLE_DEVICES']=''
   cmd=[str(ROOT/b['binary'])] if language=='cpp' else [sys.executable,str(ROOT/'rocm/ported/NPP/nppCanny/npp_canny_simple.py')];rc=e.command(cmd,'actual-'+language+'-'+fault,env=env,cwd=work,timeout=180);r=dict(case=fault,language=language,return_code=rc,build=b,experiment_id=e.id,work=str(work.relative_to(ROOT)),audit=str(audit.relative_to(ROOT)));write(e.path/'run.json',r);r['evidence']=e.finish('EXECUTED' if fault=='default-image' and rc==0 else 'RUNTIME_ERROR' if fault=='default-image' else 'OBSERVED');rows.append(r);write(ROOT/'migration/reports/canny-color-cli.json',rows);record('I1','C3 CLI '+language+'/'+fault+'实际rc='+str(rc)+'；具体诊断与默认输出由独立CPU验收。',[r['evidence']]);print(language,fault,rc,flush=True)
 return 0
if __name__=='__main__':raise SystemExit(main())
