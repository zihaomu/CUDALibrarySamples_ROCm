#!/usr/bin/env python3
"""Mutation tests for complete masks, workflow files and actual runtime payloads."""
import copy,json,shutil
import cv2,numpy as np
from experiment import ROOT,Experiment,write,digest
from canny_color_reference import validate_masks,validate_originals
from canny_color_runtime_validate import validate as runtime_validate
from canny_color_cpp_reference import validate as cpp_validate
from image_progress import record

MASK_FAULTS=['good-exact','missing-case','duplicate-case','nonzero-process','missing-output','extra-output','trailing-byte-updated-ledger','wrong-pixel-updated-ledger','padding-updated-ledger','wrong-hash','wrong-library','wrong-input','wrong-declared-bytes','native-nonzero','native-wrong-input','native-trailing-byte','native-nonbinary','native-padding','native-variant-accepted']
RUNTIME_FAULTS=['runtime-missing-case','runtime-missing-payload','runtime-ABI-status','runtime-query-size','runtime-exception-type','runtime-storage','runtime-wrong-input','empty-trace']
CPP_FAULTS=['cpp-missing-case','cpp-diagnostic','cpp-output-value','cpp-trailing-byte']
ORIGINAL_FAULTS=['original-missing-entry','original-duplicate-entry','original-nonzero','original-short-loops','original-missing-PNG','original-wrong-PNG','original-wrong-input']

def main():
 plan=ROOT/'migration/rewrite/canny-color-negative-cases.json';names=MASK_FAULTS+['native-empty-original']+RUNTIME_FAULTS+CPP_FAULTS+ORIGINAL_FAULTS
 if not plan.exists():write(plan,names)
 if json.loads(plan.read_text())!=names:raise RuntimeError('Negative case contract changed')
 files=[__file__,plan]+[ROOT/'tools/moat'/n for n in ['canny_color_reference.py','canny_color_runtime.py','canny_color_runtime_validate.py','canny_color_cpp_reference.py','image_canny_stages_reference.py','image_validation.py']];e=Experiment('I1','C3-Canny-validator-mutations','CPU-validator-test',sources=files);checks=[];spec=json.loads((ROOT/'migration/rewrite/canny-color-profile.json').read_text());case=next(c for c in spec['cases'] if c['case']=='independent-noise-983743');run=json.loads((ROOT/'migration/reports/canny-color-rocm.json').read_text())[0];allrows=json.loads((ROOT/run['outputs']/'results.json').read_text());natives=json.loads((ROOT/'migration/reports/canny-color-native.json').read_text())
 def ledger(path):return dict(sha256=digest(path),bytes=path.stat().st_size)
 def outcome(name,v,accept=False):
  write(e.path/name/'validation.json',v);checks.append(dict(check=name,passed=(v['status']=='PASSED')==accept,expected_accept=accept,rejections=[c['check'] for c in v.get('checks',[]) if not c['passed']]))
 for fault in MASK_FAULTS+['native-empty-original']:
  selected=next(c for c in spec['cases'] if c['case']=='original-teapot') if fault=='native-empty-original' else case;name=selected['case'];mini=dict(spec,cases=[selected]);root=e.path/fault;out=root/'outputs';out.mkdir(parents=True);shutil.copytree(ROOT/run['outputs']/name,out/name);r=copy.deepcopy(run);r['outputs']=str(out.relative_to(ROOT));rows=[copy.deepcopy(next(row for row in allrows if row['case']==name))];native=[copy.deepcopy(next(row for row in natives if row['case']==name))];file=out/name/'tensor.bin'
  if fault.startswith('native-'):
   dest=root/'native';shutil.copytree(ROOT/native[0]['outputs'],dest);native[0]['outputs']=str(dest.relative_to(ROOT))
  if fault=='missing-case':rows=[]
  elif fault=='duplicate-case':rows.append(copy.deepcopy(rows[0]))
  elif fault=='nonzero-process':r['return_code']=1
  elif fault=='missing-output':file.unlink()
  elif fault=='extra-output':(out/name/'extra.txt').write_text('unexpected')
  elif fault=='trailing-byte-updated-ledger':file.write_bytes(file.read_bytes()+b'\0');rows[0]['files']['tensor.bin']=ledger(file)
  elif fault=='wrong-pixel-updated-ledger':
   a=bytearray(file.read_bytes());a[137]^=255;file.write_bytes(a);rows[0]['files']['tensor.bin']=ledger(file)
  elif fault=='padding-updated-ledger':
   file=out/name/'pitched.bin';a=bytearray(file.read_bytes());a[131]^=1;file.write_bytes(a);rows[0]['files']['pitched.bin']=ledger(file)
  elif fault=='wrong-hash':rows[0]['files']['tensor.bin']['sha256']='0'*64
  elif fault=='wrong-library':rows[0]['library_sha256']='0'*64
  elif fault=='wrong-input':rows[0]['input_manifest_sha256']='0'*64
  elif fault=='wrong-declared-bytes':rows[0]['files']['tensor.bin']['bytes']+=1
  elif fault=='native-nonzero':native[0]['return_code']=1
  elif fault=='native-wrong-input':native[0]['input_manifest_sha256']='0'*64
  elif fault=='native-trailing-byte':
   file=ROOT/native[0]['outputs']/'output.bin';file.write_bytes(file.read_bytes()+b'\0');native[0]['files']['output.bin']=ledger(file)
  elif fault in {'native-nonbinary','native-padding','native-variant-accepted','native-empty-original'}:
   file=ROOT/native[0]['outputs']/'output.bin';a=np.fromfile(file,np.uint8).reshape(600,805) if fault=='native-empty-original' else np.fromfile(file,np.uint8).reshape(97,136)
   if fault=='native-nonbinary':a[13,31]=7
   elif fault=='native-padding':a[13,131]=172
   elif fault=='native-variant-accepted':a[13,31]^=255
   else:a[:,:800]=0
   a.tofile(file);native[0]['files']['output.bin']=ledger(file)
  write(out/'results.json',rows);outcome(fault,validate_masks(r,mini,native),fault in {'good-exact','native-variant-accepted'})
 for fault in RUNTIME_FAULTS:
  trace=fault=='empty-trace';r=json.loads((ROOT/('migration/reports/canny-color-'+('trace' if trace else 'runtime')+'.json')).read_text());dest=e.path/fault;shutil.copytree(ROOT/r['outputs'],dest/'outputs');r['outputs']=str((dest/'outputs').relative_to(ROOT));rows=json.loads((dest/'outputs/results.json').read_text())
  if fault=='runtime-missing-case':rows.pop()
  elif fault=='runtime-missing-payload':next(r for r in rows if r['case']=='stream-a').pop('files')
  elif fault=='runtime-ABI-status':next(r for r in rows if r['case']=='ABI/zero-width')['status']=0
  elif fault=='runtime-query-size':next(r for r in rows if r['case']=='query/zero-width')['size_after']=0
  elif fault=='runtime-exception-type':next(r for r in rows if r['case']=='python/rank-two')['exception_type']='RuntimeError'
  elif fault=='runtime-storage':
   row=next(r for r in rows if r['case']=='rejected-output-preserved');file=dest/'outputs'/row['case']/'buffer.bin';a=bytearray(file.read_bytes());a[0]^=1;file.write_bytes(a);row['files']['buffer.bin']=ledger(file)
  elif fault=='runtime-wrong-input':
   row=next(r for r in rows if r['case']=='stream-a');file=dest/'outputs/stream-a/input.bin';a=bytearray(file.read_bytes());a[0]^=1;file.write_bytes(a);row['files']['input.bin']=ledger(file)
  else:(dest/'trace').mkdir();r['trace']=str((dest/'trace').relative_to(ROOT))
  write(dest/'outputs/results.json',rows)
  try:v=runtime_validate(r,trace)
  except Exception as error:v=dict(status='FAILED',error=repr(error))
  outcome(fault,v)
 for fault in CPP_FAULTS:
  r=json.loads((ROOT/'migration/reports/canny-color-cpp-runtime.json').read_text());dest=e.path/fault;shutil.copytree(ROOT/r['outputs'],dest/'outputs');r['outputs']=str((dest/'outputs').relative_to(ROOT));v=json.loads((dest/'outputs/checks.json').read_text())
  if fault=='cpp-missing-case':v['checks'].pop()
  elif fault=='cpp-diagnostic':next(c for c in v['checks'] if c['case']=='invalid-low')['diagnostic']='unrelated loader failure'
  else:
   file=dest/'outputs/noncontiguous.bin';a=bytearray(file.read_bytes())
   if fault=='cpp-output-value':a[0]^=255
   else:a+=b'\0'
   file.write_bytes(a)
  write(dest/'outputs/checks.json',v);outcome(fault,cpp_validate(r))
 originals=json.loads((ROOT/'migration/reports/canny-color-originals.json').read_text())
 for fault in ORIGINAL_FAULTS:
  dest=e.path/fault;dest.mkdir();runs=copy.deepcopy(originals);target=next(r for r in runs if r['case']=='constant-zero' and r['language']=='cpp');shutil.copytree(ROOT/target['outputs'],dest/'outputs');shutil.copytree(ROOT/target['audit'],dest/'audit');target['outputs']=str((dest/'outputs').relative_to(ROOT));target['audit']=str((dest/'audit').relative_to(ROOT))
  if fault=='original-missing-entry':runs.pop()
  elif fault=='original-duplicate-entry':runs.append(copy.deepcopy(runs[0]))
  elif fault=='original-nonzero':target['return_code']=1
  elif fault=='original-short-loops':
   metadata=json.loads((dest/'audit/workflow.json').read_text());metadata['iterations']=9;write(dest/'audit/workflow.json',metadata)
  elif fault=='original-missing-PNG':(dest/'outputs/edges_npp.png').unlink()
  elif fault=='original-wrong-PNG':cv2.imwrite(str(dest/'outputs/edges_npp.png'),np.full((67,91),255,np.uint8))
  elif fault=='original-wrong-input':
   file=dest/'audit/input.bin';a=bytearray(file.read_bytes());a[0]^=1;file.write_bytes(a)
  outcome(fault,validate_originals(runs,spec))
 result=dict(status='PASSED' if len(checks)==len(names) and all(c['passed'] for c in checks) else 'FAILED',checks=checks,case_count=len(checks));write(e.path/'checks.json',result);result['evidence']=e.finish('PASSED' if result['status']=='PASSED' else 'SELF_TEST_FAILED',result);write(ROOT/'migration/reports/canny-color-checks.json',result);record('I1',f'C3验收器{len(checks)}项完整像素/ABI/stream/文件流程正反向检查：'+result['status']+'；允许明确算法变体的native差异，但结构/字节/输入/失败码均严格。',[result['evidence']]);print(result['status'],[c for c in checks if not c['passed']]);return int(result['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
