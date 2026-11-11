#!/usr/bin/env python3
import argparse,json,shutil,os
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from qualification_common import fixture

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='*',default=[]);a=parser.parse_args();build=json.loads((ROOT/'migration/reports/rewrite-R9-crc-benchmark-build.json').read_text());cases=json.loads((ROOT/'migration/rewrite/crc-benchmark-cases.json').read_text());report=ROOT/'migration/reports/rewrite-R9-crc-benchmark-rocm.json';records=json.loads(report.read_text()) if report.exists() else {};observed=capture();observed['rocr_visible_devices']=os.environ.get('ROCR_VISIBLE_DEVICES')
 if build['status']!='BUILT' or any(digest(ROOT/n)!=h for n,h in build['dependencies'].items()) or digest(ROOT/build['binary'])!=build['binary_sha256']:raise RuntimeError('stale/unavailable benchmark binary')
 for case in cases:
  if a.only and case['case'] not in a.only:continue
  src=ROOT/'tests/fixtures/rewrite-crc-benchmark'/case['case'];fixture(src,kind='crc32-benchmark');mh=digest(src/'manifest.json');e=Experiment('R9','nvCOMP/benchmarks::benchmark_crc32.cpp','rocm-benchmark',case=case['case'],sources=[__file__,ROOT/'tools/moat/crc_benchmark_reference.py']+[ROOT/n for n in build['dependencies']],parent=build['experiment_id'],comparison_id='crc32-benchmark/'+case['case']+'/'+mh);shutil.copytree(src,e.path/'inputs');out=e.path/'outputs';out.mkdir();write(e.path/'backend.observed.json',observed);env=dict(REWRITE_OUTPUT=str(out))
  if case['storage']:env['REWRITE_BENCH_INPUT']=str(e.path/'inputs/input.bin')
  rc=e.command([str(ROOT/build['binary'])]+case['argv'],'original-benchmark-CLI',cwd=out,env=env,timeout=900);cpu=1
  if rc==0:cpu=e.command(['python3',str(ROOT/'tools/moat/crc_benchmark_reference.py'),'--output',str(out),'--case',str(e.path/'inputs/case.json'),'--report',str(e.path/'cpu-validation.json')],'independent-zlib-grid-CSV-validation',timeout=600)
  valid=json.loads((e.path/'cpu-validation.json').read_text()) if (e.path/'cpu-validation.json').exists() else dict(status='FAILED',checks=[dict(check='CPU-validator-completed',passed=False)])
  ok=rc==0 and cpu==0 and valid['status']=='PASSED'
  row=dict(case=case['case'],return_code=rc,cpu_return_code=cpu,status='PASSED' if ok else 'FAILED',validation=valid,input_manifest_sha256=mh,output=str(out.relative_to(ROOT)),input_snapshot=str((e.path/'inputs').relative_to(ROOT)),experiment_id=e.id,comparison_id=e.meta['comparison_id'],build=build);write(e.path/'case-result.json',row);row['evidence']=e.finish('PASSED' if ok else 'NUMERIC_OR_HARNESS_MISMATCH',valid);records[case['case']]=row;write(report,records);print(case['case'],row['status'],valid.get('valid_cells'),flush=True)
 return int(any(r['status']!='PASSED' for r in records.values()))
if __name__=='__main__':raise SystemExit(main())
