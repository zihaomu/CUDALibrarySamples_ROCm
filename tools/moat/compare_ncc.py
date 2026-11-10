#!/usr/bin/env python3
"""Compare actual native NPP and project HIP outputs; accept valid argmax ties."""
import json,sys
from experiment import ROOT,Experiment,write,digest
sys.path.insert(0,str(ROOT/'build/python-reference'));import numpy as np
rocm=json.loads((ROOT/'migration/reports/rewrite-ncc-rocm.json').read_text());cuda=json.loads((ROOT/'migration/reports/rewrite-ncc-cuda.json').read_text());results=[]
for case,a in rocm.items():
 b=cuda[case];e=Experiment('R3','NCC/'+case,'native-comparison',sources=[__file__],parent=a['experiment_id'],comparison_id=a['input_manifest_sha256']);checks=[]
 def gate(name,value,**fields):checks.append(dict(check=name,passed=bool(value),**fields))
 x=ROOT/a['output'];y=ROOT/b['output']
 for name in ['input.bin','template.bin']:gate('identical-'+name,digest(x/name)==digest(y/name))
 aa=np.fromfile(x/'scores.bin',np.float32).astype(np.float64);bb=np.fromfile(y/'scores.bin',np.float32).astype(np.float64);delta=np.abs(aa-bb);gate('full-native-NPP-score-agreement',aa.shape==bb.shape and np.isfinite(aa).all() and np.isfinite(bb).all() and np.all(delta<=2e-4),elements=int(aa.size),max_abs=float(delta.max(initial=0)),atol=2e-4)
 expected=1 if case.startswith('constant-') else 0;gate('original-harness-return-semantics',a['return_code']==b['return_code']==expected)
 validation=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks);validation.update(evidence=e.finish('PASSED' if validation['status']=='PASSED' else 'NATIVE_MISMATCH',validation),case=case,rocm=a,cuda=b);results.append(validation);write(ROOT/'migration/reports/rewrite-ncc-native-comparison.json',dict(status='PASSED' if all(r['status']=='PASSED' for r in results) else 'FAILED',cases=results));print(case,validation['status'],float(delta.max(initial=0)),flush=True)
