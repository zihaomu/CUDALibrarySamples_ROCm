#!/usr/bin/env python3
"""Trace complete per-cell CRC computation and independently replay the same bytes."""
import csv,json,shutil,os
from experiment import ROOT,Experiment,write,digest
from snapshot import capture
from crc_benchmark_reference import validate

def main():
 build=json.loads((ROOT/'migration/reports/rewrite-R9-crc-benchmark-build.json').read_text());src=ROOT/'tests/fixtures/rewrite-crc-benchmark/storage-small';case=json.loads((src/'case.json').read_text());mh=digest(src/'manifest.json');e=Experiment('R9','CRC32-benchmark-GPU-trace-and-repeat','rocm-profile',case='storage-small',sources=[__file__,ROOT/'tools/moat/crc_benchmark_reference.py']+[ROOT/n for n in build['dependencies']],parent=build['experiment_id'],comparison_id='crc32-benchmark/storage-small/'+mh);shutil.copytree(src,e.path/'inputs');observed=capture();observed['rocr_visible_devices']=os.environ.get('ROCR_VISIBLE_DEVICES');write(e.path/'backend.observed.json',observed);trace=e.path/'trace';trace.mkdir();validations=[];outputs=[];rc=0
 for phase in ['profile','repeat']:
  out=e.path/('outputs-'+phase);out.mkdir();outputs.append(out);env=dict(REWRITE_OUTPUT=str(out),REWRITE_BENCH_INPUT=str(e.path/'inputs/input.bin'));argv=[str(ROOT/build['binary'])]+case['argv']
  if phase=='profile':argv=['rocprofv3','--kernel-trace','--output-format','csv','json','--output-directory',str(trace),'--output-file','crc-benchmark','--']+argv
  actual=e.command(argv,'actual-'+phase,cwd=out,env=env,timeout=300);rc=rc or actual
  validation=validate(out,case) if actual==0 else dict(status='FAILED',checks=[dict(check='execution',passed=False)]);validations.append(validation);write(e.path/(phase+'-CPU-validation.json'),validation)
 rows=[]
 for path in trace.rglob('*kernel_trace.csv'):
  with path.open() as f:rows.extend(csv.DictReader(f))
 names=[r.get('Kernel_Name') or r.get('Name') or '' for r in rows];segments=[n for n in names if 'crc_benchmark::segments_kernel' in n];combine=[n for n in names if 'crc_benchmark::combine_kernel' in n];expected_segments=0;expected_combines=0
 if validations[0]['status']=='PASSED':
  for cell in validations[0]['cells']:
   size,count=cell['size'],cell['count'];selected=json.loads((outputs[0]/('cell_'+str(size)+'_'+str(count)+'_selected.json')).read_text())['segment'];expected_segments+=4
   expected_combines+=sum((((size+segment-1)//segment).bit_length()-1) for segment in [256,1024,4096,selected])
 checks=[dict(check='both-real-executions-and-CPU-validation',passed=rc==0 and all(v['status']=='PASSED' for v in validations)),dict(check='complete-segment-CRC-dispatches',passed=expected_segments>0 and len(segments)==expected_segments),dict(check='complete-GF2-search-and-final-reductions',passed=expected_combines>0 and len(combine)==expected_combines),dict(check='same-input-and-final-checksums-after-repeat',passed=validations[0].get('cells')==validations[1].get('cells') and (outputs[0]/'input.bin').read_bytes()==(outputs[1]/'input.bin').read_bytes())]
 summary=dict(binary_sha256=build['binary_sha256'],build_experiment_id=build['experiment_id'],input_manifest_sha256=mh,return_code=rc,segment_dispatches=len(segments),expected_segment_dispatches=expected_segments,combine_dispatches=len(combine),expected_combine_dispatches=expected_combines,kernel_names=names);write(e.path/'kernel-summary.json',summary);validation=dict(status='PASSED' if all(c['passed'] for c in checks) else 'FAILED',checks=checks);summary.update(status=validation['status'],checks=checks);summary['evidence']=e.finish('PASSED' if validation['status']=='PASSED' else 'PROFILER_FAILED',validation);write(ROOT/'migration/reports/rewrite-R9-crc-benchmark-trace.json',summary);print(validation['status'],len(segments),len(combine))
if __name__=='__main__':main()
