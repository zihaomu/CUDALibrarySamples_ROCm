#!/usr/bin/env python3
import json,sys,argparse,shutil
from experiment import ROOT,Experiment,write,digest
p=argparse.ArgumentParser();p.add_argument('--backend',default='rocm');args=p.parse_args();records=json.loads((ROOT/f'migration/reports/rewrite-crc32-{args.backend}.json').read_text());results={}
for case,r in records.items():
 e=Experiment('R4','nvCOMP/examples::nvcomp_crc32.cu','cpu-validation',case=case,sources=[__file__,ROOT/'tools/moat/crc32_reference.py'],parent=r['experiment_id'],comparison_id='crc32/'+case+'/'+r['input_manifest_sha256']);src=e.path/'inputs';shutil.copytree(ROOT/r['input_snapshot'],src)
 if digest(src/'manifest.json')!=r['input_manifest_sha256']:raise RuntimeError('CRC input identity mismatch')
 report=e.path/'cpu-report.json';command=[sys.executable,str(ROOT/'tools/moat/crc32_reference.py'),'--input',str(src),'--output',str(ROOT/r['output']),'--report',str(report)]
 if json.loads((src/'manifest.json').read_text())['expected_run_outcome']=='ZERO_CHUNKS_REJECTED':write(e.path/'run-record.json',r);command+=['--run-record',str(e.path/'run-record.json')]
 rc=e.command(command,'independent-zlib-or-explicit-rejection');v=json.loads(report.read_text()) if report.exists() else dict(status='FAILED',checks=[dict(check='oracle-ran',passed=False)]);v.update(evidence=e.finish('PASSED' if rc==0 else 'NUMERIC_OR_HARNESS_MISMATCH',v),run=r,validation_source_sha256=digest(ROOT/'tools/moat/crc32_reference.py'));results[case]=v;write(ROOT/f'migration/reports/rewrite-crc32-{args.backend}-validation.json',results);print(args.backend,case,v['status'],flush=True)
