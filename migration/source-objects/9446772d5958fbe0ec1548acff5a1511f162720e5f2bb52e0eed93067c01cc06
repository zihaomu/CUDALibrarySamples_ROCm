#!/usr/bin/env python3
"""Fresh-build and replay the existing EDT and full NCC contracts without altering their reports."""
import argparse,json,shutil,sys
from pathlib import Path
from experiment import ROOT,Experiment,write,digest
from image_progress import record

EDT=['original','irregular','changed-values','boundary','repeat','singular-or-empty']
NCC={'original':[],'changed-values':['-g','1.1','-o','7','-noise','1','-n','2'],'changed-template':['-tw','64','-th','48','-n','1'],'no-timing':['-n','0'],'repeat':['-n','3'],'constant-template':['-g','0','-o','13','-noise','0','-n','0'],'constant-image':['-n','0'],'constant-both':['-g','0','-o','13','-noise','0','-n','0']}

def verify_legacy_fixture(directory,case):
 frozen=json.loads((ROOT/'migration/environments/batch15-fixtures.json').read_text())['records'];rows=[r for r in frozen if r['kind']=='distance' and r['case']==case]
 if int((directory/'count.txt').read_text())!=len(rows) or {p.name for p in directory.iterdir()}!={'count.txt',*[str(r['index']) for r in rows]}:raise ValueError('frozen legacy distance input count')
 for r in rows:
  p=directory/str(r['index'])
  if digest(p/'input.bin')!=r['input_sha256'] or list(map(int,(p/'params.txt').read_text().split()))!=r['params']:raise ValueError('frozen legacy original geometry/input/config')

def execute():
 from snapshot import capture
 legacy=next(r for r in json.loads((ROOT/'migration/reports/batches12_15-rocm.json').read_text()) if r['source']=='NPP/distanceTransform/distanceTransform.cpp');ncc=json.loads((ROOT/'migration/reports/rewrite-extension-builds.json').read_text())['ncc'];deps=dict(legacy['dependencies'],**ncc['dependencies']);deps[legacy['implementation']]=legacy['implementation_sha256'];deps['migration/environments/batch15-fixtures.json']=digest(ROOT/'migration/environments/batch15-fixtures.json');assert all(digest(ROOT/n)==sha for n,sha in deps.items());e=Experiment('I2','Distance-legacy-EDT-and-full-NCC-fresh-build','rocm-build',sources=[__file__,*[ROOT/n for n in deps]]);write(e.path/'backend.observed.json',capture());commands={'distance':json.loads((ROOT/legacy['evidence']/'commands.json').read_text())['build'],'ncc':json.loads((ROOT/ncc['evidence']/'commands.json').read_text())[0]['argv']};binaries={};rc=0
 for name,command in commands.items():
  argv=list(command);binary=e.path/(name+'-regression');argv[argv.index('-o')+1]=str(binary)
  if '-MF' in argv:argv[argv.index('-MF')+1]=str(e.path/(name+'.d'))
  rc=e.command(argv,'rebuild-unchanged-'+name,timeout=300)
  if rc:break
  binaries[name]=dict(binary=str(binary.relative_to(ROOT)),sha256=digest(binary))
 build=dict(status='BUILT' if not rc else 'BUILD_ERROR',binaries=binaries,dependencies=deps,experiment_id=e.id);write(e.path/'build.json',build);build['evidence']=e.finish('EXECUTED' if not rc else 'BUILD_ERROR');write(ROOT/'migration/reports/image-distance-regression-build.json',build);record('I2','既有NPP unsigned EDT与完整NCC原始合格实现新构建：'+build['status']+'；不改原资格/旧报告。',[build['evidence']])
 if rc:return rc
 rows=[]
 for name,cases in [('distance',{c:[] for c in EDT}),('ncc',NCC)]:
  for case,args in cases.items():
   e=Experiment('I2','Distance-regression-'+name,'rocm-regression',case=case,sources=[__file__,*[ROOT/n for n in deps]],parent=build['experiment_id']);write(e.path/'backend.observed.json',capture());out=e.path/'outputs';out.mkdir();cwd=e.path/'work';cwd.mkdir();environment={};actual_args=list(args);inputs=e.path/'inputs';inputs.mkdir()
   if name=='distance':
    fixture=ROOT/'build/batch15-fixtures/distance'/case;shutil.copytree(fixture,inputs/'fixture');source_files={str(p.relative_to(fixture)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in fixture.rglob('*') if p.is_file()};environment=dict(MIGRATION_CASE=case,MIGRATION_OUTPUT_DIR=str(out));working=ROOT;verify_legacy_fixture(inputs/'fixture',case)
   else:
    image=inputs/'image.raw'
    if case in ['constant-image','constant-both']:image.write_bytes(bytes([13])*(2048*1024))
    else:shutil.copyfile(ROOT/'NPP/templateMatching/images/CircuitBoard_2048x1024_8u.raw',image)
    source_files={'image.raw':dict(bytes=image.stat().st_size,sha256=digest(image))};environment=dict(REWRITE_OUTPUT=str(out));working=cwd
    if case=='original':(e.path/'images').mkdir();shutil.copyfile(image,e.path/'images/CircuitBoard_2048x1024_8u.raw')
    else:actual_args=['-i',str(image),*args]
   binary=binaries[name];assert digest(ROOT/binary['binary'])==binary['sha256'];expected_rc=1 if name=='ncc' and case.startswith('constant-') else 0;rc=e.command([str(ROOT/binary['binary']),*actual_args],'actual-unchanged-'+name+'-'+case,cwd=working,env=environment,timeout=600)
   if name=='ncc' and (cwd/'match_result.pgm').exists():shutil.copyfile(cwd/'match_result.pgm',out/'match_result.pgm')
   if name=='distance' and source_files!={str(p.relative_to(fixture)):dict(bytes=p.stat().st_size,sha256=digest(p)) for p in fixture.rglob('*') if p.is_file()}:raise RuntimeError('legacy fixture drift during regression')
   r=dict(kind=name,case=case,return_code=rc,expected_return_code=expected_rc,outputs=str(out.relative_to(ROOT)),input_files=source_files,build=build,experiment_id=e.id,stdout=e.commands[-1]['stdout'],stderr=e.commands[-1]['stderr']);write(e.path/'run.json',r);r['evidence']=e.finish(('EXPECTED_REJECTION' if expected_rc else 'EXECUTED') if rc==expected_rc else 'RUNTIME_ERROR');rows.append(r);write(ROOT/'migration/reports/image-distance-regression.json',rows);record('I2','旧'+name+'/'+case+'原规模/原循环实际GPU回归rc='+str(rc)+'，独立CPU另验。',[r['evidence']]);print(name,case,rc,flush=True)
   if rc!=expected_rc:return rc or 1
 return 0

def validate(rows):
 import numpy,scipy
 sys.path.insert(0,str(ROOT/'tools/migration'));from batch15_reference import validate as distance
 from ncc_reference import validate as ncc
 if len(rows)!=14 or {(r['kind'],r['case']) for r in rows}!={('distance',c) for c in EDT}|{('ncc',c) for c in NCC}:raise ValueError('all six existing EDT and eight complete NCC cases')
 results=[]
 for r in rows:
  meta=json.loads((ROOT/r['evidence']/'manifest.json').read_text());raw=ROOT/meta['raw_artifact_dir'];out=ROOT/r['outputs'];commands=json.loads((raw/'commands.json').read_text());binary=r['build']['binaries'][r['kind']]
  expected_rc=1 if r['kind']=='ncc' and r['case'].startswith('constant-') else 0
  if r['return_code']!=expected_rc or r['expected_return_code']!=expected_rc or len(commands)!=1 or commands[0]['return_code']!=expected_rc or commands[0]['argv'][0]!=str(ROOT/binary['binary']):raise ValueError('actual legacy regression process/binary/rejection')
  command=commands[0]
  if r['kind']=='distance':
   verify_legacy_fixture(raw/'inputs/fixture',r['case'])
   if command['argv']!=[str(ROOT/binary['binary'])] or command['cwd']!=str(ROOT) or command['environment_changes']['MIGRATION_CASE']!=r['case'] or command['environment_changes']['MIGRATION_OUTPUT_DIR']!=str(out):raise ValueError('legacy distance actual case/output binding')
   for entry in [x for x in json.loads((ROOT/'migration/environments/batch15-fixtures.json').read_text())['records'] if x['kind']=='distance' and x['case']==r['case']]:
    if digest(out/('i'+str(entry['index'])+'_input.bin'))!=entry['input_sha256'] or numpy.fromfile(out/('i'+str(entry['index'])+'_params.bin'),numpy.int32).tolist()!=entry['params']:raise ValueError('actual legacy emitted inputs are frozen')
  else:
   image=raw/'inputs/image.raw';argv=[str(ROOT/binary['binary'])]+([] if r['case']=='original' else ['-i',str(image),*NCC[r['case']]])
   if command['argv']!=argv or command['cwd']!=str(raw/'work') or command['environment_changes']['REWRITE_OUTPUT']!=str(out) or (out/'input.bin').read_bytes()!=image.read_bytes():raise ValueError('full NCC actual argv/input/output binding')
   expected_image=bytes([13])*(2048*1024) if r['case'] in ['constant-image','constant-both'] else (ROOT/'NPP/templateMatching/images/CircuitBoard_2048x1024_8u.raw').read_bytes()
   if image.read_bytes()!=expected_image:raise ValueError('full frozen NCC source image')
   if r['case']=='original' and (raw/'images/CircuitBoard_2048x1024_8u.raw').read_bytes()!=expected_image:raise ValueError('actual NCC default input')
   config=numpy.fromfile(out/'config.bin',numpy.int32);iterations=50 if r['case']=='original' else 2 if r['case']=='changed-values' else 1 if r['case']=='changed-template' else 3 if r['case']=='repeat' else 0
   if len(config)!=9 or int(config[6])!=iterations:raise ValueError('full NCC original timing iteration contract')
   if expected_rc:
    log=(raw/r['stdout']).read_text()
    if 'Located the template within 1 pixel: NO' not in log or '[PASS]' not in log:raise ValueError('expected ambiguous NCC rejection must retain numerical selfcheck')
  result=distance('NPP/distanceTransform/distanceTransform.cpp',r['case'],out) if r['kind']=='distance' else ncc(out,raw/r['stdout']);result.update(kind=r['kind'],case=r['case']);results.append(result);print(r['kind'],r['case'],result['status'],flush=True)
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 if not a.check:return execute()
 sources=[__file__,*[ROOT/'tools/moat'/n for n in ['ncc_reference.py']],*[ROOT/'tools/migration'/n for n in ['batch15_reference.py','validate_blas.py','batches12_15_spec.py','catalog.py']],ROOT/'migration/roadmap.json',ROOT/'migration/environments/batch15-fixtures.json'];e=Experiment('I2','Distance-legacy-six-EDT-eight-NCC-independent-CPU','CPU-reference',sources=sources)
 try:results=validate(json.loads((ROOT/'migration/reports/image-distance-regression.json').read_text()));v=dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',case_count=len(results),results=results)
 except Exception as error:v=dict(status='FAILED',results=[],error=repr(error))
 write(e.path/'results.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'NUMERIC_MISMATCH',dict(status=v['status'],checks=[dict(check='all-unchanged-existing-EDT-and-full-NCC-contracts',passed=v['status']=='PASSED')]));write(ROOT/'migration/reports/image-distance-regression-validation.json',v);record('I2','旧unsigned EDT6组及完整NCC8组/2048x1024/原50次计时、PGM、常量policy/完整scores独立CPU回归：'+v['status'],[v['evidence']]);print(v['status'],v.get('error'),[r for r in v['results'] if r['status']=='FAILED']);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
