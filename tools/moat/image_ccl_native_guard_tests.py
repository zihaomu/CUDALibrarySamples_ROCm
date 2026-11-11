#!/usr/bin/env python3
"""Run actual original-runner rejection paths without issuing remote commands."""
import copy,json,types
from unittest.mock import patch
from experiment import ROOT,Experiment,write
import image_ccl_native_original_verify as runner
from image_progress import record

def main():
 e=Experiment('I2','CCL-native-original-preflight-negative-tests','CPU-selftest',sources=[__file__,ROOT/'tools/moat/image_ccl_native_original_verify.py',ROOT/'tools/moat/image_ccl_native.py',ROOT/'migration/rewrite/image-ccl-profile.json']);build_path=ROOT/'migration/reports/image-ccl-native-build.json';text=build_path.read_text();build=json.loads(text);ready_path=ROOT/'migration/reports/image-ccl-native-originals-preflight.json';before=ready_path.read_bytes();checks=[];children=[];original_write=runner.write
 for name in ['failed-original-build','missing-binary-identity','missing-original-branch']:
  fake=copy.deepcopy(build)
  if name=='failed-original-build':fake['status']='BUILD_ERROR';fake['originals'][0]['return_code']=1
  elif name=='missing-binary-identity':fake['identities'].pop(fake['originals'][0]['binary'])
  else:fake['originals'].pop()
  output=e.path/(name+'.json');seen=[]
  def load(value):return copy.deepcopy(fake) if value==text else json.loads(value)
  def save(path,value):
   path=type(ready_path)(path)
   if path==ready_path:seen.append(copy.deepcopy(value));return original_write(output,value)
   return original_write(path,value)
  # Only this runner's parser/report aliases are replaced. Experiment logging,
  # seals and its own JSON parser remain real and current.
  with patch.object(runner,'json',types.SimpleNamespace(loads=load)),patch.object(runner,'write',save),patch.object(runner,'record',lambda *args,**kwargs:None):rc=runner.main()
  valid=rc==1 and len(seen)==1 and seen[0]['status']=='REJECTED' and any(c['passed'] is False for c in seen[0]['checks']) and ready_path.read_bytes()==before
  children.append(seen[0]['evidence'] if seen else None);checks.append(dict(check=name,passed=valid))
 v=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',case_count=3,checks=checks,child_evidence=children);write(e.path/'checks.json',v);v['evidence']=e.finish('PASSED' if v['status']=='PASSED' else 'SELF_TEST_FAILED',dict(status=v['status'],checks=checks));write(ROOT/'migration/reports/image-ccl-native-guard-tests.json',v);record('I2','原生原例runner三项真实预检反向执行：失败build、缺binary身份、缺分支均先封存拒绝，不发远端命令、不创建逐例记录，原READY报告不修改。'+v['status'],[v['evidence'],*children]);print(v['status'],checks);return int(v['status']!='PASSED')
if __name__=='__main__':raise SystemExit(main())
