#!/usr/bin/env python3
import argparse,json,sys
from experiment import ROOT,Experiment,write,digest
from inputs import copy_run_inputs
p=argparse.ArgumentParser();p.add_argument('--backend',default='rocm');args=p.parse_args();records=json.loads((ROOT/f'migration/reports/rewrite-extension-{args.backend}.json').read_text());dest=ROOT/f'migration/reports/rewrite-extension-{args.backend}-validation.json';results={}
for key,r in records.items():
 oracle=ROOT/'tools/moat/svd_reference.py';e=Experiment('R3',key,'cpu-validation',sources=[__file__,oracle,ROOT/'tools/moat/inputs.py'],parent=r['experiment_id'],comparison_id=r['comparison_id']);snapshot=copy_run_inputs(r,e.path/'inputs');report=e.path/'cpu-report.json';rc=e.command([sys.executable,str(oracle),'--input',str(snapshot),'--output',str(ROOT/r['output']),'--report',str(report)],'independent-reference');v=json.loads(report.read_text()) if report.exists() else dict(status='FAILED',checks=[dict(check='oracle-ran',passed=False)])
 v.update(evidence=e.finish('PASSED' if rc==0 else 'NUMERIC_MISMATCH',v),run=r,validation_source_sha256=digest(oracle));results[key]=v;write(dest,results);print(key,v['status'],[c['check'] for c in v['checks'] if not c['passed']],flush=True)
