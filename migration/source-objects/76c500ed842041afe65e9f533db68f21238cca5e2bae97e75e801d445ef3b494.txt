#!/usr/bin/env python3
"""Validate captured original device outputs against CPU and the same-input HIP run."""
import json,sys
from pathlib import Path
from experiment import Experiment,ROOT,write,digest
from inputs import copy_run_inputs
from first_reference import np

native=json.loads((ROOT/'migration/reports/rewrite-native-mathdx.json').read_text())
amd=json.loads((ROOT/'migration/reports/rewrite-first-rocm.json').read_text());results={}
for kind,r in native.items():
    run=amd[kind+'/original'];e=Experiment('R2',kind+'/original-native-comparison','cpu-native-validation',sources=[__file__,ROOT/'tools/moat/first_reference.py',ROOT/'tools/moat/inputs.py'],parent=r['experiment_id'],comparison_id=run['comparison_id'])
    inputs=copy_run_inputs(run,e.path/'inputs');out=ROOT/r['output'];checks=[]
    for name in ['A','B']:
        if (inputs/(name+'.bin')).exists():checks.append(dict(check='native-HIP-input-identical-'+name,passed=digest(inputs/(name+'.bin'))==digest(out/('input_'+name+'.bin'))))
    report=e.path/'independent-native-cpu.json'
    rc=e.command([sys.executable,str(ROOT/'tools/moat/first_reference.py'),'--kind',kind,'--case','original','--output',str(out),'--input',str(inputs),'--backend','cuda-native','--report',str(report)],'independent-native-cpu')
    checks.append(dict(check='native-independent-CPU',passed=rc==0))
    files=['output','pivots','info'] if kind=='lu' else ['output','factor','info'] if kind=='posv' else ['output','A_after']
    for name in files:
        dtype=np.int32 if name in ['pivots','info'] else np.complex64 if kind=='lu' else np.complex128 if kind=='posv' else np.float64
        x=np.fromfile(out/(name+'.bin'),dtype);y=np.fromfile(ROOT/run['output']/(name+'.bin'),dtype)
        exact=name in ['pivots','info'];rtol=1e-4 if kind=='lu' else 5e-12;atol=2e-5 if kind=='lu' else 2e-12
        checks.append(dict(check='native-versus-HIP-'+name,passed=x.shape==y.shape and bool(np.array_equal(x,y) if exact else np.allclose(x,y,rtol=rtol,atol=atol)),max_abs=float(np.max(np.abs(x-y),initial=0)),rtol=0 if exact else rtol,atol=0 if exact else atol))
    validation=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks)
    evidence=e.finish('PASSED' if validation['status']=='PASSED' else 'NUMERIC_MISMATCH',validation)
    results[kind]=dict(**validation,evidence=evidence,native=r,rocm=run,experiment_id=e.id);write(ROOT/'migration/reports/rewrite-native-mathdx-validation.json',results)
    print(kind,validation['status'],flush=True)
