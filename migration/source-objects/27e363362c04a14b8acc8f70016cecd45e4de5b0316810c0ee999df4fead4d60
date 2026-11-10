#!/usr/bin/env python3
import argparse,json,sys
from experiment import ROOT,Experiment,write,digest
from inputs import copy_run_inputs
p=argparse.ArgumentParser();p.add_argument('--backend',default='rocm');a=p.parse_args();records=json.loads((ROOT/'migration/reports'/('rewrite-extension-rocm.json' if a.backend=='rocm' else 'rewrite-sparse24-cuda.json')).read_text());results={}
for key,run in records.items():
 if run['kind'] not in ['sparse24','sparse24_advanced']:continue
 e=Experiment('R7',run.get('sample_id',run['kind']),'cpu-validation',case=run['case'],sources=[__file__,ROOT/'tools/moat/sparse24_reference.py',ROOT/'tools/moat/inputs.py'],parent=run['experiment_id'],comparison_id=run['comparison_id']);src=copy_run_inputs(run,e.path/'inputs');report=e.path/'reference.json';rc=e.command([sys.executable,str(ROOT/'tools/moat/sparse24_reference.py'),'--input',str(src),'--output',str(ROOT/run['output']),'--report',str(report),'--backend',a.backend],'independent-capacity-DP-and-FP64');r=json.loads(report.read_text());r['checks'].append(dict(check='process-success',passed=run['return_code']==0));r['status']='PASSED' if all(c['passed'] for c in r['checks']) else 'FAILED';r.update(run=run,validation_source_sha256=digest(ROOT/'tools/moat/sparse24_reference.py'));r['evidence']=e.finish('PASSED' if r['status']=='PASSED' else 'NUMERIC_MISMATCH',r);results[key]=r;write(ROOT/f'migration/reports/rewrite-sparse24-{a.backend}-validation.json',results);print(key,r['status'],[c['check'] for c in r['checks'] if not c['passed']],flush=True)
