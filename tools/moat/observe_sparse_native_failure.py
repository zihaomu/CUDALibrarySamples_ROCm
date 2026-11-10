#!/usr/bin/env python3
"""Record a native numerical failure as an observation, never a passing baseline."""
import argparse,json,shutil,sys
from experiment import ROOT,Experiment,write
from qualification_common import fixture
def observe(src,out):
 import numpy as np
 from pathlib import Path
 src=Path(src);out=Path(out);mf=fixture(src,kind='sparse-binding',case='singular-info');s=mf['systems'][0];n=s['n'];nrhs=s['nrhs'];ldx=s['ldx'];ldb=s['ldb'];base=s['base'];checks=[]
 def check(name,value):checks.append(dict(check=name,passed=bool(value)))
 def read(root,name,dtype,count):
  p=root/name
  if p.stat().st_size!=count*np.dtype(dtype).itemsize:raise ValueError('whole file bytes '+name)
  return np.fromfile(p,dtype=dtype)
 rows=read(src,'b0_rows.bin','<i4',n+1)-base;cols=read(src,'b0_columns.bin','<i4',s['nnz'])-base;values=read(src,'b0_values.bin','<f8',s['nnz']);a=np.zeros((n,n))
 for i in range(n):a[i,cols[rows[i]:rows[i+1]]]=values[rows[i]:rows[i+1]]
 x=read(out,'b0_solution.bin','<f8',nrhs*ldx).reshape(nrhs,ldx);initial=read(src,'b0_X.bin','<f8',nrhs*ldx).reshape(nrhs,ldx)
 check('frozen-GENERAL-singular-input',mf['profile']=='residual' and s['mtype']==0 and np.linalg.matrix_rank(a)<n);check('native-info-zero-observed',read(out,'b0_info.bin','<i4',1)[0]==0);check('native-factor-and-solve-executed',np.array_equal(read(out,'b0_phase.bin','<i4',4),[0,1,2,3]));check('native-nonfinite-active-solution-observed',np.any(~np.isfinite(x[:,:n])));check('native-padding-preserved',np.array_equal(x[:,n:],initial[:,n:]));check('native-RHS-preserved',np.array_equal(read(out,'b0_B_after.bin','<f8',nrhs*ldb),read(src,'b0_B.bin','<f8',nrhs*ldb)))
 return dict(status='OBSERVED_NATIVE_NUMERIC_FAILURE',observation_valid=all(c['passed'] for c in checks),numeric_baseline_passed=False,checks=checks,nonfinite_active_count=int(np.sum(~np.isfinite(x[:,:n]))),reason='After explicit factor completion synchronization the locked native SDK still returned INFO=0 and nonfinite active X. Observed numerical failure; internal cause is not inferred. HIP rejects the singular input with INFO>0. This extra negative input is not a three-way passing numerical case.')
p=argparse.ArgumentParser();p.add_argument('--single',nargs=3);args=p.parse_args()
if args.single:
 r=observe(args.single[0],args.single[1]);write(args.single[2],r);raise SystemExit(not r['observation_valid'])
run=json.loads((ROOT/'migration/reports/rewrite-sparse-binding-cuda.json').read_text())['residual/singular-info'];e=Experiment('R5',run['sample_id'],'cpu-native-failure-observation',case=run['case'],sources=[__file__,ROOT/'tools/moat/cuda_sparse_binding_reference.cu'],parent=run['experiment_id'],comparison_id=run['comparison_id']);shutil.copytree(ROOT/run['input_snapshot'],e.path/'inputs');report=e.path/'observation.json';rc=e.command([sys.executable,__file__,'--single',str(e.path/'inputs'),str(ROOT/run['output']),str(report)],'verify-native-numerical-failure');r=json.loads(report.read_text());r.update(run=run);r['evidence']=e.finish('OBSERVED' if rc==0 else 'VALIDATOR_GAP',r);write(ROOT/'migration/reports/rewrite-sparse-native-failure.json',r);print(r['status'],r['observation_valid'])
