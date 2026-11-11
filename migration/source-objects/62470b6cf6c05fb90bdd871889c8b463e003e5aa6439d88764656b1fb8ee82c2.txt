#!/usr/bin/env python3
import json,shlex
from experiment import ROOT,Experiment,write,digest
def main():
 build=json.loads((ROOT/'migration/reports/rewrite-R9-helper-native-build.json').read_text());remote=build['remote'];profiles=[p for p in json.loads((ROOT/'migration/rewrite/helpers-benchmark.json').read_text())['helpers'] if p['language']=='cpp'];results=[]
 for p in profiles:
  e=Experiment('R9',p['sample_id'],'cuda-original',case='unmodified-original',sources=[__file__,ROOT/p['source']],parent=build['experiment_id']);binary=remote+'/original-'+p['kind'];cmd=['/usr/local/cuda-13.4/bin/nvcc','-x','cu','-std=c++17','-O2','-arch=sm_120',remote+'/'+p['source'],'-I'+remote+'/sdk/include','-L'+remote+'/sdk/lib','-Xlinker','-rpath='+remote+'/sdk/lib','-l:libcudss.so.1','-o',binary];rc=e.command(['ssh','nvidia-5090x2',shlex.join(cmd)],'unmodified-original-build',timeout=240)
  if rc==0:rc=e.command(['ssh','nvidia-5090x2',shlex.join(['env','CUDA_VISIBLE_DEVICES=0',binary])],'unmodified-original-execution')
  text=(e.path/e.commands[-1]['stdout']).read_text();valid=dict(status='PASSED' if rc==0 and 'PASSED' in text and 'FAILED' not in text else 'FAILED',checks=[dict(check='unmodified-native-original-assertions',passed=rc==0 and 'PASSED' in text and 'FAILED' not in text)]);r=dict(sample_id=p['sample_id'],return_code=rc,original_sha256=digest(ROOT/p['source']),status=valid['status']);r['evidence']=e.finish('PASSED' if valid['status']=='PASSED' else 'NATIVE_MISMATCH',valid);results.append(r);print(p['kind'],valid['status'])
 e=Experiment('R9','original-Fortran-toolchain-inventory','cuda-host',sources=[__file__]);rc=e.command(['ssh','nvidia-5090x2','for tool in nvfortran gfortran flang; do command -v "$tool" || true; done'],'native-Fortran-compiler-inventory');evidence=e.finish('OBSERVED' if rc==0 else 'SDK_UNAVAILABLE');write(ROOT/'migration/reports/rewrite-R9-helper-originals.json',dict(originals=results,Fortran_toolchain_evidence=evidence));return int(any(r['status']!='PASSED' for r in results))
if __name__=='__main__':raise SystemExit(main())
