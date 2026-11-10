#!/usr/bin/env python3
import json,shlex,sys
from pathlib import Path
from experiment import Experiment,ROOT,write
sys.path.insert(0,str(ROOT/'build/python-reference'))
import numpy as np
e=Experiment('P0','cuBLAS/Level-3/gemm-existing-profile','three-way',sources=[ROOT/'rocm/cuBLAS/Level-3/gemm/sample.cpp',ROOT/'tools/moat/p0_native_gemm.cu',Path(__file__)])
rc=e.command(['/home/zihaomu/zihaomu_workspace/rocm10-launch.sh','python','tools/moat/m1_trial_inner.py','--output',str(e.path/'backend.observed.json')],'existing-AMD-M1',env={'HIP_VISIBLE_DEVICES':'2'},timeout=120)
remote='/tmp/'+e.id;host='nvidia-5090x2'
commands=[(['ssh',host,shlex.join(['mkdir','-p',remote])],'prepare-CUDA'),(['scp',str(ROOT/'tools/moat/p0_native_gemm.cu'),host+':'+remote+'/probe.cu'],'upload-CUDA'),(['ssh',host,shlex.join(['/usr/local/cuda-13.4/bin/nvcc',remote+'/probe.cu','-lcublas','-o',remote+'/probe'])],'build-CUDA'),(['ssh',host,remote+'/probe'],'run-CUDA')]
codes=[rc]
for cmd,phase in commands:codes.append(e.command(cmd,phase,timeout=120))
def original(record):
 for line in (e.path/record['stdout']).read_text().splitlines():
  try:r=json.loads(line)
  except ValueError:continue
  if r.get('case')=='original_profile':return np.asarray(r['values'])
 raise ValueError('missing original output')
expected=(np.array([[1,2],[3,4]])@np.array([[5,6],[7,8]])).ravel(order='F')
checks=[dict(check='all-real-processes-succeeded',passed=all(x==0 for x in codes)),dict(check='independent-CPU-AMD',passed=np.array_equal(original(e.commands[0]),expected)),dict(check='independent-CPU-CUDA',passed=np.array_equal(original(e.commands[-1]),expected))]
write(e.path/'cpu-reference.json',dict(A=[1,3,2,4],B=[5,7,6,8],expected=expected.tolist()))
validation=dict(status='PASSED' if all(x['passed'] for x in checks) else 'FAILED',checks=checks)
evidence=e.finish(validation['status'],validation);write(ROOT/'migration/reports/rewrite-p0-trial.json',dict(**validation,evidence=evidence));print(evidence)
