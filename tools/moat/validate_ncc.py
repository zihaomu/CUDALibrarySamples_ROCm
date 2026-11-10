#!/usr/bin/env python3
"""Independently check both NCC backends, including correctly reproduced failures."""
import json,sys
from experiment import ROOT,Experiment,write,digest
results={}
for backend in ['rocm','cuda']:
 p=ROOT/f'migration/reports/rewrite-ncc-{backend}.json'
 if not p.exists():continue
 for case,r in json.loads(p.read_text()).items():
  e=Experiment('R3','NCC/'+case,'cpu-validation',sources=[__file__,ROOT/'tools/moat/ncc_reference.py'],parent=r['experiment_id'],comparison_id=r['input_manifest_sha256'])
  commands=json.loads((ROOT/r['evidence']/'commands.json').read_text());cmd=next(c for c in commands if c['phase'] in ['original-harness','native-original-harness']);log=ROOT/r['evidence']/cmd['stdout'];report=e.path/'cpu-report.json'
  rc=e.command([sys.executable,str(ROOT/'tools/moat/ncc_reference.py'),'--output',str(ROOT/r['output']),'--log',str(log),'--report',str(report)],'independent-FFT-and-file-oracle',timeout=120)
  v=json.loads(report.read_text()) if report.exists() else dict(status='FAILED',checks=[dict(check='oracle-executed',passed=False)])
  v.update(evidence=e.finish('PASSED' if rc==0 else 'NUMERIC_OR_HARNESS_MISMATCH',v),run=r,validation_source_sha256=digest(ROOT/'tools/moat/ncc_reference.py'));results[backend+'/'+case]=v;write(ROOT/'migration/reports/rewrite-ncc-validation.json',results);print(backend,case,v['status'],flush=True)
