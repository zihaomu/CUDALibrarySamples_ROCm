#!/usr/bin/env python3
"""Corrupt returned metadata, alias identities, storage and lifetime observations."""
import json,shutil
from experiment import ROOT,Experiment,write,digest
from helper_reference import validate

def main():
 profiles=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'];runs=json.loads((ROOT/'migration/reports/rewrite-R9-helper-rocm.json').read_text());results=[]
 for p in profiles:
  run=next(r for r in runs if r['sample_id']==p['sample_id'] and r['case']=='original');input=ROOT/run['input_snapshot'];original=ROOT/run['output']
  for fault in ['metadata','device-bytes','lifetime']+(['shape-alias'] if p['kind']=='batch_sparse_matrix_helpers' else []):
   e=Experiment('R9',p['sample_id'],'CPU-negative',case=fault,sources=[__file__,ROOT/'tools/moat/helper_reference.py'],parent=run['experiment_id'],comparison_id=run['comparison_id']);shutil.copytree(input,e.path/'inputs');out=e.path/'outputs';shutil.copytree(original,out)
   name={'metadata':'r0_A3_meta.bin','device-bytes':'r0_A2_b0_values.bin','lifetime':'r0_lifetime.bin','shape-alias':'r0_aliases0.bin'}[fault];data=bytearray((out/name).read_bytes());data[0]^=1;(out/name).write_bytes(data);validation=validate(e.path/'inputs',out);valid=dict(status='PASSED' if validation['status']=='FAILED' else 'FAILED',checks=[dict(check='targeted-output-corruption-rejected',passed=validation['status']=='FAILED')],rejected_checks=[c['check'] for c in validation['checks'] if not c['passed']]);write(e.path/'rejection.json',valid)
   row=dict(sample_id=p['sample_id'],fault=fault,passed=valid['status']=='PASSED',parent_experiment_id=run['experiment_id'],input_manifest_sha256=run['input_manifest_sha256'],rejected_checks=valid['rejected_checks']);row['evidence']=e.finish('PASSED' if row['passed'] else 'SELF_TEST_FAILED',valid);results.append(row)
 write(ROOT/'migration/reports/rewrite-R9-helper-negative.json',dict(status='PASSED' if all(r['passed'] for r in results) else 'FAILED',checks=results));print('helper faults',len(results),sum(r['passed'] for r in results))
if __name__=='__main__':main()
