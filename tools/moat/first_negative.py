#!/usr/bin/env python3
import argparse,json,shutil,sys
from pathlib import Path
from experiment import Experiment,ROOT,write,digest
from inputs import copy_run_inputs
from first_reference import validate,np
p=argparse.ArgumentParser();p.add_argument('--single',nargs=4,metavar=('KIND','CASE','OUTPUT','REPORT'));a=p.parse_args()
if a.single:
 kind,case,output,report=a.single;result=validate(kind,case,Path(output));write(report,result);print(json.dumps(result));raise SystemExit(0 if result['status']=='FAILED' else 1)
records=json.loads((ROOT/'migration/reports/rewrite-first-rocm.json').read_text());results=[]
tests=[(kind,'changed-values',mode) for kind in ['gemm3m','herk3m','syrk3m','planar','igemm','lu','posv','trsm'] for mode in ['numerical','contract']]
tests += [(kind,'layout','subtle-padding') for kind in ['gemm3m','herk3m','syrk3m','planar']]
tests += [(kind,'layout','subtle-triangle') for kind in ['herk3m','syrk3m']]
tests += [('planar','half-max','finite-half-maximum')]
tests += [('posv','nonspd-second-minor',mode) for mode in ['wrong-failure-minor','failed-RHS','failed-upper','failed-padding']]
for kind,case,mode in tests:
 original=records[kind+'/'+case]
 if True:
  e=Experiment('R1-R2-negative',kind+'/'+mode,'cpu-negative',sources=[Path(__file__),ROOT/'tools/moat/first_reference.py'],parent=original['experiment_id'])
  snapshot=copy_run_inputs(original,e.path/'inputs');cfg=json.loads((snapshot/'config.json').read_text())
  if validate(kind,case,ROOT/original['output'],inputs=snapshot)['status']!='PASSED':raise RuntimeError('negative test requires a passing unchanged baseline: '+kind+'/'+case)
  out=e.path/'outputs';shutil.copytree(ROOT/original['output'],out)
  if (out/'manifest.json').exists():(out/'manifest.json').rename(out/'manifest.before-injection.json')
  if mode=='numerical':
   dtype=np.float16 if kind=='planar' else np.int32 if kind=='igemm' else np.float32 if kind in ['gemm3m','herk3m','syrk3m','lu'] else np.float64
   path=out/'output.bin';data=np.fromfile(path,dtype);data[0]+=10;data.tofile(path)
  elif mode=='contract':
   name='packed_B' if kind=='igemm' else 'pivots' if kind=='lu' else 'info' if kind=='posv' else 'A_after' if kind=='trsm' else 'output' if kind=='planar' else 'trace'
   dtype=np.int8 if kind=='igemm' else np.int32 if kind in ['lu','posv','gemm3m','herk3m','syrk3m'] else np.float16 if kind=='planar' else np.float64
   path=out/(name+'.bin');data=np.fromfile(path,dtype);data[0]=np.inf if kind=='planar' else data[0]+1;data.tofile(path)
  elif mode.startswith('subtle'):
   path=out/'output.bin';dtype=np.float16 if kind=='planar' else np.complex64;data=np.fromfile(path,dtype);index=cfg['m'] if mode=='subtle-padding' else cfg['ldc'];data[index]+=np.float16(.0625) if kind=='planar' else .001 if mode=='subtle-padding' else 1e-7;data.tofile(path)
  elif mode=='finite-half-maximum':
   path=out/'output.bin';data=np.fromfile(path,np.float16);index=cfg['ldc']*cfg['n'];assert data[index]==65504;data[index]=0;data.tofile(path)
  else:
   name='info' if mode=='wrong-failure-minor' else 'output' if mode=='failed-RHS' else 'factor';dtype=np.int32 if name=='info' else np.complex128;path=out/(name+'.bin');data=np.fromfile(path,dtype);index=0 if mode in ['wrong-failure-minor','failed-RHS'] else cfg['lda'] if mode=='failed-upper' else cfg['n'];data[index]=999 if name=='info' else data[index]+.001;data.tofile(path)
  write(out/'manifest.json',dict(injection=mode,files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in out.glob('*.bin')}))
  report=e.path/'injected-check.json';rc=e.command([sys.executable,str(Path(__file__).resolve()),'--single',kind,case,str(out),str(report)],'reject-injected-error',timeout=90)
  check=dict(check='reject-'+kind+'-'+mode,passed=rc==0);evidence=e.finish('PASSED' if rc==0 else 'VALIDATOR_GAP',dict(checks=[check]),reason=None if rc==0 else 'corrupted output accepted')
  results.append(dict(**check,evidence=evidence));print(kind,mode,rc,flush=True)
write(ROOT/'migration/reports/rewrite-first-negative.json',dict(status='PASSED' if all(x['passed'] for x in results) else 'FAILED',checks=results))
