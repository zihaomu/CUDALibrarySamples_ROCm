#!/usr/bin/env python3
"""Rebuild the ten R9 entries in a clean checkout and replay bounded profiles."""
import json,os,subprocess,time
from experiment import ROOT,write,digest
from snapshot import capture
from helper_reference import validate as helper_cpu
from crc_benchmark_reference import validate as crc_cpu

def main():
 work=ROOT/'build/clean-r9';work.mkdir(parents=True,exist_ok=False);commands=[];cases=[]
 result=dict(status='RUNNING',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),initial_clean=not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),environment=capture(),commands=commands,cases=cases,scope='Clean rebuild of M1 and all ten R9 entries; nine original helper profiles and four bounded CRC benchmark profiles. The 16 GiB default/native CUDA proofs are separate, not reproduced by this clean replay.')
 def run(argv,name,cwd=ROOT,env=None):
  stdout=work/(name+'.stdout.log');stderr=work/(name+'.stderr.log');started=time.time()
  with stdout.open('w') as o,stderr.open('w') as e:r=subprocess.run(list(map(str,argv)),cwd=cwd,env=dict(os.environ,**(env or {})),stdout=o,stderr=e,timeout=480)
  commands.append(dict(argv=list(map(str,argv)),cwd=str(cwd),environment=env or {},return_code=r.returncode,seconds=time.time()-started,stdout=str(stdout.relative_to(ROOT)),stderr=str(stderr.relative_to(ROOT))))
  if r.returncode:raise RuntimeError(name+' returned '+str(r.returncode))
  return stdout
 try:
  if not result['initial_clean']:raise RuntimeError('initial checkout is dirty')
  env=result['environment'];lock=json.loads((ROOT/'migration/environments/project.lock.json').read_text())
  if env['image_id']!=lock['foundation_image_id'] or env['rocm_release']!=lock['rocm_release'] or not env['devices'] or any(d['physical_id']==3 for d in env['devices']):raise RuntimeError('environment lock/device guard')
  run(['python3','tools/migration/bootstrap_sdk.py'],'bootstrap')
  run(['cmake','-S','rocm','-B','build/r9-cmake','-DCMAKE_BUILD_TYPE=Release'],'configure')
  run(['cmake','--build','build/r9-cmake','-j4'],'build-M1')
  run(['cmake','--build','build/r9-cmake','--target','rewrite_matrix_helpers','rewrite_crc32_benchmark','-j2'],'build-R9')
  log=run(['ctest','--test-dir','build/r9-cmake','--output-on-failure','--parallel','1'],'CTest')
  if '100% tests passed, 0 tests failed out of 16' not in log.read_text():raise RuntimeError('CTest denominator')
  build=json.loads((ROOT/'migration/reports/rewrite-R9-helper-build.json').read_text())
  for index,p in enumerate(json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers']):
   src=ROOT/'tests/fixtures/rewrite-helpers'/p['language']/p['kind']/'original';binary=ROOT/next(b['binary'] for b in build['binaries'] if b['sample_id']==p['sample_id']);out=work/('helper-'+str(index));out.mkdir();run([binary],'helper-'+str(index),env=dict(REWRITE_INPUT=str(src),REWRITE_OUTPUT=str(out)));v=helper_cpu(src,out);write(work/('helper-'+str(index)+'-CPU.json'),v)
   if v['status']!='PASSED':raise RuntimeError('helper CPU '+p['sample_id'])
   cases.append(dict(sample_id=p['sample_id'],case='original',status=v['status'],binary_sha256=digest(binary),input_manifest_sha256=digest(src/'manifest.json')))
  build=json.loads((ROOT/'migration/reports/rewrite-R9-crc-benchmark-build.json').read_text())
  for c in json.loads((ROOT/'migration/rewrite/crc-benchmark-cases.json').read_text()):
   if not c['storage']:continue
   src=ROOT/'tests/fixtures/rewrite-crc-benchmark'/c['case'];out=work/c['case'];out.mkdir();run([ROOT/build['binary']]+c['argv'],c['case'],cwd=out,env=dict(REWRITE_OUTPUT=str(out),REWRITE_BENCH_INPUT=str(src/'input.bin')));v=crc_cpu(out,c);write(work/(c['case']+'-CPU.json'),v)
   if v['status']!='PASSED':raise RuntimeError('CRC CPU '+c['case'])
   cases.append(dict(sample_id='nvCOMP/benchmarks::benchmark_crc32.cpp',case=c['case'],status=v['status'],binary_sha256=build['binary_sha256'],input_manifest_sha256=digest(src/'manifest.json')))
  if len(cases)!=13:raise RuntimeError('replay denominator')
  result.update(status='PASSED',m1_tests=16,helper_original_profiles=9,bounded_crc_profiles=4,historical_binaries_reused=False)
 except Exception as e:result.update(status='FAILED',error=str(e))
 write(work/'result.json',result);print(result['status'],result.get('error',''));return int(result['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
