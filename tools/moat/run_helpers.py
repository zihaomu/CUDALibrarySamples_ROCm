#!/usr/bin/env python3
import json,shutil
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from helper_reference import validate

def main():
 spec=json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'];build=json.loads((ROOT/'migration/reports/rewrite-R9-helper-build.json').read_text());observed=capture();records=[]
 if build['status']!='BUILT' or any(digest(ROOT/n)!=sha for n,sha in build['dependencies'].items()) or digest(ROOT/build['shared_library'])!=build['shared_library_sha256']:raise RuntimeError('unavailable/stale helper build')
 for p in spec:
  binary=next(b for b in build['binaries'] if b['sample_id']==p['sample_id'])
  if digest(ROOT/binary['binary'])!=binary['binary_sha256']:raise RuntimeError('binary identity')
  for case in p['cases']:
   src=ROOT/'tests/fixtures/rewrite-helpers'/p['language']/p['kind']/case;mh=digest(src/'manifest.json');e=Experiment('R9',p['sample_id'],'rocm-helper',case=case,sources=[__file__,ROOT/'tools/moat/helper_reference.py']+[ROOT/n for n in build['dependencies']],parent=build['experiment_id'],comparison_id=p['sample_id']+'/'+case+'/'+mh);shutil.copytree(src,e.path/'inputs');out=e.path/'outputs';out.mkdir();write(e.path/'backend.observed.json',observed)
   rc=e.command([str(ROOT/binary['binary'])],'actual-'+p['language']+'-caller',env=dict(REWRITE_INPUT=str(e.path/'inputs'),REWRITE_OUTPUT=str(out)))
   valid=validate(e.path/'inputs',out) if rc==0 else dict(status='FAILED',checks=[dict(check='actual-entry-exit',passed=False)])
   result=dict(sample_id=p['sample_id'],kind=p['kind'],language=p['language'],case=case,return_code=rc,input_manifest_sha256=mh,input_snapshot=str((e.path/'inputs').relative_to(ROOT)),output=str(out.relative_to(ROOT)),build=build,experiment_id=e.id,comparison_id=e.meta['comparison_id'],status=valid['status'],checks=valid['checks']);write(e.path/'case-result.json',result)
   result['evidence']=e.finish('PASSED' if rc==0 and valid['status']=='PASSED' else 'NUMERIC_OR_HARNESS_MISMATCH',valid);records.append(result);write(ROOT/'migration/reports/rewrite-R9-helper-rocm.json',records);print(p['language'],p['kind'],case,result['status'],flush=True)
 return int(any(r['status']!='PASSED' for r in records))
if __name__=='__main__':raise SystemExit(main())
