#!/usr/bin/env python3
import ctypes,ctypes.util,json,struct,shutil,csv,copy
from pathlib import Path
from experiment import ROOT,Experiment,write
from snapshot import capture
from crc_benchmark_reference import validate

def main():
 build=json.loads((ROOT/'migration/reports/rewrite-R9-crc-benchmark-build.json').read_text());runs=json.loads((ROOT/'migration/reports/rewrite-R9-crc-benchmark-rocm.json').read_text());run=runs['complete-small'];case=json.loads((ROOT/run['input_snapshot']/'case.json').read_text());results=[];observed=capture()
 for fault in ['CRC-value','candidate-value','CSV-negative-infinity','CSV-skipped-active','timing-zero','selected-not-minimum','missing-cell']:
  e=Experiment('R9','CRC32-benchmark-output-negative','CPU-negative',case=fault,sources=[__file__,ROOT/'tools/moat/crc_benchmark_reference.py'],parent=run['experiment_id'],comparison_id=run['comparison_id']);out=e.path/'outputs';shutil.copytree(ROOT/run['output'],out);prefix='cell_1024_1'
  if fault in ['CRC-value','candidate-value']:
   p=out/(prefix+('_final.bin' if fault=='CRC-value' else '_segment256.bin'));data=bytearray(p.read_bytes());data[0]^=1;p.write_bytes(data)
  elif fault.startswith('CSV'):
   p=out/case['csv'];rows=list(csv.reader(p.open()));rows[1][1]='-inf' if fault.endswith('infinity') else '-1'
   with p.open('w',newline='') as f:csv.writer(f).writerows(rows)
  elif fault=='timing-zero':
   p=out/(prefix+'_timing.json');data=json.loads(p.read_text());data['elapsed_ms']=0;write(p,data)
  elif fault=='selected-not-minimum':
   search=[json.loads(line) for line in (out/'search.jsonl').read_text().splitlines()];candidates=[r for r in search if r['size']==1024 and r['count']==1];worst=max(candidates,key=lambda r:r['elapsed_ms']);write(out/(prefix+'_selected.json'),dict(segment=worst['segment'],threads=worst['threads']))
   # Force a strict nonminimum even if the original timing values tied.
   worst['elapsed_ms']=max(r['elapsed_ms'] for r in candidates)+1;(out/'search.jsonl').write_text('\n'.join(json.dumps(r) for r in search)+'\n')
  else:(out/(prefix+'_final.bin')).unlink()
  try:validation=validate(out,case);rejected=validation['status']=='FAILED';reason=[c['check'] for c in validation['checks'] if not c['passed']]
  except (OSError,ValueError,KeyError,IndexError) as error:rejected=True;reason=[type(error).__name__+': '+str(error)]
  valid=dict(status='PASSED' if rejected else 'FAILED',checks=[dict(check='corrupted-benchmark-rejected',passed=rejected)],reason=reason);row=dict(fault=fault,passed=rejected);write(e.path/'rejection.json',valid);row['evidence']=e.finish('PASSED' if rejected else 'SELF_TEST_FAILED',valid);results.append(row)
 runtime=[]
 for name,args,expected in [('help',['-h'],0),('unknown',['--unknown'],1),('missing-output',['-o'],1),('missing-storage',['-s'],1),('not-power-two',['-s','3'],1),('empty-table',['-s','1'],1),('over-capacity',['-s',str(1<<62)],1),('unwritable-CSV',['-s','32768','-o','/no-such-directory/out.csv'],1)]:
  e=Experiment('R9','CRC32-benchmark-runtime','rocm-runtime',case=name,sources=[__file__]+[ROOT/n for n in build['dependencies']],parent=build['experiment_id']);out=e.path/'outputs';out.mkdir();write(e.path/'backend.observed.json',observed);rc=e.command([str(ROOT/build['binary'])]+args,'actual-original-CLI',cwd=out,env=dict(REWRITE_OUTPUT=str(out)),timeout=180);diagnostics={'help':'','unknown':'unknown argument','missing-output':'missing value for -o','missing-storage':'missing value for -s','not-power-two':'must be a power of two','empty-table':'cannot contain a minimum-sized buffer','over-capacity':'exceeds available GPU memory','unwritable-CSV':'Failed to open output file'};stderr=(e.path/e.commands[-1]['stderr']).read_text();passed=rc==expected and diagnostics[name] in stderr;valid=dict(status='PASSED' if passed else 'FAILED',checks=[dict(check='actual-CLI-contract',passed=passed)]);row=dict(case=name,argv=args,return_code=rc,passed=passed);row['evidence']=e.finish('PASSED' if passed and expected==0 else 'EXPECTED_REJECTION' if passed else 'SELF_TEST_FAILED',valid);runtime.append(row)
 source=ROOT/'rocm/probes/crc_benchmark_lengths.cpp';e=Experiment('R9','CRC32-64bit-combine-boundary','rocm-probe',sources=[__file__,source]+[ROOT/n for n in build['dependencies']],parent=build['experiment_id']);write(e.path/'backend.observed.json',observed);core=Path('/opt/venv/lib/python3.13/site-packages/_rocm_sdk_core');binary=e.path/'probe';out=e.path/'outputs';out.mkdir();cmd=['hipcc','--rocm-path='+str(ROOT/'build/rocm-sdk-overlay'),'--hip-path='+str(ROOT/'build/rocm-sdk-overlay'),'--rocm-device-lib-path='+str(core/'lib/llvm/amdgcn/bitcode'),'--offload-arch=gfx1201','-std=c++17','-O2','-D__HIP_PLATFORM_AMD__','-I'+str(ROOT/'rocm/backends/codec'),'-I/opt/rocm/core-10.1/include','-x','hip',str(source),'-o',str(binary)]
 rc=e.command(cmd,'64bit-boundary-build');rc=rc or e.command([str(binary)],'actual-GPU-combine-for-large-lengths',env=dict(REWRITE_OUTPUT=str(out)));checks=[]
 if rc==0:
  lib=ctypes.CDLL(ctypes.util.find_library('z'));combine=lib.crc32_combine64;combine.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_int64];combine.restype=ctypes.c_ulong;raw=(out/'lengths.bin').read_bytes();data=struct.unpack('<'+str(len(raw)//8)+'Q',raw)
  for i in range(0,len(data),4):length,left,right,actual=data[i:i+4];checks.append(dict(check='GPU-vs-independent-libz-length-'+str(length),passed=actual==(combine(left,right,length)&0xffffffff)))
 valid=dict(status='PASSED' if len(checks)==6 and all(c['passed'] for c in checks) and rc==0 else 'FAILED',checks=checks or [dict(check='probe-executed',passed=False)]);boundary=dict(**valid,evidence=e.finish('PASSED' if valid['status']=='PASSED' else 'PROBE_FAILED',valid));write(ROOT/'migration/reports/rewrite-R9-crc-benchmark-checks.json',dict(status='PASSED' if all(r['passed'] for r in results+runtime) and boundary['status']=='PASSED' else 'FAILED',negative=results,runtime=runtime,boundary=boundary));print('CRC',len(results),'faults',len(runtime),'CLI',boundary['status'])
if __name__=='__main__':main()
