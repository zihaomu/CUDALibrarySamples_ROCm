#!/usr/bin/env python3
import argparse,json,shutil,sys
from pathlib import Path
from experiment import ROOT,Experiment,write
from inputs import copy_run_inputs
from svd_reference import validate,np
p=argparse.ArgumentParser();p.add_argument('--single',nargs=3);args=p.parse_args()
if args.single:
 inputs,out,report=args.single;v=validate(Path(inputs),Path(out));write(report,v);raise SystemExit(0 if v['status']=='FAILED' else 1)
records=json.loads((ROOT/'migration/reports/rewrite-extension-rocm.json').read_text());results=[]
for mode in ['singular-value','residual-norm','V-vector','info','stride-padding']:
 case='layout' if mode=='stride-padding' else 'original';run=records['svd/'+case];e=Experiment('R3','svd/'+mode,'cpu-negative',case=case,sources=[__file__,ROOT/'tools/moat/svd_reference.py',ROOT/'tools/moat/inputs.py'],parent=run['experiment_id'],comparison_id=run['comparison_id']);inputs=copy_run_inputs(run,e.path/'inputs');out=e.path/'outputs';shutil.copytree(ROOT/run['output'],out)
 if validate(inputs,out)['status']!='PASSED':raise RuntimeError('negative injection requires passing unchanged output')
 name='S' if mode=='singular-value' else 'RnrmF' if mode=='residual-norm' else 'info' if mode=='info' else 'U' if mode=='stride-padding' else 'V';dtype=np.float64 if name=='RnrmF' else np.int32 if name=='info' else np.float32;path=out/(name+'.bin');data=np.fromfile(path,dtype);index=json.loads((inputs/'config.json').read_text())['m'] if mode=='stride-padding' else 0;data[index]+=.001 if mode=='stride-padding' else 1;data.tofile(path)
 report=e.path/'rejected.json';rc=e.command([sys.executable,__file__,'--single',str(inputs),str(out),str(report)],'reject-'+mode);v=dict(checks=[dict(check=mode,passed=rc==0)]);evidence=e.finish('PASSED' if rc==0 else 'VALIDATOR_GAP',v);results.append(dict(mode=mode,case=case,passed=rc==0,evidence=evidence));print(mode,rc,flush=True)
write(ROOT/'migration/reports/rewrite-svd-negative.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',tests=results))
