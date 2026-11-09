#!/usr/bin/env python3
"""Check original 4x4 FP32 and half batched Lt profiles with CPU GEMM."""
import fcntl,json
from validate_blas import ROOT,np,observed
from run import digest
results=[]
with (ROOT/'migration/.state.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text())
 for s in cat['samples']:
  if s['source'] not in {'cuBLASLt/LtSgemm/main.cpp','cuBLASLt/LtHSHgemmPointerArrayBatchSimple/main.cpp','cuBLASLt/LtHSHgemmStridedBatchSimple/main.cpp'}:continue
  a=s['original_port']
  if a['return_code']!=0 or digest(ROOT/a['implementation'])!=a['implementation_sha256']:continue
  o=observed(ROOT/a['evidence']/'run.log');half='HSH' in s['source'];batches=2 if half else 1;actual=o.get('D',o['C']);expected=[]
  for batch in range(batches):
   A=o['A'][batch*16:batch*16+16].reshape((4,4),order='F');B=o['B'][batch*16:batch*16+16].reshape((4,4),order='F');C=2*(A@B);expected.extend((C.astype(np.float16).astype(float) if half else C.astype(np.float32)).flatten(order='F'))
  expected=np.asarray(expected);err=float(np.max(abs(actual-expected)));passed=bool(np.all(np.isfinite(actual)) and np.allclose(actual,expected,atol=1e-5,rtol=1e-5));r={'id':s['id'],'status':'PASSED' if passed else 'FAILED','max_abs_error':err,'atol':1e-5,'rtol':1e-5,'oracle':'NumPy independent FP32 GEMM, explicit half output rounding for HSH profiles','profile':{'m':4,'n':4,'k':4,'batches':batches,'alpha':2,'beta':0},'evidence':a['evidence'],'implementation_sha256':a['implementation_sha256'],'source_sha256':s['source_sha256']};results.append(r)
  if passed and not s.get('passed_cases'):s.update(status='PASSED',level='L4',actual_library='hipBLASLt',backend_library='hipBLASLt',required_cases=['original-fixed-input-cpu-gemm'],passed_cases=['original-fixed-input-cpu-gemm'],reason_code='VALIDATED_ORIGINAL_PROFILE',reason='使用 hipBLASLt 保留原始 4×4 profile、alpha/beta 与 FP16 input/output + FP32 compute（HSH）或 FP32（SGEMM）及 batch 存储方式；完整输出通过独立 NumPy GEMM 与显式 half 舍入检查。')
  s['original_profile_validation']=r;s['evidence'].append('migration/reports/blaslt-original-validation.json')
 p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
(ROOT/'migration/reports/blaslt-original-validation.json').write_text(json.dumps(results,indent=2)+'\n');print([(r['id'],r['status'],r['max_abs_error']) for r in results])
