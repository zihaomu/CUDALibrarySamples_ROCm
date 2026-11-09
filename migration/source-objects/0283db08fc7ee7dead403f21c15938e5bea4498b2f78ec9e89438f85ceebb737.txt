#!/usr/bin/env python3
"""Promote only original-profile BLAS CPU + unchanged CUDA observations."""
import collections,fcntl,json
from validate_blas import ROOT,observed,np
from run import digest
cpu=json.loads((ROOT/'migration/reports/blas-original-cpu.json').read_text());cuda={v['sample_id']:v for v in json.loads((ROOT/'migration/reports/original-cuda-latest.json').read_text())['results']};results=[]
with (ROOT/'migration/.state.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=ROOT/'migration/samples.yaml';cat=json.loads(p.read_text());rows={v['id']:v for v in cat['samples']}
 for c in cpu:
  if c['status']!='PASSED':continue
  s=rows[c['id']];a=s['original_port'];b=cuda.get(s['id']);r={'id':s['id'],'status':'PENDING','cpu_report':'migration/reports/blas-original-cpu.json','rocm_evidence':a['evidence']}
  if not b or b['return_code']!=0:r['reason']='CUDA baseline missing/failed'
  elif digest(ROOT/a['implementation'])!=a['implementation_sha256']:r['reason']='port changed since qualified run'
  elif not a.get('qualified_physical_devices'):r['reason']='physical device not qualified'
  else:
   ro=observed(ROOT/a['evidence']/'run.log');cu=observed(ROOT/b['evidence']/'run.log');checks=[]
   for x in c['checks']:
    n=x['buffer'];passed=n in cu and n in ro and ro[n].shape==cu[n].shape and np.allclose(ro[n],cu[n],atol=x['atol'],rtol=x['rtol']);checks.append({'buffer':n,'passed':bool(passed),'max_abs_error':float(np.max(abs(ro[n]-cu[n]))) if n in cu and n in ro and ro[n].shape==cu[n].shape else None})
   r.update(status='PASSED' if all(x['passed'] for x in checks) else 'FAILED',checks=checks,cuda_evidence=b['evidence'],source_sha256=s['source_sha256'],implementation_sha256=a['implementation_sha256'],scope='Original fixed teaching profile; independently parsed CPU BLAS mathematics + unmodified CUDA mathematical calls with observation-only output')
   if r['status']=='PASSED':
    # Preserve the richer M1 driver and its 95-case set.
    if not s.get('passed_cases'):
     s.update(status='PASSED',level='L4',actual_library='hipBLAS',backend_library='rocBLAS',required_cases=['original-fixed-input-cpu','original-fixed-input-cuda'],passed_cases=['original-fixed-input-cpu','original-fixed-input-cuda'],reason_code='VALIDATED_ORIGINAL_PROFILE',reason='使用 hipBLAS/rocBLAS 实现原始固定教学输入；结果逐缓冲区通过独立 NumPy 数学参考与原始 CUDA 对照。其它规模/精度/性能不在本例验收范围。',cuda_comparison='PASSED')
    s['original_profile_validation']=r;s['evidence'].append('migration/reports/blas-three-way.json')
  results.append(r)
 p.write_text(json.dumps(cat,indent=2,ensure_ascii=False)+'\n')
(ROOT/'migration/reports/blas-three-way.json').write_text(json.dumps(results,indent=2)+'\n');print(collections.Counter(v['status'] for v in results))
