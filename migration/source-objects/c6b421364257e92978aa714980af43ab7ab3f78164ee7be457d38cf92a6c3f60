#!/usr/bin/env python3
"""Mutation checks against the real acceptance functions, retaining every payload."""
import copy,csv,json,shutil
import numpy as np
from experiment import ROOT,Experiment,write,digest
from canny_plus_validate import validate
from canny_plus_runtime_validate import validate as runtime_validate
from image_progress import record

def main():
 sources=[__file__,ROOT/'tools/moat/canny_plus_validate.py',ROOT/'tools/moat/canny_plus_runtime_validate.py',ROOT/'tools/moat/image_validation.py',ROOT/'tools/moat/canny_plus_runtime.py',ROOT/'tools/moat/image_canny_stages_reference.py',ROOT/'tools/moat/image_canny_local_research.py',ROOT/'migration/rewrite/canny-plus-profile.json']
 e=Experiment('I1','CannyPlus-acceptance-mutations','CPU-validator-test',sources=sources);checks=[]
 spec=json.loads((ROOT/'migration/rewrite/canny-plus-profile.json').read_text());case=next(c for c in spec['cases'] if c['case']=='new-odd-noise');mini=dict(spec,cases=[case]);run=json.loads((ROOT/'migration/reports/canny-plus-rocm.json').read_text());native=json.loads((ROOT/'migration/reports/canny-plus-native.json').read_text());native=[next(r for r in native if r['case']==case['case'])]
 parent_rows=json.loads((ROOT/run['outputs']/'results.json').read_text());parent_row=next(r for r in parent_rows if r['case']==case['case'])
 faults=['good-exact','missing-case','duplicate-case','nonzero-process','extra-output','missing-output','trailing-byte-with-updated-hash','wrong-hash','wrong-pixel-with-updated-hash','padding-with-updated-hash','wrong-library','wrong-input','native-nonzero','native-input','native-trailing-byte','native-within-budget','native-outside-budget']
 for fault in faults:
  root=e.path/fault;root.mkdir();out=root/'outputs';out.mkdir();shutil.copytree(ROOT/run['outputs']/case['case'],out/case['case']);r=copy.deepcopy(run);r['outputs']=str(out.relative_to(ROOT));rows=[copy.deepcopy(parent_row)];nr=copy.deepcopy(native)
  if fault.startswith('native-'):
   dest=root/'native';shutil.copytree(ROOT/nr[0]['outputs'],dest);nr[0]['outputs']=str(dest.relative_to(ROOT))
  p=out/case['case']/'python.bin'
  if fault=='missing-case':rows=[]
  elif fault=='duplicate-case':rows.append(copy.deepcopy(rows[0]))
  elif fault=='nonzero-process':r['return_code']=9
  elif fault=='extra-output':(out/case['case']/'extra.txt').write_text('unexpected')
  elif fault=='missing-output':p.unlink()
  elif fault=='trailing-byte-with-updated-hash':p.write_bytes(p.read_bytes()+b'\0');rows[0]['outputs']['python.bin']['sha256']=digest(p)
  elif fault=='wrong-hash':rows[0]['outputs']['python.bin']['sha256']='0'*64
  elif fault=='wrong-pixel-with-updated-hash':
   a=bytearray(p.read_bytes());a[137]^=255;p.write_bytes(a);rows[0]['outputs']['python.bin']['sha256']=digest(p)
  elif fault=='padding-with-updated-hash':
   p=out/case['case']/'pitched.bin';a=bytearray(p.read_bytes());a[131]^=1;p.write_bytes(a);rows[0]['outputs']['pitched.bin']['sha256']=digest(p)
  elif fault=='wrong-library':rows[0]['library_sha256']='0'*64
  elif fault=='wrong-input':rows[0]['input_manifest_sha256']='0'*64
  elif fault=='native-nonzero':nr[0]['return_code']=1
  elif fault=='native-input':nr[0]['input_manifest_sha256']='0'*64
  elif fault=='native-trailing-byte':
   p=ROOT/nr[0]['outputs']/'output.bin';p.write_bytes(p.read_bytes()+b'\0');nr[0]['output_sha256']['output.bin']=digest(p)
  elif fault in {'native-within-budget','native-outside-budget'}:
   p=ROOT/nr[0]['outputs']/'output.bin';a=np.fromfile(p,np.uint8).reshape(97,136)
   if fault=='native-within-budget':a[15,30]^=255
   else:a[:,:131]=0
   a.tofile(p);nr[0]['output_sha256']['output.bin']=digest(p)
  write(out/'results.json',rows);v=validate(r,mini,nr);write(root/'validation.json',v)
  expected=fault in {'good-exact','native-within-budget'};checks.append(dict(check=fault,passed=(v['status']=='PASSED')==expected,expected_accept=expected,rejected=[c['check'] for c in v['checks'] if not c['passed']]))
 for fault in ['runtime-missing-case','runtime-wrong-status','empty-trace']:
  trace=fault=='empty-trace';r=json.loads((ROOT/('migration/reports/canny-plus-'+('trace' if trace else 'runtime')+'.json')).read_text());dest=e.path/fault;shutil.copytree(ROOT/r['outputs'],dest/'outputs');r['outputs']=str((dest/'outputs').relative_to(ROOT));rows=json.loads((dest/'outputs/results.json').read_text())
  if fault=='runtime-missing-case':rows.pop()
  elif fault=='runtime-wrong-status':rows[0]['passed']=False
  else:(dest/'trace').mkdir();r['trace']=str((dest/'trace').relative_to(ROOT))
  write(dest/'outputs/results.json',rows)
  try:v=runtime_validate(r,trace)
  except Exception as error:v=dict(status='FAILED',error=repr(error))
  write(dest/'validation.json',v);checks.append(dict(check=fault,passed=v['status']=='FAILED'))
 # Exercise the original file/loop validator with all eight original sizes.
 r=json.loads((ROOT/'migration/reports/canny-plus-original.json').read_text());dest=e.path/'original-mutations';shutil.copytree(ROOT/r['outputs'],dest/'outputs');shutil.copytree(ROOT/r['audit'],dest/'audit');r['outputs']=str((dest/'outputs').relative_to(ROOT));r['audit']=str((dest/'audit').relative_to(ROOT));bench=json.loads((dest/'audit/benchmark.json').read_text());bench['resolutions'][0]['iterations']=999;write(dest/'audit/benchmark.json',bench)
 csvpath=dest/'outputs/performance_results.csv';csvrows=list(csv.DictReader(csvpath.open()));csvrows[0]['HIP Time (ms)']='9999'
 with csvpath.open('w') as f:
  writer=csv.DictWriter(f,fieldnames=list(csvrows[0]));writer.writeheader();writer.writerows(csvrows)
 (dest/'outputs/out_npp_640x360.png').unlink();v=validate(r,spec,json.loads((ROOT/'migration/reports/canny-plus-native.json').read_text()),True);write(dest/'validation.json',v)
 for name in ['original-eight-sizes-5-warmup-1000-measurements','CSV-actual-measurement-mean-and-size','exact-output-file-set','PNG-full-CPU-pixels']:
  checks.append(dict(check='original/'+name,passed=v['status']=='FAILED' and any(c['check'].endswith(name) and not c['passed'] for c in v['checks'])))
 v=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks,case_count=len(checks));write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',v);write(ROOT/'migration/reports/canny-plus-checks.json',v)
 record('I1',f'Canny验收器{len(checks)}项正向/反向检查：'+v['status']+'；包括容差内native差异、超限、尾字节、padding、丢例、失败rc、错误CSV/循环和空trace。',[v['evidence']]);print(v['status'],[c for c in checks if not c['passed']]);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
